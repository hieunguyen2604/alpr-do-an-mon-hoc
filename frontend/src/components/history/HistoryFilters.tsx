/**
 * Filter panel of the history page (FR-4.3 to FR-4.5, FR-5.2).
 *
 * Every control here narrows the same list and they combine: a search string,
 * an input type, a date range and a confidence floor are sent together as one
 * query. The panel is purely presentational — it owns no filter state, so the
 * URL stays the only source of truth (see `useHistoryQuery`).
 */

import { Download, FilterX, Loader2, Search } from 'lucide-react';

import { Button } from '@/components/ui';
import { cn } from '@/lib/cn';
import { INPUT_TYPE_LABELS } from '@/lib/constants';
import type { InputType } from '@/types';

/** Options of the input-type dropdown, with "all" first. */
const INPUT_TYPE_OPTIONS: readonly { value: InputType | ''; label: string }[] = [
  { value: '', label: 'Tất cả loại' },
  { value: 'image', label: INPUT_TYPE_LABELS.image },
  { value: 'video', label: INPUT_TYPE_LABELS.video },
  { value: 'webcam', label: INPUT_TYPE_LABELS.webcam },
];

/** Props of {@link HistoryFilters}. */
export interface HistoryFiltersProps {
  searchInput: string;
  onSearchInputChange: (value: string) => void;
  inputType: InputType | '';
  onInputTypeChange: (value: InputType | '') => void;
  dateFrom: string;
  onDateFromChange: (value: string) => void;
  dateTo: string;
  onDateToChange: (value: string) => void;
  /** Minimum detector confidence, as a whole percentage. */
  confidencePercent: number;
  onConfidencePercentChange: (value: number) => void;
  /** Whether any filter is applied; drives the reset button and the hint. */
  hasActiveFilters: boolean;
  onReset: () => void;
  /**
   * CSV download URL carrying the **current** filters.
   *
   * Opened through a plain anchor rather than fetched: the server sets the file
   * name and the UTF-8 BOM in its own headers, and re-wrapping the body in a
   * blob would throw both away (FR-5.2).
   */
  exportUrl: string;
  /** Whether there is anything to export. Disabled when the result set is empty. */
  canExport: boolean;
  /** Whether a debounced control is waiting to be applied. */
  isPendingInput: boolean;
  className?: string;
}

/**
 * Render the filter panel.
 *
 * @param props - Current filter values and their change handlers.
 * @returns The filter panel element.
 */
