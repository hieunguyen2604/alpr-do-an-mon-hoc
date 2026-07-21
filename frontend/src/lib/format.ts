/**
 * Display formatting helpers — the single source of truth for how a value
 * reaches the screen.
 *
 * Vietnamese conventions are the point of this module: a **comma** decimal mark
 * and a **dot** thousands separator, the reverse of the English defaults. Every
 * number therefore goes through `toLocaleString('vi-VN')` rather than
 * `toFixed`, which would hard-code an English decimal point into the UI.
 *
 * Missing values render as an em dash rather than as zero. The API sends `null`
 * to mean "nothing to average yet", and an average confidence printed as
 * "0,0%" reads as "the model is certain of nothing" — a different and wrong
 * statement, and a plausible enough one to survive review.
 */

import type { InputType, JobStatus } from '@/types';

/** Locale driving every number and date in the interface. */
const LOCALE = 'vi-VN';

/** Rendered wherever the API reported no value at all. */
export const NO_VALUE = '—';

/**
 * Format a 0.0-1.0 ratio as a Vietnamese percentage.
 *
 * @param value - Ratio between 0.0 and 1.0, or `null`/`undefined` when
 *   unavailable.
 * @param fractionDigits - Decimal places to keep.
 * @returns For example `formatPercent(0.876)` is `"87,6%"`; `"—"` when there is
 *   no value.
 */
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

/**
 * Format a confidence score for display.
 *
 * A named wrapper over {@link formatPercent}: confidence is the value shown
 * most often in this interface, and naming it makes the call sites say what
 * they mean.
 *
 * @param value - Score between 0.0 and 1.0, or `null` when OCR read nothing.
 * @param fractionDigits - Decimal places to keep.
 * @returns For example `formatConfidence(0.876)` is `"87,6%"`.
 */
export function formatConfidence(
  value: number | null | undefined,
  fractionDigits = 1,
): string {
  return formatPercent(value, fractionDigits);
}

/**
 * Format a duration given in seconds.
 *
 * Switches to milliseconds below one second, where "0,23 s" reads worse than
 * "234 ms" — and where the millisecond figure is the one being compared
 * against the performance requirements.
 *
 * A duration that is real but shorter than half a millisecond reports as
 * `"< 1 ms"` rather than rounding to `"0 ms"`. Zero is a claim that the work
 * took no time at all, which is never true of work that ran — the same reason
 * a missing average prints as a dash instead of as `0`. The stub pipeline
 * averages around 5e-05 s, so this is the ordinary case before the real model
 * is wired up, not a hypothetical one.
 *
 * @param seconds - Duration in seconds, or `null` when unavailable.
 * @returns For example `formatProcessingTime(0.234)` is `"234 ms"` and
 *   `formatProcessingTime(1.24)` is `"1,24 s"`; `"—"` when there is no value.
 */
export function formatProcessingTime(
  seconds: number | null | undefined,
): string {
  if (seconds === null || seconds === undefined || Number.isNaN(seconds)) {
    return NO_VALUE;
  }
  if (seconds < 1) {
    const milliseconds = seconds * 1000;
    // A genuine zero still prints as "0 ms"; only a positive value too small to
    // round to one millisecond takes the "less than" form.
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

/**
 * Alias of {@link formatProcessingTime} for durations that are not a
 * processing time.
 *
 * @param seconds - Duration in seconds, or `null` when unavailable.
 * @returns The formatted duration.
 */
export function formatDuration(seconds: number | null | undefined): string {
  return formatProcessingTime(seconds);
}

/**
 * Format an integer with Vietnamese thousands separators.
 *
 * @param value - The number to format, or `null` when unavailable.
 * @returns For example `"1.234"`; `"—"` when there is no value.
 */
export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return NO_VALUE;
  }
  return value.toLocaleString(LOCALE);
}

/**
 * Format an ISO 8601 timestamp as a local date and time.
 *
 * The API sends UTC with a trailing `Z`, which `Date` converts to the viewer's
 * own zone — the correct behaviour here, since a user in Vietnam reading
 * "09:31" wants their own clock, not the server's. A timestamp arriving
 * *without* the `Z` would be read as local time and be silently seven hours
 * off, so the marker is added when the backend omits it.
 *
 * @param isoString - Timestamp from the API.
 * @returns For example `"19/07/2026 16:32:05"`; `"—"` if absent or unparsable.
 */
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

/**
 * Format an ISO 8601 timestamp as a local date, without the time.
 *
 * @param isoString - Timestamp or `YYYY-MM-DD` date from the API.
 * @returns For example `"19/07/2026"`; `"—"` if absent or unparsable.
 */
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

