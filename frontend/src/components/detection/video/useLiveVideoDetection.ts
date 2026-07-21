/**
 * Detect plates in a `<video>` element while it plays or is scrubbed.
 *
 * How it works
 * ------------
 * A timer grabs whatever frame is currently on screen, draws it to an offscreen
 * canvas, encodes it as JPEG and posts it to `POST /api/detect/frame`. The boxes
 * that come back are held in state until the next answer replaces them.
 *
 * The single-slot rule
 * --------------------
 * At most **one** request is ever in flight. When the timer fires while a
 * request is still running, that frame is dropped and never queued.
 *
 * Skipping is the correct behaviour here, not a fallback. Inference costs
 * roughly 400 ms on the CPU this runs on, and the timer fires far more often
 * than that. A queue would grow without bound, and every box it eventually drew
 * would describe a frame the video had long since passed — the display would
 * drift further behind reality the longer it ran. Dropping frames keeps the
 * boxes attached to a moment close to the one on screen, which is the only
 * property that makes a live overlay worth showing.
 *
 * What this is, and is not
 * ------------------------
 * A **preview**. It reads whatever frames it can keep up with, so it sees a
 * fraction of the video and does not merge a plate seen across several frames
 * into one record. The background job started from the same file is what
 * produces the complete, de-duplicated result; the two run side by side.
 *
 * Presenting this as the measurement would understate the system: it processes
 * fewer frames than the batch path by design.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

import { detectFrame, getErrorMessage } from '@/services/api';
import type { DetectionResult } from '@/types';

/**
 * Milliseconds between capture attempts.
 *
 * Slightly above the measured inference cost (~400 ms warm). Firing much faster
 * would only increase the number of frames dropped by the single-slot rule
 * without putting a single extra frame through the model; firing slower would
 * leave the overlay visibly stale during fast motion.
 */
const CAPTURE_INTERVAL_MS = 450;

/** JPEG quality for the captured frame. */
const FRAME_QUALITY = 0.75;

/**
 * Longest edge of the captured frame, in pixels.
 *
 * The detector runs at 640 px, so sending a 4K frame costs upload time and JPEG
 * encoding for detail the model immediately discards. Capping here keeps each
 * request small enough that transfer stays negligible beside inference.
 */
const MAX_CAPTURE_EDGE = 960;

/**
 * Largest number of log entries kept in memory.
 *
 * The log exists to be read during a demonstration, and nobody scrolls past a
 * hundred lines of it. Keeping every entry of a ten-minute clip would grow
 * without bound and re-render a list thousands of rows long on every frame.
 */
const MAX_EVENTS = 100;

/** One plate seen in one frame, recorded for the log. */
export interface LiveDetectionEvent {
  /** Stable key for React; monotonic within a session. */
  id: number;
  /** Position in the video the frame was taken from, in seconds. */
  videoTime: number;
  /** The plate as it should be shown, already separator-formatted. */
  display: string | null;
  /** Normalised plate string, `null` when nothing was read. */
  plateNumber: string | null;
  /** Unmodified OCR output, so the correction step stays visible. */
  rawText: string | null;
  /** Detector confidence for this box. */
  detectionConfidence: number;
  /** OCR confidence, `null` when no text was read. */
  ocrConfidence: number | null;
  /** Whether the string matched a civil Vietnamese layout. */
  isValidFormat: boolean;
  /** Plate family inferred from the string. */
  kind: DetectionResult['plate_kind'];
  /** Background colour read from the crop. */
  color: DetectionResult['plate_color'];
  /** Box size in the captured frame, for judging how small the plate was. */
  boxWidth: number;
  boxHeight: number;
}

/** What {@link useLiveVideoDetection} reports back to the component. */
export interface LiveDetectionState {
  /** Plates found in the most recent answered frame. */
  results: DetectionResult[];
  /** Width of the frame those boxes were measured against. */
  frameWidth: number;
  /** Height of the frame those boxes were measured against. */
  frameHeight: number;
  /** Whether a frame is being processed right now. */
  isBusy: boolean;
  /** Frames captured and sent since the preview started. */
  sent: number;
  /** Frames dropped because a request was already in flight. */
  skipped: number;
  /** Every plate seen so far, newest first, capped at {@link MAX_EVENTS}. */
  events: LiveDetectionEvent[];
  /** Distinct plate strings seen, in first-seen order. */
  distinctPlates: string[];
  /** Display-ready Vietnamese error from the last failure, or `null`. */
  error: string | null;
}

/** Options of {@link useLiveVideoDetection}. */
export interface LiveDetectionOptions {
  /** The playing video element, or `null` before it mounts. */
  videoRef: React.RefObject<HTMLVideoElement>;
  /** Whether the preview should be running. */
  enabled: boolean;
}

/**
 * Run live plate detection against a video element.
 *
 * @param options - The video element and whether the preview is active.
 * @returns The latest boxes and the counters behind them.
 */
