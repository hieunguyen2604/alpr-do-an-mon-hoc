/**
 * Realtime webcam detection page (FR-3.1 to FR-3.5).
 *
 * Frames are captured in the browser and posted one at a time over plain HTTP
 * (decision AD-03). WebSocket was rejected because the bottleneck is inference
 * at roughly 300-400 ms per frame, not the few milliseconds of HTTP overhead; a
 * socket would add reconnection and connection state without moving the number
 * that actually matters.
 *
 * The page itself is composition and states. The two mechanisms worth knowing
 * about live in the hooks it uses, and both are documented there:
 *
 * - `useCameraStream` owns the `MediaStream` and guarantees every track is
 *   stopped, so the camera indicator light goes out when the user says stop.
 * - `useFrameCaptureLoop` enforces the single-slot rule (at most one request in
 *   flight, extra frames dropped rather than queued) and reuses one `job_id`
 *   for the whole session, which is what keeps `total_jobs` on the dashboard
 *   meaning "uploads" instead of "frames".
 *
 * All four states are handled: the camera is starting (spinner over the stage),
 * failed (a message plus the specific fix for that failure), succeeded but
 * empty (nothing recognised yet), and succeeded with results.
 */

import { useCallback, useState } from 'react';
import { AlertTriangle, RefreshCw, Trash2 } from 'lucide-react';

import { InlineError, PageSection } from '@/components/StateViews';
import {
  CameraControls,
  CameraStage,
  CaptureMetricsPanel,
  DEFAULT_FRAME_INTERVAL_MS,
  SessionPlateTable,
  useCameraStream,
  useFrameCaptureLoop,
} from '@/components/detection/webcam';
import type { CameraError } from '@/components/detection/webcam';
import { formatNumber } from '@/lib/format';

/** Props of {@link CameraErrorPanel}. */
interface CameraErrorPanelProps {
  error: CameraError;
  onRetry: () => void;
  onDismiss: () => void;
}

/**
 * Explain a camera failure and how to recover from it.
 *
 * Kept separate from the generic {@link InlineError} because a camera problem
 * needs two lines, not one: what happened, and the steps that fix it. Telling a
 * user "không truy cập được camera" without saying whether to grant permission,
 * plug a device in, or close Zoom leaves them with nothing to try.
 *
 * @param props - The error and the retry/dismiss handlers.
 * @returns The error panel.
 */
function CameraErrorPanel({
  error,
  onRetry,
  onDismiss,
}: CameraErrorPanelProps): JSX.Element {
  return (
    <div
      className="flex flex-col gap-3 rounded-lg border border-danger/30 bg-danger/5 px-4 py-3.5"
      role="alert"
    >
      <div className="flex items-start gap-2.5">
        <AlertTriangle
          size={18}
          className="mt-0.5 shrink-0 text-danger"
          aria-hidden="true"
        />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-content">{error.message}</p>
          <p className="mt-1 text-sm text-content-muted">{error.hint}</p>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <button type="button" onClick={onRetry} className="btn-primary">
          <RefreshCw size={15} aria-hidden="true" />
          Thử lại
        </button>
        <button type="button" onClick={onDismiss} className="btn-secondary">
          Đóng
        </button>
      </div>
    </div>
  );
}

/**
 * Webcam detection page.
 *
 * @returns The realtime detection view.
 */