/**
 * Format a `YYYY-MM-DD` day as a short `dd/mm` label for a chart axis.
 *
 * Parsed as a plain calendar day rather than as an instant: `daily_counts`
 * entries are dates, and converting them through a timezone can shift a bar to
 * the neighbouring day.
 *
 * @param isoDate - Calendar date, `YYYY-MM-DD`.
 * @returns For example `"19/07"`; the input unchanged if it does not parse.
 */
export function formatChartDate(isoDate: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(isoDate);
  if (!match) {
    return isoDate;
  }
  return `${match[3]}/${match[2]}`;
}

/**
 * Parse a timestamp coming from the API.
 *
 * @param isoString - The value to parse.
 * @returns A `Date`, or `null` when absent or unparsable.
 */
function parseApiDate(isoString: string | null | undefined): Date | null {
  if (!isoString) {
    return null;
  }
  // A bare `YYYY-MM-DD` is already interpreted as UTC midnight by `Date`; only
  // a date-time lacking a zone designator needs one supplied.
  const hasTime = isoString.includes('T') || isoString.includes(' ');
  const hasZone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(isoString);
  const normalized = hasTime && !hasZone ? `${isoString}Z` : isoString;

  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : date;
}

/**
 * Format a byte count in binary units.
 *
 * @param bytes - Size in bytes.
 * @returns For example `formatFileSize(4404019)` is `"4,20 MB"`.
 */
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

/**
 * Normalise a plate string for display.
 *
 * Only whitespace and case are touched. The characters themselves are never
 * "corrected" here — turning an OCR `O` into a `0` in the presentation layer
 * would hide exactly the error the evaluation chapter measures, and would make
 * the displayed text disagree with the stored record.
 *
 * @param plateNumber - Plate text from the API, or `null` when OCR read
 *   nothing.
 * @returns The tidied plate, or `"Không đọc được"` when there is no text.
 */
export function formatPlateNumber(
  plateNumber: string | null | undefined,
): string {
  if (!plateNumber) {
    return 'Không đọc được';
  }
  const trimmed = plateNumber.replace(/\s+/g, ' ').trim().toUpperCase();
  return trimmed.length > 0 ? trimmed : 'Không đọc được';
}

/** Vietnamese labels for the input types. */
const INPUT_TYPE_LABEL: Readonly<Record<InputType, string>> = {
  image: 'Ảnh',
  video: 'Video',
  webcam: 'Webcam',
};

/**
 * Translate an input type into its Vietnamese label.
 *
 * @param inputType - Value from the API.
 * @returns The label to display.
 */
export function formatInputType(inputType: InputType): string {
  return INPUT_TYPE_LABEL[inputType];
}

/** Vietnamese labels for the job statuses. */
const JOB_STATUS_LABEL: Readonly<Record<JobStatus, string>> = {
  pending: 'Đang chờ',
  processing: 'Đang xử lý',
  completed: 'Hoàn thành',
  failed: 'Thất bại',
  cancelled: 'Đã huỷ',
};

/**
 * Translate a job status into its Vietnamese label.
 *
 * @param status - Value from the API.
 * @returns The label to display.
 */
export function formatJobStatus(status: JobStatus): string {
  return JOB_STATUS_LABEL[status];
}

/**
 * Pick Tailwind colour classes for a confidence score.
 *
 * The thresholds are a display convention only — nothing is filtered by them.
 * A low-confidence result is still shown, just visually flagged.
 *
 * @param confidence - Score between 0.0 and 1.0, or `null` when OCR read
 *   nothing. A missing score is styled neutrally rather than as a low one: an
 *   unread plate has no confidence, which is not the same as a bad one.
 * @returns Tailwind classes for background and text colour.
 */
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

/**
 * Pick Tailwind colour classes for a job status.
 *
 * @param status - The job status.
 * @returns Tailwind classes for background and text colour.
 */
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

/**
 * Render a position within a video as `m:ss`.
 *
 * Distinct from {@link formatProcessingTime}, which measures how long something
 * took. This measures *where* in a clip a plate was found, so the reader can
 * seek to it — the difference matters enough that reusing the duration
 * formatter here would produce "74,2 s" where "1:14" is what a video player
 * shows.
 *
 * @param seconds - Offset from the start of the clip, or `null`.
 * @returns For example `formatVideoTime(74.2)` is `"1:14"`; {@link NO_VALUE}
 *   when there is no value — a plate from an image has no position in a video,
 *   and `0:00` would claim it came from the opening frame.
 */
export function formatVideoTime(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || !Number.isFinite(seconds)) {
    return NO_VALUE;
  }
  const total = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(total / 60);
  return `${minutes}:${String(total % 60).padStart(2, '0')}`;
}
