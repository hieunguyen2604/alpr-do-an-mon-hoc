/**
 * Compact Video Upload Panel (Auto-collapsing when video is selected).
 */

import { FileVideo, RefreshCw, Trash2 } from 'lucide-react';

import { Button, FileDropzone, ProgressBar } from '@/components/ui';
import {
  ACCEPTED_VIDEO_LABEL,
  ACCEPTED_VIDEO_TYPES,
  MAX_VIDEO_MB,
} from '@/lib/constants';
import { formatFileSize } from '@/lib/format';

export interface VideoUploadPanelProps {
  selectedFile: File | null;
  onFileSelect: (file: File) => void;
  onClear: () => void;
  isUploading: boolean;
  uploadProgress: number;
  isJobRunning: boolean;
}

export function VideoUploadPanel({
  selectedFile,
  onFileSelect,
  onClear,
  isUploading,
  uploadProgress,
  isJobRunning,
}: VideoUploadPanelProps): JSX.Element {
  const isLocked = isUploading || isJobRunning;

  if (selectedFile) {
    return (
      <div className="space-y-4">
        {/* Compact Mini Action Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border/80 bg-surface p-3 shadow-sm">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary/10 border border-primary/20 text-primary">
              <FileVideo className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-bold text-content">{selectedFile.name}</p>
              <p className="text-xs text-content-muted">
                {formatFileSize(selectedFile.size)} · {isUploading ? 'Đang tải lên…' : 'Đang xử lý'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {!isLocked && (
              <label className="cursor-pointer">
                <input
                  type="file"
                  className="hidden"
                  accept={ACCEPTED_VIDEO_TYPES.join(',')}
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) onFileSelect(file);
                  }}
                />
                <span className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-surface-raised px-2.5 py-1.5 text-xs font-semibold text-content hover:border-primary transition-colors">
                  <RefreshCw className="h-3.5 w-3.5" /> Đổi video
                </span>
              </label>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={onClear}
              disabled={isLocked}
              className="text-xs text-danger hover:bg-danger/10 hover:text-danger h-8"
              leftIcon={<Trash2 className="h-3.5 w-3.5" />}
            >
              Xóa
            </Button>
          </div>
        </div>

        {isUploading && (
          <div className="rounded-xl border border-border/60 bg-surface-raised/40 p-3">
            <ProgressBar
              value={uploadProgress}
              label="Đang tải video lên máy chủ"
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
        acceptedTypes={ACCEPTED_VIDEO_TYPES}
        maxSizeMb={MAX_VIDEO_MB}
        acceptedLabel={ACCEPTED_VIDEO_LABEL}
        selectedFile={selectedFile}
        onClear={onClear}
        disabled={isLocked}
        label="Kéo thả video vào đây hoặc bấm để chọn"
      />
    </div>
  );
}

export default VideoUploadPanel;