export default function WebcamDetection(): JSX.Element {
  const [intervalMs, setIntervalMs] = useState(DEFAULT_FRAME_INTERVAL_MS);

  const camera = useCameraStream();
  const capture = useFrameCaptureLoop({
    videoRef: camera.videoRef,
    // Capture is bound to the stream, so stopping the camera stops the loop in
    // the same tick: no frame can be sent from a device that has been released.
    enabled: camera.isStreaming,
    intervalMs,
  });

  const { resetSession } = capture;
  const { start, stop, selectDevice } = camera;

  /** Open the camera and begin a fresh session. */
  const handleStart = useCallback((): void => {
    // A new session means a new job id: reusing the previous one would file
    // this capture's plates under the earlier upload.
    resetSession();
    void start();
  }, [resetSession, start]);

  /** Release the camera. The session log is kept for review. */
  const handleStop = useCallback((): void => {
    stop();
  }, [stop]);

  /**
   * Switch cameras mid-session.
   *
   * The session is reset because the backend groups a job by upload, and frames
   * from two different cameras are not one continuous capture.
   */
  const handleSelectDevice = useCallback(
    (deviceId: string): void => {
      resetSession();
      void selectDevice(deviceId);
    },
    [resetSession, selectDevice],
  );

  const plateCount = capture.plates.length;
  const totalSightings = capture.plates.reduce(
    (sum, row) => sum + row.occurrences,
    0,
  );

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1.55fr)_minmax(0,1fr)]">
      <PageSection
        title="Camera trực tiếp"
        subtitle="Khung hình được chụp trong trình duyệt và gửi lần lượt lên máy chủ để nhận dạng"
      >
        <div className="space-y-4">
          <CameraControls
            isStreaming={camera.isStreaming}
            isStarting={camera.status === 'starting'}
            devices={camera.devices}
            activeDeviceId={camera.activeDeviceId}
            intervalMs={intervalMs}
            onStart={handleStart}
            onStop={handleStop}
            onSelectDevice={handleSelectDevice}
            onIntervalChange={setIntervalMs}
          />

          {/* Error state: the camera itself could not be used. */}
          {camera.error && (
            <CameraErrorPanel
              error={camera.error}
              onRetry={handleStart}
              onDismiss={camera.dismissError}
            />
          )}

          {/* Error state: the camera works but the server is refusing frames.
              Separate from the panel above because the camera is still usable
              and the picture should stay on screen. */}
          {capture.error && !capture.isPaused && (
            <InlineError message={capture.error} onDismiss={capture.dismissError} />
          )}

          {capture.isPaused && (
            <div
              className="flex flex-col gap-3 rounded-lg border border-warning/40 bg-warning/5 px-4 py-3.5"
              role="alert"
            >
              <div className="flex items-start gap-2.5">
                <AlertTriangle
                  size={18}
                  className="mt-0.5 shrink-0 text-warning"
                  aria-hidden="true"
                />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-content">
                    Đã tạm dừng gửi khung hình
                  </p>
                  <p className="mt-1 text-sm text-content-muted">
                    {capture.error ??
                      'Máy chủ không phản hồi cho nhiều khung hình liên tiếp.'}{' '}
                    Camera vẫn đang bật. Hãy kiểm tra máy chủ rồi bấm &ldquo;Tiếp
                    tục&rdquo;.
                  </p>
                </div>
              </div>
              <div>
                <button type="button" onClick={capture.resume} className="btn-primary">
                  <RefreshCw size={15} aria-hidden="true" />
                  Tiếp tục nhận dạng
                </button>
              </div>
            </div>
          )}

          <CameraStage
            videoRef={camera.videoRef}
            isStreaming={camera.isStreaming}
            isStarting={camera.status === 'starting'}
            isSending={capture.isSending}
            detection={capture.latestDetection}
          />

          <CaptureMetricsPanel metrics={capture.metrics} jobId={capture.jobId} />
        </div>
      </PageSection>

      <PageSection
        title="Biển số trong phiên"
        subtitle={
          plateCount > 0
            ? `${formatNumber(plateCount)} biển số khác nhau · ${formatNumber(totalSightings)} lượt nhận dạng`
            : 'Mỗi biển số chỉ hiển thị một dòng, kèm số lần xuất hiện'
        }
        actions={
          plateCount > 0 && (
            <button
              type="button"
              onClick={capture.clearPlates}
              className="btn-secondary"
            >
              <Trash2 size={15} aria-hidden="true" />
              Xoá danh sách
            </button>
          )
        }
      >
        <SessionPlateTable
          rows={capture.plates}
          unreadableCount={capture.unreadableCount}
          isStreaming={camera.isStreaming}
        />
      </PageSection>
    </div>
  );
}
