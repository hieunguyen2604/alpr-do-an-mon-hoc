/**
 * Determinate progress bar.
 *
 * Used for upload progress and for video job progress, both of which routinely
 * run past 500 ms and so require visible feedback (NFR-U2).
 */

import { cn } from '@/lib/cn';
import { formatPercent } from '@/lib/format';

/** Colour of the filled portion. */
export type ProgressBarVariant = 'primary' | 'success' | 'warning' | 'danger';

/** Props of {@link ProgressBar}. */
export interface ProgressBarProps {
  /**
   * Completion from 0.0 to 1.0.
   *
   * A ratio rather than a percentage, matching `DetectionJob.progress` so the
   * value can be passed straight through without a conversion that could be
   * applied twice.
   */
  value: number;
  variant?: ProgressBarVariant;
  /** Show the percentage beside the bar. */
  showLabel?: boolean;
  /** Text describing what is progressing, shown above the bar. */
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  /** Animate the fill, for work whose completion is not precisely known. */
  indeterminate?: boolean;
  className?: string;
}

const VARIANT_CLASS: Readonly<Record<ProgressBarVariant, string>> = {
  primary: 'bg-primary',
  success: 'bg-success',
  warning: 'bg-warning',
  danger: 'bg-danger',
};

const SIZE_CLASS = {
  sm: 'h-1.5',
  md: 'h-2.5',
  lg: 'h-4',
} as const;

/**
 * Render a progress bar.
 *
 * @param props - Progress ratio, variant, labelling and size.
 * @returns The progress bar element.
 */
export function ProgressBar({
  value,
  variant = 'primary',
  showLabel = false,
  label,
  size = 'md',
  indeterminate = false,
  className,
}: ProgressBarProps): JSX.Element {
  // Clamped because a bar wider than its track escapes the rounded corners, and
  // a negative width is simply invalid.
  const ratio = Number.isFinite(value) ? Math.min(Math.max(value, 0), 1) : 0;
  const percent = ratio * 100;

  return (
    <div className={cn('w-full', className)}>
      {(label ?? showLabel) && (
        <div className="mb-1.5 flex items-center justify-between gap-2 text-sm">
          {label && <span className="text-content">{label}</span>}
          {showLabel && !indeterminate && (
            <span className="font-medium tabular-nums text-content-muted">
              {formatPercent(ratio, 0)}
            </span>
          )}
        </div>
      )}

      <div
        role="progressbar"
        // Omitted while indeterminate: a bar that reports a value it does not
        // actually know is worse than one that reports none.
        aria-valuenow={indeterminate ? undefined : Math.round(percent)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label ?? 'Tiến độ xử lý'}
        className={cn(
          'w-full overflow-hidden rounded-full bg-surface-raised',
          SIZE_CLASS[size],
        )}
      >
        <div
          className={cn(
            'h-full rounded-full transition-[width] duration-300 ease-out',
            VARIANT_CLASS[variant],
            indeterminate && 'animate-pulse',
          )}
          style={{ width: indeterminate ? '100%' : `${percent}%` }}
        />
      </div>
    </div>
  );
}

export default ProgressBar;
