/**
 * Dashboard: aggregate statistics, activity charts and service health.
 *
 * Covers FR-4.1 (summary metrics) and FR-4.2 (charts over time and by source).
 *
 * Three independent requests feed this page, and they are deliberately *not*
 * combined into one all-or-nothing load. Health, statistics and the recent list
 * fail for different reasons, and a failed health check should not blank out
 * statistics that arrived perfectly well. Only a failure of the statistics call
 * — the page's actual subject — escalates to a full-page error.
 */

import { useCallback, useEffect } from 'react';
import { Activity, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';

import {
  DailyTrendChart,
  InputTypeChart,
  RecentDetections,
  StatisticsCards,
  SystemStatusCard,
} from '@/components/dashboard';
import { EmptyState, ErrorState } from '@/components/StateViews';
import { SkeletonTable } from '@/components/ui';
import { useApi } from '@/hooks/useApi';
import { DEFAULT_TREND_DAYS } from '@/lib/constants';
import { getHealth, getHistory, getStatistics } from '@/services/api';
import type { HistoryListResponse } from '@/types';

/** How many recent records the dashboard lists. */
const RECENT_RECORD_COUNT = 5;

/**
 * Fetch the dashboard's trend window.
 *
 * Declared at module scope so its identity is stable across renders — `useApi`
 * memoises on the function it is given, and an inline arrow would restart the
 * request on every render.
 *
 * @returns The statistics payload.
 */
function fetchStatistics() {
  return getStatistics({ days: DEFAULT_TREND_DAYS });
}

/**
 * Fetch the newest few history records.
 *
 * Sorted by `detected_time` descending, which is what "gần đây" means here —
 * when the plate was recognised, not when the row happened to be written.
 *
 * @returns One short page of history.
 */
function fetchRecentHistory(): Promise<HistoryListResponse> {
  return getHistory({
    page: 1,
    page_size: RECENT_RECORD_COUNT,
    sort_by: 'detected_time',
    order: 'desc',
  });
}

/**
 * Dashboard page.
 *
 * @returns The dashboard view.
 */
export default function Dashboard(): JSX.Element {
  const statisticsCall = useApi(fetchStatistics);
  const healthCall = useApi(getHealth);
  const recentCall = useApi(fetchRecentHistory);

  const { run: runStatistics } = statisticsCall;
  const { run: runHealth } = healthCall;
  const { run: runRecent } = recentCall;

  /**
   * Load, or reload, everything the page shows.
   *
   * The three calls are issued together rather than in sequence: they are
   * independent, and awaiting them one after another would make the slowest
   * request gate the other two for no reason.
   */
  const loadAll = useCallback((): void => {
    void runStatistics();
    void runHealth();
    void runRecent();
  }, [runStatistics, runHealth, runRecent]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const statistics = statisticsCall.data;
  const health = healthCall.data;
  const recentRecords = recentCall.data?.items ?? [];

  // Only the very first load shows skeletons. A refresh keeps the previous
  // figures on screen instead of flashing placeholders, which would make the
  // whole page jump for a request that usually returns in milliseconds.
  const isInitialLoading = statisticsCall.isLoading && statistics === null;

  // ---------------------------------------------------------------------------
  // Error — the statistics call is the page's subject, so its failure is fatal
  // ---------------------------------------------------------------------------
  if (statisticsCall.error && statistics === null) {
    return (
      <div className="card">
        <ErrorState message={statisticsCall.error} onRetry={loadAll} />
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Loading — skeletons in the real layout, so nothing shifts when data lands
  // ---------------------------------------------------------------------------
  if (isInitialLoading) {
    return (
      <div className="space-y-5" aria-busy="true">
        <StatisticsCards statistics={null} isLoading />
        <SystemStatusCard health={null} isLoading />
        <div className="card p-5">
          <SkeletonTable rows={6} columns={3} />
        </div>
        <div className="card p-5">
          <SkeletonTable rows={5} columns={4} />
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Empty — nothing has ever been processed
  // ---------------------------------------------------------------------------
  // Keyed on uploads *and* plates. Checking `total_detections` alone would show
  // the empty state to someone who has uploaded images in which no plate was
  // found — they have used the system, and telling them otherwise is wrong.
  const hasNoData =
    statistics !== null &&
    statistics.total_jobs === 0 &&
    statistics.total_detections === 0;

  if (hasNoData) {
    return (
      <div className="space-y-5">
        {/* Health still shows: knowing the model is not loaded is most useful
            precisely *before* the first upload. */}
        <SystemStatusCard
          health={health}
          isLoading={healthCall.isLoading && health === null}
          error={healthCall.error}
        />
        <div className="card">
          <EmptyState
            icon={Activity}
            title="Chưa có dữ liệu nhận dạng"
            description="Hãy tải lên một ảnh hoặc video để bắt đầu. Số liệu thống kê và biểu đồ sẽ xuất hiện tại đây ngay sau lần nhận dạng đầu tiên."
            action={
              <Link to="/image" className="btn-primary mt-1">
                Nhận dạng ảnh đầu tiên
              </Link>
            }
          />
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Success
  // ---------------------------------------------------------------------------
  return (
    <div className="space-y-5">
      <div className="flex items-center justify-end">
        <button
          type="button"
          onClick={loadAll}
          disabled={statisticsCall.isLoading}
          className="btn-secondary px-3 py-1.5 text-xs"
        >
          <RefreshCw
            className={`h-3.5 w-3.5 ${statisticsCall.isLoading ? 'animate-spin' : ''}`}
            aria-hidden="true"
          />
          {statisticsCall.isLoading ? 'Đang làm mới…' : 'Làm mới'}
        </button>
      </div>

      <StatisticsCards statistics={statistics} />

      <SystemStatusCard
        health={health}
        isLoading={healthCall.isLoading && health === null}
        error={healthCall.error}
      />

      {statistics && (
        <>
          <DailyTrendChart
            points={statistics.daily_counts}
            windowDays={DEFAULT_TREND_DAYS}
          />
          <InputTypeChart breakdown={statistics.by_input_type} />
        </>
      )}

      {recentCall.error ? (
        <div className="card">
          <ErrorState
            message={recentCall.error}
            onRetry={() => void runRecent()}
          />
        </div>
      ) : (
        <RecentDetections
          records={recentRecords}
          isLoading={recentCall.isLoading && recentCall.data === null}
        />
      )}
    </div>
  );
}
