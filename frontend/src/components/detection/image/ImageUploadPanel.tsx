/**
 * Multi-Image Upload Panel with Filmstrip Carousel & Batch Queue.
 */

import { Loader2, Plus, XCircle } from 'lucide-react';

import { FileDropzone, ProgressBar } from '@/components/ui';
import {
  ACCEPTED_IMAGE_LABEL,
  ACCEPTED_IMAGE_TYPES,
  MAX_IMAGE_MB,
} from '@/lib/constants';
import { formatFileSize } from '@/lib/format';
import { cn } from '@/lib/cn';

export interface ImageUploadPanelProps {
  files: File[];
  activeIndex: number;
  onSelectIndex: (index: number) => void;
  onAddFiles: (newFiles: File[]) => void;
  onRemoveFile: (index: number) => void;
  onClearAll: () => void;
  isDetecting: boolean;
  uploadProgress: number;
  statusMap?: Record<number, 'detecting' | 'completed' | 'error'>;
  plateCountMap?: Record<number, number>;
}

export function ImageUploadPanel({
  files,
  activeIndex,
  onSelectIndex,
  onAddFiles,
  onRemoveFile,
  onClearAll,
  isDetecting,
  uploadProgress,
  statusMap = {},
  plateCountMap = {},
}: ImageUploadPanelProps): JSX.Element {
  const isUploadFinished = uploadProgress >= 1;
  const activeFile = files[activeIndex];

  if (files.length > 0 && activeFile) {
    return (
      <div className="space-y-3">
        {/* Top Filmstrip Carousel */}
        <div className="flex items-center gap-2 overflow-x-auto rounded-2xl border border-border/80 bg-surface p-2.5 shadow-sm scrollbar-thin">
          {files.map((file, idx) => {
            const isSelected = idx === activeIndex;
            const status = statusMap[idx];
            const plateCount = plateCountMap[idx];

            return (
              <button
                key={`${file.name}-${idx}`}
                type="button"
                onClick={() => onSelectIndex(idx)}
                className={cn(
                  'group relative flex shrink-0 items-center gap-2 rounded-xl border px-3 py-1.5 text-xs font-semibold transition-all',
                  isSelected
                    ? 'border-primary bg-primary/10 text-primary ring-2 ring-primary/20 shadow-sm'
                    : 'border-border/80 bg-surface-raised/60 text-content-muted hover:border-border hover:text-content',
                )}
              >
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-surface-raised text-[10px] font-bold">
                  {idx + 1}
                </span>
                <span className="max-w-[110px] truncate">{file.name}</span>

                {status === 'detecting' && (
                  <Loader2 className="h-3 w-3 animate-spin text-primary" />
                )}
                {status === 'completed' && (
                  <span className="rounded-full bg-emerald-500/20 px-1 text-[10px] font-bold text-emerald-400">
                    {plateCount !== undefined ? `${plateCount} biển` : '✓'}
                  </span>
                )}
                {status === 'error' && (
                  <XCircle className="h-3 w-3 text-danger" />
                )}

                <span
                  role="button"
                  tabIndex={0}
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemoveFile(idx);
                  }}
                  className="ml-1 rounded-md p-0.5 opacity-60 hover:bg-danger/20 hover:opacity-100 hover:text-danger"
                  title="Xoá ảnh này"
                >
                  ✕
                </span>
              </button>
            );
          })}

          {/* Add more files button */}
          <label className="cursor-pointer shrink-0">
            <input
              type="file"
              multiple
              className="hidden"
              accept={ACCEPTED_IMAGE_TYPES.join(',')}
              onChange={(e) => {
                const newFiles = Array.from(e.target.files ?? []);
                if (newFiles.length > 0) onAddFiles(newFiles);
                e.target.value = '';
              }}
            />
            <span className="flex items-center gap-1 rounded-xl border border-dashed border-border bg-surface-raised/40 px-3 py-1.5 text-xs font-semibold text-content-muted hover:border-primary hover:text-primary transition-colors">
              <Plus className="h-3.5 w-3.5" /> Thêm ảnh
            </span>
          </label>

          {/* Clear all */}
          <button
            type="button"
            onClick={onClearAll}
            className="ml-auto shrink-0 text-xs font-semibold text-danger hover:underline px-2"
          >
            Xoá hết
          </button>
        </div>

        {/* Active file summary bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border/60 bg-surface-raised/40 px-3.5 py-2 text-xs">
          <div className="flex items-center gap-2 min-w-0">
            <span className="font-bold text-content">Ảnh {activeIndex + 1}/{files.length}:</span>
            <span className="font-medium text-content-muted truncate">{activeFile.name}</span>
            <span className="text-content-muted font-mono">({formatFileSize(activeFile.size)})</span>
          </div>

          <div className="flex items-center gap-2">
            {isDetecting && (
              <span className="flex items-center gap-1 font-semibold text-primary">
                <Loader2 className="h-3 w-3 animate-spin" /> Đang nhận dạng…
              </span>
            )}
          </div>
        </div>

        {/* Progress bar */}
        {isDetecting && (
          <div className="rounded-xl border border-border/60 bg-surface-raised/40 p-3">
            <ProgressBar
              value={uploadProgress}
              indeterminate={isUploadFinished}
              label={
                isUploadFinished
                  ? `Mô hình đang phân tích ảnh #${activeIndex + 1}…`
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
        multiple
        onFilesSelect={onAddFiles}
        acceptedTypes={ACCEPTED_IMAGE_TYPES}
        acceptedLabel={ACCEPTED_IMAGE_LABEL}
        maxSizeMb={MAX_IMAGE_MB}
        label="Kéo thả một hoặc nhiều ảnh vào đây để nhận dạng"
      />
    </div>
  );
}

export default ImageUploadPanel;
