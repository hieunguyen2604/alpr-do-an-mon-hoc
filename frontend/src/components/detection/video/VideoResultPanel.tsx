/** Results list and video summary for a completed video detection job. */

import { useState } from 'react';
import {
  Check,
  Clock,
  Copy,
  Download,
  Eye,
  Film,
  ScanLine,
  ShieldCheck,
  AlertTriangle,
} from 'lucide-react';

import {
  Badge,
  Button,
  Card,
  ConfidenceBar,
  EmptyState,
  ErrorState,
  Skeleton,
} from '@/components/ui';
import { fileUrl } from '@/services/api';
import { formatProcessingTime, formatVideoTime } from '@/lib/format';
import { plateClassBadges } from '@/lib/plateClass';
import { cn } from '@/lib/cn';
import type { DetectionHistory, DetectionJob } from '@/types';

export interface VideoResultPanelProps {
  job: DetectionJob;
  plates: DetectionHistory[];
  isLoading: boolean;
  error: string | null;
  onRetry: () => void;
  onOpenDetails?: (record: DetectionHistory) => void;
}

function DeduplicationNote(): JSX.Element {
  return (
    <p className="rounded-xl border border-border/60 bg-surface-raised/40 p-3 text-xs leading-relaxed text-content-muted">
      <span className="font-semibold text-content">Quy tắc khử trùng lặp (Deduplication): </span>
      Một xe xuất hiện trong nhiều khung hình liên tiếp được tự động gộp thành{' '}
      <span className="font-semibold text-emerald-400">1 bản ghi duy nhất</span> với độ tin cậy cao nhất.
    </p>
  );
}

function PlateCard({
  record,
  onOpenDetails,
}: {
  record: DetectionHistory;
  onOpenDetails?: (record: DetectionHistory) => void;
}): JSX.Element {
  const [copied, setCopied] = useState(false);
  const cropUrl = fileUrl(record.plate_image_path);
  const displayPlate = record.plate_display ?? record.plate_number ?? 'Không đọc được';

  const handleCopy = async () => {
    if (record.plate_number || record.plate_display) {
      await navigator.clipboard.writeText(displayPlate);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <li className="group rounded-xl border border-border/80 bg-surface p-3.5 transition-all duration-200 hover:border-primary/50 hover:shadow-md">
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
        {/* Cropped Plate Image */}
        <div className="relative shrink-0">
          {cropUrl ? (
            <img
              src={cropUrl}
              alt={`Ảnh biển số ${displayPlate}`}
              loading="lazy"
              className={cn(
                'h-14 w-28 rounded-lg border object-contain bg-surface-raised cursor-pointer transition-all',
                record.is_valid_format
                  ? 'border-emerald-500/40 shadow-[0_0_8px_rgba(16,185,129,0.15)] group-hover:border-emerald-400'
                  : 'border-amber-500/40 shadow-[0_0_8px_rgba(245,158,11,0.15)] group-hover:border-amber-400',
              )}
              onClick={() => onOpenDetails?.(record)}
              title="Nhấp để xem chi tiết"
            />
          ) : (
            <div
              aria-hidden="true"
              className="flex h-14 w-28 shrink-0 items-center justify-center rounded-lg border border-dashed border-border bg-surface-muted text-content-muted"
            >
              <ScanLine className="h-5 w-5" />
            </div>
          )}
        </div>

        {/* Plate Content */}
        <div className="min-w-0 flex-1 space-y-1.5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="font-mono text-base font-bold tracking-wider text-content">
                {displayPlate}
              </span>

              {record.plate_number && (
                <div className="flex flex-wrap gap-1">
                  {plateClassBadges(
                    record.is_valid_format,
                    record.plate_kind,
                    record.plate_color,
                  ).map((badge) => (
                    <Badge key={badge.label} variant={badge.tone} title={badge.title}>
                      {badge.label}
                    </Badge>
                  ))}
                  {record.is_valid_format ? (
                    <Badge variant="success" className="gap-1 text-[11px]">
                      <ShieldCheck className="h-3 w-3" /> Chuẩn TT 79
                    </Badge>
                  ) : (
                    <Badge variant="warning" className="gap-1 text-[11px]">
                      <AlertTriangle className="h-3 w-3" /> Cảnh báo
                    </Badge>
                  )}
                </div>
              )}
            </div>

            {/* Quick Actions */}
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={handleCopy}
                className="flex h-7 items-center gap-1 rounded-lg border border-border/80 bg-surface-raised px-2 text-xs font-medium text-content hover:border-primary transition-colors"
                title="Sao chép biển số"
              >
                {copied ? (
                  <Check className="h-3 w-3 text-emerald-400" />
                ) : (
                  <Copy className="h-3 w-3 text-content-muted" />
                )}
                <span className="text-[11px]">{copied ? 'Đã chép' : 'Chép'}</span>
              </button>

              {onOpenDetails && (
                <button
                  type="button"
                  onClick={() => onOpenDetails(record)}
                  className="flex h-7 items-center gap-1 rounded-lg border border-border/80 bg-surface-raised px-2 text-xs font-medium text-primary hover:border-primary transition-colors"
                  title="Xem chi tiết"
                >
                  <Eye className="h-3 w-3" />
                  <span className="text-[11px]">Chi tiết</span>
                </button>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
            <ConfidenceBar
              value={record.confidence}
              label="Độ tin cậy phát hiện"
              size="sm"
              showValue
            />
            <div className="flex items-center gap-1.5 text-[11px] text-content-muted font-mono sm:justify-end">
              {record.video_time_seconds !== null && (
                <span className="flex items-center gap-1 font-semibold text-primary">
                  <Clock className="h-3 w-3" />
                  {formatVideoTime(record.video_time_seconds)}
                </span>
              )}
              {record.plate_line_count !== null && (
                <span>· {record.plate_line_count} dòng</span>
              )}
              <span>· {formatProcessingTime(record.processing_time)}</span>
            </div>
          </div>
        </div>
      </div>
    </li>
  );
}

export function VideoResultPanel({
  job,
  plates,
  isLoading,
  error,
  onRetry,
  onOpenDetails,
}: VideoResultPanelProps): JSX.Element {
  const outputUrl = fileUrl(job.output_url);

  return (
    <Card
      title="Kết quả nhận dạng video"
      description={`Đã phát hiện ${plates.length} biển số xe khác nhau`}
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
            <Skeleton className="h-20 w-full" rounded="lg" />
            <Skeleton className="h-20 w-full" rounded="lg" />
          </div>
        )}

        {error && (
          <ErrorState
            title="Không tải được danh sách biển số"
            message={error}
            onRetry={onRetry}
            retryLabel="Thử tải lại"
          />
        )}

        {!isLoading && !error && plates.length === 0 && (
          <EmptyState
            icon={<Film className="h-6 w-6" aria-hidden="true" />}
            title="Không tìm thấy biển số nào"
            description="Tác vụ đã xử lý xong toàn bộ video nhưng không phát hiện được biển số nào. Hãy thử lại với video rõ nét hơn hoặc xe di chuyển gần camera hơn."
          />
        )}

        {!isLoading && !error && plates.length > 0 && (
          <>
            <DeduplicationNote />
            <ul className="space-y-2.5 max-h-[520px] overflow-y-auto pr-1">
              {plates.map((record) => (
                <PlateCard
                  key={record.id}
                  record={record}
                  onOpenDetails={onOpenDetails}
                />
              ))}
            </ul>
          </>
        )}
      </div>
    </Card>
  );
}

export default VideoResultPanel;
