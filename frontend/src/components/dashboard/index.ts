/**
 * Dashboard building blocks.
 *
 * Re-exported so the page composes them in one import statement.
 */

export { ChartViewToggle } from './ChartViewToggle';
export type { ChartView, ChartViewToggleProps } from './ChartViewToggle';

// The two charts are re-exported from `LazyCharts`, not from their own modules:
// that is what keeps Recharts out of the startup bundle. Importing them from
// here is unchanged for callers, and the type re-exports below are erased at
// compile time so they pull in no runtime code.
export { DailyTrendChart, InputTypeChart } from './LazyCharts';
export type { DailyTrendChartProps } from './DailyTrendChart';

export { InfoTooltip } from './InfoTooltip';
export type { InfoTooltipProps } from './InfoTooltip';

export type { InputTypeChartProps } from './InputTypeChart';

export { RecentDetections } from './RecentDetections';
export type { RecentDetectionsProps } from './RecentDetections';

export { StatisticsCards } from './StatisticsCards';
export type { StatisticsCardsProps } from './StatisticsCards';

export { SystemStatusCard } from './SystemStatusCard';
export type { SystemStatusCardProps } from './SystemStatusCard';

export { SERIES_LABELS, useChartTheme } from './chartTheme';
export type { ChartTheme } from './chartTheme';
