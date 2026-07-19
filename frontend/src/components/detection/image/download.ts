/**
 * Download helpers for the image detection page (FR-1.7).
 *
 * Two different downloads are offered and they are produced in two different
 * ways. The cropped plate images already exist as files on the server, so they
 * are fetched and handed to the browser. The *annotated* image does not exist
 * anywhere: `POST /api/detect/image` returns the untouched upload plus a list of
 * boxes, and only the browser has drawn the two together. Saving that view
 * therefore means re-drawing it onto a canvas here rather than asking the server
 * for a file it never rendered.
 */

import type { DetectionResult } from '@/types';

/** Colour of the box outline on a downloaded image, RGB. */
const BOX_COLOR = '#2563eb';

/** Colour of the label text drawn inside the label chip. */
const LABEL_TEXT_COLOR = '#ffffff';

/** Shown instead of a plate string when OCR read nothing. */
const UNREADABLE_LABEL = 'Không đọc được';

/**
 * Failure of a download, carrying a message that is safe to show a user.
 *
 * The page renders `message` verbatim, so it is written in Vietnamese and never
 * contains a status code or an exception string (NFR-U3).
 */
export class DownloadError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'DownloadError';
  }
}

/**
 * Hand a blob to the browser as a file download.
 *
 * The object URL is revoked on the next tick rather than immediately: revoking
 * synchronously after the click can cancel the download in some browsers, which
 * fails silently and looks like a dead button.
 *
 * @param blob - The bytes to save.
 * @param filename - Name suggested to the browser.
 */
function saveBlob(blob: Blob, filename: string): void {
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = objectUrl;
  anchor.download = filename;
  anchor.rel = 'noopener';
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1_000);
}

/**
 * Replace every character a filesystem may reject.
 *
 * Plate strings contain a hyphen and sometimes a dot, and an unreadable plate
 * falls back to a Vietnamese phrase with diacritics — none of which is safe to
 * drop straight into a filename.
 *
 * @param value - Raw text to use in a filename.
 * @param fallback - Used when nothing usable survives the substitution.
 * @returns A filename-safe fragment.
 */
export function toFilenameFragment(
  value: string | null | undefined,
  fallback: string,
): string {
  if (!value) {
    return fallback;
  }
  const cleaned = value
    .normalize('NFD')
    // Strip combining marks so "biển" becomes "bien" rather than being erased.
    .replace(/[̀-ͯ]/g, '')
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'D')
    .replace(/[^A-Za-z0-9._-]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return cleaned.length > 0 ? cleaned : fallback;
}

/**
 * Fetch a file served by the API and save it locally.
 *
 * Fetched into a blob rather than navigated to, because a plain link to
 * `/files/...` opens the image in a tab in some browsers instead of saving it —
 * the `download` attribute is only honoured same-origin, and the API origin is
 * configurable.
 *
 * @param url - A `/files/...` URL from the API.
 * @param filename - Name suggested to the browser.
 * @throws {DownloadError} When the file cannot be retrieved.
 */
export async function downloadRemoteFile(
  url: string,
  filename: string,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(url, { credentials: 'same-origin' });
  } catch {
    throw new DownloadError(
      'Không tải được tệp về máy. Vui lòng kiểm tra kết nối tới máy chủ rồi thử lại.',
    );
  }

  if (!response.ok) {
    throw new DownloadError(
      'Không tìm thấy tệp trên máy chủ. Ảnh có thể đã bị xoá khỏi lịch sử.',
    );
  }

  saveBlob(await response.blob(), filename);
}

/**
 * Load an image element from a URL.
 *
 * `crossOrigin` is requested up front because the result is drawn onto a canvas
 * that must stay readable. Without it a cross-origin image taints the canvas and
 * `toBlob` throws — after the drawing has already succeeded, which makes the
 * failure look like it comes from the export rather than from the load.
 *
 * @param url - Image URL.
 * @returns The loaded image.
 * @throws {DownloadError} When the image cannot be loaded.
 */
