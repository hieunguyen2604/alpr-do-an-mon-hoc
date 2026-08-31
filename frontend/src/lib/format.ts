import type { InputType, JobStatus } from '@/types';

/** Locale driving number and date formatting. */
const LOCALE = 'vi-VN';

/** Rendered fallback when value is null/undefined. */
export const NO_VALUE = '—';

/** Format a 0.0-1.0 ratio as a Vietnamese percentage (e.g. "87,6%"). */
export function formatPercent(
  value: number | null | undefined,
  fractionDigits = 1,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return NO_VALUE;
  }
  return `${(value * 100).toLocaleString(LOCALE, {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  })}%`;
}

/** Format confidence score as a percentage. */
export function formatConfidence(
  value: number | null | undefined,
  fractionDigits = 1,
): string {
  return formatPercent(value, fractionDigits);
}

/** Format duration in seconds (switches to ms under 1s). */
export function formatProcessingTime(
  seconds: number | null | undefined,
): string {
  if (seconds === null || seconds === undefined || Number.isNaN(seconds)) {
    return NO_VALUE;
  }
  if (seconds < 1) {
    const milliseconds = seconds * 1000;
    if (milliseconds > 0 && milliseconds < 0.5) {
      return '< 1 ms';
    }
    return `${Math.round(milliseconds).toLocaleString(LOCALE)} ms`;
  }
  return `${seconds.toLocaleString(LOCALE, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} s`;
}

/** Alias of formatProcessingTime for generic durations. */
export function formatDuration(seconds: number | null | undefined): string {
  return formatProcessingTime(seconds);
}

/** Format an integer with thousands separators. */
export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return NO_VALUE;
  }
  return value.toLocaleString(LOCALE);
}

/** Format ISO timestamp as local date and time string. */
export function formatDateTime(isoString: string | null | undefined): string {
  const date = parseApiDate(isoString);
  if (!date) {
    return NO_VALUE;
  }
  return date.toLocaleString(LOCALE, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

/** Format ISO timestamp as local date string. */
export function formatDate(isoString: string | null | undefined): string {
  const date = parseApiDate(isoString);
  if (!date) {
    return NO_VALUE;
  }
  return date.toLocaleDateString(LOCALE, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

/** Format YYYY-MM-DD date as dd/mm label for chart axis. */
export function formatChartDate(isoDate: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(isoDate);
  if (!match) {
    return isoDate;
  }
  return `${match[3]}/${match[2]}`;
}

/** Parse ISO timestamp string to Date object. */
function parseApiDate(isoString: string | null | undefined): Date | null {
  if (!isoString) {
    return null;
  }
  const hasTime = isoString.includes('T') || isoString.includes(' ');
  const hasZone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(isoString);
  const normalized = hasTime && !hasZone ? `${isoString}Z` : isoString;

  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : date;
}

/** Format byte size to human readable units (B, KB, MB, GB). */
export function formatFileSize(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined || Number.isNaN(bytes)) {
    return NO_VALUE;
  }
  const units = ['B', 'KB', 'MB', 'GB', 'TB'] as const;
  let size = Math.max(0, bytes);
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }
  const decimals = unitIndex === 0 ? 0 : 2;
  return `${size.toLocaleString(LOCALE, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })} ${units[unitIndex]}`;
}

/** Normalise plate string whitespace and casing for display. */
export function formatPlateNumber(
  plateNumber: string | null | undefined,
): string {
  if (!plateNumber) {
    return 'Không đọc được';
  }
  const trimmed = plateNumber.replace(/\s+/g, ' ').trim().toUpperCase();
  return trimmed.length > 0 ? trimmed : 'Không đọc được';
}

/** Vietnamese labels for input types. */
const INPUT_TYPE_LABEL: Readonly<Record<InputType, string>> = {
  image: 'Ảnh',
  video: 'Video',
  webcam: 'Webcam',
};

/** Translate input type to Vietnamese label. */
export function formatInputType(inputType: InputType): string {
  return INPUT_TYPE_LABEL[inputType];
}

/** Vietnamese labels for job statuses. */
const JOB_STATUS_LABEL: Readonly<Record<JobStatus, string>> = {
  pending: 'Đang chờ',
  processing: 'Đang xử lý',
  completed: 'Hoàn thành',
  failed: 'Thất bại',
  cancelled: 'Đã huỷ',
};

/** Translate job status to Vietnamese label. */
export function formatJobStatus(status: JobStatus): string {
  return JOB_STATUS_LABEL[status];
}

/** Return Tailwind CSS colour classes for confidence score level. */
export function confidenceColorClass(
  confidence: number | null | undefined,
): string {
  if (confidence === null || confidence === undefined) {
    return 'bg-surface-muted text-content-muted';
  }
  if (confidence >= 0.85) {
    return 'bg-success/10 text-success';
  }
  if (confidence >= 0.6) {
    return 'bg-warning/10 text-warning';
  }
  return 'bg-danger/10 text-danger';
}

/** Return Tailwind CSS colour classes for job status badge. */
export function jobStatusColorClass(status: JobStatus): string {
  switch (status) {
    case 'completed':
      return 'bg-success/10 text-success';
    case 'processing':
    case 'pending':
      return 'bg-primary/10 text-primary';
    case 'failed':
      return 'bg-danger/10 text-danger';
    case 'cancelled':
      return 'bg-content-muted/10 text-content-muted';
    default:
      return 'bg-content-muted/10 text-content-muted';
  }
}

/** Render position within a video as m:ss. */
export function formatVideoTime(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || !Number.isFinite(seconds)) {
    return NO_VALUE;
  }
  const total = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(total / 60);
  return `${minutes}:${String(total % 60).padStart(2, '0')}`;
}
