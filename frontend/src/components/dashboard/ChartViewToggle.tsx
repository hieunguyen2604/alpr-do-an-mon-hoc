/**
 * Switch between a chart and the same data as a table.
 *
 * A chart encodes values as position and colour, which leaves them unreadable
 * to a screen reader and hard to read for anyone who needs an exact figure. The
 * table view is the equivalent that carries every value as text, so the
 * information is never available through the graphic alone (NFR-U5).
 */

import { BarChart3, TableIcon } from 'lucide-react';

import { cn } from '@/lib/cn';

/** Which representation is on screen. */
export type ChartView = 'chart' | 'table';

/** Props of {@link ChartViewToggle}. */
export interface ChartViewToggleProps {
  value: ChartView;
  onChange: (view: ChartView) => void;
  /**
   * Names what is being switched, e.g. `"biểu đồ theo ngày"`. Used to build a
   * distinct accessible label for each toggle on the page — several identical
   * "Xem dạng bảng" buttons are ambiguous when listed out of context.
   */
  subject: string;
}

/**
 * Render a two-option segmented control.
 *
 * Built from real buttons in a `radiogroup`, so the pair is reachable by
 * keyboard and its state is announced. Each option keeps a text label rather
 * than relying on its icon alone.
 *
 * @param props - Current view, change handler and the subject being toggled.
 * @returns The segmented control.
 */
export function ChartViewToggle({
  value,
  onChange,
  subject,
}: ChartViewToggleProps): JSX.Element {
  const options = [
    { view: 'chart' as const, label: 'Biểu đồ', Icon: BarChart3 },
    { view: 'table' as const, label: 'Bảng', Icon: TableIcon },
  ];

  return (
    <div
      role="radiogroup"
      aria-label={`Cách hiển thị ${subject}`}
      className="inline-flex rounded-lg border border-border p-0.5"
    >
      {options.map(({ view, label, Icon }) => {
        const isActive = value === view;
        return (
          <button
            key={view}
            type="button"
            role="radio"
            aria-checked={isActive}
            onClick={() => onChange(view)}
            className={cn(
              'inline-flex items-center gap-1.5 rounded-md px-2.5 py-1',
              'text-xs font-medium transition-colors',
              isActive
                ? 'bg-primary text-white dark:text-slate-950'
                : 'text-content-muted hover:text-content',
            )}
          >
            <Icon className="h-3.5 w-3.5" aria-hidden="true" />
            {label}
          </button>
        );
      })}
    </div>
  );
}

export default ChartViewToggle;
