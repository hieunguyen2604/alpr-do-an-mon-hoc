/**
 * Results of a finished video job.
 *
 * The plate list does not come from the job object — `DetectionJob` carries
 * only a `detection_count`. The rows themselves are read from
 * `GET /api/history?job_id=…`, which is the same data the history page shows,
 * so the two views cannot disagree about what a job produced.
 */

import { Download, Film, ScanLine } from 'lucide-react';

import {
  Badge,
  Button,
  Card,
  ConfidenceBar,
  EmptyState,
  ErrorState,
  PlateChip,
  Skeleton,
} from '@/components/ui';
import { fileUrl } from '@/services/api';
import { formatDateTime, formatNumber, formatProcessingTime, formatVideoTime } from '@/lib/format';
import { plateClassBadges } from '@/lib/plateClass';
import type { DetectionHistory, DetectionJob } from '@/types';

/** Props of {@link VideoResultPanel}. */
export interface VideoResultPanelProps {
  /** The completed job. */
  job: DetectionJob;
  /** Plates recorded against this job, already de-duplicated by the backend. */
  plates: DetectionHistory[];
  /** Whether the plate list is being fetched. */
  isLoading: boolean;
  /** Display-ready Vietnamese error from the plate-list request, or `null`. */
  error: string | null;
  /** Re-request the plate list. */
  onRetry: () => void;
}

/**
 * Explanation of the backend's frame merging, shown under every result set.
 *
 * Required as an explicit note because the count is otherwise surprising: a car
 * visible for four seconds appears in dozens of sampled frames, yet produces a
 * single row. Without this the user reads a low plate count as missed
 * detections.
 *
 * @returns The note element.
 */
function DeduplicationNote(): JSX.Element {
  return (
    <p className="rounded-lg border border-border bg-surface-muted px-4 py-3 text-xs leading-relaxed text-content-muted">
      <span className="font-medium text-content">Về cách đếm biển số: </span>
      một xe xuất hiện trong nhiều khung hình liên tiếp chỉ được tính là{' '}
      <span className="font-medium text-content">một bản ghi</span>. Hệ thống gộp
      các lần xuất hiện của cùng một biển số trong toàn bộ video và giữ lại lần
      đọc có độ tin cậy cao nhất. Vì vậy số biển số dưới đây là số{' '}
      <span className="font-medium text-content">xe khác nhau</span> đã nhận
      dạng được, không phải số lần xuất hiện.
    </p>
  );
}

/**
 * Render one detected plate.
 *
 * @param props - The history record to render.
 * @returns The plate card.
 */
function PlateCard({ record }: { record: DetectionHistory }): JSX.Element {
  const cropUrl = fileUrl(record.plate_image_path);

  return (
    <li className="flex gap-3 rounded-lg border border-border bg-surface p-3">
      {cropUrl ? (
        <img
          src={cropUrl}
          alt={`Ảnh biển số ${record.plate_number ?? 'không đọc được'}`}
          loading="lazy"
          className="h-14 w-24 shrink-0 rounded border border-border object-cover"
        />
      ) : (
        <div
          aria-hidden="true"
          className="flex h-14 w-24 shrink-0 items-center justify-center rounded border border-dashed border-border bg-surface-muted text-content-muted"
        >
          <ScanLine className="h-5 w-5" />
        </div>
      )}

      <div className="min-w-0 flex-1 space-y-2">
        <PlateChip
          plateNumber={record.plate_display ?? record.plate_number}
          isValidFormat={record.is_valid_format}
          size="sm"
        />

        {/* Same badges as the image page. A video result is the same kind of
            evidence as a still one, and an army plate shown here without them
            would carry the "wrong format" reading that the badges exist to
            prevent. */}
        {record.plate_number && (
          <div className="flex flex-wrap gap-1.5">
            {plateClassBadges(
              record.is_valid_format,
              record.plate_kind,
              record.plate_color,
            ).map((badge) => (
              <Badge key={badge.label} variant={badge.tone} title={badge.title}>
                {badge.label}
              </Badge>
            ))}
          </div>
        )}

        <ConfidenceBar
          value={record.confidence}
          label="Độ tin cậy phát hiện"
          size="sm"
          showValue
        />
        <p className="text-xs text-content-muted">
          {/* Where in the clip, first: it is the field that makes a video result
              checkable. Without it a list of plates cannot be traced back to
              the moments that produced them. */}
          {record.video_time_seconds !== null && (
            <>
              <span className="font-medium text-content">
                {formatVideoTime(record.video_time_seconds)}
              </span>
              {' · '}
            </>
          )}
          {record.plate_line_count !== null && `${record.plate_line_count} dòng · `}
          {formatDateTime(record.detected_time)} ·{' '}
          {formatProcessingTime(record.processing_time)}
        </p>
      </div>
    </li>
  );
}

/**
 * Render the results panel of a finished video job.
 *
 * @param props - Job, plate list, request state and the retry handler.
 * @returns The results card.
 */
export function VideoResultPanel({
  job,
  plates,
  isLoading,
  error,
  onRetry,
}: VideoResultPanelProps): JSX.Element {
  const outputUrl = fileUrl(job.output_url);

  return (
    <Card
      title="Kết quả nhận dạng"
      description={`Tác vụ hoàn thành lúc ${formatDateTime(job.completed_at)}`}
      actions={
        outputUrl ? (
          <a href={outputUrl} download>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              leftIcon={<Download className="h-4 w-4" aria-hidden="true" />}
            >
              Tải video kết quả
            </Button>
          </a>
        ) : undefined
      }
    >
      <div className="space-y-4">
        {isLoading && (
          <div className="space-y-3" aria-busy="true">
            <p className="text-sm text-content-muted">
              Đang tải danh sách biển số…
            </p>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {[0, 1, 2].map((key) => (
                <Skeleton key={key} className="h-24 w-full rounded-lg" />
              ))}
            </div>
          </div>
        )}

        {!isLoading && error && (
          <ErrorState
            title="Không tải được danh sách biển số"
            message={error}
            onRetry={onRetry}
            retryLabel="Thử lại"
          />
        )}

        {!isLoading && !error && plates.length === 0 && (
          <EmptyState
            icon={<ScanLine className="h-6 w-6" aria-hidden="true" />}
            title="Không tìm thấy biển số nào"
            description="Video đã được xử lý xong nhưng hệ thống không nhận dạng được biển số nào. Hãy thử video có biển số rõ nét hơn, ít bị che khuất hoặc quay ở khoảng cách gần hơn."
          />
        )}

        {!isLoading && !error && plates.length > 0 && (
          <>
            <p className="text-sm text-content">
              Đã nhận dạng{' '}
              <span className="font-semibold">
                {formatNumber(plates.length)}
              </span>{' '}
              biển số khác nhau trong video.
            </p>
            <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {plates.map((record) => (
                <PlateCard key={record.id} record={record} />
              ))}
            </ul>
          </>
        )}

        {!isLoading && !error && <DeduplicationNote />}

        {/* Absent rather than broken: the backend does not yet render an
            annotated copy of the video, so `output_url` is null on every job
            today. Saying so is better than leaving a user hunting for a
            download button that was never going to appear. */}
        {!outputUrl && (
          <p className="flex items-start gap-2 text-xs text-content-muted">
            <Film className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            <span>
              Video kết quả có gắn khung nhận dạng chưa khả dụng cho tác vụ này.
              Các biển số nhận được vẫn đã được lưu vào lịch sử và có thể xem
              hoặc xuất ra tệp CSV ở trang Lịch sử.
            </span>
          </p>
        )}
      </div>
    </Card>
  );
}

export default VideoResultPanel;
