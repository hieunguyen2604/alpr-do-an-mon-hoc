/**
 * Live progress of the background video job (FR-2.1, FR-2.6).
 *
 * Two backend details drive almost every decision in this file, and both are
 * easy to render misleadingly:
 *
 * 1. **`progress` is a position in the video, `processed_frames` is a count of
 *    analysed frames.** The backend samples one frame in every `frame_stride`
 *    (5 by default) but computes `progress` as `frame_index / total_frames`.
 *    So `processed_frames / total_frames` is roughly one fifth of the real
 *    completion, and drawing a bar from it would show 20% on a finished job.
 *    The bar is driven by `progress`; the two frame counters are shown as two
 *    separate labelled facts rather than as a fraction.
 * 2. **`progress` is pinned to 0.99 when the frame count is unknown.** Some
 *    containers carry no reliable count, and the backend then reports a
 *    constant 0.99 so the client keeps polling. Rendering that as "99%" would
 *    promise an imminent finish that may be minutes away, so the bar switches
 *    to indeterminate whenever `total_frames` is null.
 */

import { useEffect, useState } from 'react';
import { Ban, RefreshCw } from 'lucide-react';

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

/**
 * Parse a timestamp coming from the API.
 *
 * The backend sends UTC. A date-time arriving without a zone designator would
 * be read as local time and land seven hours out in Vietnam, so the marker is
 * supplied when it is missing.
 *
 * @param isoString - Timestamp from the API.
 * @returns A `Date`, or `null` when absent or unparsable.
 */
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

/**
 * Format a rough remaining time in Vietnamese.
 *
 * Deliberately coarse — "khoảng 2 phút" rather than "1 phút 47 giây". The
 * estimate is a linear extrapolation from a job whose per-frame cost varies,
 * so a to-the-second figure would claim a precision it does not have.
 *
 * @param seconds - Estimated seconds remaining.
 * @returns A display string such as `"khoảng 2 phút"`.
 */
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

/**
 * Estimate the time left on a running job.
 *
 * Returns `null` whenever the estimate would be untrustworthy rather than
 * showing a confident wrong number:
 *
 * - the job is not actually processing;
 * - `total_frames` is unknown, in which case `progress` is the backend's fixed
 *   0.99 placeholder and extrapolating from it is meaningless;
 * - too little progress has been made for the rate to have settled.
 *
 * @param job - The job being followed.
 * @param nowMs - Current wall-clock time in milliseconds.
 * @returns Estimated seconds remaining, or `null` when not calculable.
 */
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
  // Below a few percent the elapsed time is dominated by start-up cost and the
  // extrapolation swings wildly between polls.
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

/**
 * Render the progress panel for a background video job.
 *
 * @param props - Job state, polling state and the refresh handler.
 * @returns The progress card.
 */
export function JobProgressPanel({
  job,
  jobId,
  isPolling,
  pollError,
  onRefresh,
}: JobProgressPanelProps): JSX.Element {
  const [nowMs, setNowMs] = useState<number>(() => Date.now());

  const isActive = job !== null && !isTerminalStatus(job.status);

  // Same idea as `isActive`, but true *before* the first poll as well. Used
  // only for what is shown: a control that appeared a second after the panel
  // did would read as a glitch, whereas starting the elapsed-time ticker for a
  // job that has not reported yet would be wrong.
  const isPossiblyRunning = job === null || !isTerminalStatus(job.status);

  // The remaining-time estimate is derived from wall-clock elapsed time, so it
  // has to advance between polls; without this ticker it would freeze for the
  // 1.5 s between updates and jump.
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

  // Unknown frame count means `progress` is the backend's fixed 0.99 filler.
  // Showing that as a near-complete bar would be a promise the job cannot keep.
  const isFrameCountUnknown = job !== null && job.total_frames === null;
  const isIndeterminate =
    job === null || status === 'pending' || (status === 'processing' && isFrameCountUnknown);

  return (
    <Card
      title="Tiến độ xử lý"
      description="Trạng thái được cập nhật tự động trong khi tác vụ chạy"
      actions={
        <>
          {/* FR-2.6 asks for a cancel control. The backend worker does honour a
              cancellation — it re-reads the job status every few frames and
              stops — but no HTTP route exists to set that status: the live
              OpenAPI document exposes nine paths and none of them cancels a
              job. The button is therefore present and disabled rather than
              wired to an invented endpoint, which would 404 and leave the user
              believing the job had stopped while it kept running.

              Shown only while the job can still be running: a dead "Huỷ tác
              vụ" beside a finished job is noise with nothing to explain it.
              The limitation itself is spelled out in the body below rather
              than left to a hover-only tooltip, which nobody reads and a
              projector never shows. */}
          {isPossiblyRunning && (
            <span
              title="Chưa hỗ trợ huỷ tác vụ: máy chủ chưa có API dừng một tác vụ đang chạy."
              className="inline-flex"
            >
              <Button
                type="button"
                variant="secondary"
                size="sm"
                disabled
                leftIcon={<Ban className="h-4 w-4" aria-hidden="true" />}
              >
                Huỷ tác vụ
              </Button>
            </span>
          )}

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

        {/* States the limitation in plain sight instead of hiding it behind the
            disabled button's tooltip. Honest about scope: the worker-side
            support exists, the HTTP route does not. */}
        {isPossiblyRunning && (
          <p className="rounded-lg border border-border bg-surface-muted px-4 py-3 text-xs text-content-muted">
            <span className="font-medium text-content">
              Về nút “Huỷ tác vụ”:
            </span>{' '}
            chức năng dừng tác vụ mới hoàn thiện ở phía xử lý nền — máy chủ chưa
            mở API để dừng một tác vụ đang chạy, nên nút được để ở trạng thái vô
            hiệu thay vì gọi một địa chỉ không tồn tại. Bạn có thể rời khỏi
            trang: tác vụ vẫn chạy tiếp và kết quả được lưu vào trang Lịch sử.
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
