/**
 * Detail dialog for one history record (FR-4.7).
 *
 * Shows the source image, the cropped plate and **every** stored field —
 * including the ones the table has no room for: the raw OCR text, the OCR
 * confidence, the bounding box, the line count, the format verdict and the
 * `source_job_id` that ties this plate to the other plates from the same
 * upload. Those are exactly the fields the evaluation chapter is written from,
 * so a record that cannot be inspected in full is a record that cannot be
 * cited.
 */

import { useEffect, useState } from 'react';
import { ImageOff, Trash2, Wand2 } from 'lucide-react';
import type { ReactNode } from 'react';

import { Badge, Button, ConfidenceBar, Modal, PlateChip } from '@/components/ui';
import { cn } from '@/lib/cn';
import { INPUT_TYPE_LABELS } from '@/lib/constants';
import {
  NO_VALUE,
  formatDateTime,
  formatNumber,
  formatProcessingTime,
} from '@/lib/format';
import { fileUrl } from '@/services/api';
import type { BoundingBox, DetectionHistory } from '@/types';

// ---------------------------------------------------------------------------
// Image panel
// ---------------------------------------------------------------------------

/** Props of {@link ImagePanel}. */
interface ImagePanelProps {
  title: string;
  /** Resolved URL, or `null` when nothing was stored. */
  src: string | null;
  alt: string;
  /** Draw this box over the image, in source-image pixel coordinates. */
  overlay?: BoundingBox;
  /** Explains why the image is absent, when it is. */
  missingLabel: string;
}

/**
 * One image with its heading, and optionally the detected box drawn over it.
 *
 * The overlay is positioned in **percentages** derived from the image's natural
 * size, never in pixels: the element is scaled to fit the dialog, so a box
 * placed at the stored pixel offsets would drift further from the plate the
 * more the image was shrunk. Nothing is drawn until the natural size is known.
 *
 * @param props - Heading, source, alternative text and optional overlay.
 * @returns The image panel element.
 */
function ImagePanel({
  title,
  src,
  alt,
  overlay,
  missingLabel,
}: ImagePanelProps): JSX.Element {
  const [naturalSize, setNaturalSize] = useState<{
    width: number;
    height: number;
  } | null>(null);
  const [hasFailed, setHasFailed] = useState(false);

  // A new record means a new image: without this reset, the previous image's
  // dimensions would position the overlay on the next one.
  useEffect(() => {
    setNaturalSize(null);
    setHasFailed(false);
  }, [src]);

  const canDrawOverlay =
    overlay !== undefined &&
    naturalSize !== null &&
    naturalSize.width > 0 &&
    naturalSize.height > 0;

  return (
    <figure className="space-y-2">
      <figcaption className="text-xs font-medium uppercase tracking-wide text-content-muted">
        {title}
      </figcaption>

      {src && !hasFailed ? (
        <div className="relative inline-block max-w-full overflow-hidden rounded-lg border border-border bg-surface-raised">
          <img
            src={src}
            alt={alt}
            onLoad={(event) =>
              setNaturalSize({
                width: event.currentTarget.naturalWidth,
                height: event.currentTarget.naturalHeight,
              })
            }
            onError={() => setHasFailed(true)}
            className="block max-h-64 w-auto max-w-full object-contain"
          />
          {canDrawOverlay && overlay && naturalSize && (
            <span
              aria-hidden="true"
              style={{
                left: `${(overlay.x / naturalSize.width) * 100}%`,
                top: `${(overlay.y / naturalSize.height) * 100}%`,
                width: `${(overlay.width / naturalSize.width) * 100}%`,
                height: `${(overlay.height / naturalSize.height) * 100}%`,
              }}
              className="absolute rounded-sm border-2 border-primary shadow-[0_0_0_9999px_rgba(15,23,42,0.25)]"
            />
          )}
        </div>
      ) : (
        <div
          className={cn(
            'flex h-32 w-full flex-col items-center justify-center gap-2 rounded-lg',
            'border border-dashed border-border bg-surface-raised text-content-muted',
          )}
        >
          <ImageOff className="h-5 w-5" aria-hidden="true" />
          <p className="text-xs">{missingLabel}</p>
        </div>
      )}
    </figure>
  );
}

// ---------------------------------------------------------------------------
// Metadata
// ---------------------------------------------------------------------------

