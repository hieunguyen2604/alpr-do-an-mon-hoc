/** Placeholder for a view that loaded successfully but has nothing to show. */

import type { ReactNode } from 'react';

import { cn } from '@/lib/cn';

/** Props of {@link EmptyState}. */
export interface EmptyStateProps {
  /** Illustrative icon, typically a `lucide-react` element (rendered decoratively). */
  icon?: ReactNode;
  /** Short statement of what is missing. */
  title: string;
  /** Optional guidance on what to do about it. */
  description?: ReactNode;
  /** Optional call to action, such as a button clearing the filters. */
  action?: ReactNode;
  className?: string;
}

/** Render an empty state. */
export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps): JSX.Element {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-3',
        'px-6 py-12 text-center',
        className,
      )}
    >
      {icon && (
        <div
          aria-hidden="true"
          className={cn(
            'flex h-12 w-12 items-center justify-center rounded-full',
            'bg-surface-raised text-content-muted',
          )}
        >
          {icon}
        </div>
      )}
      <h3 className="text-base font-semibold text-content">{title}</h3>
      {description && (
        <p className="max-w-md text-sm text-content-muted">{description}</p>
      )}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

export default EmptyState;
