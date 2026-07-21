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
 * Tied to the cost of the **cheap** frame, not the expensive one. Three frames
 * in four skip OCR and come back in roughly 225 ms, so a 450 ms timer — chosen
 * when every frame cost 400-550 ms — left the model idle half the time and
 * capped throughput at about 1.4 frames per second no matter how fast inference
 * got. Lowering it was the second half of the optimisation: without it, making
 * inference twice as fast bought almost nothing.
 *
 * Firing much faster than this would only grow the number of frames the
 * single-slot rule drops, without putting one extra frame through the model.
 */
const CAPTURE_INTERVAL_MS = 250;

/** JPEG quality for the captured frame. */
const FRAME_QUALITY = 0.75;

/**
 * Longest edge of the captured frame, in pixels.
 *
 * Matched to the detector's own input size. Anything larger is encoded,
 * uploaded and then thrown away by the model's first resize, so the extra
 * pixels cost JPEG time and bandwidth and buy nothing.
 */
const MAX_CAPTURE_EDGE = 640;

/**
 * Read the characters on one frame in every this many.
 *
 * OCR is 55% of the per-frame budget — 274 ms against 225 ms for detection on a
 * 960x540 frame with three plates — and it re-reads the same vehicles in every
 * frame, producing the same string each time. Characters do not change while a
 * plate is in shot, so reading once and carrying the text forward onto the
 * boxes found in between roughly doubles the frame rate.
 *
 * Not larger than this, though: a plate that enters the shot is invisible to
 * the log until the next reading frame, so this value is also the worst-case
 * delay before a new plate is named.
 */
const READ_TEXT_EVERY = 4;

/**
 * Overlap needed to treat a new box as the same plate as an earlier one.
 *
 * Deliberately forgiving. Between two frames 450 ms apart a moving vehicle
 * shifts a long way, so demanding a tight overlap would fail to match exactly
 * the plates that are moving — the ones worth tracking. A false match costs a
 * briefly mislabelled box on the preview; a missed match costs the text
 * disappearing and reappearing, which reads as a fault.
 */
const MATCH_MIN_IOU = 0.3;

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
 * Intersection over union of two boxes.
 *
 * @param a - First box.
 * @param b - Second box.
 * @returns Overlap in `[0, 1]`; `0` when they do not touch.
 */
function intersectionOverUnion(
  a: DetectionResult['bbox'],
  b: DetectionResult['bbox'],
): number {
  const left = Math.max(a.x, b.x);
  const top = Math.max(a.y, b.y);
  const right = Math.min(a.x + a.width, b.x + b.width);
  const bottom = Math.min(a.y + a.height, b.y + b.height);

  const overlap = Math.max(0, right - left) * Math.max(0, bottom - top);
  if (overlap === 0) {
    return 0;
  }
  const union = a.width * a.height + b.width * b.height - overlap;
  return union > 0 ? overlap / union : 0;
}

/**
 * Attach text from an earlier reading to boxes that were located but not read.
 *
 * This is what makes the cheap frames useful. A detection-only frame comes back
 * with boxes and no characters; matching each box against the last frame that
 * *was* read lets the overlay keep naming the plate while it moves, at
 * detection cost only.
 *
 * Unmatched boxes are left as they are rather than guessed at — a new vehicle
 * entering the shot is genuinely unnamed until the next reading frame, and
 * borrowing a neighbour's number would be worse than showing none.
 *
 * @param located - Boxes from a detection-only frame.
 * @param known - Results from the most recent frame that was read.
 * @returns The located boxes, with text copied in where a match was found.
 */
function carryTextForward(
  located: DetectionResult[],
  known: DetectionResult[],
): DetectionResult[] {
  if (known.length === 0) {
    return located;
  }

  return located.map((box) => {
    let best: DetectionResult | null = null;
    let bestScore = MATCH_MIN_IOU;

    for (const candidate of known) {
      if (candidate.plate_number === null) {
        continue;
      }
      const score = intersectionOverUnion(box.bbox, candidate.bbox);
      if (score > bestScore) {
        best = candidate;
        bestScore = score;
      }
    }

    if (best === null) {
      return box;
    }
    return {
      ...box,
      plate_number: best.plate_number,
      plate_display: best.plate_display,
      raw_ocr_text: best.raw_ocr_text,
      ocr_confidence: best.ocr_confidence,
      is_valid_format: best.is_valid_format,
      plate_kind: best.plate_kind,
      plate_color: best.plate_color,
    };
  });
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
  const captureCountRef = useRef(0);
  // The most recent frame that was actually read. Detection-only frames borrow
  // their text from here, so it must hold the raw server results rather than
  // enriched ones -- otherwise text would be copied from a copy, and a single
  // mismatch would propagate through every later frame instead of expiring at
  // the next reading.
  const lastReadResultsRef = useRef<DetectionResult[]>([]);
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

      // Read on one frame in every READ_TEXT_EVERY, starting with the first so
      // the very first answer carries names rather than bare boxes.
      const readText = captureCountRef.current % READ_TEXT_EVERY === 0;
      captureCountRef.current += 1;

      void (async () => {
        const controller = new AbortController();
        abortRef.current = controller;
        let captured: { blob: Blob; bitmap: ImageBitmap } | null = null;
        try {
          captured = await captureFrame(video);
          if (captured === null) {
            return;
          }

          const response = await detectFrame(
            captured.blob,
            jobIdRef.current,
            controller.signal,
            readText,
          );
          if (!isMountedRef.current || controller.signal.aborted) {
            return;
          }

          // Carry the session id forward so the whole preview counts as one
          // upload rather than one per frame.
          jobIdRef.current = response.job_id;

          if (readText) {
            lastReadResultsRef.current = response.results;
          }
          setResults(
            readText
              ? response.results
              : carryTextForward(response.results, lastReadResultsRef.current),
          );
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

          // Only genuine readings enter the log. A carried-forward box is the
          // same reading shown again, and counting it would inflate `reads`
          // into a count of frames rather than of times the plate was read.
          if (readText && response.results.length > 0) {
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
      // Restart the read/skip cycle so the first frame after resuming is a
      // reading one, and forget the carried text -- the user may have scrubbed
      // to an entirely different part of the clip while stopped, where those
      // boxes describe nothing.
      captureCountRef.current = 0;
      lastReadResultsRef.current = [];
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
