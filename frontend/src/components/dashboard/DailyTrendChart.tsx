/**
 * Activity over time (FR-4.2).
 *
 * Plots uploads and recognised plates as two lines on **one** axis. Both are
 * plain counts of comparable magnitude, so a shared scale is honest — a second
 * y-axis would let the two lines be aligned arbitrarily and invent a
 * relationship the data does not contain.
 */

import { useState } from 'react';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { CalendarRange } from 'lucide-react';

import { EmptyState, PageSection } from '@/components/StateViews';
import { Table } from '@/components/ui';
import type { TableColumn } from '@/components/ui';
import { formatChartDate, formatDate, formatNumber } from '@/lib/format';
import type { DetectionsOverTimePoint } from '@/types';

import { ChartViewToggle } from './ChartViewToggle';
import type { ChartView } from './ChartViewToggle';
import { SERIES_LABELS, useChartTheme } from './chartTheme';

/** Props of {@link DailyTrendChart}. */
export interface DailyTrendChartProps {
  /** Per-day counts from `Statistics.daily_counts`, oldest first. */
  points: readonly DetectionsOverTimePoint[];
  /** Length of the window in days, for the section subtitle. */
  windowDays: number;
}

/** One row of the plotted series, keyed by the Vietnamese series labels. */
interface TrendDatum {
  /** Calendar day, `YYYY-MM-DD`. Kept for the table view and the tooltip. */
  date: string;
  /** Short `dd/mm` label for the x-axis. */
  axisLabel: string;
  [SERIES_LABELS.jobs]: number;
  [SERIES_LABELS.plates]: number;
}

/**
 * Render the daily activity chart with its table-view twin.
 *
 * @param props - The daily points and the window length.
 * @returns The chart section.
 */
export function DailyTrendChart({
  points,
  windowDays,
}: DailyTrendChartProps): JSX.Element {
  const theme = useChartTheme();
  const [view, setView] = useState<ChartView>('chart');

  const data: TrendDatum[] = points.map((point) => ({
    date: point.date,
    axisLabel: formatChartDate(point.date),
    [SERIES_LABELS.jobs]: point.job_count,
    [SERIES_LABELS.plates]: point.detection_count,
  }));

  // Days with no activity come back from the API as explicit zeroes rather than
  // being omitted, so an all-zero window means "a quiet week", not "no data".
  // Drawing two flat lines along the baseline says that clearly; an empty state
  // here would wrongly suggest the window itself is missing.
  const hasAnyActivity = points.some(
    (point) => point.job_count > 0 || point.detection_count > 0,
  );

  const columns: readonly TableColumn<TrendDatum>[] = [
    {
      key: 'date',
      header: 'Ngày',
      accessor: (row) => formatDate(row.date),
    },
    {
      key: 'jobs',
      header: SERIES_LABELS.jobs,
      align: 'right',
      className: 'tabular-nums',
      accessor: (row) => formatNumber(row[SERIES_LABELS.jobs]),
    },
    {
      key: 'plates',
      header: SERIES_LABELS.plates,
      align: 'right',
      className: 'tabular-nums',
      accessor: (row) => formatNumber(row[SERIES_LABELS.plates]),
    },
  ];

  return (
    <PageSection
      title="Hoạt động theo ngày"
      subtitle={`Số lượt nhận dạng và số biển số phát hiện trong ${windowDays} ngày gần nhất`}
      actions={
        data.length > 0 ? (
          <ChartViewToggle
            value={view}
            onChange={setView}
            subject="hoạt động theo ngày"
          />
        ) : undefined
      }
    >
      {data.length === 0 ? (
        <EmptyState
          icon={CalendarRange}
          title="Chưa có dữ liệu theo ngày"
          description="Biểu đồ sẽ xuất hiện sau lần nhận dạng đầu tiên."
        />
      ) : view === 'table' ? (
        <Table
          columns={columns}
          rows={data}
          getRowKey={(row) => row.date}
          caption="Số lượt nhận dạng và số biển số phát hiện theo từng ngày"
        />
      ) : (
        <>
          {!hasAnyActivity && (
            <p className="mb-3 text-xs text-content-muted">
              Chưa có hoạt động nào trong khoảng thời gian này.
            </p>
          )}
          {/*
            The height covers the plot *and* the x-axis band. Sizing it to the
            plot alone leaves the date labels outside the box and gives the card
            its own small vertical scrollbar.
          */}
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={data}
                margin={{ top: 8, right: 12, bottom: 4, left: 4 }}
              >
                {/*
                  Horizontal rules only, solid and one shade off the surface.
                  Dashed gridlines read as a threshold or a projection when they
                  are only a grid, and vertical rules add nothing when the axis
                  already ticks once per day.
                */}
                <CartesianGrid
                  horizontal
                  vertical={false}
                  stroke={theme.grid}
                />
                <XAxis
                  dataKey="axisLabel"
                  stroke={theme.grid}
                  tick={{ fill: theme.axis, fontSize: 12 }}
                  tickLine={false}
                  axisLine={{ stroke: theme.grid }}
                />
                <YAxis
                  stroke={theme.grid}
                  tick={{ fill: theme.axis, fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                  allowDecimals={false}
                  width={40}
                />
                <Tooltip
                  cursor={{ stroke: theme.grid, strokeWidth: 1 }}
                  contentStyle={{
                    backgroundColor: theme.surface,
                    border: `1px solid ${theme.border}`,
                    borderRadius: '0.5rem',
                    fontSize: '0.75rem',
                  }}
                  // The label defaults to the abbreviated `dd/mm` axis value;
                  // the tooltip has room for the full date, which removes any
                  // ambiguity about the year.
                  labelFormatter={(_label, payload) => {
                    const point = payload?.[0]?.payload as
                      | TrendDatum
                      | undefined;
                    return point ? formatDate(point.date) : '';
                  }}
                  labelStyle={{ color: theme.text, fontWeight: 600 }}
                  itemStyle={{ color: theme.text }}
                />
                <Legend
                  wrapperStyle={{ fontSize: '0.75rem', color: theme.axis }}
                  iconType="plainline"
                />
                <Line
                  type="monotone"
                  dataKey={SERIES_LABELS.jobs}
                  stroke={theme.jobs}
                  strokeWidth={2}
                  // An 8px marker is large enough to see and to aim at; the
                  // active dot grows further so the hover target is comfortable.
                  dot={{ r: 4, strokeWidth: 0, fill: theme.jobs }}
                  activeDot={{ r: 6, strokeWidth: 2, stroke: theme.surface }}
                />
                <Line
                  type="monotone"
                  dataKey={SERIES_LABELS.plates}
                  stroke={theme.plates}
                  strokeWidth={2}
                  dot={{ r: 4, strokeWidth: 0, fill: theme.plates }}
                  activeDot={{ r: 6, strokeWidth: 2, stroke: theme.surface }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </PageSection>
  );
}

export default DailyTrendChart;
