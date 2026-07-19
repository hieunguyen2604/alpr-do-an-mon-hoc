/**
 * Local types for the realtime webcam view.
 *
 * These describe browser-side concepts only — a camera device, a capture
 * measurement, a per-session plate tally. Nothing here crosses the wire, which
 * is why the fields are `camelCase` while everything in `@/types` (the API
 * contract) stays `snake_case`. The naming difference is the reminder of which
 * side of the boundary a value came from.
 */

/**
 * Why the camera could not be opened.
 *
 * Kept as a closed union rather than a free-form string because each kind maps
 * to a different recovery instruction: telling a user to re-grant permission
 * when the real problem is that no camera is plugged in wastes their time.
 */
export type CameraErrorKind =
  | 'unsupported'
  | 'insecure_context'
  | 'permission_denied'
  | 'no_device'
  | 'device_busy'
  | 'constraints'
  | 'disconnected'
  | 'unknown';

/** A camera failure, already translated for display. */
export interface CameraError {
  kind: CameraErrorKind;
  /** What went wrong, in Vietnamese. Never a raw `DOMException` name. */
  message: string;
  /** What the user should do about it, in Vietnamese. */
  hint: string;
}

/** One selectable video input, as reported by `enumerateDevices`. */
export interface CameraDevice {
  deviceId: string;
  /**
   * Human-readable name.
   *
   * Browsers return an empty label until camera permission has been granted, so
   * this falls back to a positional name ("Camera 1") rather than rendering a
   * blank option.
   */
  label: string;
}

/**
 * One distinct plate string seen during the current webcam session.
 *
 * The session log is deduplicated by plate text on purpose. A vehicle held in
 * front of the camera for ten seconds produces roughly fifteen frames and
 * fifteen identical readings; listing each one would bury every *other* plate
 * under repetitions of the nearest one. Collapsing to one row per plate — with
 * a sighting count and the best score — keeps the list readable while losing
 * nothing that matters.
 */
export interface SessionPlateRow {
  /**
   * Deduplication key: the plate text reduced to letters and digits, uppercased.
   *
   * Separate from {@link plateNumber} because the two answer different
   * questions. The key answers "is this the same vehicle?", for which `-` and a
   * space are noise: OCR reading `90C-76040` on one frame and `90C 76040` on the
   * next must produce one row, not two. The displayed text answers "what did the
   * system read?", where deleting a separator would misreport the result.
   */
  key: string;
  /** Plate text as it should be displayed, from the most confident sighting. */
  plateNumber: string;
  /** How many frames this plate was recognised in. */
  occurrences: number;
  /** Highest detector (YOLO) confidence seen for this plate, 0.0 to 1.0. */
  bestConfidence: number;
  /**
   * Highest OCR confidence seen, or `null` if no sighting reported one.
   *
   * The best score is kept rather than the latest: across many frames the
   * clearest read is the most informative summary, and it is stable while the
   * latest value flickers with every frame.
   */
  bestOcrConfidence: number | null;
  /** Whether any sighting matched a valid Vietnamese plate format. */
  isValidFormat: boolean;
  /** Number of text lines, from the most confident sighting. */
  plateLineCount: 1 | 2 | null;
  /** When this plate was first recognised in the session. */
  firstSeenAt: Date;
  /** When this plate was most recently recognised. */
  lastSeenAt: Date;
}

/** Columns the session table can be ordered by, sorted in the browser. */
export type SessionSortKey =
  | 'plateNumber'
  | 'occurrences'
  | 'bestConfidence'
  | 'lastSeenAt';

/**
 * Live measurements of the capture loop.
 *
 * Shown on screen because NFR-P2 is stated in frames per second, and a figure
 * that is only visible in a profiler cannot be quoted in an evaluation
 * chapter. It is also the fastest way to tell a slow model from a slow network
 * during a demo: `lastProcessingTimeSeconds` is the server's own measurement,
 * while `lastRoundTripSeconds` includes upload, queueing and download.
 */
export interface CaptureMetrics {
  /** Frames actually sent to the server. */
  framesSent: number;
  /**
   * Frames dropped because a request was still in flight.
   *
   * A healthy number here is not a fault: it is the single-slot policy working.
   * It becomes interesting when it dwarfs `framesSent`, which means the capture
   * interval is set well below what the machine can process.
   */
  framesSkipped: number;
  /** Frames the server answered successfully. */
  framesCompleted: number;
  /** Measured throughput over a trailing window, or `null` before the first
   *  measurement. */
  fps: number | null;
  /** Server-reported seconds for the most recent frame. */
  lastProcessingTimeSeconds: number | null;
  /** Browser-measured seconds from send to response, including transfer. */
  lastRoundTripSeconds: number | null;
  /** Mean of every server-reported processing time this session. */
  averageProcessingTimeSeconds: number | null;
}
