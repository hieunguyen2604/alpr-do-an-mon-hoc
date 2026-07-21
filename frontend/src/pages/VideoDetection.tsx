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
  LiveVideoPanel,
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
   * Upload one video and start following the job it creates.
   *
   * Takes the file as an argument rather than reading `selectedFile` from
   * state, so that it can be called from the same tick that sets it. A React
   * state update is not visible to the callback that scheduled it, so a version
   * reading state would upload nothing on the very call that matters.
   *
   * @param file - The video to process.
   */
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
  }, []);

  /**
   * Accept a newly chosen video.
   *
   * Clears any previous run: leaving the last job's results on screen beside a
   * new file would attribute them to the wrong video.
   *
   * @param file - The file that passed the dropzone's validation.
   */
  const handleFileSelect = useCallback(
    (file: File): void => {
      setSelectedFile(file);
      setJobId(null);
      setUploadError(null);
      setUploadProgress(0);
      setPlates([]);
      setPlatesError(null);

      // Start immediately rather than waiting for a second click. Choosing a
      // video is already an unambiguous request to process it -- there is
      // nothing else the page can do with the file, and no option to set
      // between the two steps. The confirmation button was a step that asked a
      // question with only one answer.
      void startJob(file);
    },
    [startJob],
  );

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

  /** Retry the current file after a failed upload. */
  const handleRetry = useCallback((): void => {
    if (selectedFile && !isUploading) {
      void startJob(selectedFile);
    }
  }, [selectedFile, isUploading, startJob]);

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
        isUploading={isUploading}
        uploadProgress={uploadProgress}
        isJobRunning={isJobRunning}
      />

      {/* Upload failures are reported here rather than inside the panel. With
          the submit button gone, this is now the *only* way to retry, so the
          action has to live where the error does. */}
      {/* The live preview sits above the progress panel: while the background
          job is running it is the only thing on screen that shows what the
          system is actually seeing. A progress bar reports that work is
          happening, not what it is finding.

          Keyed on the file so choosing a different video remounts the panel
          with an empty log and no carried-over session. Without the key the
          previous clip's readings would sit under the new one's frames. */}
      {selectedFile !== null && uploadError === null && (
        <LiveVideoPanel
          key={`${selectedFile.name}-${selectedFile.size}-${selectedFile.lastModified}`}
          file={selectedFile}
        />
      )}

      {uploadError && (
        <ErrorState
          title="Không tải được video lên"
          message={uploadError}
          onRetry={handleRetry}
          retryLabel="Thử tải lên lại"
          isRetrying={isUploading}
        />
      )}

      {jobId === null ? (
        <Card>
          <EmptyState
            icon={<FileVideo className="h-6 w-6" aria-hidden="true" />}
            title="Chưa có tác vụ nào"
            description="Chọn một video để bắt đầu. Video được đưa vào hàng đợi và xử lý ở chế độ nền ngay khi chọn — tiến độ hiện tại đây, còn khung hình xem ngay ở phần “Xem trực tiếp”."
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
