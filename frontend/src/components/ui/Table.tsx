/**
 * Generic data table with optional sortable columns.
 *
 * Generic over the row type so a column's `accessor` is checked against the
 * data it will actually receive — a renamed field becomes a compile error here
 * rather than an empty column in the browser.
 */

import { ArrowDown, ArrowUp, ChevronsUpDown } from 'lucide-react';
import type { ReactNode } from 'react';

import { cn } from '@/lib/cn';
import type { SortOrder } from '@/types';

/** One column definition. */
export interface TableColumn<TRow> {
  /** Stable key, also used as the React key and the sort identifier. */
  key: string;
  /** Column heading. */
  header: ReactNode;
  /** Produce the cell content for a row. */
  accessor: (row: TRow) => ReactNode;
  /**
   * Whether this column can be sorted.
   *
   * Sorting is performed by the **server**, so `key` must match a value the
   * API's `sort_by` accepts. The table only reports the intent.
   */
  sortable?: boolean;
  /** Horizontal alignment of the cells. */
  align?: 'left' | 'center' | 'right';
  /** Extra classes for the cells in this column. */
  className?: string;
  /** Extra classes for the header cell. */
  headerClassName?: string;
}

/** Props of {@link Table}. */
export interface TableProps<TRow> {
  columns: readonly TableColumn<TRow>[];
  rows: readonly TRow[];
  /** Stable identity for a row, used as its React key. */
  getRowKey: (row: TRow, index: number) => string | number;
  /** Key of the column currently sorted. */
  sortKey?: string;
  /** Direction of the current sort. */
  sortOrder?: SortOrder;
  /**
   * Called when a sortable header is activated.
   *
   * Receives the column key and the direction to apply — the table works out
   * the toggle so every caller does not have to.
   */
  onSortChange?: (key: string, order: SortOrder) => void;
  /** Called when a row is activated. Rows become focusable when supplied. */
  onRowClick?: (row: TRow) => void;
  /** Shown in place of the body when there are no rows. */
  emptyState?: ReactNode;
  /** Dim the body while a refresh is in flight. */
  isLoading?: boolean;
  /** Accessible description of the table's contents. */
  caption?: string;
  className?: string;
}

const ALIGN_CLASS = {
  left: 'text-left',
  center: 'text-center',
  right: 'text-right',
} as const;

/**
 * Render a data table.
 *
 * @typeParam TRow - Shape of one row.
 * @param props - Columns, rows, sort state and handlers.
 * @returns The table element.
 */
export function Table<TRow>({
  columns,
  rows,
  getRowKey,
  sortKey,
  sortOrder = 'desc',
  onSortChange,
  onRowClick,
  emptyState,
  isLoading = false,
  caption,
  className,
}: TableProps<TRow>): JSX.Element {
  /**
   * Report the sort the user asked for by activating a header.
   *
   * Clicking the active column flips the direction; clicking a new one starts
   * it descending, which for a timestamp means newest first — the ordering a
   * user almost always wants on first click.
   *
   * @param column - The column that was activated.
   */
  const handleSort = (column: TableColumn<TRow>): void => {
    if (!column.sortable || !onSortChange) {
      return;
    }
    const nextOrder: SortOrder =
      sortKey === column.key && sortOrder === 'desc' ? 'asc' : 'desc';
    onSortChange(column.key, nextOrder);
  };

  if (rows.length === 0 && !isLoading && emptyState) {
    return <>{emptyState}</>;
  }

  return (
    // Horizontal scrolling lives on this wrapper so a wide table never makes
    // the whole page scroll sideways.
    <div className={cn('w-full overflow-x-auto', className)}>
      <table className="w-full border-collapse text-sm">
        {caption && <caption className="sr-only">{caption}</caption>}

        <thead>
          <tr className="border-b border-border">
            {columns.map((column) => {
              const isSorted = sortKey === column.key;
              const alignClass = ALIGN_CLASS[column.align ?? 'left'];

              return (
                <th
                  key={column.key}
                  scope="col"
                  // Tells assistive technology how this column is ordered.
                  // "none" on a sortable column signals that it *can* be
                  // sorted but currently is not.
                  aria-sort={
                    column.sortable
                      ? isSorted
                        ? sortOrder === 'asc'
                          ? 'ascending'
                          : 'descending'
                        : 'none'
                      : undefined
                  }
                  className={cn(
                    'whitespace-nowrap px-4 py-3 font-medium text-content-muted',
                    alignClass,
                    column.headerClassName,
                  )}
                >
                  {column.sortable && onSortChange ? (
                    <button
                      type="button"
                      onClick={() => handleSort(column)}
                      className={cn(
                        'inline-flex items-center gap-1.5 rounded',
                        'transition-colors hover:text-content',
                        isSorted && 'text-content',
                      )}
                    >
                      {column.header}
                      {isSorted ? (
                        sortOrder === 'asc' ? (
                          <ArrowUp className="h-3.5 w-3.5" aria-hidden="true" />
                        ) : (
                          <ArrowDown
                            className="h-3.5 w-3.5"
                            aria-hidden="true"
                          />
                        )
                      ) : (
                        <ChevronsUpDown
                          className="h-3.5 w-3.5 opacity-50"
                          aria-hidden="true"
                        />
                      )}
                    </button>
                  ) : (
                    column.header
                  )}
                </th>
              );
            })}
          </tr>
        </thead>

        <tbody
          aria-busy={isLoading}
          className={cn(isLoading && 'opacity-60 transition-opacity')}
        >
          {rows.map((row, rowIndex) => (
            <tr
              key={getRowKey(row, rowIndex)}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              // A clickable row must also be reachable and activatable from the
              // keyboard, otherwise the interaction exists only for mouse users.
              tabIndex={onRowClick ? 0 : undefined}
              onKeyDown={
                onRowClick
                  ? (event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        onRowClick(row);
                      }
                    }
                  : undefined
              }
              className={cn(
                'border-b border-border last:border-0',
                onRowClick && 'cursor-pointer hover:bg-surface-raised',
              )}
            >
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={cn(
                    'px-4 py-3 text-content',
                    ALIGN_CLASS[column.align ?? 'left'],
                    column.className,
                  )}
                >
                  {column.accessor(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Table;
