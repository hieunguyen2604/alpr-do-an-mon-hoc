/** Plate result card displaying plate crop, OCR text, and confidence scores (TT 79/2024). */

import { useState } from 'react';
import {
  AlertTriangle,
  Check,
  Copy,
  Download,
  Eye,
  ImageOff,
  ShieldCheck,
  Zap,
} from 'lucide-react';

import { Badge, Button, ConfidenceBar } from '@/components/ui';
import { cn } from '@/lib/cn';
import { formatProcessingTime } from '@/lib/format';
import { plateClassBadges } from '@/lib/plateClass';
import type { DetectionResult } from '@/types';

export interface PlateResultCardProps {
  result: DetectionResult;
  index: number;
  plateImageUrl: string | null;
  isActive?: boolean;
  onActiveChange?: (index: number | null) => void;
  onDownloadCrop?: (result: DetectionResult, index: number) => void;
  isDownloadingCrop?: boolean;
  onOpenDetails?: (result: DetectionResult, index: number) => void;
}

export function PlateResultCard({
  result,
  index,
  plateImageUrl,
  isActive = false,
  onActiveChange,
  onDownloadCrop,
  isDownloadingCrop = false,
  onOpenDetails,
}: PlateResultCardProps): JSX.Element {
  const [copied, setCopied] = useState(false);
  const hasPlateText = Boolean(result.plate_number || result.plate_display);
  const displayPlate = result.plate_display ?? result.plate_number ?? 'Không đọc được';

  const handleCopy = async () => {
    if (hasPlateText) {
      await navigator.clipboard.writeText(displayPlate);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <article
      className={cn(
        'group relative overflow-hidden rounded-2xl border p-5 transition-all duration-300 shadow-md',
        isActive
          ? 'border-primary ring-2 ring-primary/30 bg-surface-raised/90 shadow-primary/10'
          : 'border-border/80 bg-surface hover:border-primary/50 hover:shadow-lg',
      )}
      onMouseEnter={() => onActiveChange?.(index)}
      onMouseLeave={() => onActiveChange?.(null)}
    >
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <div className="relative shrink-0">
          {plateImageUrl ? (
            <div
              className={cn(
                'relative overflow-hidden rounded-xl border bg-surface-raised p-1 transition-all',
                result.is_valid_format
                  ? 'border-emerald-500/50 shadow-[0_0_12px_rgba(16,185,129,0.2)] group-hover:border-emerald-400'
                  : 'border-amber-500/50 shadow-[0_0_12px_rgba(245,158,11,0.2)] group-hover:border-amber-400',
              )}
            >
              <img
                src={plateImageUrl}
                alt={`Biển số ${displayPlate}`}
                className="h-20 w-36 rounded-lg object-contain cursor-pointer transition-transform duration-300 hover:scale-105"
                onClick={() => onOpenDetails?.(result, index)}
                title="Nhấp để xem chi tiết"
              />
              <span className="absolute bottom-1 right-1 rounded bg-black/70 px-1.5 py-0.5 text-[10px] font-bold text-white backdrop-blur-sm">
                #{index + 1}
              </span>
            </div>
          ) : (
            <div className="flex h-20 w-36 flex-col items-center justify-center gap-1 rounded-xl border border-dashed border-border bg-surface-muted text-content-muted">
              <ImageOff className="h-5 w-5 opacity-60" aria-hidden="true" />
              <span className="text-[11px]">Không có ảnh cắt</span>
            </div>
          )}
        </div>

        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2.5">
              <h3 className="font-mono text-2xl font-black tracking-widest text-content drop-shadow-sm">
                {displayPlate}
              </h3>
              {hasPlateText && (
                <button
                  type="button"
                  onClick={handleCopy}
                  className="flex h-7 items-center gap-1 rounded-lg border border-border/80 bg-surface-raised px-2 text-xs font-medium text-content hover:border-primary transition-colors"
                  title="Sao chép biển số"
                >
                  {copied ? (
                    <>
                      <Check className="h-3.5 w-3.5 text-emerald-400" />
                      <span className="text-emerald-400 font-semibold">Đã sao chép</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3.5 w-3.5 text-content-muted" />
                      <span>Sao chép</span>
                    </>
                  )}
                </button>
              )}
            </div>

            {result.is_valid_format ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
                <ShieldCheck className="h-3.5 w-3.5" /> Chuẩn TT 79/2024
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-400 border border-amber-500/20">
                <AlertTriangle className="h-3.5 w-3.5" /> Cảnh báo định dạng
              </span>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-1.5">
            {hasPlateText ? (
              plateClassBadges(
                result.is_valid_format,
                result.plate_kind,
                result.plate_color,
              ).map((badge) => (
                <Badge key={badge.label} variant={badge.tone} title={badge.title}>
                  {badge.label}
                </Badge>
              ))
            ) : (
              <Badge variant="neutral">Không đọc được ký tự</Badge>
            )}
            {result.plate_line_count !== null && (
              <Badge variant="neutral">
                {result.plate_line_count} dòng
              </Badge>
            )}
          </div>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3 rounded-xl border border-border/60 bg-surface-raised/40 p-3">
        <div className="min-w-0">
          <dt className="text-[11px] font-medium text-content-muted">Phát hiện (YOLO11)</dt>
          <dd className="mt-1">
            <ConfidenceBar value={result.detection_confidence} size="sm" />
          </dd>
        </div>
        <div className="min-w-0">
          <dt className="text-[11px] font-medium text-content-muted">Nhận dạng (OCR)</dt>
          <dd className="mt-1">
            <ConfidenceBar value={result.ocr_confidence} size="sm" />
          </dd>
        </div>
        <div className="min-w-0 flex flex-col justify-center">
          <dt className="text-[11px] font-medium text-content-muted flex items-center gap-1">
            <Zap className="h-3 w-3 text-amber-400" />
            Độ trễ xử lý (CPU)
          </dt>
          <dd className="mt-1 font-mono text-xs font-bold text-content">
            {formatProcessingTime(result.processing_time)}
          </dd>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between pt-1">
        {onOpenDetails ? (
          <Button
            variant="ghost"
            size="sm"
            className="text-xs text-primary hover:text-primary-hover font-semibold"
            leftIcon={<Eye className="h-3.5 w-3.5" />}
            onClick={() => onOpenDetails(result, index)}
          >
            Xem chi tiết toàn cảnh
          </Button>
        ) : (
          <div />
        )}

        {onDownloadCrop && plateImageUrl && (
          <Button
            variant="secondary"
            size="sm"
            isLoading={isDownloadingCrop}
            loadingText="Đang tải…"
            leftIcon={<Download className="h-3.5 w-3.5" />}
            onClick={() => onDownloadCrop(result, index)}
          >
            Tải ảnh cắt
          </Button>
        )}
      </div>
    </article>
  );
}

export default PlateResultCard;