export function useLiveVideoDetection({
  videoRef,
  enabled,
}: LiveDetectionOptions): LiveDetectionState {
  const [results, setResults] = useState<DetectionResult[]>([]);
  const [frameSize, setFrameSize] = useState({ width: 0, height: 0 });
  const [isBusy, setIsBusy] = useState(false);
  const [counters, setCounters] = useState({ sent: 0, skipped: 0 });
  const [events, setEvents] = useState<LiveDetectionEvent[]>([]);
  const [distinctPlates, setDistinctPlates] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const inFlightRef = useRef(false);
  const jobIdRef = useRef<string | null>(null);
  const eventIdRef = useRef(0);
  // Distinct plates are tracked in a ref as well as in state because the log is
  // capped: once old entries fall off, `events` can no longer answer "have we
  // seen this plate before" and the count would start rising again.
  const seenPlatesRef = useRef<Set<string>>(new Set());
  const abortRef = useRef<AbortController | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      abortRef.current?.abort();
    };
  }, []);

  /**
   * Encode the video's current frame as a JPEG blob.
   *
   * @param video - The source element.
   * @returns The encoded frame, or `null` when no frame is available yet.
   */
  const captureFrame = useCallback(async (video: HTMLVideoElement): Promise<Blob | null> => {
    // `readyState < 2` means no frame has been decoded, which happens right
    // after a seek. Capturing then yields a blank canvas, and a blank frame
    // returns zero plates — clearing the overlay for no reason.
    if (video.readyState < 2 || !video.videoWidth || !video.videoHeight) {
      return null;
    }

    const scale = Math.min(1, MAX_CAPTURE_EDGE / Math.max(video.videoWidth, video.videoHeight));
    const width = Math.round(video.videoWidth * scale);
    const height = Math.round(video.videoHeight * scale);

    let canvas = canvasRef.current;
    if (canvas === null) {
      canvas = document.createElement('canvas');
      canvasRef.current = canvas;
    }
    canvas.width = width;
    canvas.height = height;

    const context = canvas.getContext('2d');
    if (context === null) {
      return null;
    }
    context.drawImage(video, 0, 0, width, height);

    return new Promise<Blob | null>((resolve) => {
      canvas.toBlob((blob) => resolve(blob), 'image/jpeg', FRAME_QUALITY);
    });
  }, []);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const timer = window.setInterval(() => {
      const video = videoRef.current;
      if (video === null) {
        return;
      }

      if (inFlightRef.current) {
        setCounters((previous) => ({ ...previous, skipped: previous.skipped + 1 }));
        return;
      }

      inFlightRef.current = true;
      setIsBusy(true);

      // Read the position now, not when the answer arrives: by then the video
      // has moved on and every log entry would carry a timestamp later than the
      // frame it describes.
      const videoTime = video.currentTime;

      void (async () => {
        const controller = new AbortController();
        abortRef.current = controller;
        try {
          const blob = await captureFrame(video);
          if (blob === null) {
            return;
          }

          const response = await detectFrame(blob, jobIdRef.current, controller.signal);
          if (!isMountedRef.current || controller.signal.aborted) {
            return;
          }

          // Carry the session id forward so the whole preview counts as one
          // upload rather than one per frame.
          jobIdRef.current = response.job_id;
          setResults(response.results);
          setFrameSize({ width: response.image_width, height: response.image_height });
          setCounters((previous) => ({ ...previous, sent: previous.sent + 1 }));
          setError(null);

          if (response.results.length > 0) {
            const additions = response.results.map((result) => ({
              id: (eventIdRef.current += 1),
              videoTime,
              display: result.plate_display ?? null,
              plateNumber: result.plate_number,
              rawText: result.raw_ocr_text,
              detectionConfidence: result.detection_confidence,
              ocrConfidence: result.ocr_confidence,
              isValidFormat: result.is_valid_format,
              kind: result.plate_kind,
              color: result.plate_color,
              boxWidth: result.bbox.width,
              boxHeight: result.bbox.height,
            }));
            setEvents((previous) => [...additions, ...previous].slice(0, MAX_EVENTS));

            const fresh = response.results
              .map((result) => result.plate_number)
              .filter((plate): plate is string => plate !== null && plate.length > 0)
              .filter((plate) => !seenPlatesRef.current.has(plate));
            if (fresh.length > 0) {
              fresh.forEach((plate) => seenPlatesRef.current.add(plate));
              setDistinctPlates((previous) => [...previous, ...fresh]);
            }
          }
        } catch (caught) {
          if (isMountedRef.current && !controller.signal.aborted) {
            setError(getErrorMessage(caught));
          }
        } finally {
          inFlightRef.current = false;
          if (isMountedRef.current) {
            setIsBusy(false);
          }
        }
      })();
    }, CAPTURE_INTERVAL_MS);

    return () => {
      window.clearInterval(timer);
      abortRef.current?.abort();
      inFlightRef.current = false;
    };
  }, [enabled, videoRef, captureFrame]);

  // Stopping clears the **overlay** but keeps the **log**. The two answer
  // different questions: boxes describe the frame on screen right now, and
  // leaving them up while the user scrubs elsewhere would label the wrong
  // moment; the log is the record of what was found, and wiping it the instant
  // someone pauses to read it would destroy the thing they stopped to look at.
  //
  // A new file gets a clean slate through remounting -- the panel is keyed on
  // the file -- so nothing here has to know which video is loaded.
  useEffect(() => {
    if (!enabled) {
      setResults([]);
      setError(null);
    }
  }, [enabled]);

  return {
    results,
    frameWidth: frameSize.width,
    frameHeight: frameSize.height,
    isBusy,
    sent: counters.sent,
    skipped: counters.skipped,
    events,
    distinctPlates,
    error,
  };
}
