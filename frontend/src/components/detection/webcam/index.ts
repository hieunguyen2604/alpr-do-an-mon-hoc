/**
 * Building blocks of the realtime webcam view.
 *
 * The page composes these; nothing else imports them. They live in their own
 * folder so the camera lifecycle, the capture loop and the presentation stay
 * separable — each is testable and readable on its own, which the single
 * 600-line page they replace was not.
 */

export { CameraControls } from './CameraControls';
export type { CameraControlsProps } from './CameraControls';

export { DEFAULT_FRAME_INTERVAL_MS, FRAME_INTERVAL_OPTIONS } from './constants';
export type { FrameIntervalOption } from './constants';

export { CameraStage } from './CameraStage';
export type { CameraStageProps } from './CameraStage';

export { CaptureMetricsPanel } from './CaptureMetricsPanel';
export type { CaptureMetricsPanelProps } from './CaptureMetricsPanel';

export { SessionPlateTable } from './SessionPlateTable';
export type { SessionPlateTableProps } from './SessionPlateTable';

export { useCameraStream, mapCameraError } from './useCameraStream';
export type { CameraStatus, UseCameraStreamResult } from './useCameraStream';

export { useFrameCaptureLoop, mergeSessionPlates } from './useFrameCaptureLoop';
export type {
  UseFrameCaptureLoopOptions,
  UseFrameCaptureLoopResult,
} from './useFrameCaptureLoop';

export type {
  CameraDevice,
  CameraError,
  CameraErrorKind,
  CaptureMetrics,
  SessionPlateRow,
  SessionSortKey,
} from './types';
