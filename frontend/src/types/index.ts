/**
 * Wire types shared with the backend REST API.
 *
 * Every field name here is written in `snake_case` to match the JSON the
 * FastAPI layer emits verbatim. No camelCase conversion happens anywhere in the
 * frontend: a single naming convention end to end means a schema change shows
 * up as a TypeScript error rather than as a silently `undefined` value.
 *
 * These interfaces mirror the Pydantic response models in
 * `backend/schemas/detection.py`, which are the authoritative wire contract.
 * Field names here are the JSON names the API actually emits — note that they
 * are not always the underlying column names: the API renames
 * `detection_history.confidence` to `detection_confidence` on a detection
 * result, and omits columns such as `detection_job.error_message` entirely
 * (NFR-S4). When a schema changes, this file changes with it.
 */

// ---------------------------------------------------------------------------
// Enumerations
// ---------------------------------------------------------------------------

/** Where a detection came from. Persisted as `detection_history.input_type`. */
export type InputType = 'image' | 'video' | 'webcam';

/** Lifecycle of an asynchronous job. Persisted as `detection_job.status`. */
export type JobStatus =
  | 'pending'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'cancelled';

/** Number of text lines on a plate: 1 for cars, 2 for most motorcycles. */
export type PlateLineCount = 1 | 2;

/**
 * Plate family inferred from the character string.
 *
 * Mirrors `ai.inference.plate_rules.PlateKind`. Note what a string cannot
 * express: a commercial vehicle's yellow plate carries the same layout as a
 * private vehicle's white one, so both report `car`. See {@link PlateColor}.
 */
export type PlateKind =
  | 'car'
  | 'motorcycle_new'
  | 'motorcycle_old'
  | 'blue_car'
  | 'blue_motorcycle'
  | 'special'
  | 'diplomatic'
  | 'military'
  | 'unknown';

/**
 * Background colour read from the cropped plate.
 *
 * Per Circular 79/2024/TT-BCA: white = private or domestic organisation,
 * yellow = commercial transport, blue = state agency, red = army. Complements
 * {@link PlateKind} rather than replacing it — a diplomatic plate is white like
 * a private one, and only its string tells them apart.
 */
export type PlateColor = 'white' | 'yellow' | 'blue' | 'red' | 'unknown';

/**
 * Sortable columns of the history list (FR-4.8).
 *
 * Mirrors `SortField` in `backend/services/history_service.py`, which is a
 * `StrEnum` precisely because the value reaches an `ORDER BY` clause: an
 * unknown value is rejected by validation before any query is built. Adding a
 * member here that the backend does not know produces a 422, not a silent
 * fallback, so the two lists must stay in step.
 */
export type HistorySortField =
  | 'detected_time'
  | 'created_at'
  | 'plate_number'
  | 'confidence';

/** Sort direction. */
export type SortOrder = 'asc' | 'desc';

/**
 * A sort choice as one selectable unit, for a dropdown.
 *
 * The API takes `sort_by` and `order` as two independent parameters, but a user
 * picks "newest first" as a single idea. Pairing them here keeps a select
 * element from having to manage two pieces of state that are only meaningful
 * together.
 */
export interface SortOption {
  /** Stable key for the option, e.g. `"detected_time:desc"`. */
  value: string;
  /** Vietnamese label shown in the dropdown. */
  label: string;
  sort_by: HistorySortField;
  order: SortOrder;
}

// ---------------------------------------------------------------------------
// Detection
// ---------------------------------------------------------------------------

/**
 * Plate location in pixels, in the coordinate space of the processed image.
 *
 * The origin is the top-left corner, x grows right and y grows down — the
 * OpenCV convention used by the AI pipeline. The database stores these four
 * numbers flat as `bbox_x`, `bbox_y`, `bbox_w`, `bbox_h`; the API nests them so
 * a result object stays readable.
 *
 * Overlays must be scaled by the ratio between the rendered element size and
 * `DetectionResponse.image_width` / `image_height` — never assumed to be 1:1.
 */
export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

/**
 * One license plate found in one image or frame.
 *
 * The two confidence values are deliberately separate. `confidence` scores the
 * YOLO detection (did we find a plate?) and `ocr_confidence` scores the OCR
 * read (did we read it correctly?). Merging them would make it impossible to
 * tell which stage was uncertain, which is exactly the analysis the evaluation
 * chapter needs.
 */
