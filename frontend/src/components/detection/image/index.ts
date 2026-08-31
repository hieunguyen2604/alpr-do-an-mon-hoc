/** Components composing the image detection page. */

export { BoundingBoxOverlay } from './BoundingBoxOverlay';
export type { BoundingBoxOverlayProps } from './BoundingBoxOverlay';

export { DetectionSummary } from './DetectionSummary';
export type { DetectionSummaryProps } from './DetectionSummary';

export { ImageUploadPanel } from './ImageUploadPanel';
export type { ImageUploadPanelProps } from './ImageUploadPanel';

export { PlateResultCard } from './PlateResultCard';
export type { PlateResultCardProps } from './PlateResultCard';

export {
  DownloadError,
  downloadAnnotatedImage,
  downloadRemoteFile,
  toFilenameFragment,
} from './download';
