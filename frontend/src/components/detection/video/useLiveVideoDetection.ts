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
  const [error, setError] = useState<string | null>(null);

  const inFlightRef = useRef(false);
  const jobIdRef = useRef<string | null>(null);
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

  // Starting a fresh preview must not inherit the previous file's session id,
  // or two different videos would be recorded as one upload.
  useEffect(() => {
    if (!enabled) {
      jobIdRef.current = null;
      setResults([]);
      setCounters({ sent: 0, skipped: 0 });
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
    error,
  };
}
