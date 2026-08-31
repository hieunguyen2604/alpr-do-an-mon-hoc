/** Conditional CSS class name helper. */

/** Accepted value types for class name concatenation. */
export type ClassValue = string | number | false | null | undefined;

/** Join truthy class names into a single string. */
export function cn(...classes: ClassValue[]): string {
  return classes.filter(Boolean).join(' ');
}
