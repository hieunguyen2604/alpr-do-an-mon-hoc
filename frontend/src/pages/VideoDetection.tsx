/**
 * Video detection page: upload a clip, follow the background job, read results.
 *
 * Covers FR-2.1 (video detection) and FR-2.6 (progress tracking).
 *
 * Video is processed asynchronously (decision AD-02). `POST /api/detect/video`
 * answers 202 with a `DetectionJob`, and this page polls `GET /api/jobs/{id}`
 * through {@link useJobPolling} until the status is terminal. Awaiting the
 * response inline would guarantee a timeout instead: a 60-second clip needs
 * roughly 200 seconds on CPU (NFR-SC3).
 *
 * The page holds the job **id** rather than the job object as its source of
 * truth. `useJobPolling` owns the object, so keeping a second copy here would
 * create two versions of the same state that drift apart between polls.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { FileVideo } from 'lucide-react';

import {
  JobProgressPanel,
  VideoResultPanel,
  VideoUploadPanel,
} from '@/components/detection/video';
import { Card, EmptyState, ErrorState } from '@/components/ui';
import { useJobPolling } from '@/hooks/useJobPolling';
import { detectVideo, getErrorMessage, getHistory } from '@/services/api';
import type { DetectionHistory, DetectionJob } from '@/types';

/**
 * Largest number of plates fetched for one finished job.
 *
 * Matches `MAX_PAGE_SIZE` on the backend, which rejects anything larger with a
 * 422. A video producing more distinct plates than this is well outside the
 * demonstration scope, and the full set remains available on the history page.
 */
const RESULT_PAGE_SIZE = 100;

/**
 * Video detection page.
 *
 * @returns The video detection view.
 */
export default function VideoDetection(): JSX.Element {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [plates, setPlates] = useState<DetectionHistory[]>([]);
  const [isLoadingPlates, setIsLoadingPlates] = useState(false);
  const [platesError, setPlatesError] = useState<string | null>(null);

  // Aborts an in-flight upload when the component unmounts, so a user leaving
  // the page does not leave a request writing to state React has discarded.
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

  /**
   * Load the plates recorded against a finished job.
   *
   * Read from the history endpoint rather than from the job object, which only
   * carries a count. Filtering by `job_id` returns exactly the rows this run
   * produced — already merged across frames by the backend, so a car seen in
   * fifty frames is one row.
   *
   * @param finishedJobId - Id of the job whose results to fetch.
   */
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

  /**
   * React to a job reaching a terminal status.
   *
   * Fires for `failed` and `cancelled` too, so the status is inspected rather
   * than assumed: fetching results for a failed job would show an empty list
   * where an error belongs.
   *
   * @param finished - The settled job.
   */
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

  /**
   * Accept a newly chosen video.
   *
   * Clears any previous run: leaving the last job's results on screen beside a
   * new file would attribute them to the wrong video.
   *
   * @param file - The file that passed the dropzone's validation.
   */
  const handleFileSelect = useCallback((file: File): void => {
    setSelectedFile(file);
    setJobId(null);
    setUploadError(null);
    setUploadProgress(0);
    setPlates([]);
    setPlatesError(null);
  }, []);

  /** Clear the selection and everything derived from it. */
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

  /** Upload the selected video and start following the job it creates. */
  const handleSubmit = useCallback(async (): Promise<void> => {
    if (!selectedFile || isUploading) {
      return;
    }

    uploadAbortRef.current?.abort();
    const controller = new AbortController();
    uploadAbortRef.current = controller;

    setIsUploading(true);
    setUploadError(null);
    setUploadProgress(0);
    setPlates([]);
    setPlatesError(null);

    try {
      const created = await detectVideo(
        selectedFile,
        setUploadProgress,
        controller.signal,
      );
      if (!isMountedRef.current || controller.signal.aborted) {
        return;
      }
      // Setting the id is what starts the polling hook; the job object it
      // returns supersedes this response from the first tick onwards.
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
  }, [selectedFile, isUploading]);

  /** Poll once immediately, from the progress panel's refresh button. */
  const handleRefresh = useCallback((): void => {
    void refresh();
  }, [refresh]);

  /** Re-request the plate list after a failure. */
  const handleRetryPlates = useCallback((): void => {
    if (jobId) {
      void loadPlates(jobId);
    }
  }, [jobId, loadPlates]);

  const isJobRunning =
    jobId !== null && (job === null || job.status === 'pending' || job.status === 'processing');

  return (
    <div className="space-y-5">
      <VideoUploadPanel
        selectedFile={selectedFile}
        onFileSelect={handleFileSelect}
        onClear={handleClear}
        onSubmit={() => void handleSubmit()}
        isUploading={isUploading}
        uploadProgress={uploadProgress}
        isJobRunning={isJobRunning}
      />

      {/* Upload failures are reported here rather than inside the panel: the
          file is still selected and still valid, so the retry is the submit
          button the user already has. */}
      {uploadError && (
        <ErrorState
          title="Không tải được video lên"
          message={uploadError}
          onRetry={() => void handleSubmit()}
          retryLabel="Thử tải lên lại"
          isRetrying={isUploading}
        />
      )}

      {jobId === null ? (
        <Card>
          <EmptyState
            icon={<FileVideo className="h-6 w-6" aria-hidden="true" />}
            title="Chưa có tác vụ nào"
            description="Chọn một video và bấm “Bắt đầu xử lý”. Video sẽ được đưa vào hàng đợi và xử lý ở chế độ nền — bạn có thể theo dõi tiến độ tại đây."
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
        />
      )}
    </div>
  );
}
