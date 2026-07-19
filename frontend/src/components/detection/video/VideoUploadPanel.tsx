/**
 * Upload panel of the video detection page.
 *
 * Selection and validation only — this component never talks to the network.
 * The page owns the request so that the upload lifecycle and the job that
 * follows it stay in one place.
 */

import { FileVideo, Upload } from 'lucide-react';

import { Button, Card, FileDropzone, ProgressBar } from '@/components/ui';
import {
  ACCEPTED_VIDEO_LABEL,
  ACCEPTED_VIDEO_TYPES,
  MAX_VIDEO_MB,
} from '@/lib/constants';
import { formatFileSize } from '@/lib/format';

/** Props of {@link VideoUploadPanel}. */
export interface VideoUploadPanelProps {
  /** Video chosen by the user, or `null` when nothing is selected. */
  selectedFile: File | null;
  /** Called with a file that passed the dropzone's own validation. */
  onFileSelect: (file: File) => void;
  /** Called when the user clears the selection. */
  onClear: () => void;
  /** Called when the user starts processing. */
  onSubmit: () => void;
  /** Whether the multipart upload is in flight. */
  isUploading: boolean;
  /** Upload transfer progress from 0.0 to 1.0. */
  uploadProgress: number;
  /**
   * Whether a job from a previous upload is still running.
   *
   * Blocks a second submission: the page follows exactly one job at a time, and
   * starting another would silently orphan the first.
   */
  isJobRunning: boolean;
}

/**
 * Render the upload panel.
 *
 * @param props - Selection state, upload state and the submit handler.
 * @returns The upload card.
 */
export function VideoUploadPanel({
  selectedFile,
  onFileSelect,
  onClear,
  onSubmit,
  isUploading,
  uploadProgress,
  isJobRunning,
}: VideoUploadPanelProps): JSX.Element {
  const isLocked = isUploading || isJobRunning;

  return (
    <Card
      title="Tải video lên"
      description={`Hỗ trợ ${ACCEPTED_VIDEO_LABEL} · tối đa ${MAX_VIDEO_MB} MB`}
    >
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

        <p className="flex items-start gap-2 text-xs text-content-muted">
          <FileVideo
            className="mt-0.5 h-4 w-4 shrink-0"
            aria-hidden="true"
          />
          <span>
            Video được xử lý ở chế độ nền. Suy luận chạy trên CPU, nên một video
            60 giây có thể mất khoảng 3–4 phút. Bạn có thể theo dõi tiến độ ngay
            bên dưới sau khi tải lên.
          </span>
        </p>

        {selectedFile && (
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-surface-muted px-4 py-3">
            <div className="min-w-0">
              <p className="text-sm font-medium text-content">
                Sẵn sàng xử lý
              </p>
              <p className="mt-0.5 text-xs text-content-muted">
                {formatFileSize(selectedFile.size)} · sẽ được đưa vào hàng đợi
                xử lý nền
              </p>
            </div>
            <Button
              type="button"
              variant="primary"
              onClick={onSubmit}
              disabled={isLocked}
              isLoading={isUploading}
              loadingText="Đang tải lên…"
              leftIcon={<Upload className="h-4 w-4" aria-hidden="true" />}
            >
              Bắt đầu xử lý
            </Button>
          </div>
        )}

        {/* Transfer progress, distinct from inference progress: this bar
            reaches 100% the moment the file lands on the server, long before
            a single frame has been analysed. Labelled so the two are not
            mistaken for one another (NFR-U2). */}
        {isUploading && (
          <ProgressBar
            value={uploadProgress}
            label="Đang tải tệp lên máy chủ"
            showLabel
          />
        )}
      </div>
    </Card>
  );
}

export default VideoUploadPanel;
