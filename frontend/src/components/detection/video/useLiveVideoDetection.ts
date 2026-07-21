/**
 * Detect plates in a `<video>` element while it plays.
 *
 * How it works
 * ------------
 * A timer grabs whatever frame is currently on screen, draws it to an offscreen
 * canvas, encodes it as JPEG and posts it to `POST /api/detect/frame`. The boxes
 * that come back are held in state until the next answer replaces them, together
 * with the frame they were measured against.
 *
 * The single-slot rule
 * --------------------
 * At most **one** request is ever in flight. When the timer fires while a
 * request is still running, that frame is dropped and never queued.
 *
 * Skipping is the correct behaviour here, not a fallback. Inference costs a
 * measured 547 ms at the median on this machine, and the timer fires far more
 * often than that. A queue would grow without bound, and every box it eventually
 * drew would describe a frame the video had long since passed.
 *
 * What this is, and is not
 * ------------------------
 * A **preview**. It reads whatever frames it can keep up with, so it sees a
 * fraction of the video. The background job started from the same file is what
 * produces the complete, authoritative result; the two run side by side.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

import { detectFrame, getErrorMessage } from '@/services/api';
import type { DetectionResult } from '@/types';

/**
 * Milliseconds between capture attempts.
 *
 * Slightly above the measured inference cost. Firing much faster would only
 * increase the number of frames dropped by the single-slot rule without putting
 * a single extra frame through the model; firing slower would leave the overlay
 * visibly stale during fast motion.
 */
const CAPTURE_INTERVAL_MS = 450;

/** JPEG quality for the captured frame. */
const FRAME_QUALITY = 0.75;

/**
 * Longest edge of the captured frame, in pixels.
 *
 * The detector runs at 640 px, so sending a 4K frame costs upload time and JPEG
 * encoding for detail the model immediately discards.
 */
const MAX_CAPTURE_EDGE = 960;

/**
 * Largest number of distinct plates kept in the log.
 *
 * Merging keeps this list far shorter than a per-sighting one, but a long clip
 * on a busy street still finds new plates indefinitely, and nobody reads past a
 * hundred rows during a demonstration.
 */
const MAX_PLATES = 100;

/**
 * Bucket that collects every box whose text could not be read.
 *
 * Deliberately not a plate-shaped string: normalisation only ever emits
 * `A-Z0-9`, so this cannot collide with a real reading.
 */
const UNREAD_KEY = '__unread__';

/**
 * One **distinct plate** seen during the session, not one sighting.
 *
 * A plate stays in view for several seconds, so a chronological list of every
 * read repeats the same number over and over and buries anything new. Measured
 * on the demo clip: 8 analysed frames produced 24 log lines, and after the video
 * ended the same frozen frame kept being re-read. The background job merges its
 * results across frames for exactly this reason; the log here does the same, so
 * the two describe the world the same way.
 */
export interface LivePlateSummary {
  /** Normalised plate string, `null` for a box whose text could not be read. */
  plateNumber: string | null;
  /** The plate as it should be shown, already separator-formatted. */
  display: string | null;
  /** Unmodified OCR output, so the correction step stays visible. */
  rawText: string | null;
  /** How many frames this plate was read in. */
  reads: number;
  /** Position in the video where it was first seen, in seconds. */
  firstSeen: number;
  /** Position where it was last seen, in seconds. */
  lastSeen: number;
  /** Best detector confidence across the sightings. */
  detectionConfidence: number;
  /** Best OCR confidence across the sightings, `null` if never read. */
  ocrConfidence: number | null;
  /** Whether the string matched a civil Vietnamese layout. */
  isValidFormat: boolean;
  /** Plate family inferred from the string. */
  kind: DetectionResult['plate_kind'];
  /** Background colour read from the crop. */
  color: DetectionResult['plate_color'];
  /** Box size at the best sighting, in captured-frame pixels. */
  boxWidth: number;
  boxHeight: number;
}

