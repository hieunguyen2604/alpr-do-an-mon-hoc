/**
 * Image detection page — upload one photo, see the plates found in it.
 *
 * Covers FR-1.1 (upload with client-side validation), FR-1.2 (results with
 * bounding boxes, both confidence scores and the raw OCR string) and FR-1.7
 * (downloading the annotated image and the cropped plates).
 *
 * Four states are handled explicitly and are kept distinct on purpose:
 *
 * - **loading** — the request is in flight, with real upload progress followed
 *   by an indeterminate bar while the server runs inference (NFR-U2);
 * - **empty** — the request succeeded and found no plate. This is a normal
 *   outcome reported with HTTP 200, so it is presented as an empty state and
 *   never as a failure. Showing an error here would send the user off to debug a
 *   system that is working correctly;
 * - **error** — the request itself failed, reported with the Vietnamese message
 *   the API client produced. Raw exception text and status codes are never shown
 *   (NFR-U3); the correlation id is offered instead, which is what makes a
 *   report traceable in the server log without publishing internals;
 * - **success** — at least one plate was found.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { Download, Image as ImageIcon, SearchX } from 'lucide-react';

import {
  BoundingBoxOverlay,
  DetectionSummary,
  DownloadError,
  ImageUploadPanel,
  PlateResultCard,
  downloadAnnotatedImage,
  downloadRemoteFile,
  toFilenameFragment,
} from '@/components/detection/image';
import { InlineError, LoadingState, PageSection } from '@/components/StateViews';
import HistoryDetailModal from '@/components/history/HistoryDetailModal';
import { Button, EmptyState, ErrorState } from '@/components/ui';
import { detectImage, fileUrl, isApiError } from '@/services/api';
import type { ApiError, DetectionHistory, DetectionResponse, DetectionResult } from '@/types';

/** Fallback error, used when a thrown value is not a normalised API error. */
const UNEXPECTED_ERROR: ApiError = {
  status: 0,
  message:
    'Không nhận dạng được ảnh. Vui lòng thử lại, hoặc chọn một ảnh khác nếu lỗi vẫn tiếp diễn.',
};

/**
 * Image detection page.
 *
 * @returns The image detection view.
 */
