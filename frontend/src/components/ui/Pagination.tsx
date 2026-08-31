/**
 * Page navigation for the history list.
 */

import { ChevronLeft, ChevronRight } from 'lucide-react';

import { cn } from '@/lib/cn';
import { PAGE_SIZE_OPTIONS } from '@/lib/constants';
import { formatNumber } from '@/lib/format';

/** Props of {@link Pagination}. */
export interface PaginationProps {
  /** Current page, 1-based. */
  page: number;
  /** Total pages available for the current filters. */
  totalPages: number;
  /** Total rows matching the filters, across all pages. */
  total: number;
  /** Rows per page. */
  pageSize: number;
  onPageChange: (page: number) => void;
  /** Called when the page size changes. The selector is hidden if absent. */
  onPageSizeChange?: (pageSize: number) => void;
  /** Disable every control, e.g. while a page is loading. */
  disabled?: boolean;
  className?: string;
}

/** How many numbered buttons to show around the current page. */
const WINDOW_RADIUS = 1;

/** Compute list of visible page numbers with ellipsis gaps. */
function buildPageItems(
  page: number,
  totalPages: number,
): readonly (number | null)[] {
  // Few enough to list them all; no gaps needed.
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }

  const pages = new Set<number>([1, totalPages]);
  for (let offset = -WINDOW_RADIUS; offset <= WINDOW_RADIUS; offset += 1) {
    const candidate = page + offset;
    if (candidate >= 1 && candidate <= totalPages) {
      pages.add(candidate);
    }
  }

  const sorted = [...pages].sort((a, b) => a - b);
  const items: (number | null)[] = [];
  let previous = 0;

  for (const current of sorted) {
    // A gap of exactly one is filled rather than elided: an ellipsis hiding a
    // single page is longer than the page number it replaces.
    if (current - previous === 2) {
      items.push(previous + 1);
    } else if (current - previous > 2) {
      items.push(null);
    }
    items.push(current);
    previous = current;
  }

  return items;
}

/**
 * Render the pagination controls.
 *
 * @param props - Page state and change handlers.
 * @returns The pagination element, or `null` when there is nothing to show.
 */
export function Pagination({
  page,
  totalPages,
  total,
  pageSize,
  onPageChange,
  onPageSizeChange,
  disabled = false,
  className,
}: PaginationProps): JSX.Element | null {
  if (total === 0) {
    return null;
  }

  const firstRow = (page - 1) * pageSize + 1;
  const lastRow = Math.min(page * pageSize, total);
  const items = buildPageItems(page, totalPages);

  /**
   * Move to a page, clamped to the valid range.
   *
   * @param nextPage - The requested page.
   */
  const goTo = (nextPage: number): void => {
    const clamped = Math.min(Math.max(nextPage, 1), Math.max(totalPages, 1));
    if (clamped !== page) {
      onPageChange(clamped);
    }
  };

  const navButtonClass = cn(
    'inline-flex h-9 min-w-9 items-center justify-center rounded-lg px-2',
    'border border-border bg-surface text-content',
    'transition-colors hover:bg-surface-raised',
    'disabled:cursor-not-allowed disabled:opacity-50',
  );

  return (
    <nav
      aria-label="Phân trang"
      className={cn(
        'flex flex-wrap items-center justify-between gap-3',
        className,
      )}
    >
      <p className="text-sm text-content-muted">
        Hiển thị {formatNumber(firstRow)}–{formatNumber(lastRow)} trong tổng số{' '}
        {formatNumber(total)} bản ghi
      </p>

      <div className="flex flex-wrap items-center gap-2">
        {onPageSizeChange && (
          <label className="flex items-center gap-2 text-sm text-content-muted">
            <span>Số dòng</span>
            <select
              value={pageSize}
              disabled={disabled}
              onChange={(event) =>
                onPageSizeChange(Number(event.target.value))
              }
              className={cn(
                'rounded-lg border border-border bg-surface px-2 py-1.5',
                'text-sm text-content disabled:opacity-50',
              )}
            >
              {PAGE_SIZE_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
        )}

        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => goTo(page - 1)}
            disabled={disabled || page <= 1}
            aria-label="Trang trước"
            className={navButtonClass}
          >
            <ChevronLeft className="h-4 w-4" aria-hidden="true" />
          </button>

          {items.map((item, index) =>
            item === null ? (
              <span
                key={`gap-${index}`}
                aria-hidden="true"
                className="px-1 text-content-muted"
              >
                …
              </span>
            ) : (
              <button
                key={item}
                type="button"
                onClick={() => goTo(item)}
                disabled={disabled}
                aria-label={`Trang ${item}`}
                // Marks the active page for assistive technology; the colour
                // change alone would not be announced.
                aria-current={item === page ? 'page' : undefined}
                className={cn(
                  navButtonClass,
                  item === page &&
                    'border-primary bg-primary text-white hover:bg-primary-hover dark:text-slate-950',
                )}
              >
                {item}
              </button>
            ),
          )}

          <button
            type="button"
            onClick={() => goTo(page + 1)}
            disabled={disabled || page >= totalPages}
            aria-label="Trang sau"
            className={navButtonClass}
          >
            <ChevronRight className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Pagination;
