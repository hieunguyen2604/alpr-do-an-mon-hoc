/**
 * Compatibility re-export.
 *
 * The formatting helpers moved to `@/lib/format`, alongside the other shared
 * library code. This module forwards to it so existing imports keep working;
 * new code should import from `@/lib/format` directly.
 *
 * @deprecated Import from `@/lib/format` instead.
 */

export * from '@/lib/format';