export default function ImageDetection(): JSX.Element {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [response, setResponse] = useState<DetectionResponse | null>(null);
  const [isDetecting, setIsDetecting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<ApiError | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [downloadingCropIndex, setDownloadingCropIndex] = useState<number | null>(
    null,
  );
  const [isDownloadingAnnotated, setIsDownloadingAnnotated] = useState(false);

  // Held in a ref as well as in state so the unmount cleanup can revoke the
  // current URL without the effect depending on it — a dependency there would
  // revoke the URL on every change and leave the preview broken.
  const previewUrlRef = useRef<string | null>(null);
  // Aborts an in-flight upload when the user clears the form or leaves the page,
  // so a late response cannot land on a component that no longer wants it.
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => {
      if (previewUrlRef.current) {
        URL.revokeObjectURL(previewUrlRef.current);
      }
      abortRef.current?.abort();
    };
  }, []);

  /**
   * Replace the local preview, releasing the previous object URL.
   *
   * Every `createObjectURL` holds its blob in memory until revoked, so skipping
   * this leaks the full image on each re-selection.
   *
   * @param file - The newly chosen file, or `null` to clear the preview.
   */
  const replacePreview = useCallback((file: File | null): void => {
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current);
      previewUrlRef.current = null;
    }
    const next = file ? URL.createObjectURL(file) : null;
    previewUrlRef.current = next;
    setPreviewUrl(next);
  }, []);

  /** Upload one image and show what was found in it.
   *
   * Takes the file as an argument instead of reading `selectedFile` from
   * state: detection starts in the same tick the file is chosen, before React
   * has re-rendered, and reading state here would race that update.
   */
  const runDetection = useCallback(async (file: File): Promise<void> => {
    const controller = new AbortController();
    abortRef.current?.abort();
    abortRef.current = controller;

    setIsDetecting(true);
    setError(null);
    setDownloadError(null);
    setResponse(null);
    setActiveIndex(null);
    setUploadProgress(0);

    try {
      const result = await detectImage(file, setUploadProgress, controller.signal);
      setResponse(result);
    } catch (caught) {
      // A cancellation is the user's own doing — clearing the form or picking a
      // different file — so it must not be reported back to them as a failure.
      if (isApiError(caught) && caught.code === 'CANCELLED') {
        return;
      }
      setError(isApiError(caught) ? caught : UNEXPECTED_ERROR);
    } finally {
      if (abortRef.current === controller) {
        abortRef.current = null;
        setIsDetecting(false);
      }
    }
  }, []);

  /**
   * Accept a file that already passed the dropzone's validation, and start
   * recognising it immediately — dropping or choosing an image IS the ask;
   * a separate "Nhận dạng" button was one click that carried no decision.
   *
   * @param file - The chosen image.
   */
  const handleFileSelect = useCallback(
    (file: File): void => {
      setSelectedFile(file);
      replacePreview(file);
      // Results belong to the previous file; keeping them beside a new image
      // would show boxes that do not match what is on screen.
      setResponse(null);
      setDownloadError(null);
      setActiveIndex(null);
      void runDetection(file);
    },
    [replacePreview, runDetection],
  );

  /** Return the page to its initial state. */
  const handleClear = useCallback((): void => {
    abortRef.current?.abort();
    abortRef.current = null;

    setSelectedFile(null);
    replacePreview(null);
    setResponse(null);
    setError(null);
    setDownloadError(null);
    setActiveIndex(null);
    setUploadProgress(0);
    setIsDetecting(false);
  }, [replacePreview]);

  /**
   * Report a failed download in Vietnamese.
   *
   * @param caught - The value thrown by the download helper.
   */
  const reportDownloadFailure = useCallback((caught: unknown): void => {
    setDownloadError(
      caught instanceof DownloadError
        ? caught.message
        : 'Không tải được tệp về máy. Vui lòng thử lại.',
    );
  }, []);

  /** Save the source image with the bounding boxes drawn onto it. */
  const handleDownloadAnnotated = useCallback(async (): Promise<void> => {
    if (!response) {
      return;
    }

    // The stored copy is preferred, but the local object URL is an equally good
    // canvas source and keeps the button working if the file is not served.
    const source = fileUrl(response.image_url) ?? previewUrl;
    if (!source) {
      setDownloadError('Không tìm thấy ảnh gốc để xuất kết quả.');
      return;
    }

    setDownloadError(null);
    setIsDownloadingAnnotated(true);
    try {
      await downloadAnnotatedImage(
        source,
        response.results,
        response.image_width,
        response.image_height,
        `ket-qua-${toFilenameFragment(response.job_id, 'nhan-dang')}.jpg`,
      );
    } catch (caught) {
      reportDownloadFailure(caught);
    } finally {
      setIsDownloadingAnnotated(false);
    }
  }, [previewUrl, reportDownloadFailure, response]);

  /**
   * Save one cropped plate image.
   *
   * @param result - The plate whose crop to download.
   * @param index - Its position in the list, used in the filename so several
   *   unreadable plates from one image do not collide.
   */
  const handleDownloadCrop = useCallback(
    async (result: DetectionResult, index: number): Promise<void> => {
      const url = fileUrl(result.plate_image_url);
      if (!url) {
        setDownloadError('Ảnh biển số đã cắt không có sẵn để tải về.');
        return;
      }

      setDownloadError(null);
      setDownloadingCropIndex(index);
      try {
        const name = toFilenameFragment(
          result.plate_number,
          `bien-so-${index + 1}`,
        );
        await downloadRemoteFile(url, `${name}.jpg`);
      } catch (caught) {
        reportDownloadFailure(caught);
      } finally {
        setDownloadingCropIndex(null);
      }
    },
    [reportDownloadFailure],
  );

  const [selectedDetailRecord, setSelectedDetailRecord] = useState<DetectionHistory | null>(null);

  const handleOpenDetailModal = useCallback(
    (result: DetectionResult, index: number) => {
      if (!response) return;
      const historyRecord: DetectionHistory = {
        id: index + 1,
        input_type: 'image',
        image_path: response.image_url,
        plate_image_path: result.plate_image_url,
        plate_number: result.plate_number,
        plate_display: result.plate_display,
        raw_ocr_text: result.raw_ocr_text,
        confidence: result.detection_confidence,
        ocr_confidence: result.ocr_confidence,
        plate_color: result.plate_color,
        plate_color_confidence: result.plate_color_confidence,
        plate_kind: result.plate_kind,
        plate_line_count: result.plate_line_count,
        is_valid_format: result.is_valid_format,
        processing_time: result.processing_time,
        bbox_x: result.bbox.x,
        bbox_y: result.bbox.y,
        bbox_w: result.bbox.width,
        bbox_h: result.bbox.height,
        bbox: result.bbox,
        video_time_seconds: null,
        detected_time: new Date().toISOString(),
        created_at: new Date().toISOString(),
        source_job_id: '',
      };
      setSelectedDetailRecord(historyRecord);
    },
    [response],
  );

  const annotatedImageUrl = response
    ? (fileUrl(response.image_url) ?? previewUrl)
    : null;
  const hasResults = response !== null && response.results.length > 0;

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-lg font-semibold text-content">Nhận dạng biển số từ ảnh</h1>
        <p className="mt-1 text-sm text-content-muted">
          Tải lên một ảnh chụp phương tiện để phát hiện và đọc biển số. Hỗ trợ ảnh
          JPG, PNG, WebP, BMP với dung lượng tối đa 10 MB.
        </p>
      </header>

      <div className="grid gap-5 lg:grid-cols-2">
        {/* ---- Upload column -------------------------------------------- */}
        <div className="space-y-5">
          <PageSection
            title="Tải ảnh lên"
            subtitle="Kéo thả hoặc bấm để chọn ảnh từ máy tính"
          >
            <ImageUploadPanel
              selectedFile={selectedFile}
              // Once results exist the annotated view below is the image to
              // look at; showing the same picture twice only wastes the screen.
              previewUrl={response ? null : previewUrl}
              onFileSelect={handleFileSelect}
              onClear={handleClear}
              isDetecting={isDetecting}
              uploadProgress={uploadProgress}
            />
          </PageSection>

          {annotatedImageUrl && response && (
            <PageSection
              title="Ảnh đã đánh dấu"
              subtitle={
                hasResults
                  ? 'Di chuột lên khung hoặc lên một kết quả để làm nổi bật biển số tương ứng'
                  : 'Không có biển số nào được đánh dấu trên ảnh này'
              }
              actions={
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => void handleDownloadAnnotated()}
                  isLoading={isDownloadingAnnotated}
                  loadingText="Đang xuất…"
                  leftIcon={<Download className="h-3.5 w-3.5" />}
                >
                  Tải ảnh kết quả
                </Button>
              }
            >
              <BoundingBoxOverlay
                imageUrl={annotatedImageUrl}
                alt="Ảnh đã nhận dạng, có đánh dấu vị trí các biển số"
                results={response.results}
                imageWidth={response.image_width}
                imageHeight={response.image_height}
                activeIndex={activeIndex}
                onActiveIndexChange={setActiveIndex}
              />
            </PageSection>
          )}
        </div>

        {/* ---- Result column -------------------------------------------- */}
        <PageSection
          title="Kết quả nhận dạng"
          subtitle={
            hasResults
              ? `Tìm thấy ${response.plate_count} biển số trong ảnh này`
              : undefined
          }
        >
          <div className="space-y-4">
            {downloadError && (
              <InlineError
                message={downloadError}
                onDismiss={() => setDownloadError(null)}
              />
            )}

            {isDetecting ? (
              // -- loading --------------------------------------------------
              <LoadingState message="Đang phát hiện và đọc biển số… Mô hình chạy trên CPU nên bước này có thể mất vài giây." />
            ) : error ? (
              // -- error ----------------------------------------------------
              <ErrorState
                title="Không nhận dạng được ảnh"
                message={error.message}
                requestId={error.request_id}
                onRetry={
                  selectedFile ? () => void runDetection(selectedFile) : undefined
                }
                retryLabel="Thử lại"
              />
            ) : !response ? (
              // -- empty: nothing has been submitted yet --------------------
              <EmptyState
                icon={<ImageIcon className="h-6 w-6" />}
                title="Chưa có kết quả"
                description="Kéo thả hoặc chọn một ảnh ở khung bên trái — hệ thống nhận dạng ngay khi ảnh được chọn."
              />
            ) : !hasResults ? (
              // -- empty: the image was processed but held no plate ---------
              // Reported with HTTP 200, so this is an outcome and not a
              // failure; it is styled as an empty state accordingly.
              <EmptyState
                icon={<SearchX className="h-6 w-6" />}
                title="Không tìm thấy biển số nào trong ảnh"
                description="Ảnh đã được xử lý thành công nhưng không phát hiện được biển số. Hãy thử ảnh chụp gần hơn, rõ nét hơn, hoặc ảnh có biển số ít bị che khuất."
                action={
                  <Button variant="secondary" onClick={handleClear}>
                    Chọn ảnh khác
                  </Button>
                }
              />
            ) : (
              // -- success --------------------------------------------------
              <>
                <DetectionSummary response={response} />

                <ul className="space-y-3">
                  {response.results.map((result, index) => (
                    <li key={`${result.plate_number ?? 'unread'}-${index}`}>
                      <PlateResultCard
                        result={result}
                        index={index}
                        plateImageUrl={fileUrl(result.plate_image_url)}
                        isActive={activeIndex === index}
                        onActiveChange={setActiveIndex}
                        onDownloadCrop={(plate, position) =>
                          void handleDownloadCrop(plate, position)
                        }
                        isDownloadingCrop={downloadingCropIndex === index}
                        onOpenDetails={handleOpenDetailModal}
                      />
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        </PageSection>
      </div>

      {/* Detection Details Modal (Deep Navy 2-column view) */}
      <HistoryDetailModal
        record={selectedDetailRecord}
        onClose={() => setSelectedDetailRecord(null)}
        onDelete={() => setSelectedDetailRecord(null)}
      />
    </div>
  );
}
