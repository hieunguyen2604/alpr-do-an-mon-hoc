/**
 * Conditional class name joining.
 *
 * Small on purpose: the UI components need to merge a base class list with
 * variant classes and an optional caller-supplied `className`, where several of
 * those are conditional. Without a helper each component grows its own template
 * literal full of `&&` expressions that render `"false"` into the DOM when a
 * condition fails.
 *
 * This does not de-duplicate conflicting Tailwind utilities the way
 * `tailwind-merge` does. Components here are written so the caller's
 * `className` comes last, which is enough for the override to win.
 */

/** A value accepted by {@link cn}. Falsy entries are dropped. */
export type ClassValue = string | number | false | null | undefined;

/**
 * Join class names, discarding falsy entries.
 *
 * @param classes - Class names, or falsy values to skip.
 * @returns The joined class string.
 *
 * @example
 * ```ts
 * cn('btn', isActive && 'btn-active', className)
 * ```
 */
export function cn(...classes: ClassValue[]): string {
  return classes.filter(Boolean).join(' ');
}
