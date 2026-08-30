/**
 * Streamlined Image Detection Page (Ultra-compact 2-Column Responsive Layout).
 *
 * All content fits cleanly in a single screen viewport without unnecessary stacking or redundant headers.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { Download, Image as ImageIcon, SearchX } from 'lucide-react';

import {
  BoundingBoxOverlay,
  DetectionSummary,
  ImageUploadPanel,
  PlateResultCard,
  downloadAnnotatedImage,
  downloadRemoteFile,
  toFilenameFragment,
} from '@/components/detection/image';
import HistoryDetailModal from '@/components/history/HistoryDetailModal';
import { InlineError, LoadingState } from '@/components/StateViews';
import { Button, Card, EmptyState, ErrorState } from '@/components/ui';
import { detectImage, fileUrl, isApiError } from '@/services/api';
import type { ApiError, DetectionHistory, DetectionResponse, DetectionResult } from '@/types';

const UNEXPECTED_ERROR: ApiError = {
  status: 0,
  message:
    'Không nhận dạng được ảnh. Vui lòng thử lại, hoặc chọn một ảnh khác nếu lỗi vẫn tiếp diễn.',
};

export default function ImageDetection(): JSX.Element {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [response, setResponse] = useState<DetectionResponse | null>(null);
  const [isDetecting, setIsDetecting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<ApiError | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [downloadingCropIndex, setDownloadingCropIndex] = useState<number | null>(null);
  const [isDownloadingAnnotated, setIsDownloadingAnnotated] = useState(false);
  const [selectedDetailRecord, setSelectedDetailRecord] = useState<DetectionHistory | null>(null);

  const previewUrlRef = useRef<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => {
      if (previewUrlRef.current) {
        URL.revokeObjectURL(previewUrlRef.current);
      }
      abortRef.current?.abort();
    };
  }, []);

  const replacePreview = useCallback((file: File | null): void => {
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current);
      previewUrlRef.current = null;
    }
    const next = file ? URL.createObjectURL(file) : null;
    previewUrlRef.current = next;
    setPreviewUrl(next);
  }, []);

  const runDetection = useCallback(
    async (file: File): Promise<void> => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setIsDetecting(true);
      setError(null);
      setDownloadError(null);
      setResponse(null);
      setActiveIndex(null);
      setUploadProgress(0);

      try {
        const payload = await detectImage(
          file,
          setUploadProgress,
          controller.signal,
        );
        if (controller.signal.aborted) return;
        setResponse(payload);
      } catch (caught) {
        if (controller.signal.aborted) return;
        if (isApiError(caught)) {
          setError(caught);
        } else {
          setError(UNEXPECTED_ERROR);
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsDetecting(false);
        }
      }
    },
    [],
  );

  const handleFileSelect = useCallback(
    (file: File): void => {
      setSelectedFile(file);
      replacePreview(file);
      void runDetection(file);
    },
    [replacePreview, runDetection],
  );

  const handleClear = useCallback((): void => {
    abortRef.current?.abort();
    setSelectedFile(null);
    replacePreview(null);
    setResponse(null);
    setError(null);
    setDownloadError(null);
    setActiveIndex(null);
    setIsDetecting(false);
    setUploadProgress(0);
  }, [replacePreview]);

  const handleDownloadAnnotated = useCallback(async (): Promise<void> => {
    if (!response || !response.results.length) return;
    const url = fileUrl(response.image_url) ?? previewUrl;
    if (!url) return;

    setIsDownloadingAnnotated(true);
    setDownloadError(null);
    try {
      const firstPlate = response.results[0]?.plate_number;
      const baseName = toFilenameFragment(firstPlate, 'ket-qua');
      await downloadAnnotatedImage(
        url,
        response.results,
        response.image_width,
        response.image_height,
        `${baseName}-danh-dau.jpg`,
      );
    } catch {
      setDownloadError('Không thể tải ảnh đã vẽ khung. Vui lòng thử lại.');
    } finally {
      setIsDownloadingAnnotated(false);
    }
  }, [response, previewUrl]);

  const handleDownloadCrop = useCallback(
    async (result: DetectionResult, index: number): Promise<void> => {
      const url = fileUrl(result.plate_image_url);
      if (!url) return;

      setDownloadError(null);
      setDownloadingCropIndex(index);
      try {
        const name = toFilenameFragment(result.plate_number, `bien-so-${index + 1}`);
        await downloadRemoteFile(url, `${name}.jpg`);
      } catch {
        setDownloadError('Không thể tải ảnh cắt biển số. Vui lòng thử lại.');
      } finally {
        setDownloadingCropIndex(null);
      }
    },
    [],
  );

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
    : previewUrl;
  const hasResults = response !== null && response.results.length > 0;

  return (
    <div className="space-y-4">
      {/* 2-Column Responsive Layout */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        {/* Left Column: Upload Bar & Big Visual Canvas (7 cols) */}
        <div className="space-y-3.5 lg:col-span-7">
          <ImageUploadPanel
            selectedFile={selectedFile}
            onFileSelect={handleFileSelect}
            onClear={handleClear}
            isDetecting={isDetecting}
            uploadProgress={uploadProgress}
          />

          {/* Annotated Visual Box */}
          {selectedFile && annotatedImageUrl && (
            <div className="relative overflow-hidden rounded-2xl border border-border/80 bg-surface shadow-md">
              <div className="flex items-center justify-between border-b border-border/60 bg-surface-raised/50 px-4 py-2.5">
                <span className="text-xs font-bold uppercase tracking-wider text-content-muted">
                  Ảnh toàn cảnh & Bounding Box
                </span>
                {hasResults && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => void handleDownloadAnnotated()}
                    isLoading={isDownloadingAnnotated}
                    loadingText="Đang xuất…"
                    className="h-7 text-xs font-semibold text-primary hover:text-primary-hover"
                    leftIcon={<Download className="h-3.5 w-3.5" />}
                  >
                    Tải ảnh có khung
                  </Button>
                )}
              </div>

              <div className="p-2 bg-surface-raised/30 flex items-center justify-center min-h-[360px] max-h-[520px]">
                {response && hasResults ? (
                  <BoundingBoxOverlay
                    imageUrl={annotatedImageUrl}
                    alt="Ảnh đã nhận dạng"
                    results={response.results}
                    imageWidth={response.image_width}
                    imageHeight={response.image_height}
                    activeIndex={activeIndex}
                    onActiveIndexChange={setActiveIndex}
                  />
                ) : (
                  <img
                    src={annotatedImageUrl}
                    alt="Xem trước ảnh"
                    className="max-h-[480px] w-auto max-w-full rounded-xl object-contain shadow-inner"
                  />
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Metrics & Results Feed (5 cols) */}
        <div className="space-y-3.5 lg:col-span-5">
          {downloadError && (
            <InlineError
              message={downloadError}
              onDismiss={() => setDownloadError(null)}
            />
          )}

          {isDetecting ? (
            <Card>
              <LoadingState message="Đang phát hiện và đọc ký tự biển số (YOLO11 + PaddleOCR trên CPU)…" />
            </Card>
          ) : error ? (
            <ErrorState
              title="Không nhận dạng được ảnh"
              message={error.message}
              requestId={error.request_id}
              onRetry={selectedFile ? () => void runDetection(selectedFile) : undefined}
              retryLabel="Thử lại"
            />
          ) : !response ? (
            <Card title="Kết quả nhận dạng">
              <EmptyState
                icon={<ImageIcon className="h-6 w-6" />}
                title="Chưa có kết quả"
                description="Kéo thả hoặc chọn một ảnh ở khung bên trái — hệ thống sẽ tự động phát hiện và hiển thị kết quả tại đây."
              />
            </Card>
          ) : !hasResults ? (
            <Card title="Kết quả nhận dạng">
              <EmptyState
                icon={<SearchX className="h-6 w-6" />}
                title="Không tìm thấy biển số nào"
                description="Ảnh đã xử lý xong nhưng không phát hiện được biển số xe hợp lệ. Hãy thử lại với ảnh rõ nét hơn."
                action={
                  <Button variant="secondary" size="sm" onClick={handleClear}>
                    Chọn ảnh khác
                  </Button>
                }
              />
            </Card>
          ) : (
            <div className="space-y-3">
              {/* Summary Stats */}
              <DetectionSummary response={response} />

              {/* Scrollable Plate List */}
              <div className="space-y-2.5 max-h-[500px] overflow-y-auto pr-1">
                {response.results.map((result, index) => (
                  <PlateResultCard
                    key={`${result.plate_number ?? 'unread'}-${index}`}
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
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Detection Details Modal */}
      <HistoryDetailModal
        record={selectedDetailRecord}
        onClose={() => setSelectedDetailRecord(null)}
        onDelete={() => setSelectedDetailRecord(null)}
      />
    </div>
  );
}
