/** Video license plate detection page with background processing and live preview (FR-2.1). */

import { useCallback, useEffect, useRef, useState } from 'react';
import { FileVideo } from 'lucide-react';

import {
  JobProgressPanel,
  LiveVideoPanel,
  VideoResultPanel,
  VideoUploadPanel,
} from '@/components/detection/video';
import HistoryDetailModal from '@/components/history/HistoryDetailModal';
import { Card, EmptyState, ErrorState } from '@/components/ui';
import { useJobPolling } from '@/hooks/useJobPolling';
import { detectVideo, getErrorMessage, getHistory } from '@/services/api';
import type { DetectionHistory, DetectionJob } from '@/types';

const RESULT_PAGE_SIZE = 100;

export default function VideoDetection(): JSX.Element {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [plates, setPlates] = useState<DetectionHistory[]>([]);
  const [isLoadingPlates, setIsLoadingPlates] = useState(false);
  const [platesError, setPlatesError] = useState<string | null>(null);
  const [selectedDetailRecord, setSelectedDetailRecord] = useState<DetectionHistory | null>(null);

  const uploadAbortRef = useRef<AbortController | null>(null);
  const platesAbortRef = useRef<AbortController | null>(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      uploadAbortRef.current?.abort();
      platesAbortRef.current?.abort();
    };
  }, []);

  const loadPlates = useCallback(
    async (finishedJobId: string): Promise<void> => {
      platesAbortRef.current?.abort();
      const controller = new AbortController();
      platesAbortRef.current = controller;

      setIsLoadingPlates(true);
      setPlatesError(null);

      try {
        const page = await getHistory(
          {
            job_id: finishedJobId,
            page: 1,
            page_size: RESULT_PAGE_SIZE,
            sort_by: 'confidence',
            order: 'desc',
          },
          controller.signal,
        );
        if (!isMountedRef.current || controller.signal.aborted) {
          return;
        }
        setPlates(page.items);
      } catch (caught) {
        if (!isMountedRef.current || controller.signal.aborted) {
          return;
        }
        setPlatesError(getErrorMessage(caught));
      } finally {
        if (isMountedRef.current && !controller.signal.aborted) {
          setIsLoadingPlates(false);
        }
      }
    },
    [],
  );

  const handleSettled = useCallback(
    (finished: DetectionJob): void => {
      if (finished.status === 'completed') {
        void loadPlates(finished.id);
      }
    },
    [loadPlates],
  );

  const {
    job,
    isPolling,
    error: pollError,
    refresh,
  } = useJobPolling(jobId, { onSettled: handleSettled });

  const startJob = useCallback(async (file: File): Promise<void> => {
    uploadAbortRef.current?.abort();
    const controller = new AbortController();
    uploadAbortRef.current = controller;

    setIsUploading(true);
    setUploadError(null);
    setUploadProgress(0);
    setPlates([]);
    setPlatesError(null);

    try {
      const created = await detectVideo(file, setUploadProgress, controller.signal);
      if (!isMountedRef.current || controller.signal.aborted) {
        return;
      }
      setJobId(created.id);
    } catch (caught) {
      if (!isMountedRef.current || controller.signal.aborted) {
        return;
      }
      setUploadError(getErrorMessage(caught));
    } finally {
      if (isMountedRef.current && !controller.signal.aborted) {
        setIsUploading(false);
      }
    }
  }, []);

  const handleFileSelect = useCallback(
    (file: File): void => {
      setSelectedFile(file);
      setJobId(null);
      setUploadError(null);
      setUploadProgress(0);
      setPlates([]);
      setPlatesError(null);
      void startJob(file);
    },
    [startJob],
  );

  const handleClear = useCallback((): void => {
    uploadAbortRef.current?.abort();
    platesAbortRef.current?.abort();
    setSelectedFile(null);
    setJobId(null);
    setUploadError(null);
    setUploadProgress(0);
    setPlates([]);
    setPlatesError(null);
  }, []);

  const handleRetry = useCallback((): void => {
    if (selectedFile && !isUploading) {
      void startJob(selectedFile);
    }
  }, [selectedFile, isUploading, startJob]);

  const handleRefresh = useCallback((): void => {
    void refresh();
  }, [refresh]);

  const handleRetryPlates = useCallback((): void => {
    if (jobId) {
      void loadPlates(jobId);
    }
  }, [jobId, loadPlates]);

  const isJobRunning =
    jobId !== null && (job === null || job.status === 'pending' || job.status === 'processing');

  return (
    <div className="space-y-6">
      {/* 2-Column Responsive Layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left Column: Upload & Live Video Preview (7 cols) */}
        <div className="space-y-5 lg:col-span-7">
          <VideoUploadPanel
            selectedFile={selectedFile}
            onFileSelect={handleFileSelect}
            onClear={handleClear}
            isUploading={isUploading}
            uploadProgress={uploadProgress}
            isJobRunning={isJobRunning}
          />

          {uploadError && (
            <ErrorState
              title="Không tải được video lên"
              message={uploadError}
              onRetry={handleRetry}
              retryLabel="Thử tải lên lại"
              isRetrying={isUploading}
            />
          )}

          {selectedFile !== null && uploadError === null && (
            <LiveVideoPanel
              key={`${selectedFile.name}-${selectedFile.size}-${selectedFile.lastModified}`}
              file={selectedFile}
            />
          )}
        </div>

        {/* Right Column: Background Progress & Plate Results (5 cols) */}
        <div className="space-y-5 lg:col-span-5">
          {jobId === null ? (
            <Card title="Hàng đợi xử lý nền">
              <EmptyState
                icon={<FileVideo className="h-6 w-6" aria-hidden="true" />}
                title="Chưa có tác vụ nào"
                description="Chọn một video ở khung bên trái để bắt đầu. Video được đưa vào hàng đợi xử lý nền — tiến độ hiển thị tại đây, còn khung hình xem trực tiếp ở bên trái."
              />
            </Card>
          ) : (
            <JobProgressPanel
              job={job}
              jobId={jobId}
              isPolling={isPolling}
              pollError={pollError}
              onRefresh={handleRefresh}
            />
          )}

          {job !== null && job.status === 'completed' && (
            <VideoResultPanel
              job={job}
              plates={plates}
              isLoading={isLoadingPlates}
              error={platesError}
              onRetry={handleRetryPlates}
              onOpenDetails={(record) => setSelectedDetailRecord(record)}
            />
          )}
        </div>
      </div>

      {/* Detection Details Modal for inspect */}
      <HistoryDetailModal
        record={selectedDetailRecord}
        onClose={() => setSelectedDetailRecord(null)}
        onDelete={() => setSelectedDetailRecord(null)}
      />
    </div>
  );
}
