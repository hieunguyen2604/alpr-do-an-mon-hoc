/** Confidence score visual progress bar with color thresholds. */

import { cn } from '@/lib/cn';
import { CONFIDENCE_THRESHOLDS } from '@/lib/constants';
import { NO_VALUE, formatConfidence } from '@/lib/format';

/** Props of {@link ConfidenceBar}. */
export interface ConfidenceBarProps {
  /** Score from 0.0 to 1.0, or `null` when OCR read nothing (renders neutrally). */
  value: number | null | undefined;
  /** Show the percentage beside the bar. */
  showValue?: boolean;
  /** Text describing which score this is, e.g. "Độ tin cậy OCR". */
  label?: string;
  size?: 'sm' | 'md';
  className?: string;
}

/** Classify a score into a display band. */
function classify(value: number | null | undefined): {
  barClass: string;
  textClass: string;
  wording: string;
} {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return {
      barClass: 'bg-content-muted/30',
      textClass: 'text-content-muted',
      wording: 'không có',
    };
  }
  if (value >= CONFIDENCE_THRESHOLDS.high) {
    return { barClass: 'bg-success', textClass: 'text-success', wording: 'cao' };
  }
  if (value >= CONFIDENCE_THRESHOLDS.medium) {
    return {
      barClass: 'bg-warning',
      textClass: 'text-warning',
      wording: 'trung bình',
    };
  }
  return { barClass: 'bg-danger', textClass: 'text-danger', wording: 'thấp' };
}

/** Render a confidence bar. */
export function ConfidenceBar({
  value,
  showValue = true,
  label,
  size = 'md',
  className,
}: ConfidenceBarProps): JSX.Element {
  const hasValue =
    value !== null && value !== undefined && !Number.isNaN(value);
  const ratio = hasValue ? Math.min(Math.max(value, 0), 1) : 0;
  const { barClass, textClass, wording } = classify(value);

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {label && (
        <span className="shrink-0 text-xs text-content-muted">{label}</span>
      )}

      <div
        className={cn(
          'min-w-16 flex-1 overflow-hidden rounded-full bg-surface-raised',
          size === 'sm' ? 'h-1.5' : 'h-2',
        )}
        role="img"
        // The bar is meaningless to a screen reader without this: the band is
        // stated in words as well as in colour, so the meaning survives when
        // the colour is not perceivable (NFR-U5).
        aria-label={
          hasValue
            ? `Độ tin cậy ${formatConfidence(value)}, mức ${wording}`
            : 'Không có độ tin cậy'
        }
      >
        <div
          className={cn('h-full rounded-full transition-all', barClass)}
          style={{ width: `${ratio * 100}%` }}
        />
      </div>

      {showValue && (
        <span
          className={cn(
            'shrink-0 text-xs font-medium tabular-nums',
            hasValue ? textClass : 'text-content-muted',
          )}
        >
          {hasValue ? formatConfidence(value) : NO_VALUE}
        </span>
      )}
    </div>
  );
}

export default ConfidenceBar;
