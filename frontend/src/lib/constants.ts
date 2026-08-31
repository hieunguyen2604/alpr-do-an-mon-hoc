import type { HistorySortField, InputType, JobStatus, SortOption } from '@/types';

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

/** Job statuses after which processing has ended. */
export const TERMINAL_JOB_STATUSES: readonly JobStatus[] = [
  'completed',
  'failed',
  'cancelled',
];

/** Return true if status represents a completed/failed/cancelled terminal state. */
export function isTerminalStatus(status: JobStatus): boolean {
  return TERMINAL_JOB_STATUSES.includes(status);
}

/** Sort choices available on the history page. */
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

/** Default sort option for history list. */
export const DEFAULT_SORT_OPTION: SortOption = {
  value: 'detected_time:desc',
  label: 'Mới nhất trước',
  sort_by: 'detected_time',
  order: 'desc',
};

/** Page sizes offered to the user. */
export const PAGE_SIZE_OPTIONS: readonly number[] = [10, 20, 50, 100];

/** Default page size for paginated requests. */
export const DEFAULT_PAGE_SIZE = 20;

/** Max page size supported by the backend. */
export const MAX_PAGE_SIZE = 100;

/** Maximum allowed upload image size in megabytes. */
export const MAX_IMAGE_MB = 10;

/** Maximum allowed upload video size in megabytes. */
export const MAX_VIDEO_MB = 200;

/** Maximum allowed upload image size in bytes. */
export const MAX_IMAGE_BYTES = MAX_IMAGE_MB * 1024 * 1024;

/** Maximum allowed upload video size in bytes. */
export const MAX_VIDEO_BYTES = MAX_VIDEO_MB * 1024 * 1024;

/** Accepted image MIME types. */
export const ACCEPTED_IMAGE_TYPES: readonly string[] = [
  'image/jpeg',
  'image/png',
  'image/webp',
  'image/bmp',
];

/** Accepted video MIME types. */
export const ACCEPTED_VIDEO_TYPES: readonly string[] = [
  'video/mp4',
  'video/quicktime',
  'video/x-msvideo',
  'video/x-matroska',
];

/** File input accept attribute string for images. */
export const ACCEPTED_IMAGE_ACCEPT = ACCEPTED_IMAGE_TYPES.join(',');

/** File input accept attribute string for videos. */
export const ACCEPTED_VIDEO_ACCEPT = ACCEPTED_VIDEO_TYPES.join(',');

/** Human-readable image formats label. */
export const ACCEPTED_IMAGE_LABEL = 'JPG, PNG, WebP, BMP';

/** Human-readable video formats label. */
export const ACCEPTED_VIDEO_LABEL = 'MP4, MOV, AVI, MKV';

/** Polling interval for background video jobs in ms. */
export const DEFAULT_POLL_INTERVAL_MS = 1500;

/** Search input debounce delay in ms. */
export const DEFAULT_DEBOUNCE_MS = 400;

/** Default dashboard trend window in days. */
export const DEFAULT_TREND_DAYS = 7;

/** Confidence score threshold levels. */
export const CONFIDENCE_THRESHOLDS = {
  high: 0.85,
  medium: 0.6,
} as const;
