/**
 * Surface container grouping related content.
 */

import type { HTMLAttributes, ReactNode } from 'react';

import { cn } from '@/lib/cn';

/** Props of {@link Card}. */
export interface CardProps extends Omit<HTMLAttributes<HTMLDivElement>, 'title'> {
  /** Heading shown in the card's header. Omit for a bare surface. */
  title?: ReactNode;
  /** Supporting line under the title. */
  description?: ReactNode;
  /** Controls placed at the trailing edge of the header. */
  actions?: ReactNode;
  /** Remove the body padding, for a card wrapping a full-bleed table. */
  noPadding?: boolean;
  children?: ReactNode;
}

/** Render a card. */
export function Card({
  title,
  description,
  actions,
  noPadding = false,
  className,
  children,
  ...rest
}: CardProps): JSX.Element {
  const hasHeader = Boolean(title ?? description ?? actions);

  return (
    <section
      className={cn(
        'rounded-xl border border-border bg-surface shadow-sm',
        className,
      )}
      {...rest}
    >
      {hasHeader && (
        <header
          className={cn(
            'flex flex-wrap items-start justify-between gap-3',
            'border-b border-border px-5 py-4',
          )}
        >
          <div className="min-w-0">
            {title && (
              <h2 className="text-base font-semibold text-content">{title}</h2>
            )}
            {description && (
              <p className="mt-1 text-sm text-content-muted">{description}</p>
            )}
          </div>
          {actions && (
            <div className="flex shrink-0 items-center gap-2">{actions}</div>
          )}
        </header>
      )}
      <div className={cn(!noPadding && 'p-5')}>{children}</div>
    </section>
  );
}

export default Card;
