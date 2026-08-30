/**
 * Compact Filter Toolbar for the History Page (Deep Navy Cyber Theme).
 */

import { Download, FilterX, Loader2, Search } from 'lucide-react';

import { Button } from '@/components/ui';
import { cn } from '@/lib/cn';
import { INPUT_TYPE_LABELS } from '@/lib/constants';
import type { InputType } from '@/types';

const INPUT_TYPE_OPTIONS: readonly { value: InputType | ''; label: string }[] = [
  { value: '', label: 'Tất cả loại nguồn' },
  { value: 'image', label: INPUT_TYPE_LABELS.image },
  { value: 'video', label: INPUT_TYPE_LABELS.video },
  { value: 'webcam', label: INPUT_TYPE_LABELS.webcam },
];

export interface HistoryFiltersProps {
  searchInput: string;
  onSearchInputChange: (value: string) => void;
  inputType: InputType | '';
  onInputTypeChange: (value: InputType | '') => void;
  dateFrom: string;
  onDateFromChange: (value: string) => void;
  dateTo: string;
  onDateToChange: (value: string) => void;
  confidencePercent: number;
  onConfidencePercentChange: (value: number) => void;
  hasActiveFilters: boolean;
  onReset: () => void;
  exportUrl: string;
  canExport: boolean;
  isPendingInput: boolean;
  className?: string;
}

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
  return (
    <section
      aria-label="Bộ lọc lịch sử"
      className={cn(
        'rounded-2xl border border-border/80 bg-surface p-4 shadow-sm space-y-3',
        className,
      )}
    >
      {/* Primary Row: Search + Type + Quick Action */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Search Input */}
        <div className="relative flex-1 min-w-[220px]">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-content-muted"
            aria-hidden="true"
          />
          <input
            id="history-search"
            type="search"
            value={searchInput}
            onChange={(event) => onSearchInputChange(event.target.value)}
            placeholder="Tìm biển số (VD: 51G, 30A-466.67)…"
            className="w-full rounded-xl border border-border bg-surface-raised/60 py-2 pl-9 pr-9 text-xs text-content placeholder:text-content-muted focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          />
          {isPendingInput && (
            <Loader2
              className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-primary"
              aria-hidden="true"
            />
          )}
        </div>

        {/* Input Type Select */}
        <div className="w-44">
          <select
            id="history-input-type"
            value={inputType}
            onChange={(event) =>
              onInputTypeChange(event.target.value as InputType | '')
            }
            className="w-full rounded-xl border border-border bg-surface-raised/60 py-2 px-3 text-xs text-content focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary font-medium"
          >
            {INPUT_TYPE_OPTIONS.map((option) => (
              <option key={option.value || 'all'} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Actions on the right */}
        <div className="flex items-center gap-2 ml-auto">
          {hasActiveFilters && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={onReset}
              className="h-8 px-2.5 text-xs text-content-muted hover:text-danger"
              leftIcon={<FilterX className="h-3.5 w-3.5" />}
            >
              Xoá bộ lọc
            </Button>
          )}

          {canExport ? (
            <a href={exportUrl} download="lich-su-nhan-dang.csv">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                className="h-8 px-3 text-xs font-semibold"
                leftIcon={<Download className="h-3.5 w-3.5" />}
              >
                Xuất CSV
              </Button>
            </a>
          ) : (
            <Button
              type="button"
              variant="secondary"
              size="sm"
              disabled
              className="h-8 px-3 text-xs"
              leftIcon={<Download className="h-3.5 w-3.5" />}
            >
              Xuất CSV
            </Button>
          )}
        </div>
      </div>

      {/* Secondary Row: Date Range & Confidence Slider (Inline compact) */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border/40 pt-2.5 text-xs text-content-muted">
        {/* Date Range */}
        <div className="flex items-center gap-2">
          <span className="font-medium text-[11px] text-content-muted">Thời gian:</span>
          <input
            type="date"
            value={dateFrom}
            max={dateTo || undefined}
            onChange={(event) => onDateFromChange(event.target.value)}
            className="rounded-lg border border-border bg-surface-raised/40 px-2 py-1 text-xs text-content focus:border-primary focus:outline-none"
          />
          <span>→</span>
          <input
            type="date"
            value={dateTo}
            min={dateFrom || undefined}
            onChange={(event) => onDateToChange(event.target.value)}
            className="rounded-lg border border-border bg-surface-raised/40 px-2 py-1 text-xs text-content focus:border-primary focus:outline-none"
          />
        </div>

        {/* Confidence Floor */}
        <div className="flex items-center gap-2.5">
          <span className="font-medium text-[11px] text-content-muted">Độ tin cậy ≥</span>
          <input
            type="range"
            min={0}
            max={100}
            step={5}
            value={confidencePercent}
            onChange={(event) => onConfidencePercentChange(Number(event.target.value))}
            className="h-1.5 w-24 cursor-pointer appearance-none rounded-full bg-surface-raised accent-primary"
          />
          <span className="font-mono text-xs font-bold text-primary w-8 text-right">
            {confidencePercent}%
          </span>
        </div>
      </div>
    </section>
  );
}

export default HistoryFilters;
