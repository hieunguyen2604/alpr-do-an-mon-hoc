/**
 * Placeholder shapes shown while content loads.
 *
 * Preferred over a bare spinner for content whose layout is known: the page
 * settles into the same shape it was already showing, instead of jumping when
 * the data lands.
 */

import type { HTMLAttributes } from 'react';

import { cn } from '@/lib/cn';

/** Props of {@link Skeleton}. */
export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  /** Corner rounding. Use `full` for an avatar, `md` for a text line. */
  rounded?: 'sm' | 'md' | 'lg' | 'full';
}

const ROUNDED_CLASS = {
  sm: 'rounded',
  md: 'rounded-md',
  lg: 'rounded-lg',
  full: 'rounded-full',
} as const;

/**
 * Render one placeholder block.
 *
 * Hidden from assistive technology: a screen reader gains nothing from a
 * description of a grey rectangle. The surrounding container should carry the
 * `aria-busy` state instead.
 *
 * @param props - Rounding and native div attributes. Size comes from
 *   `className`.
 * @returns The placeholder element.
 */
export function Skeleton({
  rounded = 'md',
  className,
  ...rest
}: SkeletonProps): JSX.Element {
  return (
    <div
      aria-hidden="true"
      className={cn(
        'animate-pulse bg-surface-raised',
        ROUNDED_CLASS[rounded],
        className,
      )}
      {...rest}
    />
  );
}

/** Props of {@link SkeletonText}. */
export interface SkeletonTextProps {
  /** Number of lines to draw. */
  lines?: number;
  className?: string;
}

/**
 * Render several placeholder lines resembling a paragraph.
 *
 * The last line is drawn short, which is what makes the block read as text
 * rather than as a solid rectangle.
 *
 * @param props - Line count and extra classes.
 * @returns The placeholder block.
 */
export function SkeletonText({
  lines = 3,
  className,
}: SkeletonTextProps): JSX.Element {
  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }, (_, index) => (
        <Skeleton
          key={index}
          className={cn('h-4', index === lines - 1 ? 'w-2/3' : 'w-full')}
        />
      ))}
    </div>
  );
}

/** Props of {@link SkeletonTable}. */
export interface SkeletonTableProps {
  rows?: number;
  columns?: number;
  className?: string;
}

/**
 * Render a grid of placeholders matching a table's shape.
 *
 * @param props - Row and column counts, plus extra classes.
 * @returns The placeholder grid.
 */
export function SkeletonTable({
  rows = 5,
  columns = 4,
  className,
}: SkeletonTableProps): JSX.Element {
  return (
    <div className={cn('space-y-3', className)} aria-busy="true">
      {Array.from({ length: rows }, (_, rowIndex) => (
        <div key={rowIndex} className="flex gap-3">
          {Array.from({ length: columns }, (_, columnIndex) => (
            <Skeleton key={columnIndex} className="h-8 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

export default Skeleton;
