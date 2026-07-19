/**
 * Small status pill.
 */

import type { HTMLAttributes, ReactNode } from 'react';

import { cn } from '@/lib/cn';

/** Semantic colour of a badge. */
export type BadgeVariant =
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'neutral';

/** Props of {@link Badge}. */
export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  /** Icon placed before the label. */
  icon?: ReactNode;
  children?: ReactNode;
}

/**
 * Variant styles.
 *
 * A 10% tint of the status colour over the page surface, with the status colour
 * itself as the text. The text sits on a background barely distinguishable from
 * the surface, so the contrast ratio remains essentially that of the status
 * colour against the surface — which the palette already holds above 4.5:1 in
 * both themes.
 */
const VARIANT_CLASS: Readonly<Record<BadgeVariant, string>> = {
  success: 'bg-success/10 text-success',
  warning: 'bg-warning/10 text-warning',
  danger: 'bg-danger/10 text-danger',
  info: 'bg-primary/10 text-primary',
  neutral: 'bg-surface-raised text-content-muted',
};

/**
 * Render a badge.
 *
 * Colour alone never carries the meaning — the label states it in words too,
 * so the badge is still readable to a colour-blind user (NFR-U5).
 *
 * @param props - Variant, optional icon and native span attributes.
 * @returns The badge element.
 */
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
