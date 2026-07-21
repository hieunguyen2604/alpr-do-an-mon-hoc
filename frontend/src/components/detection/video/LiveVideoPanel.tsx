/**
 * Live preview: watch the chosen video with plate boxes drawn over it.
 *
 * Three states, in the order a user meets them:
 *
 * 1. **Chosen.** The video appears immediately, playable and scrubbable, with
 *    no detection running. Seeing the frame is what confirms the right file was
 *    picked, and that answer should not cost a single inference call.
 * 2. **Running.** Pressing the button starts detection against whatever frame
 *    is on screen; boxes track the plates and every reading is appended to the
 *    log below.
 * 3. **Stopped.** The overlay clears — stale boxes over a frame the user has
 *    since scrubbed away from would label the wrong moment — but the log stays,
 *    because that is the thing they stopped to read.
 *
 * Runs beside the background job, not instead of it. The job produces the
 * complete, de-duplicated result and the downloadable per-plate crops; this
 * panel shows what the system is seeing *while* that runs, which is what makes
 * a demonstration legible.
 *
 * Boxes are scaled, never assumed 1:1. The API reports coordinates against the
 * frame it received, which is capped at 960 px on the long edge, while the
 * element on screen is whatever CSS made it. Drawing raw coordinates would put
 * every box in the wrong place, and consistently enough to look like a
 * detection bug rather than a scaling one.
 */

import { useEffect, useRef, useState } from 'react';
import { Play, ScanLine, Square } from 'lucide-react';

import { Badge, Button, Card } from '@/components/ui';
import { formatConfidence, formatVideoTime } from '@/lib/format';
import { plateClassBadges } from '@/lib/plateClass';

import { useLiveVideoDetection } from './useLiveVideoDetection';

/** Props of {@link LiveVideoPanel}. */
export interface LiveVideoPanelProps {
  /** The video the user selected. */
  file: File;
}

/**
 * Colour of a box and its label, by whether the plate parsed as a civil format.
 *
 * Two colours only. More would encode information the viewer cannot decode at a
 * glance on a moving image.
 */
const BOX_COLOURS = {
  valid: '#16a34a',
  invalid: '#ea580c',
} as const;

/** Length of each focus-bracket arm, as a fraction of the shorter box side. */
const BRACKET_RATIO = 0.28;

/** Shortest bracket arm worth drawing, in pixels. */
const MIN_BRACKET = 8;

/**
 * Draw a camera-style focus bracket around one plate.
 *
 * Corner brackets rather than a closed rectangle: a plate is small on screen and
 * a solid box drawn around it covers the very characters the viewer is trying to
 * read. Open corners mark the same region while leaving the glyphs visible.
 *
 * @param context - Target 2-D context.
 * @param x - Left edge, in element pixels.
 * @param y - Top edge, in element pixels.
 * @param width - Box width, in element pixels.
 * @param height - Box height, in element pixels.
 * @param colour - Stroke colour.
 */
function drawFocusBracket(
  context: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  colour: string,
): void {
  const arm = Math.max(MIN_BRACKET, Math.min(width, height) * BRACKET_RATIO);

  // A faint full outline underneath keeps the region legible when the plate sits
  // against a busy background, without the weight of a solid box.
  context.save();
  context.globalAlpha = 0.35;
  context.strokeStyle = colour;
  context.lineWidth = 1;
  context.strokeRect(x, y, width, height);
  context.restore();

  context.strokeStyle = colour;
  context.lineWidth = 3;
  context.lineCap = 'round';
  context.beginPath();
  // Top-left
  context.moveTo(x, y + arm);
  context.lineTo(x, y);
  context.lineTo(x + arm, y);
  // Top-right
  context.moveTo(x + width - arm, y);
  context.lineTo(x + width, y);
  context.lineTo(x + width, y + arm);
  // Bottom-right
  context.moveTo(x + width, y + height - arm);
  context.lineTo(x + width, y + height);
  context.lineTo(x + width - arm, y + height);
  // Bottom-left
  context.moveTo(x + arm, y + height);
  context.lineTo(x, y + height);
  context.lineTo(x, y + height - arm);
  context.stroke();
}

/**
 * Live detection preview over the selected video.
 *
 * @param props - The selected video file.
 * @returns The preview card.
 */
