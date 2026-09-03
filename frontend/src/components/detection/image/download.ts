/** Download helpers for image detection results and annotated previews (FR-1.7). */

import type { DetectionResult } from '@/types';

/** Colour of the box outline on a downloaded image. */
const BOX_COLOR = '#2563eb';

/** Colour of the label text drawn inside the label chip. */
const LABEL_TEXT_COLOR = '#ffffff';

/** Shown instead of a plate string when OCR read nothing. */
const UNREADABLE_LABEL = 'Không đọc được';

/** Download error with user-facing message. */
export class DownloadError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'DownloadError';
  }
}

/** Trigger browser file download from Blob. */
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

/** Sanitize string for safe use as a filename fragment. */
export function toFilenameFragment(
  value: string | null | undefined,
  fallback: string,
): string {
  if (!value) {
    return fallback;
  }
  const cleaned = value
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'D')
    .replace(/[^A-Za-z0-9._-]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return cleaned.length > 0 ? cleaned : fallback;
}

/** Fetch remote file from URL and trigger download. */
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

/** Load an image element from URL. */
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

/** Draw one bounding box and label onto canvas context. */
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

  const plate = result.plate_display ?? result.plate_number;
  const label = `${index + 1}. ${plate ?? UNREADABLE_LABEL}`;
  context.font = `600 ${fontSize}px "Segoe UI", Roboto, Arial, sans-serif`;
  context.textBaseline = 'top';

  const paddingX = Math.round(fontSize * 0.5);
  const paddingY = Math.round(fontSize * 0.3);
  const textWidth = context.measureText(label).width;
  const chipWidth = textWidth + paddingX * 2;
  const chipHeight = fontSize + paddingY * 2;

  const chipY = y - chipHeight >= 0 ? y - chipHeight : y;

  context.fillStyle = BOX_COLOR;
  context.fillRect(x, chipY, chipWidth, chipHeight);
  context.fillStyle = LABEL_TEXT_COLOR;
  context.fillText(label, x + paddingX, chipY + paddingY);
}

/** Render annotated image with bounding boxes onto canvas and download as JPEG. */
export async function downloadAnnotatedImage(
  imageUrl: string,
  results: readonly DetectionResult[],
  imageWidth: number,
  imageHeight: number,
  filename: string,
): Promise<void> {
  const image = await loadImage(imageUrl);

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