export interface DetectionResult {
  /**
   * Normalised plate string after regex correction, e.g. `"51F-12345"`.
   * `null` when OCR read nothing — the detection is still reported.
   */
  plate_number: string | null;
  /** Unmodified OCR output, kept so post-processing gain stays measurable. */
  raw_ocr_text: string | null;
  /**
   * Detector (YOLO) confidence, 0.0 to 1.0.
   *
   * Named `detection_confidence` rather than `confidence` to mirror
   * `DetectionResultSchema` on the backend, where the explicit name keeps it
   * from being confused with `ocr_confidence` at the call site.
   */
  detection_confidence: number;
  /** OCR confidence, 0.0 to 1.0. `null` when no text was read. */
  ocr_confidence: number | null;
  /** Where the plate sits in the source image. */
  bbox: BoundingBox;
  /**
   * Whether `plate_number` matches a known **civil** Vietnamese plate format.
   *
   * Do not render this alone. An army plate is a genuine plate that reports
   * `false` by design, because it lies outside the civil registration system —
   * showing that as "wrong format" contradicts a correct reading. Pass it
   * through `plateClassBadges` together with `plate_kind`.
   */
  is_valid_format: boolean;
  /**
   * Plate family inferred from the character string. `null` on records stored
   * before 2026-07-20, when the classification was computed and then discarded.
   */
  plate_kind: PlateKind | null;
  /**
   * Background colour read from the crop. Carries what no rule over the string
   * can: a commercial vehicle's yellow plate and a private vehicle's white one
   * are the same string.
   */
  plate_color: PlateColor | null;
  /** Fraction of sampled pixels supporting `plate_color`. Not a probability. */
  plate_color_confidence: number | null;
  /**
   * `plate_number` with the separators the physical plate carries, e.g.
   * `29E-015.66`. Display only — search and comparison use `plate_number`.
   */
  plate_display: string | null;
  /** 1 or 2. Reported so accuracy can be split by plate layout. */
  plate_line_count: PlateLineCount | null;
  /** Seconds spent on this plate: detection plus OCR. */
  processing_time: number;
  /** URL of the cropped plate image, or `null` if the crop was not kept. */
  plate_image_url: string | null;
}

/**
 * Response of `POST /api/detect/image` and `POST /api/detect/frame`.
 *
 * A single upload can contain several plates, so `results` is a list. All of
 * them share one `job_id` — that grouping is what makes dashboard statistics
 * count uploads instead of rows.
 *
 * An empty `results` array is a normal outcome (no plate in the picture), not
 * an error, and is returned with HTTP 200.
 */
export interface DetectionResponse {
  /** Identifier grouping every plate found in this one upload. */
  job_id: string;
  input_type: InputType;
  /**
   * URL of the stored source image. `null` for webcam frames, which are
   * processed but deliberately not persisted.
   */
  image_url: string | null;
  /** Width of the processed image, needed to scale bounding-box overlays. */
  image_width: number;
  /** Height of the processed image, needed to scale bounding-box overlays. */
  image_height: number;
  /**
   * Wall-clock seconds for the whole run. Not the sum of the per-plate times:
   * it also covers decoding, pre-processing and work shared between plates.
   */
  processing_time: number;
  /** Number of plates detected, i.e. the length of `results`. */
  plate_count: number;
  results: DetectionResult[];
}

// ---------------------------------------------------------------------------
// History
// ---------------------------------------------------------------------------

/**
 * One stored row of `detection_history` — a single plate, not a single upload.
 *
 * Fields map one-to-one onto the table columns, including the flat `bbox_*`
 * quartet, so the record can be rendered without a second request.
 */
export interface DetectionHistory {
  id: number;
  /** `null` when OCR read nothing; the located plate is still recorded. */
  plate_number: string | null;
  raw_ocr_text: string | null;
  /** Detector (YOLO) confidence, 0.0 to 1.0. */
  confidence: number;
  /** OCR confidence, 0.0 to 1.0. `null` when no text was read. */
  ocr_confidence: number | null;
  input_type: InputType;
  /**
   * URL of the source image. The backend replaces the stored filesystem path
   * with a `/files/...` URL before serialising, so the server's directory
   * layout is never published.
   */
  image_path: string | null;
  /** URL of the cropped plate image, same treatment as `image_path`. */
  plate_image_path: string | null;
  bbox_x: number;
  bbox_y: number;
  bbox_w: number;
  bbox_h: number;
  /** Civil-format verdict. Read together with `plate_kind` — see the note on
   * {@link DetectionResult.is_valid_format}. */
  is_valid_format: boolean;
  /** Plate family from the string. `null` on rows stored before 2026-07-20. */
  plate_kind: PlateKind | null;
  /** Background colour from the crop. `null` on rows stored before 2026-07-20. */
  plate_color: PlateColor | null;
  /** Fraction of sampled pixels supporting `plate_color`. */
  plate_color_confidence: number | null;
  /**
   * `plate_number` with the separators the physical plate carries. Derived on
   * read rather than stored, so it is present on every row including old ones.
   */
  plate_display: string | null;
  /**
   * Where in the source clip this plate was found, in seconds. `null` for
   * images and realtime frames, which have no timeline, and for rows written
   * before migration `0003`.
   */
  video_time_seconds: number | null;
  plate_line_count: PlateLineCount | null;
  /** Seconds. */
  processing_time: number;
  /** ISO 8601 timestamp. */
  detected_time: string;
  /** ISO 8601 timestamp. */
  created_at: string;
  /**
   * Groups every plate belonging to the same upload. Never null: the column is
   * mandatory precisely so usage statistics and the history list cannot
   * disagree about how many uploads exist.
   */
  source_job_id: string;
  /** The four `bbox_*` columns as one object, derived by the backend. */
  bbox: BoundingBox;
}

