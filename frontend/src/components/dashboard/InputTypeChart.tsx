/**
 * Distribution by input source (FR-4.2).
 *
 * A **grouped bar** rather than a pie, for two reasons. The section has to show
 * `job_count` and `detection_count` together, and a pie can only encode one
 * measure — showing uploads alone would hide that webcam sessions produce many
 * plates per session while a photo usually produces one. And the categories are
 * routinely close in size, which is exactly where angle comparison fails and
 * length comparison works.
 *
 * The two bars in each group carry the same two colours as the daily chart:
 * blue is always uploads, green is always plates, on every chart of the page.
 */

import { useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { PieChart as PieChartIcon } from 'lucide-react';

import { EmptyState, PageSection } from '@/components/StateViews';
import { Table } from '@/components/ui';
import type { TableColumn } from '@/components/ui';
import { formatInputType, formatNumber } from '@/lib/format';
import type { InputTypeBreakdown } from '@/types';

import { ChartViewToggle } from './ChartViewToggle';
import type { ChartView } from './ChartViewToggle';
import { SERIES_LABELS, useChartTheme } from './chartTheme';

/** Props of {@link InputTypeChart}. */
export interface InputTypeChartProps {
  /** Per-source counts from `Statistics.by_input_type`. */
  breakdown: readonly InputTypeBreakdown[];
}

/** One category row, keyed by the Vietnamese series labels. */
interface InputTypeDatum {
  /** Stable key: the raw API value, not the translated label. */
  key: string;
  /** Vietnamese category name shown on the axis. */
  name: string;
  [SERIES_LABELS.jobs]: number;
  [SERIES_LABELS.plates]: number;
}

/**
 * Render the input-type distribution with its table-view twin.
 *
 * @param props - The per-source breakdown.
 * @returns The chart section.
 */
export function InputTypeChart({ breakdown }: InputTypeChartProps): JSX.Element {
  const theme = useChartTheme();
  const [view, setView] = useState<ChartView>('chart');

  const data: InputTypeDatum[] = breakdown.map((entry) => ({
    key: entry.input_type,
    name: formatInputType(entry.input_type),
    [SERIES_LABELS.jobs]: entry.job_count,
    [SERIES_LABELS.plates]: entry.detection_count,
  }));

  // The API returns all three sources whether or not they were used, so an
  // all-zero breakdown means "nothing processed yet" rather than "no such
  // categories".
  const hasAnyActivity = breakdown.some(
    (entry) => entry.job_count > 0 || entry.detection_count > 0,
  );

  const columns: readonly TableColumn<InputTypeDatum>[] = [
    {
      key: 'name',
      header: 'Loại đầu vào',
      accessor: (row) => row.name,
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
      title="Phân bố theo loại đầu vào"
      subtitle="So sánh số lượt nhận dạng và số biển số phát hiện giữa ảnh, video và webcam"
      actions={
        data.length > 0 ? (
          <ChartViewToggle
            value={view}
            onChange={setView}
            subject="phân bố theo loại đầu vào"
          />
        ) : undefined
      }
    >
      {data.length === 0 ? (
        <EmptyState
          icon={PieChartIcon}
          title="Chưa có dữ liệu phân bố"
          description="Biểu đồ sẽ xuất hiện sau lần nhận dạng đầu tiên."
        />
      ) : view === 'table' ? (
        <Table
          columns={columns}
          rows={data}
          getRowKey={(row) => row.key}
          caption="Số lượt nhận dạng và số biển số phát hiện theo từng loại đầu vào"
        />
      ) : (
        <>
          {!hasAnyActivity && (
            <p className="mb-3 text-xs text-content-muted">
              Chưa có hoạt động nào để so sánh.
            </p>
          )}
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={data}
                margin={{ top: 8, right: 12, bottom: 4, left: 4 }}
                // A 2px surface gap separates the paired bars. A drawn border
                // around each bar would do the same job with more visual noise.
                barGap={2}
                barCategoryGap="28%"
              >
                <CartesianGrid
                  horizontal
                  vertical={false}
                  stroke={theme.grid}
                />
                <XAxis
                  dataKey="name"
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
                  cursor={{ fill: theme.grid, fillOpacity: 0.35 }}
                  contentStyle={{
                    backgroundColor: theme.surface,
                    border: `1px solid ${theme.border}`,
                    borderRadius: '0.5rem',
                    fontSize: '0.75rem',
                  }}
                  labelStyle={{ color: theme.text, fontWeight: 600 }}
                  itemStyle={{ color: theme.text }}
                />
                <Legend
                  wrapperStyle={{ fontSize: '0.75rem', color: theme.axis }}
                />
                {/* Rounded only at the data end, anchored on the baseline. */}
                <Bar
                  dataKey={SERIES_LABELS.jobs}
                  fill={theme.jobs}
                  radius={[4, 4, 0, 0]}
                  maxBarSize={44}
                />
                <Bar
                  dataKey={SERIES_LABELS.plates}
                  fill={theme.plates}
                  radius={[4, 4, 0, 0]}
                  maxBarSize={44}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </PageSection>
  );
}

export default InputTypeChart;
