/**
 * Upload side of the image detection page (FR-1.1).
 *
 * Format and size are checked in the browser before anything is sent, so an
 * obviously unacceptable file never costs the user an upload. The check is a
 * **convenience, not a control**: the backend identifies a file by its magic
 * bytes rather than by the `Content-Type` the browser guessed (NFR-S1) and
 * enforces the same 10 MB ceiling, so a crafted request is rejected there
 * whatever passes here.
 *
 * There is deliberately no "Nhận dạng" button: dropping or choosing an image
 * IS the ask, so the page starts recognising immediately (mirroring the video
 * page, which plays on selection). The extra click carried no decision — it
 * only stood between the user and the result.
 */

import { Trash2, Upload } from 'lucide-react';

import { Button, FileDropzone, ProgressBar } from '@/components/ui';
import {
  ACCEPTED_IMAGE_LABEL,
  ACCEPTED_IMAGE_TYPES,
  MAX_IMAGE_MB,
} from '@/lib/constants';
import { formatFileSize } from '@/lib/format';

/** Props of {@link ImageUploadPanel}. */
export interface ImageUploadPanelProps {
  /** File currently chosen, or `null` when nothing is selected. */
  selectedFile: File | null;
  /** Object URL of the local preview, or `null`. */
  previewUrl: string | null;
  /** Called with a file that passed client-side validation. */
  onFileSelect: (file: File) => void;
  /** Called when the user clears the selection. */
  onClear: () => void;
  /** Whether a detection request is in flight. */
  isDetecting: boolean;
  /**
   * Upload completion from 0.0 to 1.0.
   *
   * Only meaningful while `isDetecting`. Once it reaches 1.0 the bytes have
   * arrived but the server is still working, which is why the panel switches to
   * an indeterminate bar instead of showing a finished one — a bar stuck at
   * 100% while nothing happens reads as a hang.
   */
  uploadProgress: number;
}

/**
 * Render the upload panel.
 *
 * @param props - Selection state, handlers and upload progress.
 * @returns The upload panel.
 */
export function ImageUploadPanel({
  selectedFile,
  previewUrl,
  onFileSelect,
  onClear,
  isDetecting,
  uploadProgress,
}: ImageUploadPanelProps): JSX.Element {
  const isUploadFinished = uploadProgress >= 1;

  return (
    <div className="space-y-4">
      <FileDropzone
        onFileSelect={onFileSelect}
        acceptedTypes={ACCEPTED_IMAGE_TYPES}
        acceptedLabel={ACCEPTED_IMAGE_LABEL}
        maxSizeMb={MAX_IMAGE_MB}
        selectedFile={selectedFile}
        onClear={onClear}
        disabled={isDetecting}
        label="Kéo thả ảnh vào đây hoặc bấm để chọn"
      />

      {/* Local preview of the chosen file, before any request is made. The
          annotated version replaces it once results come back. */}
      {previewUrl && (
        <figure className="overflow-hidden rounded-lg border border-border bg-surface-raised">
          <img
            src={previewUrl}
            alt={
              selectedFile
                ? `Xem trước ảnh ${selectedFile.name}`
                : 'Xem trước ảnh đã chọn'
            }
            className="mx-auto block max-h-72 w-auto max-w-full object-contain"
          />
          {selectedFile && (
            <figcaption className="border-t border-border px-3 py-2 text-xs text-content-muted">
              {selectedFile.name} · {formatFileSize(selectedFile.size)}
            </figcaption>
          )}
        </figure>
      )}

      {/*
        Any action past 500 ms needs visible feedback (NFR-U2). Upload progress
        is real while bytes are moving; afterwards the server is running
        inference on CPU and reports nothing until it answers, so the bar goes
        indeterminate rather than inventing a number.
      */}
      {isDetecting && (
        <ProgressBar
          value={uploadProgress}
          indeterminate={isUploadFinished}
          showLabel={!isUploadFinished}
          label={
            isUploadFinished
              ? 'Đang phát hiện và đọc biển số…'
              : 'Đang tải ảnh lên máy chủ…'
          }
        />
      )}

      <div className="flex flex-wrap items-center gap-2">
        {selectedFile && !isDetecting && (
          <Button
            variant="secondary"
            onClick={onClear}
            leftIcon={<Trash2 className="h-4 w-4" />}
          >
            Xoá ảnh
          </Button>
        )}

        {!selectedFile && (
          <span className="inline-flex items-center gap-1.5 text-xs text-content-muted">
            <Upload className="h-3.5 w-3.5" aria-hidden="true" />
            Chọn ảnh là nhận dạng chạy ngay — không cần bấm gì thêm
          </span>
        )}
      </div>
    </div>
  );
}

export default ImageUploadPanel;