/**
 * Alias of {@link DetectionHistory}, for call sites that read better as "a
 * record" than as "a history".
 *
 * One row is one **license plate**, not one upload: an image containing three
 * plates is three records sharing one `source_job_id`.
 */
export type DetectionRecord = DetectionHistory;

/** Query parameters accepted by `GET /api/history` (FR-4.3 to FR-4.5, FR-4.8). */
export interface HistoryQuery {
  /** 1-based page number. */
  page?: number;
  /** Rows per page. */
  page_size?: number;
  /** Partial, case-insensitive match on the plate string. */
  search?: string;
  input_type?: InputType;
  /** Inclusive lower bound on `detected_time`, ISO 8601. */
  date_from?: string;
  /** Inclusive upper bound on `detected_time`, ISO 8601. */
  date_to?: string;
  /** Keep only rows whose detector confidence is at least this value. */
  min_confidence?: number;
  /** Keep only rows whose plate matched a valid Vietnamese format. */
  is_valid_format?: boolean;
  /** Keep only the plates found in one upload. */
  job_id?: string;
  sort_by?: HistorySortField;
  /**
   * Sort direction.
   *
   * Named `order`, not `sort_order`: that is the query parameter the backend
   * declares. FastAPI ignores unknown parameters rather than rejecting them, so
   * sending `sort_order` produces a perfectly successful 200 that is silently
   * sorted by the server's default instead of by what the user asked for.
   */
  order?: SortOrder;
}

/**
 * Filters as a page holds them in state.
 *
 * Identical in shape to {@link HistoryQuery} — the alias exists so that UI code
 * reads as "the filters the user chose" while the client reads as "the query
 * sent to the API", without two definitions that could drift apart.
 */
export type HistoryFilters = HistoryQuery;

/** Paginated envelope returned by `GET /api/history`. */
export interface HistoryListResponse {
  items: DetectionHistory[];
  /** Total rows matching the filters, across every page. */
  total: number;
  /** 1-based page number that was returned. */
  page: number;
  page_size: number;
  total_pages: number;
}

// ---------------------------------------------------------------------------
// Jobs
// ---------------------------------------------------------------------------

/**
 * An asynchronous processing task, as returned by `GET /api/jobs/{job_id}`.
 *
 * Video runs are queued rather than awaited: a 60-second clip takes roughly
 * 200 seconds on CPU, well past any sensible HTTP timeout. `POST /api/detect/video`
 * answers 202 with this object, and the frontend polls until `status` becomes
 * `completed` or `failed`.
 *
 * There is deliberately no `error_message` field. A failed job's technical
 * reason is written to the server log under the request's `request_id` and is
 * never serialised here (NFR-S4); the UI reports the failure from `status`
 * alone.
 */
export interface DetectionJob {
  /** UUID. Matches `detection_history.source_job_id` of the rows it produced. */
  id: string;
  input_type: InputType;
  status: JobStatus;
  /** Completion ratio from 0.0 to 1.0 — multiply by 100 to show a percentage. */
  progress: number;
  /** URL of the rendered annotated output, present once `status` is `completed`. */
  output_url: string | null;
  /** Total frames to process. `null` until the video has been probed. */
  total_frames: number | null;
  /** Frames processed so far. */
  processed_frames: number;
  /** License plates found by this job so far. */
  detection_count: number;
  /** ISO 8601 timestamp. */
  created_at: string;
  /** ISO 8601 timestamp, `null` while the job is still running. */
  completed_at: string | null;
}

// ---------------------------------------------------------------------------
// Statistics
// ---------------------------------------------------------------------------

/** One slice of the input-type distribution shown on the dashboard. */
export interface InputTypeBreakdown {
  input_type: InputType;
  /** Number of uploads (rows in `detection_job`). */
  job_count: number;
  /** Number of plates found across those uploads. */
  detection_count: number;
}

/** One point on the "detections over time" chart (FR-4.2). */
export interface DetectionsOverTimePoint {
  /** Calendar day, `YYYY-MM-DD`. */
  date: string;
  /** Uploads on that day. */
  job_count: number;
  /** Plates recognised on that day. */
  detection_count: number;
}

