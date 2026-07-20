/**
 * Deferred loading for the two Recharts-backed dashboard charts.
 *
 * Recharts is by far the heaviest dependency in the project, and it is used by
 * exactly two components — both of them on the dashboard. Importing them
 * statically pulled the whole charting library into the startup bundle, so the
 * webcam page paid for a library it never renders.
 *
 * These wrappers keep the public API of `@/components/dashboard` unchanged: the
 * page still writes `<DailyTrendChart points={…} />`. Only the moment the code
 * arrives changes. While the chunk is in flight a card-shaped placeholder of the
 * same height is shown, so the surrounding layout does not shift when the real
 * chart replaces it.
 */

import { lazy, Suspense } from 'react';

import { Skeleton } from '@/components/ui';

import type { DailyTrendChartProps } from './DailyTrendChart';
import type { InputTypeChartProps } from './InputTypeChart';

/**
 * Both modules expose the component as a named *and* a default export;
 * `lazy` requires the default one, which is what is imported here.
 */
const DailyTrendChartImpl = lazy(() => import('./DailyTrendChart'));
const InputTypeChartImpl = lazy(() => import('./InputTypeChart'));

/**
 * Placeholder occupying the same box as a loaded chart card.
 *
 * The `h-72` body matches the plot height used by both charts, and the header
 * block matches `PageSection`'s header, so swapping the placeholder for the
 * chart does not move anything below it on the page.
 *
 * @returns The placeholder card.
 */
function ChartCardFallback(): JSX.Element {
  return (
    <section className="card" aria-busy="true">
      <div className="border-b border-border px-5 py-3.5">
        <Skeleton className="h-4 w-48" />
        <Skeleton className="mt-2 h-3 w-72 max-w-full" />
      </div>
      <div className="p-5">
        <Skeleton className="h-72 w-full" rounded="lg" />
      </div>
    </section>
  );
}

/**
 * Daily activity chart, loaded on demand.
 *
 * @param props - Same props as the underlying chart.
 * @returns The chart, or a placeholder while its chunk loads.
 */
export function DailyTrendChart(props: DailyTrendChartProps): JSX.Element {
  return (
    <Suspense fallback={<ChartCardFallback />}>
      <DailyTrendChartImpl {...props} />
    </Suspense>
  );
}

/**
 * Input-type breakdown chart, loaded on demand.
 *
 * @param props - Same props as the underlying chart.
 * @returns The chart, or a placeholder while its chunk loads.
 */
export function InputTypeChart(props: InputTypeChartProps): JSX.Element {
  return (
    <Suspense fallback={<ChartCardFallback />}>
      <InputTypeChartImpl {...props} />
    </Suspense>
  );
}
