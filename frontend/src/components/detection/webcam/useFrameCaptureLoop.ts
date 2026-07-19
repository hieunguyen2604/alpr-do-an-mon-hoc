/**
 * The capture loop: grab a frame, send it, merge what comes back.
 *
 * Two decisions in here are load-bearing and easy to undo by accident.
 *
 * **One request in flight, never a queue.** Inference runs on CPU at roughly
 * 5 FPS. A naive timer that fires every 700 ms and awaits each response will,
 * the moment a frame takes 900 ms, start a second request before the first
 * returns — and from then on the backlog only grows. Latency compounds, the
 * overlay drifts further behind the picture with every frame, and the tab
 * eventually stalls under the weight of pending uploads. So the loop keeps a
 * single slot: if `inFlightRef` is set when the timer fires, the frame is
 * **dropped**, not queued. Dropping a frame costs nothing — the next one is
 * 700 ms away and shows a more current picture anyway.
 *
 * **One job id for the whole session.** The backend groups results by
 * `job_id`, and dashboard statistics count *uploads* (`total_jobs`) separately
 * from *plates* (`total_detections`). Sending each frame without an id opens a
 * new job per frame, so a thirty-second capture is recorded as ~40 uploads
 * instead of one. Nothing fails visibly; the dashboard just quietly becomes
 * wrong. The id from the first response is therefore held in a ref and resent
 * on every subsequent frame.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import type { RefObject } from 'react';

import { detectFrame, getErrorMessage } from '@/services/api';
import type { DetectionResponse, DetectionResult } from '@/types';
import { formatPlateNumber } from '@/lib/format';

import type { CaptureMetrics, SessionPlateRow } from './types';

/** JPEG quality for captured frames: legible plates at a modest upload size. */
const FRAME_JPEG_QUALITY = 0.8;

/** Trailing window used to measure throughput, in milliseconds. */
const FPS_WINDOW_MS = 5_000;

/**
 * Consecutive failures tolerated before the loop pauses itself.
 *
 * Without this, a backend that has gone away is hit every 700 ms for as long
 * as the tab stays open, and the user sees the same error flash forever.
 * Pausing turns an endless failure into one clear message with a retry.
 */
const MAX_CONSECUTIVE_ERRORS = 5;

const EMPTY_METRICS: CaptureMetrics = {
  framesSent: 0,
  framesSkipped: 0,
  framesCompleted: 0,
  fps: null,
  lastProcessingTimeSeconds: null,
  lastRoundTripSeconds: null,
  averageProcessingTimeSeconds: null,
};

/** Options for {@link useFrameCaptureLoop}. */
export interface UseFrameCaptureLoopOptions {
  /** The element to capture from. */
  videoRef: RefObject<HTMLVideoElement>;
  /** Whether the loop should be running. */
  enabled: boolean;
  /** Delay between capture attempts, in milliseconds. */
  intervalMs: number;
}

/** What {@link useFrameCaptureLoop} returns. */
export interface UseFrameCaptureLoopResult {
  /** Session id shared by every frame, or `null` before the first response. */
  jobId: string | null;
  /** Most recent response, used to draw the overlay. */
  latestDetection: DetectionResponse | null;
  /** Session log, one row per distinct plate string. */
  plates: SessionPlateRow[];
  /** Plates located but not readable by OCR, counted rather than listed. */
  unreadableCount: number;
  metrics: CaptureMetrics;
  /** `true` while a frame is awaiting its response. */
  isSending: boolean;
  /** Display-ready Vietnamese message for the latest failure, or `null`. */
  error: string | null;
  /** `true` once the loop stopped itself after repeated failures. */
  isPaused: boolean;
  /** Clear the failure count and start capturing again. */
  resume: () => void;
  dismissError: () => void;
  /**
   * Empty the plate log without ending the session.
   *
   * The job id survives on purpose: clearing a list on screen is a display
   * choice, and splitting the backend job because of it would record one
   * capture as two uploads.
   */
  clearPlates: () => void;
  /** Forget the job id, the plate log and every measurement. */
  resetSession: () => void;
}

