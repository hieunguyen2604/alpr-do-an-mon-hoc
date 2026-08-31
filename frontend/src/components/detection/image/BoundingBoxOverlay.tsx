/** Source image with detected plate bounding box overlay (FR-1.2). */

import { cn } from '@/lib/cn';
import type { DetectionResult } from '@/types';

/** Props for BoundingBoxOverlay component. */
export interface BoundingBoxOverlayProps {
  imageUrl: string;
  alt: string;
  results: readonly DetectionResult[];
  imageWidth: number;
  imageHeight: number;
  activeIndex?: number | null;
  onActiveIndexChange?: (index: number | null) => void;
  className?: string;
}

/** Convert pixel measurement into CSS percentage string. */
function toPercent(value: number, total: number): string {
  if (!Number.isFinite(total) || total <= 0) {
    return '0%';
  }
  return `${(value / total) * 100}%`;
}

/** Render annotated image with responsive percentage bounding boxes. */
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