/**
 * Aggregates from `GET /api/statistics` (was FR-4.1, FR-4.2).
 *
 * **No consumer in this application since 2026-07-20.** The Dashboard page was
 * removed from the interface, so nothing in `src/` reads this type today. It is
 * kept because the endpoint it mirrors is still served and still tested — this
 * file is the frontend's copy of the wire contract, and dropping the mirror
 * while the contract lives would make a future dashboard, or any external
 * client, start from a blank page. Do not "clean it up" without also checking
 * `backend/api/routes/statistics.py`.
 *
 * `total_jobs` and `total_detections` are separate on purpose and must not be used
 * interchangeably. One image containing three plates is **one** job and
 * **three** plates. The headline "number of recognitions" figure is
 * `total_jobs`, counted over distinct `source_job_id` values — counting
 * `detection_history` rows instead would overstate usage on every multi-plate
 * upload.
 */
export interface Statistics {
  /** Uploads processed — rows in `detection_job`. The headline metric. */
  total_jobs: number;
  /** Plates found — rows in `detection_history`. Always >= `total_jobs`. */
  total_detections: number;
  /** Distinct plate numbers recognised. */
  unique_plates: number;
  /** Plates whose text matched a valid Vietnamese format. */
  valid_format_count: number;
  /** Plates whose text was read but matched no known format. */
  invalid_format_count: number;
  /**
   * Plates located by the detector that OCR could not read at all.
   *
   * These three counters partition `total_detections`, so a chart built from
   * them adds up to the total sitting next to it.
   */
  unreadable_count: number;
  /**
   * Mean detector confidence, 0.0 to 1.0.
   *
   * `null` rather than `0` when there is nothing to average — a mean of zero
   * would read as "the model is certain of nothing", which is a different
   * statement from "no data yet".
   */
  average_confidence: number | null;
  /** Mean OCR confidence across records that produced text, 0.0 to 1.0. */
  average_ocr_confidence: number | null;
  /** Mean seconds per plate. */
  average_processing_time: number | null;
  /** Uploads created today, UTC. */
  jobs_today: number;
  /** Plates detected today, UTC. */
  detections_today: number;
  by_input_type: InputTypeBreakdown[];
  /** Per-day activity over the requested window, oldest first. */
  daily_counts: DetectionsOverTimePoint[];
}

/** Query parameters accepted by `GET /api/statistics`. */
export interface StatisticsQuery {
  /**
   * Length of the daily trend window in days, ending today (UTC).
   *
   * Days with no activity come back with zero counts rather than being
   * omitted, so a chart drawn from `daily_counts` does not silently close the
   * gaps and overstate a quiet week.
   */
  days?: number;
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

/**
 * Service readiness, from `GET /health`.
 *
 * Note that this endpoint sits at the **root**, not under the `/api` prefix: a
 * health check that moves when the API prefix changes is not much of a health
 * check.
 *
 * Reports readiness rather than liveness. `status` is `degraded` when the
 * process is answering but a dependency is not usable — most commonly the
 * detector weights failed to load, in which case the API is up and yet cannot
 * serve a single detection.
 */
export interface HealthStatus {
  status: 'ok' | 'degraded';
  app_name: string;
  version: string;
  database_connected: boolean;
  /** Whether the detection model weights are loaded and ready. */
  model_loaded: boolean;
  uptime_seconds: number;
  /** ISO 8601 timestamp. */
  timestamp: string;
}

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

/**
 * Error body returned by the API.
 *
 * The backend never exposes a stack trace; it logs the traceback against the
 * request id and returns only these safe fields. `request_id` is surfaced in
 * the UI so a user can quote it when reporting a problem, which is what makes
 * a report traceable back to the server log.
 */
export interface ApiErrorResponse {
  /**
   * Stable machine-readable code, e.g. `"FILE_TOO_LARGE"`. Branch on this
   * rather than on `message`, whose wording may change.
   */
  error: string;
  /** Message intended for display, already in Vietnamese. */
  message?: string;
  /** Correlation id echoed from the `X-Request-ID` header. */
  request_id?: string;
}

/**
 * A failed request, normalised by the axios interceptor.
 *
 * Every rejection surfaced to a component is one of these, so error handling
 * never has to inspect raw axios internals or guess at a shape.
 */
export interface ApiError {
  /** HTTP status, or 0 when the request never reached the server. */
  status: number;
  /** Vietnamese, display-ready, free of any stack trace. */
  message: string;
  /** Machine-readable code when the backend supplied one. */
  code?: string;
  /** Correlation id for cross-referencing the server log. */
  request_id?: string;
}
