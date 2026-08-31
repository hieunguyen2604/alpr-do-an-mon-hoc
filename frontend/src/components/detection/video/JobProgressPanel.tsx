/** Live progress of the background video job (FR-2.1, FR-2.6). */

import { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';

import { Badge, Button, Card, ProgressBar } from '@/components/ui';
import { cn } from '@/lib/cn';
import { JOB_STATUS_LABELS, isTerminalStatus } from '@/lib/constants';
import { formatDateTime, formatNumber } from '@/lib/format';
import type { BadgeVariant, ProgressBarVariant } from '@/components/ui';
import type { DetectionJob, JobStatus } from '@/types';

/** Props of {@link JobProgressPanel}. */
export interface JobProgressPanelProps {
  /** Latest job state, or `null` before the first successful poll. */
  job: DetectionJob | null;
  /** Id of the job being followed, known before the first poll returns. */
  jobId: string;
  /** Whether the polling hook is actively requesting updates. */
  isPolling: boolean;
  /** Display-ready Vietnamese polling error, or `null`. */
  pollError: string | null;
  /** Poll once immediately, for the retry button. */
  onRefresh: () => void;
}

/** Badge colour for each job status. */
const STATUS_BADGE_VARIANT: Readonly<Record<JobStatus, BadgeVariant>> = {
  pending: 'info',
  processing: 'info',
  completed: 'success',
  failed: 'danger',
  cancelled: 'neutral',
};

/** Progress-bar colour for each job status. */
const STATUS_BAR_VARIANT: Readonly<Record<JobStatus, ProgressBarVariant>> = {
  pending: 'primary',
  processing: 'primary',
  completed: 'success',
  failed: 'danger',
  cancelled: 'warning',
};

/** One-line explanation of what each status means for the user. */
const STATUS_HINTS: Readonly<Record<JobStatus, string>> = {
  pending: 'Video đã được nhận và đang xếp hàng chờ xử lý.',
  processing: 'Hệ thống đang phân tích từng khung hình để tìm biển số.',
  completed: 'Đã xử lý xong toàn bộ video.',
  failed:
    'Quá trình xử lý không hoàn tất. Bạn có thể thử lại với một video khác.',
  cancelled: 'Tác vụ đã được dừng trước khi xử lý xong.',
};

/** Parse a timestamp coming from the API (assumes UTC if no timezone is provided). */
function parseApiDate(isoString: string | null | undefined): Date | null {
  if (!isoString) {
    return null;
  }
  const hasTime = isoString.includes('T') || isoString.includes(' ');
  const hasZone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(isoString);
  const normalized = hasTime && !hasZone ? `${isoString}Z` : isoString;

  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : date;
}

/** Format a rough remaining time in Vietnamese (e.g. "khoảng 2 phút"). */
function formatRemainingTime(seconds: number): string {
  if (seconds < 10) {
    return 'chỉ còn vài giây';
  }
  if (seconds < 60) {
    return `khoảng ${Math.round(seconds / 10) * 10} giây`;
  }
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) {
    return `khoảng ${minutes} phút`;
  }
  const hours = Math.floor(minutes / 60);
  const restMinutes = minutes % 60;
  return restMinutes === 0
    ? `khoảng ${hours} giờ`
    : `khoảng ${hours} giờ ${restMinutes} phút`;
}

/** Estimate the time left on a running job, returning `null` if the estimate is untrustworthy. */
function estimateRemainingSeconds(
  job: DetectionJob,
  nowMs: number,
): number | null {
  if (job.status !== 'processing') {
    return null;
  }
  if (job.total_frames === null || job.total_frames <= 0) {
    return null;
  }
  // Suppress remaining time extrapolation below 5% or when completed
  if (job.progress < 0.05 || job.progress >= 1) {
    return null;
  }

  const startedAt = parseApiDate(job.created_at);
  if (!startedAt) {
    return null;
  }

  const elapsedSeconds = (nowMs - startedAt.getTime()) / 1000;
  if (elapsedSeconds <= 0) {
    return null;
  }

  const remaining = (elapsedSeconds * (1 - job.progress)) / job.progress;
  return Number.isFinite(remaining) && remaining > 0 ? remaining : null;
}

