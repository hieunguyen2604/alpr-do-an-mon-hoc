/**
 * Shared constants: labels, limits and accepted file types.
 *
 * The upload limits here are a **client-side** convenience, not the rule. The
 * backend enforces its own ceilings and rejects an oversized file with 413
 * regardless of what this file says. Checking in the browser only saves the
 * user a pointless upload; it is not a control, and these numbers must be kept
 * in step with `max_image_size_bytes` and `max_video_size_bytes` in
 * `backend/core/config.py` or the two layers will disagree about what fits.
 */

import type { HistorySortField, InputType, JobStatus, SortOption } from '@/types';

// ---------------------------------------------------------------------------
// Labels
// ---------------------------------------------------------------------------

/** Vietnamese label for each input type. */
export const INPUT_TYPE_LABELS: Readonly<Record<InputType, string>> = {
  image: 'Ảnh',
  video: 'Video',
  webcam: 'Webcam',
};

/** Vietnamese label for each job status. */
export const JOB_STATUS_LABELS: Readonly<Record<JobStatus, string>> = {
  pending: 'Đang chờ',
  processing: 'Đang xử lý',
  completed: 'Hoàn thành',
  failed: 'Thất bại',
  cancelled: 'Đã huỷ',
};

/** Vietnamese label for each sortable column. */
export const SORT_FIELD_LABELS: Readonly<Record<HistorySortField, string>> = {
  detected_time: 'Thời điểm nhận dạng',
  created_at: 'Thời điểm lưu',
  plate_number: 'Biển số',
  confidence: 'Độ tin cậy',
};

/**
 * Job statuses after which nothing further will change.
 *
 * Polling must stop on these — a completed job polled forever is a request
 * every 1.5 seconds for as long as the tab stays open.
 */
export const TERMINAL_JOB_STATUSES: readonly JobStatus[] = [
  'completed',
  'failed',
  'cancelled',
];

/**
 * Whether a job has reached a terminal state.
 *
 * @param status - The status to test.
 * @returns `true` when no further change is expected.
 */
export function isTerminalStatus(status: JobStatus): boolean {
  return TERMINAL_JOB_STATUSES.includes(status);
}

// ---------------------------------------------------------------------------
// Sorting
// ---------------------------------------------------------------------------

/**
 * Sort choices offered on the history page.
 *
 * Each pairs the `sort_by` and `order` parameters the API takes separately, so
 * a dropdown manages one piece of state instead of two.
 */
export const SORT_OPTIONS: readonly SortOption[] = [
  {
    value: 'detected_time:desc',
    label: 'Mới nhất trước',
    sort_by: 'detected_time',
    order: 'desc',
  },
  {
    value: 'detected_time:asc',
    label: 'Cũ nhất trước',
    sort_by: 'detected_time',
    order: 'asc',
  },
  {
    value: 'confidence:desc',
    label: 'Độ tin cậy cao nhất',
    sort_by: 'confidence',
    order: 'desc',
  },
  {
    value: 'confidence:asc',
    label: 'Độ tin cậy thấp nhất',
    sort_by: 'confidence',
    order: 'asc',
  },
  {
    value: 'plate_number:asc',
    label: 'Biển số A → Z',
    sort_by: 'plate_number',
    order: 'asc',
  },
  {
    value: 'plate_number:desc',
    label: 'Biển số Z → A',
    sort_by: 'plate_number',
    order: 'desc',
  },
];

/** The sort applied when the user has not chosen one. */
export const DEFAULT_SORT_OPTION: SortOption = {
  value: 'detected_time:desc',
  label: 'Mới nhất trước',
  sort_by: 'detected_time',
  order: 'desc',
};

// ---------------------------------------------------------------------------
// Pagination
// ---------------------------------------------------------------------------

/**
 * Page sizes offered to the user.
 *
 * Capped at 100 because the backend rejects anything larger (`MAX_PAGE_SIZE`
 * in `history_service.py`) with a 422.
 */
export const PAGE_SIZE_OPTIONS: readonly number[] = [10, 20, 50, 100];

/** Rows per page before the user changes it. */
export const DEFAULT_PAGE_SIZE = 20;

/** Largest page size the API accepts. Mirrors `MAX_PAGE_SIZE` on the backend. */
export const MAX_PAGE_SIZE = 100;

// ---------------------------------------------------------------------------
// Upload limits
// ---------------------------------------------------------------------------

/** Largest image accepted, in megabytes. */
export const MAX_IMAGE_MB = 10;

/** Largest video accepted, in megabytes. */
export const MAX_VIDEO_MB = 200;

/** Largest image accepted, in bytes. */
export const MAX_IMAGE_BYTES = MAX_IMAGE_MB * 1024 * 1024;

/** Largest video accepted, in bytes. */
export const MAX_VIDEO_BYTES = MAX_VIDEO_MB * 1024 * 1024;

/**
 * Image MIME types the pipeline can decode.
 *
 * Note that the backend identifies a file by its **magic bytes**, not by this
 * header or by the extension (NFR-S1). A `.jpg` that is really a ZIP passes the
 * check in the browser and is still rejected with 415 by the server, which is
 * the intended division of labour.
 */
export const ACCEPTED_IMAGE_TYPES: readonly string[] = [
  'image/jpeg',
  'image/png',
  'image/webp',
  'image/bmp',
];

/** Video MIME types the pipeline can decode. */
export const ACCEPTED_VIDEO_TYPES: readonly string[] = [
  'video/mp4',
  'video/quicktime',
  'video/x-msvideo',
  'video/x-matroska',
];

/** Value for an `<input type="file">` accept attribute, images. */
export const ACCEPTED_IMAGE_ACCEPT = ACCEPTED_IMAGE_TYPES.join(',');

/** Value for an `<input type="file">` accept attribute, videos. */
export const ACCEPTED_VIDEO_ACCEPT = ACCEPTED_VIDEO_TYPES.join(',');

/** Human-readable image formats, for a Vietnamese hint under a dropzone. */
export const ACCEPTED_IMAGE_LABEL = 'JPG, PNG, WebP, BMP';

/** Human-readable video formats, for a Vietnamese hint under a dropzone. */
export const ACCEPTED_VIDEO_LABEL = 'MP4, MOV, AVI, MKV';

// ---------------------------------------------------------------------------
// Polling and interaction
// ---------------------------------------------------------------------------

/** How often to poll a running video job, in milliseconds. */
export const DEFAULT_POLL_INTERVAL_MS = 1500;

/** Delay before a search box issues a request, in milliseconds. */
export const DEFAULT_DEBOUNCE_MS = 400;

/** Length of the dashboard trend window, in days. */
export const DEFAULT_TREND_DAYS = 7;

// ---------------------------------------------------------------------------
// Confidence bands
// ---------------------------------------------------------------------------

/**
 * Thresholds separating high, medium and low confidence.
 *
 * A display convention shared by {@link confidenceColorClass} and the
 * confidence bar, so the colour and the wording cannot disagree about where a
 * given score sits.
 */
export const CONFIDENCE_THRESHOLDS = {
  /** At or above this counts as high. */
  high: 0.85,
  /** At or above this counts as medium. */
  medium: 0.6,
} as const;