/** What {@link useLiveVideoDetection} reports back to the component. */
export interface LiveDetectionState {
  /** Plates found in the most recent answered frame. */
  results: DetectionResult[];
  /**
   * The exact frame those plates were read from.
   *
   * Handed back so the panel can display *this* image rather than whatever the
   * video has moved on to. Inference costs a measured 547 ms at the median and
   * up to 1.7 s, so at 1x playback the picture on screen is roughly half a
   * second ahead of the boxes — far enough for a moving vehicle to leave its
   * own box behind, which looks like a tracking failure and is really just two
   * different moments drawn on top of each other.
   */
  frameImage: ImageBitmap | null;
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
  /** Distinct plates seen, merged across frames, most recently seen first. */
  plates: LivePlateSummary[];
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
 * Fold one sighting into the merged list.
 *
 * Keeps the **best** reading rather than the latest. A plate is read many times
 * as it crosses the frame, and those reads are not equally good — it is small
 * and blurred at the edges of its pass and largest in the middle. Overwriting
 * with the newest would leave every plate described by its worst sighting, the
 * one taken as it leaves the shot.
 *
 * @param list - Current merged list.
 * @param result - One plate from one frame.
 * @param videoTime - Where in the clip the frame came from.
 * @returns A new list; the input is not modified.
 */
export function mergePlateSighting(
  list: LivePlateSummary[],
  result: DetectionResult,
  videoTime: number,
): LivePlateSummary[] {
  const key = result.plate_number ?? UNREAD_KEY;
  const index = list.findIndex((entry) => (entry.plateNumber ?? UNREAD_KEY) === key);

  if (index === -1) {
    const entry: LivePlateSummary = {
      plateNumber: result.plate_number,
      display: result.plate_display ?? null,
      rawText: result.raw_ocr_text,
      reads: 1,
      firstSeen: videoTime,
      lastSeen: videoTime,
      detectionConfidence: result.detection_confidence,
      ocrConfidence: result.ocr_confidence,
      isValidFormat: result.is_valid_format,
      kind: result.plate_kind,
      color: result.plate_color,
      boxWidth: result.bbox.width,
      boxHeight: result.bbox.height,
    };
    return [entry, ...list].slice(0, MAX_PLATES);
  }

  const current = list[index];
  if (current === undefined) {
    // Unreachable: findIndex returned a valid position. The check exists
    // because indexed access is typed as possibly-undefined, and silently
    // asserting it away is how a real out-of-range bug would slip through
    // later.
    return list;
  }

  const isBetter = result.detection_confidence > current.detectionConfidence;
  const betterOcr =
    result.ocr_confidence !== null &&
    (current.ocrConfidence === null || result.ocr_confidence > current.ocrConfidence);

  const merged: LivePlateSummary = {
    ...current,
    reads: current.reads + 1,
    firstSeen: Math.min(current.firstSeen, videoTime),
    lastSeen: Math.max(current.lastSeen, videoTime),
    detectionConfidence: Math.max(current.detectionConfidence, result.detection_confidence),
    ocrConfidence: betterOcr ? result.ocr_confidence : current.ocrConfidence,
    // The descriptive fields travel together. Taking the family from one
    // sighting and the colour from another would describe a plate that was
    // never actually seen.
    ...(isBetter
      ? {
          display: result.plate_display ?? null,
          rawText: result.raw_ocr_text,
          isValidFormat: result.is_valid_format,
          kind: result.plate_kind,
          color: result.plate_color,
          boxWidth: result.bbox.width,
          boxHeight: result.bbox.height,
        }
      : {}),
  };

  // Move it to the front, so the log reads as "what the system is looking at".
  const rest = list.filter((_, position) => position !== index);
  return [merged, ...rest];
}

/**
 * Run live plate detection against a video element.
 *
 * @param options - The video element and whether the preview is active.
 * @returns The latest boxes, the frame they came from, and the merged log.
 */
export function useLiveVideoDetection({
  videoRef,
  enabled,
}: LiveDetectionOptions): LiveDetectionState {
  const [results, setResults] = useState<DetectionResult[]>([]);
  const [frameImage, setFrameImage] = useState<ImageBitmap | null>(null);
  const [frameSize, setFrameSize] = useState({ width: 0, height: 0 });
  const [isBusy, setIsBusy] = useState(false);
  const [counters, setCounters] = useState({ sent: 0, skipped: 0 });
  const [plates, setPlates] = useState<LivePlateSummary[]>([]);
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
   * Encode the video's current frame as a JPEG blob, and keep the pixels.
   *
   * The bitmap is taken from the same canvas contents that produced the blob,
   * so the image the panel later displays is byte-for-byte the image the model
   * was asked about — not a re-read of the video at some other instant.
   *
   * @param video - The source element.
   * @returns The encoded frame and its bitmap, or `null` when no frame is
   *   available yet.
   */
  const captureFrame = useCallback(
    async (video: HTMLVideoElement): Promise<{ blob: Blob; bitmap: ImageBitmap } | null> => {
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

      const blob = await new Promise<Blob | null>((resolve) => {
        canvas.toBlob((encoded) => resolve(encoded), 'image/jpeg', FRAME_QUALITY);
      });
      if (blob === null) {
        return null;
      }

      return { blob, bitmap: await createImageBitmap(canvas) };
    },
    [],
  );

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const timer = window.setInterval(() => {
      const video = videoRef.current;
      if (video === null) {
        return;
      }

      // A still video is not a new moment. Without this the timer keeps
      // re-reading one frozen frame: measured after the demo clip ended, seven
      // further requests went out in six seconds, each returning the same
      // plates and inflating both the counters and the log. Not counted as
      // skipped either — nothing was there to miss.
      if (video.paused || video.ended) {
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
        let captured: { blob: Blob; bitmap: ImageBitmap } | null = null;
        try {
          captured = await captureFrame(video);
          if (captured === null) {
            return;
          }

          const response = await detectFrame(captured.blob, jobIdRef.current, controller.signal);
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

          // Hand the pixels over and release the previous frame in the same
          // step. An ImageBitmap holds decoded pixels outside the JS heap, so
          // dropping the reference without closing it leaks until the garbage
          // collector happens to notice — over a long clip that is hundreds of
          // frames.
          const { bitmap } = captured;
          setFrameImage((previous) => {
            previous?.close();
            return bitmap;
          });
          captured = null;

          if (response.results.length > 0) {
            setPlates((previous) => {
              let next = previous;
              for (const result of response.results) {
                next = mergePlateSighting(next, result, videoTime);
              }
              return next;
            });
          }
        } catch (caught) {
          if (isMountedRef.current && !controller.signal.aborted) {
            setError(getErrorMessage(caught));
          }
        } finally {
          // Still set means the frame never reached state — an aborted request,
          // an unmounted component or a failed call. Close it here or those
          // pixels are never released.
          captured?.bitmap.close();
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
  // A new file gets a clean slate through remounting — the panel is keyed on
  // the file — so nothing here has to know which video is loaded.
  useEffect(() => {
    if (!enabled) {
      setResults([]);
      setFrameImage((previous) => {
        previous?.close();
        return null;
      });
      setError(null);
    }
  }, [enabled]);

  // Release the last frame on unmount; navigating away mid-detection would
  // otherwise strand one decoded bitmap per mounted panel.
  useEffect(
    () => () => {
      setFrameImage((previous) => {
        previous?.close();
        return null;
      });
    },
    [],
  );

  return {
    results,
    frameImage,
    frameWidth: frameSize.width,
    frameHeight: frameSize.height,
    isBusy,
    sent: counters.sent,
    skipped: counters.skipped,
    plates,
    error,
  };
}
