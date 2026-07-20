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

import { Download, ImageOff, Wand2 } from 'lucide-react';

import { Badge, Button, ConfidenceBar } from '@/components/ui';
import { cn } from '@/lib/cn';
import { NO_VALUE, formatProcessingTime } from '@/lib/format';
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
 * Whether post-processing actually changed the OCR output.
 *
 * Compared with whitespace and case normalised away, because a difference of
 * only spacing is a formatting detail rather than a correction, and presenting
 * it as one would overstate what the post-processing step achieved.
 *
 * @param raw - Unmodified OCR output.
 * @param corrected - Normalised plate string.
 * @returns `true` when the two differ meaningfully.
 */
function wasCorrected(
  raw: string | null,
  corrected: string | null,
): raw is string {
  if (!raw) {
    return false;
  }
  const normalize = (value: string): string =>
    value.replace(/[\s-]+/g, '').toUpperCase();
  return normalize(raw) !== normalize(corrected ?? '');
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
  const showRawComparison = wasCorrected(result.raw_ocr_text, result.plate_number);
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

          <dl className="mt-3 grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2">
            <div>
              <dt className="text-xs text-content-muted">Độ tin cậy phát hiện</dt>
              <dd className="mt-1">
                <ConfidenceBar value={result.detection_confidence} size="sm" />
              </dd>
            </div>
            <div>
              <dt className="text-xs text-content-muted">Độ tin cậy OCR</dt>
              <dd className="mt-1">
                <ConfidenceBar value={result.ocr_confidence} size="sm" />
              </dd>
            </div>
            <div>
              <dt className="text-xs text-content-muted">Số dòng của biển</dt>
              <dd className="mt-1 text-sm font-medium text-content">
                {result.plate_line_count !== null
                  ? `${result.plate_line_count} dòng`
                  : NO_VALUE}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-content-muted">Thời gian xử lý</dt>
              <dd className="mt-1 text-sm font-medium tabular-nums text-content">
                {formatProcessingTime(result.processing_time)}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      {/*
        Shown only when post-processing changed something. Putting the raw string
        next to the corrected one is the clearest demonstration that the
        correction step does real work — with the two identical there is nothing
        to show, and the notice would be noise on every card.
      */}
      {showRawComparison && (
        <div
          className={cn(
            'mt-3 flex flex-wrap items-center gap-x-2 gap-y-1 rounded-md',
            'border border-primary/20 bg-primary/5 px-3 py-2 text-xs',
          )}
        >
          <Wand2
            className="h-3.5 w-3.5 shrink-0 text-primary"
            aria-hidden="true"
          />
          <span className="text-content-muted">Hậu xử lý đã sửa:</span>
          <span className="plate-text text-content-muted line-through">
            {result.raw_ocr_text}
          </span>
          <span aria-hidden="true" className="text-content-muted">
            →
          </span>
          <span className="plate-text text-content">{result.plate_number}</span>
        </div>
      )}

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
