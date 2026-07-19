/**
 * Headline figures for one completed image detection.
 *
 * The plate count is the number of plates found in this **one** upload. On the
 * dashboard the equivalent distinction is `total_jobs` versus
 * `total_detections`; here there is exactly one job, so the figure shown is
 * unambiguously a plate count and is labelled as such rather than as a number of
 * "recognitions", which would blur the two ideas.
 */

import { Clock, ScanLine, Type } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

import { cn } from '@/lib/cn';
import { formatNumber, formatProcessingTime } from '@/lib/format';
import type { DetectionResponse } from '@/types';

/** Props of {@link DetectionSummary}. */
export interface DetectionSummaryProps {
  /** The completed detection to summarise. */
  response: DetectionResponse;
  className?: string;
}

/** One figure in the summary strip. */
interface SummaryItemProps {
  icon: LucideIcon;
  label: string;
  value: string;
  hint?: string;
}

/**
 * Render one labelled figure.
 *
 * @param props - Icon, label, value and optional clarifying hint.
 * @returns The figure element.
 */
function SummaryItem({
  icon: Icon,
  label,
  value,
  hint,
}: SummaryItemProps): JSX.Element {
  return (
    <div className="flex items-start gap-2.5">
      <span
        aria-hidden="true"
        className={cn(
          'mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center',
          'rounded-lg bg-surface-raised text-content-muted',
        )}
      >
        <Icon className="h-4 w-4" />
      </span>
      <div className="min-w-0">
        <p className="text-xs text-content-muted">{label}</p>
        <p className="text-sm font-semibold tabular-nums text-content">{value}</p>
        {hint && <p className="mt-0.5 text-[11px] text-content-muted">{hint}</p>}
      </div>
    </div>
  );
}

/**
 * Render the summary strip.
 *
 * @param props - The detection response to summarise.
 * @returns The summary element.
 */
export function DetectionSummary({
  response,
  className,
}: DetectionSummaryProps): JSX.Element {
  const readableCount = response.results.filter(
    (result) => result.plate_number !== null,
  ).length;
  const validCount = response.results.filter(
    (result) => result.is_valid_format && result.plate_number !== null,
  ).length;

  return (
    <div
      className={cn(
        'grid gap-4 rounded-lg border border-border bg-surface-muted p-4',
        'sm:grid-cols-3',
        className,
      )}
    >
      <SummaryItem
        icon={ScanLine}
        label="Biển số phát hiện được"
        value={formatNumber(response.plate_count)}
        hint="Trong một lượt tải lên"
      />
      <SummaryItem
        icon={Type}
        label="Đọc được ký tự"
        value={`${formatNumber(readableCount)}/${formatNumber(response.plate_count)}`}
        hint={`${formatNumber(validCount)} biển đúng định dạng`}
      />
      <SummaryItem
        icon={Clock}
        label="Thời gian xử lý"
        value={formatProcessingTime(response.processing_time)}
        hint="Tổng thời gian toàn ảnh"
      />
    </div>
  );
}

export default DetectionSummary;