/**
 * Encode the current video frame as a JPEG blob.
 *
 * @param video - The playing video element.
 * @param canvas - A scratch canvas, reused between frames.
 * @returns The encoded frame, or `null` if the video has no displayable frame
 *   yet — which is normal for the first few hundred milliseconds after start.
 */
async function captureFrame(
  video: HTMLVideoElement,
  canvas: HTMLCanvasElement,
): Promise<Blob | null> {
  if (video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) {
    return null;
  }
  const { videoWidth, videoHeight } = video;
  if (videoWidth === 0 || videoHeight === 0) {
    return null;
  }

  canvas.width = videoWidth;
  canvas.height = videoHeight;

  const context = canvas.getContext('2d');
  if (!context) {
    return null;
  }
  context.drawImage(video, 0, 0, videoWidth, videoHeight);

  return new Promise<Blob | null>((resolve) => {
    canvas.toBlob((blob) => resolve(blob), 'image/jpeg', FRAME_JPEG_QUALITY);
  });
}

/**
 * Reduce a plate string to its deduplication key.
 *
 * Everything that is not a letter or a digit is dropped and the rest is
 * uppercased, so `"90C-76040"`, `"90c 76040"` and `"90C76040"` all key to
 * `"90C76040"` and collapse into one row. Separators are the part of a plate
 * reading that OCR is least consistent about between consecutive frames, and
 * they carry no identity — two readings that differ only in a hyphen are the
 * same vehicle.
 *
 * This is a **key**, never a display value. The characters themselves are not
 * "corrected" here: an OCR `O` stays an `O`, because silently turning it into a
 * `0` would hide exactly the error the evaluation chapter measures.
 *
 * @param plateNumber - Plate text from the API.
 * @returns The key to deduplicate on.
 */
function sessionPlateKey(plateNumber: string): string {
  return plateNumber.replace(/[^0-9a-z]/gi, '').toUpperCase();
}

/**
 * Fold one frame's results into the running session log.
 *
 * Exported so the deduplication rule can be exercised directly: it is the one
 * piece of logic here that is worth a test and impossible to observe from the
 * outside without a camera.
 *
 * Results with no plate text are skipped — the detector found a plate but OCR
 * read nothing, which has no key to deduplicate on. The caller counts those
 * separately instead of inventing a row for each.
 *
 * @param previous - The log as it stands.
 * @param results - Plates from the frame just processed.
 * @param seenAt - Capture time to record against the sightings.
 * @returns A new log; the input is never mutated.
 */
export function mergeSessionPlates(
  previous: readonly SessionPlateRow[],
  results: readonly DetectionResult[],
  seenAt: Date,
): SessionPlateRow[] {
  if (results.length === 0) {
    return previous as SessionPlateRow[];
  }

  const byPlate = new Map<string, SessionPlateRow>();
  for (const row of previous) {
    byPlate.set(row.key, row);
  }

  let changed = false;

  for (const result of results) {
    if (!result.plate_number) {
      continue;
    }
    const key = sessionPlateKey(result.plate_number);
    if (key.length === 0) {
      continue;
    }
    const display = formatPlateNumber(result.plate_number);
    const existing = byPlate.get(key);
    changed = true;

    if (!existing) {
      byPlate.set(key, {
        key,
        plateNumber: display,
        occurrences: 1,
        bestConfidence: result.detection_confidence,
        bestOcrConfidence: result.ocr_confidence,
        isValidFormat: result.is_valid_format,
        plateLineCount: result.plate_line_count,
        firstSeenAt: seenAt,
        lastSeenAt: seenAt,
      });
      continue;
    }

    const isBetter = result.detection_confidence > existing.bestConfidence;
    byPlate.set(key, {
      ...existing,
      // Show the reading the detector was most sure of, rather than whichever
      // arrived first — the clearest frame is the most trustworthy rendering.
      plateNumber: isBetter ? display : existing.plateNumber,
      occurrences: existing.occurrences + 1,
      bestConfidence: Math.max(existing.bestConfidence, result.detection_confidence),
      bestOcrConfidence:
        existing.bestOcrConfidence === null
          ? result.ocr_confidence
          : result.ocr_confidence === null
            ? existing.bestOcrConfidence
            : Math.max(existing.bestOcrConfidence, result.ocr_confidence),
      // One valid reading is enough to call the plate well-formed: a later
      // blurred frame should not retract what a clear frame established.
      isValidFormat: existing.isValidFormat || result.is_valid_format,
      plateLineCount: isBetter ? result.plate_line_count : existing.plateLineCount,
      lastSeenAt: seenAt,
    });
  }

  return changed ? Array.from(byPlate.values()) : (previous as SessionPlateRow[]);
}

