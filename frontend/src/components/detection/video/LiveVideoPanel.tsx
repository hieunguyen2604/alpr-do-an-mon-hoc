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

/**
 * Playback speed while detection is running.
 *
 * The analysed picture updates a few times a second, and that is bounded by
 * inference cost, not by the player. Halving the playback speed does not make
 * the system faster — it makes each analysed frame cover half as much motion,
 * so the sequence reads as continuous instead of jumping. The clip takes twice
 * as long to watch, which for a fourteen-second demo is a good trade.
 *
 * Reset to 1 when detection stops, so the player behaves normally for anyone
 * scrubbing through the video by hand.
 */
const ANALYSIS_PLAYBACK_RATE = 0.5;

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
    frameImage,
    frameWidth,
    frameHeight,
    isBusy,
    sent,
    skipped,
    plates,
    error,
  } = useLiveVideoDetection({ videoRef, enabled });

  // Stop when the clip finishes. Otherwise the panel stays in its running
  // state over a frozen last frame, with the seek bar hidden and no way to
  // replay — and it goes on claiming to be analysing something.
  //
  // Keyed on `objectUrl`, not on nothing: the <video> element is only rendered
  // once the object URL exists, so an effect with an empty dependency list runs
  // while `videoRef.current` is still null and attaches the listener to
  // nothing. That is exactly what happened first time round — capture stopped
  // correctly but the button went on saying "Dừng nhận dạng" over a finished
  // clip.
  useEffect(() => {
    const video = videoRef.current;
    if (video === null) {
      return;
    }
    const handleEnded = (): void => setEnabled(false);
    video.addEventListener('ended', handleEnded);
    return () => video.removeEventListener('ended', handleEnded);
  }, [objectUrl]);

  // The button drives playback as well as detection. Separating them made the
  // two easy to leave out of step -- detection running against a paused frame,
  // or a video playing with nothing reading it -- and there is no use for
  // either state. One control, one meaning: "analyse this video".
  useEffect(() => {
    const video = videoRef.current;
    if (video === null) {
      return;
    }
    if (enabled) {
      video.playbackRate = ANALYSIS_PLAYBACK_RATE;
      // Started from a click, so the autoplay policy is satisfied; a rejection
      // here means the file itself will not play and the empty overlay already
      // says so.
      void video.play().catch(() => {});
    } else {
      video.playbackRate = 1;
      video.pause();
    }
  }, [enabled]);

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

      // Paint the analysed frame over the live one. This is what makes the
      // picture and the boxes describe the same instant: the video element has
      // moved on by roughly half a second while the model was thinking, and
      // drawing boxes over *that* picture shows a vehicle next to its own box.
      // The cost is a picture that updates about twice a second instead of
      // smoothly -- an honest trade, because the smooth version was showing a
      // correspondence that did not exist.
      if (frameImage !== null) {
        context.drawImage(frameImage, offsetX, offsetY, pictureWidth, pictureHeight);
      }

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
  }, [results, frameImage, frameWidth, frameHeight]);

  // Unreadable boxes share one bucket in the log, and counting it among the
  // plates would claim a plate was identified when it was only located.
  const readablePlateCount = plates.filter((plate) => plate.plateNumber !== null).length;

  return (
    <Card
      title="Xem trực tiếp"
      description={
        enabled
          ? 'Đang hiện đúng khung hình mà hệ thống vừa đọc, kèm biển số tìm được trên chính khung đó'
          : 'Video đã sẵn sàng — tua để xem trước. Bấm “Chạy nhận dạng” để vừa phát vừa đọc biển số.'
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
              preload="auto"
              onLoadedMetadata={(e) => {
                const vid = e.currentTarget;
                if (vid.currentTime === 0) {
                  vid.currentTime = 0.001;
                }
              }}
              // Native controls only when stopped. While running the canvas
              // covers the picture, so a seek bar underneath it would be
              // invisible but still clickable -- a control the user cannot see
              // and cannot predict. Stopping hands the player back.
              controls={!enabled}
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
          {readablePlateCount > 0 && (
            <span>
              · <span className="font-medium text-content">{readablePlateCount}</span> biển
              khác nhau đã đọc được
            </span>
          )}
        </div>

        {/* Stated, not hidden. A viewer who sees boxes appear and vanish needs to
            know that is the design and not a fault — and that the numbers in the
            results panel come from the complete pass, not from this. */}
        <p className="rounded-lg border border-border bg-surface-muted px-4 py-3 text-xs leading-relaxed text-content-muted">
          <span className="font-medium text-content">Về chế độ xem trực tiếp: </span>
          khi đang chạy, ô hình hiện{' '}
          <span className="font-medium text-content">đúng khung đã được phân tích</span>{' '}
          chứ không phải khung video đang trôi — nhờ vậy ảnh và khung nhận dạng luôn
          thuộc cùng một khoảnh khắc. Đổi lại hình cập nhật khoảng hai lần mỗi giây,
          vì mỗi khung tốn chừng nửa giây suy luận trên CPU. Khung nào đến trong lúc
          đang bận thì <span className="font-medium text-content">bỏ qua</span>, nên
          hệ thống chỉ nhìn được một phần video. Đây là bản xem nhanh để quan sát,{' '}
          <span className="font-medium text-content">không phải kết quả cuối</span> —
          kết quả đầy đủ đã gộp trùng nằm ở bảng bên dưới khi tác vụ nền chạy xong.
        </p>

        <LiveDetectionLog plates={plates} isRunning={enabled} />

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
  plates: ReturnType<typeof useLiveVideoDetection>['plates'];
  isRunning: boolean;
}

/**
 * One row per **plate**, not per sighting.
 *
 * A vehicle stays in shot for several seconds and is read in every frame that
 * catches it, so an unmerged list says the same number a dozen times and pushes
 * anything new off the screen. Merging also matches how the background job
 * reports: one row per plate, however many frames it appeared in.
 *
 * Each row carries the raw OCR string next to the corrected one whenever they
 * differ. That comparison is the only place the post-processing stage is
 * visible to a viewer, and it is a large part of what this project claims.
 *
 * @param props - The merged plates and whether detection is currently running.
 * @returns The log section.
 */
function LiveDetectionLog({ plates, isRunning }: LiveDetectionLogProps): JSX.Element {
  return (
    <section className="rounded-lg border border-border">
      <header className="flex items-center gap-2 border-b border-border px-4 py-2.5">
        <ScanLine className="h-4 w-4 text-content-muted" aria-hidden="true" />
        <h3 className="text-sm font-medium text-content">Nhật ký nhận dạng</h3>
        {plates.length > 0 && (
          <span className="text-xs text-content-muted">
            {plates.length} biển · đã gộp các lần đọc trùng
          </span>
        )}
      </header>

      {plates.length === 0 ? (
        <p className="px-4 py-6 text-center text-xs text-content-muted">
          {isRunning
            ? 'Đang chờ khung hình đầu tiên có biển số…'
            : 'Chưa có gì. Bấm “Chạy nhận dạng” để vừa phát video vừa ghi lại biển số.'}
        </p>
      ) : (
        <ul className="max-h-72 divide-y divide-border overflow-y-auto">
          {plates.map((plate) => (
            <li
              key={plate.plateNumber ?? '__unread__'}
              className="flex flex-wrap items-center gap-x-3 gap-y-1 px-4 py-2"
            >
              {/* A range when the plate was in shot across several moments, a
                  single stamp when it was caught once. Printing "0:04 – 0:04"
                  would imply a duration that was never observed. */}
              <span className="font-mono text-xs tabular-nums text-content-muted">
                {plate.firstSeen === plate.lastSeen
                  ? formatVideoTime(plate.firstSeen)
                  : `${formatVideoTime(plate.firstSeen)}–${formatVideoTime(plate.lastSeen)}`}
              </span>

              <span className="plate-text text-sm">
                {plate.display ?? plate.plateNumber ?? 'Không đọc được'}
              </span>

              {plate.plateNumber !== null &&
                plateClassBadges(plate.isValidFormat, plate.kind, plate.color)
                  .slice(0, 2)
                  .map((badge) => (
                    <Badge key={badge.label} variant={badge.tone} title={badge.title}>
                      {badge.label}
                    </Badge>
                  ))}

              <span
                className="text-xs text-content-muted"
                title="Số khung hình biển này được đọc thấy"
              >
                ×{plate.reads}
              </span>

              {plate.rawText !== null && plate.rawText !== plate.plateNumber && (
                <span className="text-xs text-content-muted">
                  OCR thô: <span className="font-mono">{plate.rawText}</span>
                </span>
              )}

              <span className="ml-auto flex items-center gap-3 text-xs tabular-nums text-content-muted">
                <span title="Độ tin cậy phát hiện cao nhất của YOLO">
                  PH {formatConfidence(plate.detectionConfidence)}
                </span>
                {plate.ocrConfidence !== null && (
                  <span title="Độ tin cậy đọc chữ cao nhất của OCR">
                    OCR {formatConfidence(plate.ocrConfidence)}
                  </span>
                )}
                <span title="Kích thước biển số ở lần đọc tốt nhất">
                  {plate.boxWidth}×{plate.boxHeight} px
                </span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
