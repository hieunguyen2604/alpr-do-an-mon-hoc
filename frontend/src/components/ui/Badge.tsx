/** Status badge pill component (NFR-U5). */

import type { HTMLAttributes, ReactNode } from 'react';

import { cn } from '@/lib/cn';

/** Semantic colour of a badge. */
export type BadgeVariant =
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'neutral';

/** Props of Badge component. */
export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  /** Icon placed before the label. */
  icon?: ReactNode;
  children?: ReactNode;
}

/** Variant style mappings for badge tints. */
const VARIANT_CLASS: Readonly<Record<BadgeVariant, string>> = {
  success: 'bg-success/10 text-success',
  warning: 'bg-warning/10 text-warning',
  danger: 'bg-danger/10 text-danger',
  info: 'bg-primary/10 text-primary',
  neutral: 'bg-surface-raised text-content-muted',
};

/** Render a badge with semantic variant styling. */
export function Badge({
  variant = 'neutral',
  icon,
  className,
  children,
  ...rest
}: BadgeProps): JSX.Element {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2.5 py-0.5',
        'text-xs font-medium',
        VARIANT_CLASS[variant],
        className,
      )}
      {...rest}
    >
      {icon}
      {children}
    </span>
  );
}

export default Badge;
