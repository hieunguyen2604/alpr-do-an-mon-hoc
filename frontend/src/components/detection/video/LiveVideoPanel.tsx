/**
 * Live preview: play or scrub the chosen video with plate boxes drawn over it.
 *
 * Runs beside the background job, not instead of it. The job produces the
 * complete, de-duplicated result and the downloadable per-plate crops; this
 * panel shows what the system is seeing *while* that runs, which is what makes
 * a demonstration legible — a progress bar shows that work is happening, not
 * what the work is finding.
 *
 * Boxes are scaled, never assumed 1:1. The API reports coordinates against the
 * frame it received, which is capped at 960 px on the long edge, while the
 * element on screen is whatever CSS made it. Drawing raw coordinates would put
 * every box in the wrong place, and consistently enough to look like a
 * detection bug rather than a scaling one.
 */

import { useEffect, useRef, useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

import { Badge, Button, Card } from '@/components/ui';
import { formatConfidence } from '@/lib/format';
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
 * Live detection preview over the selected video.
 *
 * @param props - The selected video file.
 * @returns The preview card.
 */
export function LiveVideoPanel({ file }: LiveVideoPanelProps): JSX.Element {
  const videoRef = useRef<HTMLVideoElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);
  const [objectUrl, setObjectUrl] = useState<string | null>(null);
  const [enabled, setEnabled] = useState(true);

  const { results, frameWidth, frameHeight, isBusy, sent, skipped, error } =
    useLiveVideoDetection({ videoRef, enabled });

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
      const scaleX = width / frameWidth;
      const scaleY = height / frameHeight;

      for (const result of results) {
        const isValid = result.is_valid_format;
        const colour = isValid ? BOX_COLOURS.valid : BOX_COLOURS.invalid;
        const x = result.bbox.x * scaleX;
        const y = result.bbox.y * scaleY;
        const w = result.bbox.width * scaleX;
        const h = result.bbox.height * scaleY;

        context.strokeStyle = colour;
        context.lineWidth = 2;
        context.strokeRect(x, y, w, h);

        const label = result.plate_display ?? result.plate_number ?? 'Không đọc được';
        context.font = '600 13px system-ui, sans-serif';
        const textWidth = context.measureText(label).width;

        // Above the box when there is room, inside it otherwise — a label drawn
        // off the top edge is invisible exactly when the plate is nearest the
        // camera and most readable.
        const labelY = y > 20 ? y - 18 : y + 2;
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

  const total = sent + skipped;

  return (
    <Card
      title="Xem trực tiếp"
      description="Phát hoặc tua video — hệ thống nhận dạng theo khung hình đang hiển thị"
      actions={
        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={() => setEnabled((previous) => !previous)}
          leftIcon={
            enabled ? (
              <EyeOff className="h-4 w-4" aria-hidden="true" />
            ) : (
              <Eye className="h-4 w-4" aria-hidden="true" />
            )
          }
        >
          {enabled ? 'Tắt nhận dạng trực tiếp' : 'Bật nhận dạng trực tiếp'}
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
            {enabled ? (isBusy ? 'Đang nhận dạng…' : 'Sẵn sàng') : 'Đã tắt'}
          </Badge>
          <span>
            Đã gửi <span className="font-medium text-content">{sent}</span> khung
            {total > 0 && (
              <>
                {' · bỏ qua '}
                <span className="font-medium text-content">{skipped}</span>
              </>
            )}
          </span>
          {results.length > 0 && (
            <span>
              · thấy <span className="font-medium text-content">{results.length}</span> biển
              trong khung hiện tại
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

        {results.length > 0 && (
          <ul className="flex flex-wrap gap-2">
            {results.map((result, index) => (
              <li
                key={`${result.plate_number ?? 'unread'}-${index}`}
                className="flex items-center gap-2 rounded-lg border border-border bg-surface px-3 py-2"
              >
                <span className="plate-text text-sm">
                  {result.plate_display ?? result.plate_number ?? 'Không đọc được'}
                </span>
                {result.plate_number !== null &&
                  plateClassBadges(
                    result.is_valid_format,
                    result.plate_kind,
                    result.plate_color,
                  )
                    .slice(0, 2)
                    .map((badge) => (
                      <Badge key={badge.label} variant={badge.tone} title={badge.title}>
                        {badge.label}
                      </Badge>
                    ))}
                <span className="text-xs text-content-muted">
                  {formatConfidence(result.detection_confidence)}
                </span>
              </li>
            ))}
          </ul>
        )}

        {error !== null && (
          <p className="text-xs text-status-warning">
            Không nhận dạng được khung hình vừa rồi: {error}
          </p>
        )}
      </div>
    </Card>
  );
}
