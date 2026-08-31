/** Dashboard metric tile. */

import type { ReactNode } from 'react';

import { cn } from '@/lib/cn';
import { Skeleton } from './Skeleton';

/** Accent colour of the icon. */
export type StatCardTone = 'primary' | 'success' | 'warning' | 'danger';

/** Props of {@link StatCard}. */
export interface StatCardProps {
  /** What the number measures, in Vietnamese. */
  label: string;
  /** The figure itself, already formatted. */
  value: ReactNode;
  /** Icon shown beside the value. */
  icon?: ReactNode;
  /** Secondary line clarifying what is counted. */
  hint?: ReactNode;
  tone?: StatCardTone;
  /** Show placeholders instead of the value. */
  isLoading?: boolean;
  className?: string;
}

const TONE_CLASS: Readonly<Record<StatCardTone, string>> = {
  primary: 'bg-primary/10 text-primary',
  success: 'bg-success/10 text-success',
  warning: 'bg-warning/10 text-warning',
  danger: 'bg-danger/10 text-danger',
};

/** Render a metric tile. */
export function StatCard({
  label,
  value,
  icon,
  hint,
  tone = 'primary',
  isLoading = false,
  className,
}: StatCardProps): JSX.Element {
  return (
    <div
      className={cn(
        'rounded-xl border border-border bg-surface p-5 shadow-sm',
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium text-content-muted">{label}</p>

          {isLoading ? (
            <Skeleton className="mt-2 h-8 w-24" />
          ) : (
            <p className="mt-1 text-2xl font-semibold tabular-nums text-content">
              {value}
            </p>
          )}

          {hint && !isLoading && (
            <p className="mt-1 text-xs text-content-muted">{hint}</p>
          )}
        </div>

        {icon && (
          <div
            aria-hidden="true"
            className={cn(
              'flex h-10 w-10 shrink-0 items-center justify-center rounded-lg',
              TONE_CLASS[tone],
            )}
          >
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}

export default StatCard;
