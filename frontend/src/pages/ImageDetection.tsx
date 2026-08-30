/**
 * Multi-Image Batch Detection Page (2-Column Responsive Layout).
 *
 * Supports single & multi-image batch queueing with filmstrip switching and instant inspection.
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
  const [files, setFiles] = useState<File[]>([]);
  const [activeIndex, setActiveIndex] = useState<number>(0);
  const [previews, setPreviews] = useState<Record<number, string>>({});
  const [responses, setResponses] = useState<Record<number, DetectionResponse>>({});
  const [statusMap, setStatusMap] = useState<Record<number, 'detecting' | 'completed' | 'error'>>({});
  const [errorsMap, setErrorsMap] = useState<Record<number, ApiError>>({});

  const [isDetecting, setIsDetecting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [activePlateIndex, setActivePlateIndex] = useState<number | null>(null);
  const [downloadingCropIndex, setDownloadingCropIndex] = useState<number | null>(null);
  const [isDownloadingAnnotated, setIsDownloadingAnnotated] = useState(false);
  const [selectedDetailRecord, setSelectedDetailRecord] = useState<DetectionHistory | null>(null);

  const previewUrlsRef = useRef<Record<number, string>>({});
  const abortControllersRef = useRef<Record<number, AbortController>>({});

  // Cleanup object URLs on unmount
  useEffect(() => {
    return () => {
      Object.values(previewUrlsRef.current).forEach((url) => URL.revokeObjectURL(url));
      Object.values(abortControllersRef.current).forEach((c) => c.abort());
    };
  }, []);

  const runDetectionForFile = useCallback(
    async (file: File, fileIndex: number): Promise<void> => {
      abortControllersRef.current[fileIndex]?.abort();
      const controller = new AbortController();
      abortControllersRef.current[fileIndex] = controller;

      setStatusMap((prev) => ({ ...prev, [fileIndex]: 'detecting' }));
      if (fileIndex === activeIndex) {
        setIsDetecting(true);
        setUploadProgress(0);
      }

      try {
        const payload = await detectImage(
          file,
          (progress) => {
            if (fileIndex === activeIndex) setUploadProgress(progress);
          },
          controller.signal,
        );
        if (controller.signal.aborted) return;

        setResponses((prev) => ({ ...prev, [fileIndex]: payload }));
        setStatusMap((prev) => ({ ...prev, [fileIndex]: 'completed' }));
      } catch (caught) {
        if (controller.signal.aborted) return;
        const err = isApiError(caught) ? caught : UNEXPECTED_ERROR;
        setErrorsMap((prev) => ({ ...prev, [fileIndex]: err }));
        setStatusMap((prev) => ({ ...prev, [fileIndex]: 'error' }));
      } finally {
        if (!controller.signal.aborted && fileIndex === activeIndex) {
          setIsDetecting(false);
        }
      }
    },
    [activeIndex],
  );

  // Add multiple files to batch
  const handleAddFiles = useCallback(
    (newFiles: File[]): void => {
      if (newFiles.length === 0) return;

      const startIndex = files.length;
      const nextFiles = [...files, ...newFiles];
      setFiles(nextFiles);

      const nextPreviews = { ...previews };
      newFiles.forEach((file, i) => {
        const idx = startIndex + i;
        const url = URL.createObjectURL(file);
        previewUrlsRef.current[idx] = url;
        nextPreviews[idx] = url;
      });
      setPreviews(nextPreviews);

      if (files.length === 0) {
        setActiveIndex(0);
      }

      // Trigger detection for all newly added files
      newFiles.forEach((file, i) => {
        void runDetectionForFile(file, startIndex + i);
      });
    },
    [files, previews, runDetectionForFile],
  );

  const handleSelectIndex = useCallback(
    (index: number) => {
      setActiveIndex(index);
      setActivePlateIndex(null);
      const isFileRunning = statusMap[index] === 'detecting';
      setIsDetecting(isFileRunning);
      // If not started yet, trigger
      if (files[index] && !responses[index] && !statusMap[index]) {
        void runDetectionForFile(files[index], index);
      }
    },
    [files, responses, statusMap, runDetectionForFile],
  );

  const handleRemoveFile = useCallback(
    (removeIdx: number) => {
      abortControllersRef.current[removeIdx]?.abort();
      if (previewUrlsRef.current[removeIdx]) {
        URL.revokeObjectURL(previewUrlsRef.current[removeIdx]);
        delete previewUrlsRef.current[removeIdx];
      }

      const nextFiles = files.filter((_, i) => i !== removeIdx);
      setFiles(nextFiles);

      // Shift maps
      const shiftMap = <T,>(map: Record<number, T>): Record<number, T> => {
        const res: Record<number, T> = {};
        Object.entries(map).forEach(([key, val]) => {
          const k = Number(key);
          if (k < removeIdx) res[k] = val;
          else if (k > removeIdx) res[k - 1] = val;
        });
        return res;
      };

      setPreviews(shiftMap(previews));
      setResponses(shiftMap(responses));
      setStatusMap(shiftMap(statusMap));
      setErrorsMap(shiftMap(errorsMap));

      if (nextFiles.length === 0) {
        setActiveIndex(0);
      } else if (activeIndex >= nextFiles.length) {
        setActiveIndex(nextFiles.length - 1);
      }
    },
    [files, previews, responses, statusMap, errorsMap, activeIndex],
  );

  const handleClearAll = useCallback((): void => {
    Object.values(previewUrlsRef.current).forEach((url) => URL.revokeObjectURL(url));
    previewUrlsRef.current = {};
    Object.values(abortControllersRef.current).forEach((c) => c.abort());
    abortControllersRef.current = {};

    setFiles([]);
    setActiveIndex(0);
    setPreviews({});
    setResponses({});
    setStatusMap({});
    setErrorsMap({});
    setIsDetecting(false);
    setDownloadError(null);
    setActivePlateIndex(null);
  }, []);

  const activeResponse = responses[activeIndex] ?? null;
  const activeError = errorsMap[activeIndex] ?? null;
  const activePreview = previews[activeIndex] ?? null;
  const currentAnnotatedUrl = activeResponse
    ? (fileUrl(activeResponse.image_url) ?? activePreview)
    : activePreview;
  const hasResults = activeResponse !== null && activeResponse.results.length > 0;

  const plateCountMap: Record<number, number> = {};
  Object.entries(responses).forEach(([idx, resp]) => {
    plateCountMap[Number(idx)] = resp.plate_count;
  });

  const handleDownloadAnnotated = useCallback(async (): Promise<void> => {
    if (!activeResponse || !activeResponse.results.length) return;
    const url = fileUrl(activeResponse.image_url) ?? activePreview;
    if (!url) return;

    setIsDownloadingAnnotated(true);
    setDownloadError(null);
    try {
      const firstPlate = activeResponse.results[0]?.plate_number;
      const baseName = toFilenameFragment(firstPlate, `ket-qua-${activeIndex + 1}`);
      await downloadAnnotatedImage(
        url,
        activeResponse.results,
        activeResponse.image_width,
        activeResponse.image_height,
        `${baseName}-danh-dau.jpg`,
      );
    } catch {
      setDownloadError('Không thể tải ảnh đã vẽ khung. Vui lòng thử lại.');
    } finally {
      setIsDownloadingAnnotated(false);
    }
  }, [activeResponse, activePreview, activeIndex]);

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
      if (!activeResponse) return;
      const historyRecord: DetectionHistory = {
        id: index + 1,
        input_type: 'image',
        image_path: activeResponse.image_url,
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
    [activeResponse],
  );

  return (
    <div className="space-y-4">
      {/* 2-Column Responsive Layout */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        {/* Left Column: Upload Carousel & Big Visual Box (7 cols) */}
        <div className="space-y-3.5 lg:col-span-7">
          <ImageUploadPanel
            files={files}
            activeIndex={activeIndex}
            onSelectIndex={handleSelectIndex}
            onAddFiles={handleAddFiles}
            onRemoveFile={handleRemoveFile}
            onClearAll={handleClearAll}
            isDetecting={isDetecting}
            uploadProgress={uploadProgress}
            statusMap={statusMap}
            plateCountMap={plateCountMap}
          />

          {/* Annotated Visual Box */}
          {files.length > 0 && currentAnnotatedUrl && (
            <div className="relative overflow-hidden rounded-2xl border border-border/80 bg-surface shadow-md">
              <div className="flex items-center justify-between border-b border-border/60 bg-surface-raised/50 px-4 py-2.5">
                <span className="text-xs font-bold uppercase tracking-wider text-content-muted">
                  Ảnh #{activeIndex + 1}: {files[activeIndex]?.name}
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
                {activeResponse && hasResults ? (
                  <BoundingBoxOverlay
                    imageUrl={currentAnnotatedUrl}
                    alt={`Ảnh đã nhận dạng #${activeIndex + 1}`}
                    results={activeResponse.results}
                    imageWidth={activeResponse.image_width}
                    imageHeight={activeResponse.image_height}
                    activeIndex={activePlateIndex}
                    onActiveIndexChange={setActivePlateIndex}
                  />
                ) : (
                  <img
                    src={currentAnnotatedUrl}
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
              <LoadingState message={`Đang nhận dạng ảnh #${activeIndex + 1} (YOLO11 + PaddleOCR trên CPU)…`} />
            </Card>
          ) : activeError ? (
            <ErrorState
              title="Không nhận dạng được ảnh"
              message={activeError.message}
              requestId={activeError.request_id}
              onRetry={files[activeIndex] ? () => void runDetectionForFile(files[activeIndex]!, activeIndex) : undefined}
              retryLabel="Thử lại"
            />
          ) : !activeResponse ? (
            <Card title="Kết quả nhận dạng">
              <EmptyState
                icon={<ImageIcon className="h-6 w-6" />}
                title="Chưa có kết quả"
                description="Kéo thả hoặc chọn một hoặc nhiều ảnh ở khung bên trái để bắt đầu nhận dạng hàng loạt."
              />
            </Card>
          ) : !hasResults ? (
            <Card title="Kết quả nhận dạng">
              <EmptyState
                icon={<SearchX className="h-6 w-6" />}
                title="Không tìm thấy biển số nào"
                description="Ảnh này đã xử lý xong nhưng không phát hiện được biển số xe hợp lệ."
              />
            </Card>
          ) : (
            <div className="space-y-3">
              {/* Summary Stats */}
              <DetectionSummary response={activeResponse} />

              {/* Scrollable Plate List */}
              <div className="space-y-2.5 max-h-[500px] overflow-y-auto pr-1">
                {activeResponse.results.map((result, index) => (
                  <PlateResultCard
                    key={`${result.plate_number ?? 'unread'}-${index}`}
                    result={result}
                    index={index}
                    plateImageUrl={fileUrl(result.plate_image_url)}
                    isActive={activePlateIndex === index}
                    onActiveChange={setActivePlateIndex}
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