/** Render the progress panel for a background video job. */
export function JobProgressPanel({
  job,
  jobId,
  isPolling,
  pollError,
  onRefresh,
}: JobProgressPanelProps): JSX.Element {
  const [nowMs, setNowMs] = useState<number>(() => Date.now());

  const isActive = job !== null && !isTerminalStatus(job.status);

  // True before first poll and while job is running
  const isPossiblyRunning = job === null || !isTerminalStatus(job.status);

  // Advance elapsed wall-clock timer between polls
  useEffect(() => {
    if (!isActive) {
      return undefined;
    }
    const timerId = window.setInterval(() => {
      setNowMs(Date.now());
    }, 1000);
    return () => {
      window.clearInterval(timerId);
    };
  }, [isActive]);

  const status: JobStatus = job?.status ?? 'pending';
  const remainingSeconds = job ? estimateRemainingSeconds(job, nowMs) : null;

  // Indeterminate progress when total frame count is unknown
  const isFrameCountUnknown = job !== null && job.total_frames === null;
  const isIndeterminate =
    job === null || status === 'pending' || (status === 'processing' && isFrameCountUnknown);

  return (
    <Card
      title="Tiến độ xử lý"
      description="Trạng thái được cập nhật tự động trong khi tác vụ chạy"
      actions={
        <>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onRefresh}
            leftIcon={
              <RefreshCw
                className={cn('h-4 w-4', isPolling && 'animate-spin')}
                aria-hidden="true"
              />
            }
          >
            Cập nhật
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2.5">
            <Badge variant={STATUS_BADGE_VARIANT[status]}>
              {JOB_STATUS_LABELS[status]}
            </Badge>
            <span className="font-mono text-xs text-content-muted">
              Mã tác vụ: {jobId}
            </span>
          </div>
          {!isIndeterminate && job && (
            <span className="text-sm font-medium tabular-nums text-content">
              {Math.round(job.progress * 100)}%
            </span>
          )}
        </div>

        <ProgressBar
          value={job?.progress ?? 0}
          variant={STATUS_BAR_VARIANT[status]}
          indeterminate={isIndeterminate}
          size="lg"
        />

        <p className="text-sm text-content-muted">
          {STATUS_HINTS[status]}
          {remainingSeconds !== null && (
            <span className="text-content">
              {' '}
              Dự kiến {formatRemainingTime(remainingSeconds)} nữa.
            </span>
          )}
        </p>

        <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm lg:grid-cols-4">
          <div>
            <dt className="text-xs text-content-muted">
              Khung hình đã phân tích
            </dt>
            <dd className="mt-0.5 font-medium tabular-nums text-content">
              {formatNumber(job?.processed_frames ?? 0)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-content-muted">
              Tổng khung hình của video
            </dt>
            <dd className="mt-0.5 font-medium tabular-nums text-content">
              {job?.total_frames !== null && job?.total_frames !== undefined
                ? formatNumber(job.total_frames)
                : 'Đang xác định'}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-content-muted">Biển số tìm thấy</dt>
            <dd className="mt-0.5 font-medium tabular-nums text-content">
              {formatNumber(job?.detection_count ?? 0)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-content-muted">Bắt đầu lúc</dt>
            <dd className="mt-0.5 font-medium text-content">
              {formatDateTime(job?.created_at)}
            </dd>
          </div>
        </dl>

        {/* The two frame counters are not a fraction of one another: the
            pipeline samples one frame in every few, so "đã phân tích" is
            legitimately far smaller than the total on a finished job. Said out
            loud, because a user comparing the two numbers would otherwise
            conclude the job stopped early. */}
        <p className="text-xs text-content-muted">
          Hệ thống lấy mẫu khung hình theo chu kỳ thay vì phân tích toàn bộ, nên
          số khung hình đã phân tích luôn nhỏ hơn tổng số khung hình của video.
          Thanh tiến độ phản ánh vị trí đang xử lý trong video.
        </p>

        {/* Cancelling a running job is out of scope (FR-2.6 withdrawn). Say so
            once, plainly, so a user who wants to stop the job is not left
            hunting for a control that does not exist. */}
        {isPossiblyRunning && (
          <p className="rounded-lg border border-border bg-surface-muted px-4 py-3 text-xs text-content-muted">
            Tác vụ chạy đến khi hoàn tất và không dừng giữa chừng được. Bạn có
            thể rời khỏi trang: kết quả vẫn được lưu vào trang Lịch sử.
          </p>
        )}

        {/* A dropped poll is not a dead job, so the hook tolerates a few before
            surfacing anything. Once it does, the job may well still be running
            on the server — hence "không đọc được tiến độ", not "thất bại". */}
        {pollError && (
          <div
            role="alert"
            className="rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger"
          >
            <p className="font-medium">Không cập nhật được tiến độ</p>
            <p className="mt-1">{pollError}</p>
            <p className="mt-1 text-content-muted">
              Tác vụ có thể vẫn đang chạy trên máy chủ. Bấm “Cập nhật” để thử
              lại.
            </p>
          </div>
        )}

        {/* The API reports that a job failed but never why: the technical
            reason is logged against the request id and deliberately not
            serialised (NFR-S4). The wording here is fixed and safe rather than
            anything echoed back from the server. */}
        {status === 'failed' && (
          <div
            role="alert"
            className="rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger"
          >
            <p className="font-medium">Xử lý video thất bại</p>
            <p className="mt-1">
              Vui lòng thử lại với một video khác. Nếu lỗi lặp lại, hãy liên hệ
              quản trị viên kèm mã tác vụ ở trên.
            </p>
          </div>
        )}
      </div>
    </Card>
  );
}

export default JobProgressPanel;
