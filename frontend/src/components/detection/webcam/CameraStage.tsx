/**
 * The live picture, with recognised plates drawn over it.
 *
 * Boxes are positioned as **percentages** of the frame, computed from
 * `image_width` / `image_height` in the response — never as pixels. The video
 * is rendered at whatever width the column happens to be, and that width
 * changes with the viewport, so a pixel offset is correct only at the one size
 * it was calculated for. Percentages scale with the element for free.
 *
 * The same reasoning drives the layout below: the `<video>` is `w-full h-auto`
 * inside a wrapper that has no fixed height. Constraining the height instead
 * and using `object-contain` would letterbox the picture, and the black bars
 * are part of the *element* but not of the *frame* — every percentage would
 * then be measured against a box larger than the image, and every overlay
 * would sit slightly off the plate it is supposed to mark.
 */

import { Camera, CameraOff, Loader2 } from 'lucide-react';

import type { RefObject } from 'react';

import type { DetectionResponse } from '@/types';
import { formatPercent, formatPlateNumber } from '@/lib/format';

/** Props of {@link CameraStage}. */
export interface CameraStageProps {
  /** Ref of the `<video>` element, owned by the camera hook. */
  videoRef: RefObject<HTMLVideoElement>;
  /** Whether frames are currently flowing. */
  isStreaming: boolean;
  /** Whether the camera is still being opened. */
  isStarting: boolean;
  /** Whether a frame is awaiting its response. */
  isSending: boolean;
  /** Most recent result, or `null` before the first response arrives. */
  detection: DetectionResponse | null;
}

/**
 * Render the video feed and its detection overlay.
 *
 * @param props - Video ref, stream state and the latest detection.
 * @returns The camera stage.
 */
export function CameraStage({
  videoRef,
  isStreaming,
  isStarting,
  isSending,
  detection,
}: CameraStageProps): JSX.Element {
  // Guard against a zero denominator: a malformed response would otherwise
  // produce `Infinity%` offsets and throw every box off the screen.
  const canDrawOverlay =
    isStreaming &&
    detection !== null &&
    detection.image_width > 0 &&
    detection.image_height > 0;

  return (
    <div className="relative overflow-hidden rounded-lg border border-border bg-slate-900">
      <video
        ref={videoRef}
        playsInline
        muted
        aria-label="Luồng video trực tiếp từ camera"
        className={`h-auto w-full ${isStreaming ? 'block' : 'hidden'}`}
      />

      {/* Reserve a frame-shaped area while the camera is off, so switching it on
          does not shove the rest of the page downwards. The video is `hidden`
          rather than `invisible` here: an element with no source still carries a
          300x150 intrinsic size, which `h-auto` would stretch into a second
          block of empty height underneath this one. */}
      {!isStreaming && <div className="aspect-video w-full" />}

      {canDrawOverlay && (
        <div className="pointer-events-none absolute inset-0" aria-hidden="true">
          {detection.results.map((result, index) => {
            const left = (result.bbox.x / detection.image_width) * 100;
            const top = (result.bbox.y / detection.image_height) * 100;
            const width = (result.bbox.width / detection.image_width) * 100;
            const height = (result.bbox.height / detection.image_height) * 100;
            // Keep the caption inside the frame when the plate sits near the
            // top edge, where a label drawn above the box would be clipped.
            const isNearTop = top < 8;

            return (
              <div
                key={`${result.plate_number ?? 'unknown'}-${index}`}
                className="absolute rounded-sm border-2 border-emerald-400 shadow-[0_0_0_1px_rgba(0,0,0,0.45)]"
                style={{
                  left: `${left}%`,
                  top: `${top}%`,
                  width: `${width}%`,
                  height: `${height}%`,
                }}
              >
                <span
                  className={`absolute left-0 whitespace-nowrap rounded bg-emerald-400 px-1.5 py-0.5
                              text-xs font-semibold text-slate-950 ${
                                isNearTop ? 'top-full mt-0.5' : 'bottom-full mb-0.5'
                              }`}
                >
                  {formatPlateNumber(result.plate_number)} ·{' '}
                  {formatPercent(result.detection_confidence, 0)}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* Camera off. */}
      {!isStreaming && !isStarting && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-slate-300">
          <CameraOff size={32} aria-hidden="true" />
          <p className="text-sm">Camera đang tắt</p>
          <p className="max-w-xs text-center text-xs text-slate-400">
            Bấm &ldquo;Bật camera&rdquo; để bắt đầu nhận dạng biển số theo thời gian thực.
          </p>
        </div>
      )}

      {/* Opening the device. Shown because permission prompts and camera warm-up
          routinely take longer than the 500 ms that NFR-U2 allows in silence. */}
      {isStarting && (
        <div
          className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-slate-900/80 text-slate-100"
          role="status"
          aria-live="polite"
        >
          <Loader2 size={30} className="animate-spin" aria-hidden="true" />
          <p className="text-sm">Đang khởi động camera…</p>
          <p className="max-w-xs text-center text-xs text-slate-300">
            Nếu trình duyệt hỏi quyền truy cập camera, hãy chọn &ldquo;Cho phép&rdquo;.
          </p>
        </div>
      )}

      {/* Recording badge and in-flight indicator. */}
      {isStreaming && (
        <div className="absolute left-3 top-3 flex items-center gap-2">
          <span className="flex items-center gap-1.5 rounded-full bg-danger px-2.5 py-1 text-xs font-medium text-white">
            <span className="h-2 w-2 animate-pulse rounded-full bg-white" aria-hidden="true" />
            Đang ghi
          </span>
          {isSending && (
            <span
              className="flex items-center gap-1.5 rounded-full bg-slate-900/75 px-2.5 py-1 text-xs font-medium text-slate-100"
              role="status"
              aria-live="off"
            >
              <Loader2 size={12} className="animate-spin" aria-hidden="true" />
              Đang nhận dạng
            </span>
          )}
        </div>
      )}

      {/* Streaming, first response not back yet. */}
      {isStreaming && detection === null && (
        <div className="absolute inset-x-0 bottom-0 flex items-center justify-center gap-2 bg-slate-900/70 px-4 py-2 text-xs text-slate-100">
          <Camera size={14} aria-hidden="true" />
          Đang chờ kết quả nhận dạng đầu tiên…
        </div>
      )}

      {/* Streaming, server answered, nothing in view. Distinct from the state
          above: one means "not yet", the other means "nothing there". */}
      {isStreaming && detection !== null && detection.results.length === 0 && (
        <div className="absolute inset-x-0 bottom-0 bg-slate-900/70 px-4 py-2 text-center text-xs text-slate-100">
          Không thấy biển số trong khung hình. Hãy đưa camera lại gần biển số xe hơn.
        </div>
      )}
    </div>
  );
}

export default CameraStage;
