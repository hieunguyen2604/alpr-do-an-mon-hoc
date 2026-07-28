/**
 * Everything read from one detected plate (FR-1.2).
 *
 * The card deliberately shows the two confidence scores separately. `confidence`
 * scores the detector — did we find a plate? — and `ocr_confidence` scores the
 * read — did we get the characters right? A single merged number would hide
 * which stage was uncertain, which is exactly the distinction the evaluation
 * chapter is built on.
 *
 * A plate whose text matched no known Vietnamese format is flagged but still
 * shown in full. Hiding it would remove the very cases worth inspecting, and
 * would leave the user staring at a picture with a box on it and no explanation.
 */

import { Download, ImageOff } from 'lucide-react';

import { Badge, Button, ConfidenceBar } from '@/components/ui';
import { cn } from '@/lib/cn';
import { formatProcessingTime } from '@/lib/format';

import { plateClassBadges } from '@/lib/plateClass';
import type { DetectionResult } from '@/types';

/** Props of {@link PlateResultCard}. */
export interface PlateResultCardProps {
  /** The plate to describe. */
  result: DetectionResult;
  /** Zero-based position, shown as a number matching the box in the preview. */
  index: number;
  /** URL of the cropped plate image, already resolved. `null` when not stored. */
  plateImageUrl: string | null;
  /** Whether this card's box is currently highlighted in the preview. */
  isActive?: boolean;
  /** Called on hover so the matching box can be highlighted. */
  onActiveChange?: (index: number | null) => void;
  /** Called when the user asks to save the cropped plate image. */
  onDownloadCrop?: (result: DetectionResult, index: number) => void;
  /** Whether this card's crop download is in flight. */
  isDownloadingCrop?: boolean;
}

/**
 * Render one plate result.
 *
 * @param props - The plate, its position and the download handler.
 * @returns The result card.
 */
export function PlateResultCard({
  result,
  index,
  plateImageUrl,
  isActive = false,
  onActiveChange,
  onDownloadCrop,
  isDownloadingCrop = false,
}: PlateResultCardProps): JSX.Element {
  const hasPlateText = Boolean(result.plate_number);

  return (
    <article
      className={cn(
        'rounded-lg border p-4 transition-colors',
        isActive ? 'border-warning bg-warning/5' : 'border-border bg-surface',
      )}
      onMouseEnter={() => onActiveChange?.(index)}
      onMouseLeave={() => onActiveChange?.(null)}
    >
      <div className="flex flex-wrap items-start gap-4">
        {/* Cropped plate, so the user can check the read against the pixels it
            came from without hunting for the box in the full image. */}
        <div className="shrink-0">
          {plateImageUrl ? (
            <img
              src={plateImageUrl}
              alt={`Ảnh biển số ${result.plate_number ?? index + 1} đã cắt`}
              className={cn(
                'h-16 w-32 rounded-md border border-border bg-surface-raised',
                'object-contain',
              )}
            />
          ) : (
            <div
              className={cn(
                'flex h-16 w-32 flex-col items-center justify-center gap-1',
                'rounded-md border border-dashed border-border bg-surface-muted',
                'text-content-muted',
              )}
            >
              <ImageOff className="h-4 w-4" aria-hidden="true" />
              <span className="text-[11px]">Không có ảnh cắt</span>
            </div>
          )}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={cn(
                'flex h-6 w-6 shrink-0 items-center justify-center rounded-full',
                'bg-surface-raised text-xs font-semibold text-content-muted',
              )}
              aria-hidden="true"
            >
              {index + 1}
            </span>

            <span
              className={cn(
                'plate-text text-lg',
                hasPlateText ? 'text-content' : 'text-content-muted',
              )}
            >
              {result.plate_display ?? result.plate_number ?? 'Không đọc được'}
            </span>

            {/* Wording, not colour alone, carries the meaning (NFR-U5).
                The badges describe what the plate *is* before judging whether
                its string parsed: an army plate fails civil validation by
                design, and labelling that "wrong format" contradicts a reading
                the system got right. */}
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

          {/*
            Hai cột, không phải ba. Thẻ này sống trong cột kết quả — chỉ một
            nửa bề ngang trang — nhưng breakpoint của Tailwind đo theo khung
            nhìn, nên `sm:grid-cols-3` bật ba cột từ rất sớm và mỗi ô chỉ còn
            khoảng 150 px. Thanh độ tin cậy có bề rộng tối thiểu và nhãn phần
            trăm không co, nên phần thừa tràn sang ô bên cạnh: ảnh chụp giao
            diện 28/07 cho thấy "95,3%" đè lên "412 ms".

            `min-w-0` là nửa còn lại của bản sửa: ô lưới mặc định lấy
            `min-width: auto`, tức KHÔNG hẹp lại được dưới bề rộng nội dung —
            thiếu nó thì dù chia bao nhiêu cột, nội dung vẫn tràn thay vì
            xuống dòng.
          */}
          <dl className="mt-3 grid grid-cols-1 gap-x-5 gap-y-3 sm:grid-cols-2">
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
              <dt className="text-xs text-content-muted">Thời gian xử lý</dt>
              <dd className="mt-1 text-sm font-medium tabular-nums text-content">
                {formatProcessingTime(result.processing_time)}
              </dd>
            </div>
          </dl>

        </div>
      </div>

      {/*
        The raw-vs-corrected banner that used to sit here was removed on
        24/07/2026 (user request): the raw OCR string remains available in the
        API response and the history detail, but on the result card it was
        noise once a plate read correctly. What post-processing contributes is
        demonstrated by measurement in the thesis, not by the UI.
      */}
      {onDownloadCrop && plateImageUrl && (
        <div className="mt-3 flex justify-end">
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
        </div>
      )}
    </article>
  );
}

export default PlateResultCard;