/** Props of {@link Field}. */
interface FieldProps {
  label: string;
  children: ReactNode;
  /** Let the value span the full width, for long identifiers. */
  wide?: boolean;
}

/**
 * One labelled metadata value.
 *
 * @param props - Label, value and width.
 * @returns A definition-list pair.
 */
function Field({ label, children, wide = false }: FieldProps): JSX.Element {
  return (
    <div className={cn(wide && 'sm:col-span-2')}>
      <dt className="text-xs text-content-muted">{label}</dt>
      <dd className="mt-0.5 text-sm text-content">{children}</dd>
    </div>
  );
}

// ---------------------------------------------------------------------------
// OCR comparison
// ---------------------------------------------------------------------------

/**
 * Reduce a plate string to the characters worth comparing.
 *
 * Separators are dropped because normalisation inserts them: `"3OD04430"`
 * becoming `"30D-04430"` differs by one character, not by two, and counting the
 * hyphen as a difference would overstate what post-processing changed.
 *
 * @param value - Plate text.
 * @returns Upper-case alphanumerics only.
 */
function normalizeForDiff(value: string): string {
  return value.replace(/[^0-9A-Za-z]/g, '').toUpperCase();
}

/** Props of {@link OcrComparison}. */
interface OcrComparisonProps {
  rawText: string;
  plateNumber: string;
}

/**
 * Highlight what post-processing changed between the raw read and the final
 * plate.
 *
 * When the two normalise to the same length the differing positions are marked
 * character by character — the `O` → `0` and `I` → `1` substitutions are the
 * whole point of the correction step, and they are invisible in two strings
 * printed side by side. When the lengths differ, no alignment can be assumed,
 * so both values are shown plainly rather than with a guessed mapping.
 *
 * @param props - The raw OCR text and the corrected plate number.
 * @returns The comparison block.
 */
