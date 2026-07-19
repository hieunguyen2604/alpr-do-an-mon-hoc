/**
 * Indeterminate loading indicator.
 */

import { cn } from '@/lib/cn';

/** Diameter presets. */
export type SpinnerSize = 'sm' | 'md' | 'lg';

/** Props of {@link Spinner}. */
export interface SpinnerProps {
  size?: SpinnerSize;
  /** Extra classes, applied last so they win. */
  className?: string;
  /**
   * Description announced to assistive technology.
   *
   * A spinner is meaningless to a screen reader without one — the element is
   * pure decoration otherwise.
   */
  label?: string;
}

const SIZE_CLASS: Readonly<Record<SpinnerSize, string>> = {
  sm: 'h-4 w-4 border-2',
  md: 'h-6 w-6 border-2',
  lg: 'h-10 w-10 border-[3px]',
};

/**
 * Render a spinning ring.
 *
 * @param props - Size, extra classes and accessible label.
 * @returns The spinner element.
 */
export function Spinner({
  size = 'md',
  className,
  label = 'Đang tải',
}: SpinnerProps): JSX.Element {
  return (
    <span
      role="status"
      aria-live="polite"
      className={cn('inline-flex items-center justify-center', className)}
    >
      <span
        aria-hidden="true"
        className={cn(
          'animate-spin rounded-full border-current border-t-transparent',
          'text-primary',
          SIZE_CLASS[size],
        )}
      />
      {/* Visually hidden, but read aloud. */}
      <span className="sr-only">{label}</span>
    </span>
  );
}

export default Spinner;
