/**
 * Enhanced Plate Result Card with modern aesthetics, copy-to-clipboard,
 * glowing valid/invalid indicators, and detail modal trigger.
 */

import { useState } from 'react';
import { Check, Copy, Download, Eye, ImageOff } from 'lucide-react';

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
        'group rounded-xl border p-4 transition-all duration-200 shadow-sm',
        isActive
          ? 'border-primary ring-2 ring-primary/20 bg-surface-raised'
          : 'border-border/80 bg-surface hover:border-border hover:shadow-md',
      )}
      onMouseEnter={() => onActiveChange?.(index)}
      onMouseLeave={() => onActiveChange?.(null)}
    >
      <div className="flex flex-wrap items-start gap-4">
        {/* Cropped Plate Image */}
        <div className="shrink-0">
          {plateImageUrl ? (
            <img
              src={plateImageUrl}
              alt={`Ảnh biển số ${displayPlate} đã cắt`}
              className={cn(
                'h-16 w-32 rounded-lg border object-contain bg-surface-raised p-0.5 transition-all cursor-pointer',
                result.is_valid_format
                  ? 'border-emerald-500/40 shadow-[0_0_8px_rgba(16,185,129,0.15)] group-hover:border-emerald-500'
                  : 'border-amber-500/40 shadow-[0_0_8px_rgba(245,158,11,0.15)] group-hover:border-amber-500',
              )}
              onClick={() => onOpenDetails?.(result, index)}
              title="Nhấp để xem chi tiết"
            />
          ) : (
            <div
              className={cn(
                'flex h-16 w-32 flex-col items-center justify-center gap-1',
                'rounded-lg border border-dashed border-border bg-surface-muted text-content-muted',
              )}
            >
              <ImageOff className="h-4 w-4" aria-hidden="true" />
              <span className="text-[11px]">Không có ảnh cắt</span>
            </div>
          )}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={cn(
                  'flex h-6 w-6 shrink-0 items-center justify-center rounded-full',
                  'bg-surface-raised border border-border text-xs font-bold text-content-muted',
                )}
              >
                #{index + 1}
              </span>

              <span className="font-mono text-lg font-bold tracking-wider text-content">
                {displayPlate}
              </span>

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
            </div>

            {/* Action Buttons: Copy */}
            <div className="flex items-center gap-1.5">
              {hasPlateText && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCopy}
                  className="h-7 px-2 text-xs"
                  title="Sao chép biển số"
                  leftIcon={
                    copied ? (
                      <Check className="h-3.5 w-3.5 text-emerald-500" />
                    ) : (
                      <Copy className="h-3.5 w-3.5 text-content-muted" />
                    )
                  }
                >
                  {copied ? 'Đã chép' : 'Sao chép'}
                </Button>
              )}
            </div>
          </div>

          <dl className="mt-3 grid grid-cols-1 gap-x-4 gap-y-2.5 sm:grid-cols-3">
            <div className="min-w-0">
              <dt className="text-xs text-content-muted">Độ tin cậy phát hiện</dt>
              <dd className="mt-1">
                <ConfidenceBar value={result.detection_confidence} size="sm" />
              </dd>
            </div>
            <div className="min-w-0">
              <dt className="text-xs text-content-muted">Độ tin cậy OCR</dt>
              <dd className="mt-1">
                <ConfidenceBar value={result.ocr_confidence} size="sm" />
              </dd>
            </div>
            <div className="min-w-0">
              <dt className="text-xs text-content-muted">Độ trễ xử lý (CPU)</dt>
              <dd className="mt-1 font-mono text-xs font-semibold text-content">
                {formatProcessingTime(result.processing_time)}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between border-t border-border/40 pt-2.5">
        {onOpenDetails ? (
          <Button
            variant="ghost"
            size="sm"
            className="text-xs text-primary hover:text-primary-hover"
            leftIcon={<Eye className="h-3.5 w-3.5" />}
            onClick={() => onOpenDetails(result, index)}
          >
            Xem chi tiết
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
            Tải ảnh biển số
          </Button>
        )}
      </div>
    </article>
  );
}

export default PlateResultCard;