export function HistoryFilters({
  searchInput,
  onSearchInputChange,
  inputType,
  onInputTypeChange,
  dateFrom,
  onDateFromChange,
  dateTo,
  onDateToChange,
  confidencePercent,
  onConfidencePercentChange,
  hasActiveFilters,
  onReset,
  exportUrl,
  canExport,
  isPendingInput,
  className,
}: HistoryFiltersProps): JSX.Element {
  // A range whose end precedes its start matches nothing. Saying so is far
  // kinder than an empty table the user has to diagnose (NFR-U3).
  const isRangeInverted = Boolean(dateFrom && dateTo && dateFrom > dateTo);

  return (
    <section
      aria-label="Bộ lọc lịch sử"
      className={cn('rounded-xl border border-border bg-surface p-5', className)}
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {/* Search ------------------------------------------------------- */}
        <div className="sm:col-span-2 xl:col-span-1">
          <label htmlFor="history-search" className="label">
            Tìm theo biển số
          </label>
          <div className="relative">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-content-muted"
              aria-hidden="true"
            />
            <input
              id="history-search"
              type="search"
              value={searchInput}
              onChange={(event) => onSearchInputChange(event.target.value)}
              placeholder="Ví dụ: 51F hoặc 30D-044"
              // Announces that results update on their own as the user types,
              // instead of leaving a screen-reader user waiting for a submit.
              aria-describedby="history-search-hint"
              className="input pl-9 pr-9"
            />
            {isPendingInput && (
              <Loader2
                className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-content-muted"
                aria-hidden="true"
              />
            )}
          </div>
          <p id="history-search-hint" className="mt-1.5 text-xs text-content-muted">
            Khớp một phần, tự động tìm sau khi ngừng gõ.
          </p>
        </div>

        {/* Input type --------------------------------------------------- */}
        <div>
          <label htmlFor="history-input-type" className="label">
            Loại đầu vào
          </label>
          <select
            id="history-input-type"
            value={inputType}
            onChange={(event) =>
              onInputTypeChange(event.target.value as InputType | '')
            }
            className="input"
          >
            {INPUT_TYPE_OPTIONS.map((option) => (
              <option key={option.value || 'all'} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Date range --------------------------------------------------- */}
        <div>
          <label htmlFor="history-date-from" className="label">
            Từ ngày
          </label>
          <input
            id="history-date-from"
            type="date"
            value={dateFrom}
            // Bounding the pickers against each other prevents most inverted
            // ranges before they are ever submitted.
            max={dateTo || undefined}
            onChange={(event) => onDateFromChange(event.target.value)}
            className="input"
          />
        </div>

        <div>
          <label htmlFor="history-date-to" className="label">
            Đến ngày
          </label>
          <input
            id="history-date-to"
            type="date"
            value={dateTo}
            min={dateFrom || undefined}
            onChange={(event) => onDateToChange(event.target.value)}
            className="input"
          />
        </div>

        {/* Minimum confidence ------------------------------------------- */}
        <div className="sm:col-span-2 xl:col-span-4">
          <label htmlFor="history-min-confidence" className="label">
            Độ tin cậy tối thiểu:{' '}
            <span className="font-mono tabular-nums text-primary">
              {confidencePercent}%
            </span>
          </label>
          <div className="flex items-center gap-3">
            <span aria-hidden="true" className="text-xs text-content-muted">
              0%
            </span>
            <input
              id="history-min-confidence"
              type="range"
              min={0}
              max={100}
              step={5}
              value={confidencePercent}
              onChange={(event) =>
                onConfidencePercentChange(Number(event.target.value))
              }
              // The visible label already reads "…: 45%", but a screen reader
              // announces the number alone; the unit makes it meaningful.
              aria-valuetext={`${confidencePercent} phần trăm`}
              className="h-2 flex-1 cursor-pointer appearance-none rounded-full bg-surface-raised accent-primary"
            />
            <span aria-hidden="true" className="text-xs text-content-muted">
              100%
            </span>
            <input
              type="number"
              min={0}
              max={100}
              step={5}
              value={confidencePercent}
              onChange={(event) => {
                const parsed = Number.parseInt(event.target.value, 10);
                onConfidencePercentChange(
                  Number.isFinite(parsed)
                    ? Math.min(Math.max(parsed, 0), 100)
                    : 0,
                );
              }}
              aria-label="Độ tin cậy tối thiểu, nhập theo phần trăm"
              className="input w-20 shrink-0 text-center tabular-nums"
            />
          </div>
          <p className="mt-1.5 text-xs text-content-muted">
            Chỉ hiển thị biển số có độ tin cậy phát hiện từ mức này trở lên. Đặt
            0% để bỏ điều kiện.
          </p>
        </div>
      </div>

      {isRangeInverted && (
        <p role="alert" className="mt-4 text-sm text-warning">
          Khoảng thời gian chưa hợp lệ: ngày bắt đầu đang sau ngày kết thúc, nên
          sẽ không có bản ghi nào khớp.
        </p>
      )}

      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
        <p className="text-sm text-content-muted">
          {hasActiveFilters
            ? 'Các điều kiện lọc đang được áp dụng đồng thời.'
            : 'Chưa áp dụng bộ lọc nào — đang hiển thị toàn bộ lịch sử.'}
        </p>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="secondary"
            onClick={onReset}
            disabled={!hasActiveFilters}
            leftIcon={<FilterX className="h-4 w-4" />}
          >
            Xoá bộ lọc
          </Button>

          {/* A disabled anchor is not a thing in HTML, so the empty case is
              rendered as an inert element carrying the state explicitly rather
              than as a link that downloads an empty file. */}
          {canExport ? (
            <a
              href={exportUrl}
              download
              className={cn(
                'inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2',
                'text-sm font-medium transition-colors',
                'bg-primary text-white hover:bg-primary-hover dark:text-slate-950',
              )}
            >
              <Download className="h-4 w-4" aria-hidden="true" />
              Xuất CSV
            </a>
          ) : (
            <span
              aria-disabled="true"
              title="Không có bản ghi nào để xuất"
              className={cn(
                'inline-flex cursor-not-allowed items-center justify-center gap-2',
                'rounded-lg border border-border px-4 py-2 text-sm font-medium',
                'text-content-muted opacity-60',
              )}
            >
              <Download className="h-4 w-4" aria-hidden="true" />
              Xuất CSV
            </span>
          )}
        </div>
      </div>
    </section>
  );
}

export default HistoryFilters;
