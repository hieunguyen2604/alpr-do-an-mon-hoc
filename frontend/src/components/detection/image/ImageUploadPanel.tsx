/**
 * Compact Image Upload Panel (Auto-collapsing when file is selected).
 */

import { Image as ImageIcon, RefreshCw, Trash2 } from 'lucide-react';

import { Button, FileDropzone, ProgressBar } from '@/components/ui';
import {
  ACCEPTED_IMAGE_LABEL,
  ACCEPTED_IMAGE_TYPES,
  MAX_IMAGE_MB,
} from '@/lib/constants';
import { formatFileSize } from '@/lib/format';

export interface ImageUploadPanelProps {
  selectedFile: File | null;
  previewUrl?: string | null;
  onFileSelect: (file: File) => void;
  onClear: () => void;
  isDetecting: boolean;
  uploadProgress: number;
}

export function ImageUploadPanel({
  selectedFile,
  onFileSelect,
  onClear,
  isDetecting,
  uploadProgress,
}: ImageUploadPanelProps): JSX.Element {
  const isUploadFinished = uploadProgress >= 1;

  if (selectedFile) {
    return (
      <div className="space-y-4">
        {/* Compact Mini Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border/80 bg-surface p-3 shadow-sm">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary/10 border border-primary/20 text-primary">
              <ImageIcon className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-bold text-content">{selectedFile.name}</p>
              <p className="text-xs text-content-muted">
                {formatFileSize(selectedFile.size)} · {isDetecting ? 'Đang nhận dạng…' : 'Đã tải lên'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {!isDetecting && (
              <label className="cursor-pointer">
                <input
                  type="file"
                  className="hidden"
                  accept={ACCEPTED_IMAGE_TYPES.join(',')}
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) onFileSelect(file);
                  }}
                />
                <span className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-surface-raised px-2.5 py-1.5 text-xs font-semibold text-content hover:border-primary transition-colors">
                  <RefreshCw className="h-3.5 w-3.5" /> Đổi ảnh
                </span>
              </label>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={onClear}
              disabled={isDetecting}
              className="text-xs text-danger hover:bg-danger/10 hover:text-danger h-8"
              leftIcon={<Trash2 className="h-3.5 w-3.5" />}
            >
              Xóa
            </Button>
          </div>
        </div>

        {/* Progress bar during upload */}
        {isDetecting && (
          <div className="space-y-1.5 rounded-xl border border-border/60 bg-surface-raised/40 p-3">
            <ProgressBar
              value={uploadProgress}
              indeterminate={isUploadFinished}
              label={
                isUploadFinished
                  ? 'Mô hình YOLO11 + PaddleOCR đang phân tích…'
                  : 'Đang tải ảnh lên máy chủ'
              }
              showLabel
            />
          </div>
        )}
      </div>
    );
  }

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
    </div>
  );
}

export default ImageUploadPanel;
