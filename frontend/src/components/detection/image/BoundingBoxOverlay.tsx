/**
 * Source image with the detected plates outlined on top (FR-1.2).
 *
 * The boxes arrive in the pixel coordinate space of the *processed* image, while
 * the preview is scaled down to fit the card. Every box is therefore converted
 * to a percentage of `imageWidth` / `imageHeight` and positioned against the
 * image element itself. Percentages survive any rescaling — a responsive layout,
 * a zoomed browser, a different viewport — whereas pixel offsets computed once
 * at render time drift the moment the element resizes.
 *
 * That is also why the image is sized by width alone (`w-full h-auto`) rather
 * than with `object-contain` inside a fixed box: `object-contain` letterboxes
 * the picture inside the element, so the element's edges stop matching the
 * image's edges and every percentage silently points at the wrong place.
 */

import { cn } from '@/lib/cn';
import type { DetectionResult } from '@/types';

/** Props of {@link BoundingBoxOverlay}. */
export interface BoundingBoxOverlayProps {
  /** URL of the image to show underneath the boxes. */
  imageUrl: string;
  /** Alternative text for the image. */
  alt: string;
  /**
   * Plates to outline. Empty renders the bare image, which is the correct
   * result for a picture containing no plate.
   */
  results: readonly DetectionResult[];
  /** Processed image width in pixels, the denominator for horizontal ratios. */
  imageWidth: number;
  /** Processed image height in pixels, the denominator for vertical ratios. */
  imageHeight: number;
  /** Index of the plate currently highlighted, or `null` for none. */
  activeIndex?: number | null;
  /** Called when the pointer enters or leaves a box. */
  onActiveIndexChange?: (index: number | null) => void;
  className?: string;
}

/**
 * Convert a pixel measurement into a percentage of a total.
 *
 * @param value - Pixel measurement in the processed image's space.
 * @param total - Full width or height of the processed image.
 * @returns A CSS percentage string. Guards against a zero total, which would
 *   otherwise produce `Infinity%` and drop the box out of the layout.
 */
function toPercent(value: number, total: number): string {
  if (!Number.isFinite(total) || total <= 0) {
    return '0%';
  }
  return `${(value / total) * 100}%`;
}

/**
 * Render the annotated preview.
 *
 * @param props - Image source, dimensions and the plates to outline.
 * @returns The overlay element.
 */
export function BoundingBoxOverlay({
  imageUrl,
  alt,
  results,
  imageWidth,
  imageHeight,
  activeIndex = null,
  onActiveIndexChange,
  className,
}: BoundingBoxOverlayProps): JSX.Element {
  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-lg border border-border bg-surface-raised',
        className,
      )}
    >
      {/* The wrapper is exactly the size of the rendered image, so the
          percentage-positioned boxes below share its coordinate space. */}
      <div className="relative">
        <img
          src={imageUrl}
          alt={alt}
          className="block h-auto w-full select-none"
          draggable={false}
        />

        {results.map((result, index) => {
          const isActive = activeIndex === index;
          const label = result.plate_number ?? 'Không đọc được';

          return (
            <div
              key={`${result.plate_number ?? 'unread'}-${index}`}
              // Boxes must not swallow clicks meant for the image, but they do
              // need hover, so pointer events are re-enabled per box rather
              // than left on for the whole overlay layer.
              className={cn(
                'absolute rounded-sm border-2 transition-colors',
                isActive
                  ? 'border-warning bg-warning/20'
                  : 'border-primary bg-primary/10',
                onActiveIndexChange ? 'cursor-pointer' : 'pointer-events-none',
              )}
              style={{
                left: toPercent(result.bbox.x, imageWidth),
                top: toPercent(result.bbox.y, imageHeight),
                width: toPercent(result.bbox.width, imageWidth),
                height: toPercent(result.bbox.height, imageHeight),
              }}
              onMouseEnter={() => onActiveIndexChange?.(index)}
              onMouseLeave={() => onActiveIndexChange?.(null)}
            >
              <span
                className={cn(
                  'absolute left-0 whitespace-nowrap rounded px-1.5 py-0.5',
                  'text-xs font-semibold shadow-sm',
                  // Sits above the box, but drops inside it when the box is
                  // near the top edge, where a label above would be clipped.
                  result.bbox.y / Math.max(imageHeight, 1) > 0.08
                    ? '-top-6'
                    : 'top-0',
                  isActive
                    ? 'bg-warning text-slate-950'
                    : 'bg-primary text-white dark:text-slate-950',
                )}
              >
                {index + 1}. {label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default BoundingBoxOverlay;
