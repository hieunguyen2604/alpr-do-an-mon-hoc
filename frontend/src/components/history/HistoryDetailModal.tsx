/**
 * Upgraded Modern Detection Details Dialog (Deep Navy / Cyber Theme).
 *
 * Implements a balanced two-column layout:
 * - Left column: Full vehicle scene image with scaled bounding box overlay and zoom.
 * - Right column: Structured metadata hierarchy (Confidence, Timing, Plate Showcase, Specs, OCR Diff).
 */

import { useEffect, useState } from 'react';
import {
  AlertTriangle,
  Check,
  Clock,
  Copy,
  Cpu,
  Download,
  ImageOff,
  ShieldCheck,
  Trash2,
  Wand2,
} from 'lucide-react';

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
import { plateClassBadges } from '@/lib/plateClass';
import type { BoundingBox, DetectionHistory } from '@/types';

// ---------------------------------------------------------------------------
// Image panel (Visual Showcase)
// ---------------------------------------------------------------------------

interface ImagePanelProps {
  title: string;
  src: string | null;
  alt: string;
  overlay?: BoundingBox;
  missingLabel: string;
  badgeText?: string;
  isValid?: boolean;
}

function ImagePanel({
  title,
  src,
  alt,
  overlay,
  missingLabel,
  badgeText,
  isValid = true,
}: ImagePanelProps): JSX.Element {
  const [naturalSize, setNaturalSize] = useState<{
    width: number;
    height: number;
  } | null>(null);
  const [hasFailed, setHasFailed] = useState(false);

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
    <div className="relative flex flex-col space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-content-muted">
          {title}
        </span>
        {badgeText && (
          <span className="rounded bg-surface-muted px-2 py-0.5 text-[11px] font-medium text-content-muted">
            {badgeText}
          </span>
        )}
      </div>

      {src && !hasFailed ? (
        <div className="group relative overflow-hidden rounded-xl border border-border/80 bg-surface-raised shadow-inner">
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
            className="block max-h-[340px] w-full object-contain transition-transform duration-300 group-hover:scale-[1.02]"
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
              className={cn(
                'absolute rounded-md border-2 transition-all duration-300',
                isValid
                  ? 'border-emerald-400 shadow-[0_0_12px_rgba(52,211,153,0.6)]'
                  : 'border-amber-400 shadow-[0_0_12px_rgba(251,191,36,0.6)]',
              )}
            />
          )}
        </div>
      ) : (
        <div
          className={cn(
            'flex h-48 w-full flex-col items-center justify-center gap-2 rounded-xl',
            'border border-dashed border-border bg-surface-raised/50 text-content-muted',
          )}
        >
          <ImageOff className="h-6 w-6 opacity-60" aria-hidden="true" />
          <p className="text-xs font-medium">{missingLabel}</p>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// OCR comparison
// ---------------------------------------------------------------------------

function normalizeForDiff(value: string): string {
  return value.replace(/[^0-9A-Za-z]/g, '').toUpperCase();
}

interface OcrComparisonProps {
  rawText: string;
  plateNumber: string;
}

function OcrComparison({
  rawText,
  plateNumber,
}: OcrComparisonProps): JSX.Element {
  const rawChars = Array.from(normalizeForDiff(rawText));
  const finalChars = Array.from(normalizeForDiff(plateNumber));
  const isAligned =
    rawChars.length > 0 && rawChars.length === finalChars.length;

  return (
    <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3.5">
      <p className="flex items-center gap-1.5 text-xs font-semibold text-amber-500">
        <Wand2 className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
        Đã qua chuẩn hóa quy chuẩn Việt Nam
      </p>
      <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
        <div className="rounded-lg bg-surface-raised/80 p-2">
          <span className="text-[10px] uppercase text-content-muted">OCR thô:</span>
          <p className="mt-0.5 font-mono text-sm font-bold tracking-wider text-content">
            {isAligned
              ? rawChars.map((char, index) => (
                  <span
                    key={`raw-${index}`}
                    className={cn(
                      char !== finalChars[index] &&
                        'rounded bg-danger/20 px-0.5 text-danger font-black',
                    )}
                  >
                    {char}
                  </span>
                ))
              : rawText}
          </p>
        </div>
        <div className="rounded-lg bg-surface-raised/80 p-2">
          <span className="text-[10px] uppercase text-content-muted">Chuẩn hóa:</span>
          <p className="mt-0.5 font-mono text-sm font-bold tracking-wider text-content">
            {isAligned
              ? finalChars.map((char, index) => (
                  <span
                    key={`final-${index}`}
                    className={cn(
                      char !== rawChars[index] &&
                        'rounded bg-emerald-500/20 px-0.5 text-emerald-500 font-black',
                    )}
                  >
                    {char}
                  </span>
                ))
              : plateNumber}
          </p>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Dialog Component
// ---------------------------------------------------------------------------

export interface HistoryDetailModalProps {
  record: DetectionHistory | null;
  onClose: () => void;
  onDelete: (record: DetectionHistory) => void;
}

export function HistoryDetailModal({
  record,
  onClose,
  onDelete,
}: HistoryDetailModalProps): JSX.Element | null {
  const [copied, setCopied] = useState(false);

  if (!record) {
    return null;
  }

  const sourceUrl = fileUrl(record.image_path);
  const plateUrl = fileUrl(record.plate_image_path);
  const displayPlate = record.plate_display ?? record.plate_number ?? NO_VALUE;
  const wasCorrected =
    record.raw_ocr_text !== null &&
    record.plate_number !== null &&
    record.raw_ocr_text !== record.plate_number;

  const handleCopy = async () => {
    if (record.plate_number || record.plate_display) {
      const textToCopy = record.plate_display ?? record.plate_number ?? '';
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownloadCrop = () => {
    if (plateUrl) {
      const link = document.createElement('a');
      link.href = plateUrl;
      link.download = `crop-${record.plate_number || record.id}.jpg`;
      link.click();
    }
  };

  return (
    <Modal
      isOpen
      onClose={onClose}
      size="xl"
      title="Chi tiết nhận dạng"
      description={`Mã bản ghi #${record.id} · ${formatDateTime(record.detected_time)}`}
      footer={
        <div className="flex w-full items-center justify-between">
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={handleCopy}
              leftIcon={copied ? <Check className="h-4 w-4 text-emerald-500" /> : <Copy className="h-4 w-4" />}
            >
              {copied ? 'Đã sao chép' : 'Sao chép biển số'}
            </Button>
            {plateUrl && (
              <Button
                variant="secondary"
                size="sm"
                onClick={handleDownloadCrop}
                leftIcon={<Download className="h-4 w-4" />}
              >
                Tải ảnh cắt
              </Button>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" onClick={onClose}>
              Đóng
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={() => onDelete(record)}
              leftIcon={<Trash2 className="h-4 w-4" />}
            >
              Xoá bản ghi
            </Button>
          </div>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Main 2-Column Split */}
        <div className="grid gap-6 lg:grid-cols-12">
          {/* Left Column: Full Scene Showcase (5/12 cols) */}
          <div className="space-y-4 lg:col-span-5">
            <ImagePanel
              title="Ảnh toàn cảnh"
              src={sourceUrl}
              alt={`Ảnh gốc của bản ghi ${record.id}`}
              overlay={record.bbox}
              isValid={record.is_valid_format}
              badgeText={INPUT_TYPE_LABELS[record.input_type]}
              missingLabel={
                record.input_type === 'webcam'
                  ? 'Khung hình webcam không lưu lại'
                  : 'Không có ảnh gốc'
              }
            />

            {/* Quick Summary Info Card under Image */}
            <div className="rounded-xl border border-border/60 bg-surface-raised/40 p-3 text-xs space-y-2">
              <div className="flex items-center justify-between text-content-muted">
                <span className="flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5 text-primary" />
                  Thời điểm ghi nhận:
                </span>
                <span className="font-mono font-medium text-content">
                  {formatDateTime(record.detected_time)}
                </span>
              </div>
              <div className="flex items-center justify-between text-content-muted">
                <span className="flex items-center gap-1.5">
                  <Cpu className="h-3.5 w-3.5 text-primary" />
                  Độ trễ xử lý (CPU):
                </span>
                <span className="font-mono font-medium text-content">
                  {formatProcessingTime(record.processing_time)}
                </span>
              </div>
            </div>
          </div>

          {/* Right Column: Structured Metrics & License Plate Specs (7/12 cols) */}
          <div className="space-y-5 lg:col-span-7">
            {/* Top Row: Plate Feature Badges & Chips */}
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border/80 bg-surface-raised/50 p-4">
              <div className="flex items-center gap-3">
                <PlateChip
                  plateNumber={record.plate_display ?? record.plate_number}
                  isValidFormat={record.is_valid_format}
                  size="lg"
                />
                <div>
                  <h3 className="font-mono text-xl font-bold tracking-wider text-content">
                    {displayPlate}
                  </h3>
                  <div className="mt-1 flex flex-wrap gap-1.5">
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
                      <Badge variant="success" className="gap-1">
                        <ShieldCheck className="h-3 w-3" /> Chuẩn TT 79/2024
                      </Badge>
                    ) : (
                      <Badge variant="warning" className="gap-1">
                        <AlertTriangle className="h-3 w-3" /> Cảnh báo định dạng
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Middle Row: Crop Thumbnail & Properties */}
            <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
              {/* Plate Crop Box */}
              <div className="sm:col-span-5 flex flex-col items-center justify-center rounded-xl border border-border bg-surface-raised p-2">
                <span className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-content-muted">
                  Ảnh cắt biển số
                </span>
                {plateUrl ? (
                  <img
                    src={plateUrl}
                    alt={`Biển số ${displayPlate}`}
                    className={cn(
                      'h-20 w-full rounded-lg object-contain border',
                      record.is_valid_format
                        ? 'border-emerald-500/50 shadow-[0_0_10px_rgba(16,185,129,0.2)]'
                        : 'border-amber-500/50 shadow-[0_0_10px_rgba(245,158,11,0.2)]',
                    )}
                  />
                ) : (
                  <div className="flex h-20 w-full items-center justify-center rounded-lg border border-dashed border-border bg-surface-muted text-content-muted text-[11px]">
                    Không có ảnh cắt
                  </div>
                )}
              </div>

              {/* Confidence Metrics */}
              <div className="sm:col-span-7 space-y-2.5 rounded-xl border border-border/80 bg-surface-raised/40 p-3.5">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-content-muted">
                  Độ tin cậy mô hình
                </span>
                <ConfidenceBar
                  value={record.confidence}
                  label="Phát hiện (YOLO)"
                />
                <ConfidenceBar
                  value={record.ocr_confidence}
                  label="Đọc ký tự (OCR)"
                />
              </div>
            </div>

            {/* OCR Diff if applicable */}
            {wasCorrected && record.raw_ocr_text && record.plate_number && (
              <OcrComparison
                rawText={record.raw_ocr_text}
                plateNumber={record.plate_number}
              />
            )}

            {/* Technical Metadata Grid */}
            <div className="rounded-xl border border-border/60 bg-surface-raised/30 p-4">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-content-muted">
                Thông số kỹ thuật
              </span>
              <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2.5 text-xs">
                <div>
                  <dt className="text-content-muted">Bố cục biển:</dt>
                  <dd className="font-medium text-content mt-0.5">
                    {record.plate_line_count !== null
                      ? `${record.plate_line_count} dòng`
                      : NO_VALUE}
                  </dd>
                </div>
                <div>
                  <dt className="text-content-muted">Nguồn dữ liệu:</dt>
                  <dd className="font-medium text-content mt-0.5">
                    {INPUT_TYPE_LABELS[record.input_type]}
                  </dd>
                </div>
                <div className="col-span-2">
                  <dt className="text-content-muted">Tọa độ Bounding Box (pixel):</dt>
                  <dd className="font-mono text-[11px] text-content mt-0.5">
                    x={formatNumber(record.bbox_x)}, y={formatNumber(record.bbox_y)}, w={formatNumber(record.bbox_w)}, h={formatNumber(record.bbox_h)}
                  </dd>
                </div>
                {record.source_job_id && (
                  <div className="col-span-2">
                    <dt className="text-content-muted">Mã Job nguồn:</dt>
                    <dd className="font-mono text-[11px] text-content-muted truncate mt-0.5">
                      {record.source_job_id}
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
}

export default HistoryDetailModal;