/**
 * Run the webcam capture loop.
 *
 * @param options - Video source, whether to run, and the capture interval.
 * @returns Session results, live metrics and the controls to reset or resume.
 */
export function useFrameCaptureLoop({
  videoRef,
  enabled,
  intervalMs,
}: UseFrameCaptureLoopOptions): UseFrameCaptureLoopResult {
  const [latestDetection, setLatestDetection] = useState<DetectionResponse | null>(
    null,
  );
  const [plates, setPlates] = useState<SessionPlateRow[]>([]);
  const [unreadableCount, setUnreadableCount] = useState(0);
  const [metrics, setMetrics] = useState<CaptureMetrics>(EMPTY_METRICS);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPaused, setIsPaused] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);

  /** The single slot. `true` means a request is out and frames must be dropped. */
  const inFlightRef = useRef(false);
  /** Session id, held in a ref so the loop reads it without re-subscribing. */
  const jobIdRef = useRef<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const consecutiveErrorsRef = useRef(0);
  /** Completion timestamps inside the trailing window, for the FPS figure. */
  const completionTimesRef = useRef<number[]>([]);
  /** Running total of server-reported processing times, for the mean. */
  const processingTotalRef = useRef(0);

  /**
   * The scratch canvas.
   *
   * Created off-DOM rather than rendered hidden: it is never displayed, and a
   * mounted `<canvas>` whose dimensions are rewritten several times a second
   * invites needless layout work.
   */
  const getCanvas = useCallback((): HTMLCanvasElement => {
    if (!canvasRef.current) {
      canvasRef.current = document.createElement('canvas');
    }
    return canvasRef.current;
  }, []);

  const resetSession = useCallback((): void => {
    abortRef.current?.abort();
    abortRef.current = null;
    inFlightRef.current = false;
    jobIdRef.current = null;
    consecutiveErrorsRef.current = 0;
    completionTimesRef.current = [];
    processingTotalRef.current = 0;

    setJobId(null);
    setLatestDetection(null);
    setPlates([]);
    setUnreadableCount(0);
    setMetrics(EMPTY_METRICS);
    setIsSending(false);
    setIsPaused(false);
    setError(null);
  }, []);

  const dismissError = useCallback((): void => setError(null), []);

  const clearPlates = useCallback((): void => {
    setPlates([]);
    setUnreadableCount(0);
  }, []);

  const resume = useCallback((): void => {
    consecutiveErrorsRef.current = 0;
    setError(null);
    setIsPaused(false);
  }, []);

  /**
   * Capture and send one frame, unless a request is already out.
   *
   * Kept in a ref rather than a dependency of the interval effect: recreating
   * the timer on every metrics update would reset the interval several times a
   * second and make the real capture rate unpredictable.
   */
  const tick = useCallback(async (): Promise<void> => {
    // The single-slot rule. Skipping is the correct behaviour, not a fallback.
    if (inFlightRef.current) {
      setMetrics((current) => ({
        ...current,
        framesSkipped: current.framesSkipped + 1,
      }));
      return;
    }

    const video = videoRef.current;
    if (!video) {
      return;
    }

    const frame = await captureFrame(video, getCanvas());
    if (!frame) {
      return;
    }

    inFlightRef.current = true;
    setIsSending(true);

    const controller = new AbortController();
    abortRef.current = controller;
    const startedAt = performance.now();

    try {
      const response = await detectFrame(frame, jobIdRef.current, controller.signal);

      // Adopt the session id from the first response and reuse it thereafter,
      // so the whole capture is recorded as one upload.
      if (!jobIdRef.current && response.job_id) {
        jobIdRef.current = response.job_id;
        setJobId(response.job_id);
      }

      const roundTripSeconds = (performance.now() - startedAt) / 1000;
      const seenAt = new Date();

      consecutiveErrorsRef.current = 0;
      setError(null);
      setLatestDetection(response);
      setPlates((current) => mergeSessionPlates(current, response.results, seenAt));

      const unreadable = response.results.filter((r) => !r.plate_number).length;
      if (unreadable > 0) {
        setUnreadableCount((count) => count + unreadable);
      }

      // Throughput over a trailing window rather than since the start: a demo
      // that ran slowly for its first ten seconds should not drag the figure
      // down for the rest of the session.
      const now = performance.now();
      const times = [...completionTimesRef.current, now].filter(
        (time) => now - time <= FPS_WINDOW_MS,
      );
      completionTimesRef.current = times;
      const first = times[0];
      const elapsedSeconds =
        times.length > 1 && first !== undefined ? (now - first) / 1000 : 0;

      processingTotalRef.current += response.processing_time;

      setMetrics((current) => {
        const completed = current.framesCompleted + 1;
        return {
          ...current,
          framesSent: current.framesSent + 1,
          framesCompleted: completed,
          fps: elapsedSeconds > 0 ? (times.length - 1) / elapsedSeconds : current.fps,
          lastProcessingTimeSeconds: response.processing_time,
          lastRoundTripSeconds: roundTripSeconds,
          averageProcessingTimeSeconds: processingTotalRef.current / completed,
        };
      });
    } catch (cause) {
      // An abort is this component tearing the request down on purpose; it is
      // not a failure the user needs to hear about.
      if (controller.signal.aborted) {
        return;
      }
      consecutiveErrorsRef.current += 1;
      setMetrics((current) => ({ ...current, framesSent: current.framesSent + 1 }));
      setError(getErrorMessage(cause));

      if (consecutiveErrorsRef.current >= MAX_CONSECUTIVE_ERRORS) {
        setIsPaused(true);
      }
    } finally {
      // Releasing the slot in `finally` is what guarantees one failed frame
      // cannot wedge the loop shut for the rest of the session.
      inFlightRef.current = false;
      abortRef.current = null;
      setIsSending(false);
    }
  }, [getCanvas, videoRef]);

  const tickRef = useRef(tick);
  useEffect(() => {
    tickRef.current = tick;
  }, [tick]);

  // The timer itself. Re-created only when the loop is switched on or off or
  // the interval is changed by the user.
  useEffect(() => {
    if (!enabled || isPaused) {
      return undefined;
    }
    const timer = window.setInterval(() => {
      void tickRef.current();
    }, intervalMs);
    return () => window.clearInterval(timer);
  }, [enabled, intervalMs, isPaused]);

  // Drop any request still in the air when capturing stops, so a late response
  // cannot repaint an overlay over a video that is no longer running.
  useEffect(() => {
    if (enabled) {
      return;
    }
    abortRef.current?.abort();
    abortRef.current = null;
    inFlightRef.current = false;
    setIsSending(false);
  }, [enabled]);

  // Abort on unmount as well: navigating away mid-request must not leave a
  // promise resolving into a component that no longer exists.
  useEffect(
    () => () => {
      abortRef.current?.abort();
      abortRef.current = null;
      inFlightRef.current = false;
    },
    [],
  );

  return {
    jobId,
    latestDetection,
    plates,
    unreadableCount,
    metrics,
    isSending,
    error,
    isPaused,
    resume,
    dismissError,
    clearPlates,
    resetSession,
  };
}