function OcrComparison({
  rawText,
  plateNumber,
}: OcrComparisonProps): JSX.Element {
  const rawChars = Array.from(normalizeForDiff(rawText));
  const finalChars = Array.from(normalizeForDiff(plateNumber));
  const isAligned =
    rawChars.length > 0 && rawChars.length === finalChars.length;

  return (
    <div className="rounded-lg border border-warning/40 bg-warning/10 p-4">
      <p className="flex items-center gap-2 text-sm font-medium text-warning">
        <Wand2 className="h-4 w-4 shrink-0" aria-hidden="true" />
        Kết quả OCR đã được hậu xử lý
      </p>
      <p className="mt-1 text-xs text-content-muted">
        Chuỗi OCR thô khác với biển số cuối cùng. Đây là phần giá trị mà bước
        chuẩn hoá theo định dạng biển số Việt Nam đã sửa được.
      </p>

      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <div>
          <p className="text-xs text-content-muted">OCR thô</p>
          <p className="mt-1 font-mono text-base font-semibold tracking-wider text-content">
            {isAligned
              ? rawChars.map((character, index) => (
                  <span
                    key={`raw-${index}`}
                    className={cn(
                      character !== finalChars[index] &&
                        'rounded bg-danger/20 px-0.5 text-danger',
                    )}
                  >
                    {character}
                  </span>
                ))
              : rawText}
          </p>
        </div>

        <div>
          <p className="text-xs text-content-muted">Sau chuẩn hoá</p>
          <p className="mt-1 font-mono text-base font-semibold tracking-wider text-content">
            {isAligned
              ? finalChars.map((character, index) => (
                  <span
                    key={`final-${index}`}
                    className={cn(
                      character !== rawChars[index] &&
                        'rounded bg-success/20 px-0.5 text-success',
                    )}
                  >
                    {character}
                  </span>
                ))
              : plateNumber}
          </p>
        </div>
      </div>

      {isAligned && (
        <p className="mt-2 text-xs text-content-muted">
          Các ký tự được tô màu là những vị trí đã thay đổi.
        </p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Dialog
// ---------------------------------------------------------------------------

/** Props of {@link HistoryDetailModal}. */
export interface HistoryDetailModalProps {
  /** The record to show, or `null` when the dialog is closed. */
  record: DetectionHistory | null;
  onClose: () => void;
  /** Ask to delete the record; confirmation is handled by the page. */
  onDelete: (record: DetectionHistory) => void;
}

/**
 * Render the detail dialog.
 *
 * @param props - The record and the close and delete handlers.
 * @returns The dialog, or `null` when no record is selected.
 */
export function HistoryDetailModal({
  record,
  onClose,
  onDelete,
}: HistoryDetailModalProps): JSX.Element | null {
  if (!record) {
    return null;
  }

  const sourceUrl = fileUrl(record.image_path);
  const plateUrl = fileUrl(record.plate_image_path);
  const wasCorrected =
    record.raw_ocr_text !== null &&
    record.plate_number !== null &&
    record.raw_ocr_text !== record.plate_number;

  return (
    <Modal
      isOpen
      onClose={onClose}
      size="xl"
      title="Chi tiết bản ghi nhận dạng"
      description={`Mã bản ghi #${record.id}`}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Đóng
          </Button>
          <Button
            variant="danger"
            onClick={() => onDelete(record)}
            leftIcon={<Trash2 className="h-4 w-4" />}
          >
            Xoá bản ghi
          </Button>
        </>
      }
    >
      <div className="space-y-5">
        <div className="flex flex-wrap items-center gap-3">
          <PlateChip
            plateNumber={record.plate_number}
            isValidFormat={record.is_valid_format}
            size="lg"
          />
          <Badge variant={record.is_valid_format ? 'success' : 'warning'}>
            {record.is_valid_format
              ? 'Đúng định dạng Việt Nam'
              : 'Không khớp định dạng Việt Nam'}
          </Badge>
          <Badge variant="info">
            {INPUT_TYPE_LABELS[record.input_type]}
          </Badge>
        </div>

        {wasCorrected && record.raw_ocr_text && record.plate_number && (
          <OcrComparison
            rawText={record.raw_ocr_text}
            plateNumber={record.plate_number}
          />
        )}

        <div className="grid gap-4 sm:grid-cols-2">
          <ImagePanel
            title="Ảnh gốc"
            src={sourceUrl}
            alt={`Ảnh gốc của bản ghi ${record.id}`}
            overlay={record.bbox}
            // Webcam frames are processed but deliberately never persisted, so
            // a missing source image here is normal rather than a failure.
            missingLabel={
              record.input_type === 'webcam'
                ? 'Khung hình webcam không được lưu lại'
                : 'Không có ảnh gốc'
            }
          />
          <ImagePanel
            title="Ảnh biển số đã cắt"
            src={plateUrl}
            alt={`Ảnh biển số đã cắt của bản ghi ${record.id}`}
            missingLabel="Không có ảnh biển số đã cắt"
          />
        </div>

        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-content">Độ tin cậy</h3>
          <ConfidenceBar
            value={record.confidence}
            label="Phát hiện (YOLO)"
            className="max-w-md"
          />
          <ConfidenceBar
            value={record.ocr_confidence}
            label="Đọc ký tự (OCR)"
            className="max-w-md"
          />
        </div>

        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-content">
            Thông tin chi tiết
          </h3>
          <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
            <Field label="Biển số sau chuẩn hoá">
              <span className="font-mono">
                {record.plate_number ?? NO_VALUE}
              </span>
            </Field>
            <Field label="Chuỗi OCR thô">
              <span className="font-mono">
                {record.raw_ocr_text ?? NO_VALUE}
              </span>
            </Field>
            <Field label="Số dòng của biển số">
              {record.plate_line_count !== null
                ? `${record.plate_line_count} dòng`
                : NO_VALUE}
            </Field>
            <Field label="Thời gian xử lý">
              {formatProcessingTime(record.processing_time)}
            </Field>
            <Field label="Thời điểm nhận dạng">
              {formatDateTime(record.detected_time)}
            </Field>
            <Field label="Thời điểm lưu">
              {formatDateTime(record.created_at)}
            </Field>
            <Field label="Vùng chứa biển số (pixel)" wide>
              <span className="font-mono">
                x = {formatNumber(record.bbox_x)}, y ={' '}
                {formatNumber(record.bbox_y)}, rộng ={' '}
                {formatNumber(record.bbox_w)}, cao ={' '}
                {formatNumber(record.bbox_h)}
              </span>
            </Field>
            <Field label="Mã lần tải lên (source_job_id)" wide>
              {/* Every plate from the same image shares this id — it is what
                  distinguishes "3 biển số" from "3 lượt tải lên". */}
              <span className="break-all font-mono text-xs">
                {record.source_job_id}
              </span>
            </Field>
          </dl>
        </div>
      </div>
    </Modal>
  );
}

export default HistoryDetailModal;
