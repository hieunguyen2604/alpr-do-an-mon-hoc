/**
 * License plate shown as a chip.
 *
 * Set in a monospace face on purpose. Plate strings are read character by
 * character, and a proportional font makes `O`/`0` and `I`/`1` nearly
 * identical — precisely the confusions OCR makes, and precisely the ones a
 * reviewer is checking for.
 */

import { AlertTriangle } from 'lucide-react';

import { cn } from '@/lib/cn';
import { formatPlateNumber } from '@/lib/format';

/** Props of {@link PlateChip}. */
export interface PlateChipProps {
  /** Plate text from the API, or `null` when OCR read nothing. */
  plateNumber: string | null | undefined;
  /**
   * Whether the text matched a known Vietnamese plate format.
   *
   * `false` is **flagged, not hidden**. An unrecognised format is still a real
   * detection, and discarding it would erase the negative cases from the
   * accuracy figures.
   */
  isValidFormat?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const SIZE_CLASS = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-sm',
  lg: 'px-3 py-1.5 text-base',
} as const;

/**
 * Render a plate chip.
 *
 * @param props - Plate text, format validity and size.
 * @returns The chip element.
 */
export function PlateChip({
  plateNumber,
  isValidFormat = true,
  size = 'md',
  className,
}: PlateChipProps): JSX.Element {
  const hasText = Boolean(plateNumber && plateNumber.trim().length > 0);
  const displayText = formatPlateNumber(plateNumber);
  const isFlagged = hasText && !isValidFormat;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md border font-mono',
        'font-semibold tracking-wide',
        SIZE_CLASS[size],
        !hasText && 'border-dashed border-border bg-surface-raised text-content-muted',
        hasText &&
          isValidFormat &&
          'border-border bg-surface-raised text-content',
        isFlagged && 'border-warning/40 bg-warning/10 text-warning',
        className,
      )}
      // States the flag in words, so it is not conveyed by colour and an icon
      // alone.
      title={
        isFlagged
          ? 'Biển số không đúng định dạng Việt Nam'
          : hasText
            ? undefined
            : 'OCR không đọc được biển số'
      }
    >
      {isFlagged && (
        <AlertTriangle
          className="h-3.5 w-3.5 shrink-0"
          aria-hidden="true"
        />
      )}
      {displayText}
      {isFlagged && (
        <span className="sr-only">— không đúng định dạng Việt Nam</span>
      )}
    </span>
  );
}

export default PlateChip;