function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.crossOrigin = 'anonymous';
    image.onload = () => resolve(image);
    image.onerror = () =>
      reject(
        new DownloadError(
          'Không đọc được ảnh gốc từ máy chủ. Vui lòng thử nhận dạng lại.',
        ),
      );
    image.src = url;
  });
}

/**
 * Draw one bounding box and its label onto a canvas context.
 *
 * @param context - Target 2D context.
 * @param result - The plate to draw.
 * @param index - Position in the result list, used for the numbered label.
 * @param scale - Stroke and font scale derived from the image size, so the
 *   annotation stays legible on a 4000-pixel photo and does not swamp a small
 *   one.
 */
function drawBox(
  context: CanvasRenderingContext2D,
  result: DetectionResult,
  index: number,
  scale: number,
): void {
  const { x, y, width, height } = result.bbox;
  const lineWidth = Math.max(2, Math.round(2 * scale));
  const fontSize = Math.max(12, Math.round(14 * scale));

  context.lineWidth = lineWidth;
  context.strokeStyle = BOX_COLOR;
  context.strokeRect(x, y, width, height);

  const label = `${index + 1}. ${result.plate_number ?? UNREADABLE_LABEL}`;
  context.font = `600 ${fontSize}px "Segoe UI", Roboto, Arial, sans-serif`;
  context.textBaseline = 'top';

  const paddingX = Math.round(fontSize * 0.5);
  const paddingY = Math.round(fontSize * 0.3);
  const textWidth = context.measureText(label).width;
  const chipWidth = textWidth + paddingX * 2;
  const chipHeight = fontSize + paddingY * 2;

  // Place the chip above the box, unless that would fall off the top edge, in
  // which case it goes inside the box instead of being clipped away.
  const chipY = y - chipHeight >= 0 ? y - chipHeight : y;

  context.fillStyle = BOX_COLOR;
  context.fillRect(x, chipY, chipWidth, chipHeight);
  context.fillStyle = LABEL_TEXT_COLOR;
  context.fillText(label, x + paddingX, chipY + paddingY);
}

/**
 * Re-draw the source image with its bounding boxes and save it.
 *
 * The boxes come back in the coordinate space of the processed image, and the
 * canvas is created at exactly that size, so the coordinates are used as-is —
 * no scaling step that could be applied twice.
 *
 * @param imageUrl - URL of the stored source image.
 * @param results - Plates to annotate.
 * @param imageWidth - Processed image width, from the detection response.
 * @param imageHeight - Processed image height, from the detection response.
 * @param filename - Name suggested to the browser.
 * @throws {DownloadError} When the image cannot be loaded or exported.
 */
export async function downloadAnnotatedImage(
  imageUrl: string,
  results: readonly DetectionResult[],
  imageWidth: number,
  imageHeight: number,
  filename: string,
): Promise<void> {
  const image = await loadImage(imageUrl);

  // Prefer the response dimensions, since the boxes are expressed in them, but
  // fall back to the natural size if the response reported something unusable.
  const width = imageWidth > 0 ? imageWidth : image.naturalWidth;
  const height = imageHeight > 0 ? imageHeight : image.naturalHeight;

  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;

  const context = canvas.getContext('2d');
  if (!context) {
    throw new DownloadError(
      'Trình duyệt không hỗ trợ xuất ảnh kết quả. Vui lòng thử trên trình duyệt khác.',
    );
  }

  context.drawImage(image, 0, 0, width, height);

  const scale = Math.max(1, width / 640);
  results.forEach((result, index) => drawBox(context, result, index, scale));

  const blob = await new Promise<Blob | null>((resolve) => {
    try {
      canvas.toBlob(resolve, 'image/jpeg', 0.92);
    } catch {
      // A tainted canvas rejects the export. Resolving null routes it through
      // the same friendly message as any other export failure.
      resolve(null);
    }
  });

  if (!blob) {
    throw new DownloadError(
      'Không xuất được ảnh kết quả. Vui lòng thử lại hoặc tải ảnh gốc.',
    );
  }

  saveBlob(blob, filename);
}