export function LiveVideoPanel({ file }: LiveVideoPanelProps): JSX.Element {
  const videoRef = useRef<HTMLVideoElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);
  const [objectUrl, setObjectUrl] = useState<string | null>(null);

  // Starts off. Choosing a file is a request to *see* the video, not yet a
  // request to spend inference on every frame of it -- and on CPU that spend is
  // roughly 400 ms per frame, which is not something to begin without being
  // asked.
  const [enabled, setEnabled] = useState(false);

  const {
    results,
    frameWidth,
    frameHeight,
    isBusy,
    sent,
    skipped,
    events,
    distinctPlates,
    error,
  } = useLiveVideoDetection({ videoRef, enabled });

  // Every createObjectURL holds the file in memory until revoked. Without the
  // cleanup, choosing five videos in a row keeps all five alive.
  useEffect(() => {
    const url = URL.createObjectURL(file);
    setObjectUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  // Redraw whenever the boxes change or the element resizes.
  useEffect(() => {
    const canvas = overlayRef.current;
    const video = videoRef.current;
    if (canvas === null || video === null) {
      return;
    }

    const draw = (): void => {
      const width = video.clientWidth;
      const height = video.clientHeight;
      if (width === 0 || height === 0) {
        return;
      }

      canvas.width = width;
      canvas.height = height;
      const context = canvas.getContext('2d');
      if (context === null) {
        return;
      }
      context.clearRect(0, 0, width, height);

      if (frameWidth === 0 || frameHeight === 0) {
        return;
      }

      // A <video> letterboxes: it preserves the source aspect ratio and centres
      // the picture inside the element, padding the remainder with black. The
      // canvas covers the whole element, so scaling by the element's size
      // stretches every box across the padding as well and slides it away from
      // the plate — boxes drift left and can land entirely inside a black bar,
      // which reads as a detector fault rather than a drawing one.
      //
      // Scale against the *picture* rectangle and offset by the padding.
      const frameAspect = frameWidth / frameHeight;
      const elementAspect = width / height;
      const pictureWidth = elementAspect > frameAspect ? height * frameAspect : width;
      const pictureHeight = elementAspect > frameAspect ? height : width / frameAspect;
      const offsetX = (width - pictureWidth) / 2;
      const offsetY = (height - pictureHeight) / 2;

      const scaleX = pictureWidth / frameWidth;
      const scaleY = pictureHeight / frameHeight;

      for (const result of results) {
        const colour = result.is_valid_format ? BOX_COLOURS.valid : BOX_COLOURS.invalid;
        const x = offsetX + result.bbox.x * scaleX;
        const y = offsetY + result.bbox.y * scaleY;
        const w = result.bbox.width * scaleX;
        const h = result.bbox.height * scaleY;

        drawFocusBracket(context, x, y, w, h, colour);

        const label = result.plate_display ?? result.plate_number ?? 'Không đọc được';
        context.font = '600 13px system-ui, sans-serif';
        const textWidth = context.measureText(label).width;

        // Above the box when there is room, inside it otherwise — a label drawn
        // off the top edge is invisible exactly when the plate is nearest the
        // camera and most readable.
        const labelY = y > 22 ? y - 20 : y + 2;
        context.fillStyle = colour;
        context.fillRect(x, labelY, textWidth + 10, 18);
        context.fillStyle = '#ffffff';
        context.fillText(label, x + 5, labelY + 13);
      }
    };

    draw();
    const observer = new ResizeObserver(draw);
    observer.observe(video);
    return () => observer.disconnect();
  }, [results, frameWidth, frameHeight]);

  return (
    <Card
      title="Xem trực tiếp"
      description={
        enabled
          ? 'Phát hoặc tua video — hệ thống nhận dạng theo khung hình đang hiển thị'
          : 'Video đã sẵn sàng. Bấm “Chạy nhận dạng” để bắt đầu bắt biển số theo khung hình.'
      }
      actions={
        <Button
          type="button"
          variant={enabled ? 'secondary' : 'primary'}
          size="sm"
          onClick={() => setEnabled((previous) => !previous)}
          leftIcon={
            enabled ? (
              <Square className="h-4 w-4" aria-hidden="true" />
            ) : (
              <Play className="h-4 w-4" aria-hidden="true" />
            )
          }
        >
          {enabled ? 'Dừng nhận dạng' : 'Chạy nhận dạng'}
        </Button>
      }
    >
      <div className="space-y-3">
        <div className="relative overflow-hidden rounded-lg border border-border bg-black">
          {objectUrl !== null && (
            <video
              ref={videoRef}
              src={objectUrl}
              controls
              playsInline
              className="block max-h-[60vh] w-full"
            />
          )}
          <canvas
            ref={overlayRef}
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 h-full w-full"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs text-content-muted">
          <Badge variant={enabled ? (isBusy ? 'info' : 'success') : 'neutral'}>
            {enabled ? (isBusy ? 'Đang nhận dạng…' : 'Sẵn sàng') : 'Chưa chạy'}
          </Badge>
          {enabled && (
            <span>
              Đã gửi <span className="font-medium text-content">{sent}</span> khung
              {skipped > 0 && (
                <>
                  {' · bỏ qua '}
                  <span className="font-medium text-content">{skipped}</span>
                </>
              )}
            </span>
          )}
          {distinctPlates.length > 0 && (
            <span>
              · <span className="font-medium text-content">{distinctPlates.length}</span> biển
              khác nhau đã thấy
            </span>
          )}
        </div>

        {/* Stated, not hidden. A viewer who sees boxes appear and vanish needs to
            know that is the design and not a fault — and that the numbers in the
            results panel come from the complete pass, not from this. */}
        <p className="rounded-lg border border-border bg-surface-muted px-4 py-3 text-xs leading-relaxed text-content-muted">
          <span className="font-medium text-content">Về chế độ xem trực tiếp: </span>
          mỗi lần chỉ xử lý một khung hình, khung nào đến trong lúc đang bận thì{' '}
          <span className="font-medium text-content">bỏ qua</span> — nên khung nhận dạng
          nhấp nháy và chỉ thấy một phần video. Đây là bản xem nhanh để quan sát,{' '}
          <span className="font-medium text-content">không phải kết quả cuối</span>. Kết
          quả đầy đủ đã gộp trùng nằm ở bảng bên dưới khi tác vụ nền chạy xong.
        </p>

        <LiveDetectionLog events={events} isRunning={enabled} />

        {error !== null && (
          <p className="text-xs text-status-warning">
            Không nhận dạng được khung hình vừa rồi: {error}
          </p>
        )}
      </div>
    </Card>
  );
}

/** Props of {@link LiveDetectionLog}. */
interface LiveDetectionLogProps {
  events: ReturnType<typeof useLiveVideoDetection>['events'];
  isRunning: boolean;
}

/**
 * Chronological record of every plate the preview has read.
 *
 * Newest first, because during a demonstration the interesting line is the one
 * that just appeared, and a list that grows downwards pushes it off-screen.
 *
 * Each row carries the raw OCR string next to the corrected one whenever they
 * differ. That comparison is the only place the post-processing stage is
 * visible to a viewer, and it is a large part of what this project claims.
 *
 * @param props - The events and whether detection is currently running.
 * @returns The log section.
 */
function LiveDetectionLog({ events, isRunning }: LiveDetectionLogProps): JSX.Element {
  return (
    <section className="rounded-lg border border-border">
      <header className="flex items-center gap-2 border-b border-border px-4 py-2.5">
        <ScanLine className="h-4 w-4 text-content-muted" aria-hidden="true" />
        <h3 className="text-sm font-medium text-content">Nhật ký nhận dạng</h3>
        {events.length > 0 && (
          <span className="text-xs text-content-muted">{events.length} lượt đọc</span>
        )}
      </header>

      {events.length === 0 ? (
        <p className="px-4 py-6 text-center text-xs text-content-muted">
          {isRunning
            ? 'Đang chờ khung hình đầu tiên có biển số…'
            : 'Chưa có gì. Bấm “Chạy nhận dạng” rồi phát video để bắt đầu ghi.'}
        </p>
      ) : (
        <ul className="max-h-72 divide-y divide-border overflow-y-auto">
          {events.map((event) => (
            <li key={event.id} className="flex flex-wrap items-center gap-x-3 gap-y-1 px-4 py-2">
              <span className="font-mono text-xs tabular-nums text-content-muted">
                {formatVideoTime(event.videoTime)}
              </span>

              <span className="plate-text text-sm">
                {event.display ?? event.plateNumber ?? 'Không đọc được'}
              </span>

              {event.plateNumber !== null &&
                plateClassBadges(event.isValidFormat, event.kind, event.color)
                  .slice(0, 2)
                  .map((badge) => (
                    <Badge key={badge.label} variant={badge.tone} title={badge.title}>
                      {badge.label}
                    </Badge>
                  ))}

              {event.rawText !== null && event.rawText !== event.plateNumber && (
                <span className="text-xs text-content-muted">
                  OCR thô: <span className="font-mono">{event.rawText}</span>
                </span>
              )}

              <span className="ml-auto flex items-center gap-3 text-xs tabular-nums text-content-muted">
                <span title="Độ tin cậy phát hiện của YOLO">
                  PH {formatConfidence(event.detectionConfidence)}
                </span>
                {event.ocrConfidence !== null && (
                  <span title="Độ tin cậy đọc chữ của OCR">
                    OCR {formatConfidence(event.ocrConfidence)}
                  </span>
                )}
                <span title="Kích thước biển số trong khung hình đã gửi">
                  {event.boxWidth}×{event.boxHeight} px
                </span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
