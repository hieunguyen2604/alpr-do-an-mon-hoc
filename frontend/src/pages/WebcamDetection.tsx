/** Real-time live webcam license plate detection page (FR-3.1). */

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  Camera,
  CameraOff,
  CheckCircle2,
  Copy,
  Gauge,
  Maximize2,
  Scan,
  Sparkles,
  Zap,
} from 'lucide-react';

import HistoryDetailModal from '@/components/history/HistoryDetailModal';
import { Button, EmptyState } from '@/components/ui';
import { cn } from '@/lib/cn';
import { formatPlateNumber } from '@/lib/format';
import { detectFrame, fileUrl } from '@/services/api';
import type { DetectionHistory, DetectionResponse, DetectionResult } from '@/types';

interface LivePlateEntry {
  plateNumber: string;
  plateDisplay?: string | null;
  plateImageUrl?: string | null;
  confidence: number;
  ocrConfidence: number;
  plateColor?: string | null;
  isValidFormat: boolean;
  seenCount: number;
  lastSeenTime: Date;
  processingTimeMs: number;
  result: DetectionResult;
  historyRecord: DetectionHistory;
}

export default function WebcamDetection(): JSX.Element {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionJobId, setSessionJobId] = useState<string | null>(null);
  const [fps, setFps] = useState<number>(0);
  const [lastLatencyMs, setLastLatencyMs] = useState<number>(0);
  const [totalFramesSent, setTotalFramesSent] = useState<number>(0);
  const [detectedPlates, setDetectedPlates] = useState<Map<string, LivePlateEntry>>(new Map());
  const [selectedDetailRecord, setSelectedDetailRecord] = useState<DetectionHistory | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const overlayCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const isProcessingRef = useRef(false);
  const sessionJobIdRef = useRef<string | null>(null);
  const animationFrameIdRef = useRef<number | null>(null);
  const lastFrameTimeRef = useRef<number>(Date.now());
  const frameCounterRef = useRef<number>(0);
  const activeStreamActiveRef = useRef(false);

  // Sync state ref
  useEffect(() => {
    sessionJobIdRef.current = sessionJobId;
  }, [sessionJobId]);

  const stopWebcam = useCallback(() => {
    activeStreamActiveRef.current = false;
    if (animationFrameIdRef.current) {
      cancelAnimationFrame(animationFrameIdRef.current);
      animationFrameIdRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    if (overlayCanvasRef.current) {
      const ctx = overlayCanvasRef.current.getContext('2d');
      ctx?.clearRect(0, 0, overlayCanvasRef.current.width, overlayCanvasRef.current.height);
    }
    setIsStreaming(false);
    isProcessingRef.current = false;
  }, []);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      stopWebcam();
    };
  }, [stopWebcam]);

  // Draw bounding boxes on the overlay canvas
  const drawOverlayBoxes = useCallback((results: DetectionResult[], vidWidth: number, vidHeight: number) => {
    const canvas = overlayCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    if (canvas.width !== vidWidth || canvas.height !== vidHeight) {
      canvas.width = vidWidth;
      canvas.height = vidHeight;
    }

    ctx.clearRect(0, 0, vidWidth, vidHeight);

    for (const res of results) {
      const { x, y, width, height } = res.bbox;
      const isValid = res.is_valid_format;
      const strokeColor = isValid ? '#10B981' : '#F59E0B';
      const fillColor = isValid ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)';

      // Box
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = 3;
      ctx.fillStyle = fillColor;
      ctx.beginPath();
      ctx.roundRect(x, y, width, height, 8);
      ctx.fill();
      ctx.stroke();

      // Badge
      const text = res.plate_display || res.plate_number || 'Đang quét…';
      ctx.font = 'bold 14px monospace';
      const textWidth = ctx.measureText(text).width;
      const badgeH = 24;
      const badgeW = textWidth + 16;
      const badgeY = y > badgeH + 6 ? y - badgeH - 4 : y + height + 4;

      ctx.fillStyle = strokeColor;
      ctx.beginPath();
      ctx.roundRect(x, badgeY, badgeW, badgeH, 6);
      ctx.fill();

      ctx.fillStyle = '#090D16';
      ctx.fillText(text, x + 8, badgeY + 17);
    }
  }, []);

  // Frame processing loop
  const processLiveFrame = useCallback(async () => {
    if (!activeStreamActiveRef.current || !videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;

    // Check if video is ready
    if (video.readyState < 2 || video.videoWidth === 0 || video.videoHeight === 0) {
      if (activeStreamActiveRef.current) {
        animationFrameIdRef.current = requestAnimationFrame(processLiveFrame);
      }
      return;
    }

    // Single-slot frame skipping: if previous request is still in flight, skip this frame
    if (!isProcessingRef.current) {
      isProcessingRef.current = true;

      const vidW = video.videoWidth;
      const vidH = video.videoHeight;
      if (canvas.width !== vidW || canvas.height !== vidH) {
        canvas.width = vidW;
        canvas.height = vidH;
      }

      const ctx = canvas.getContext('2d', { willReadFrequently: true });
      if (ctx) {
        ctx.drawImage(video, 0, 0, vidW, vidH);

        canvas.toBlob(
          async (blob) => {
            if (!blob || !activeStreamActiveRef.current) {
              isProcessingRef.current = false;
              return;
            }

            const startTime = performance.now();
            try {
              const resp: DetectionResponse = await detectFrame(
                blob,
                sessionJobIdRef.current,
                undefined,
                true,
              );

              if (activeStreamActiveRef.current) {
                const latency = Math.round(performance.now() - startTime);
                setLastLatencyMs(latency);
                setTotalFramesSent((prev) => prev + 1);

                if (resp.job_id && !sessionJobIdRef.current) {
                  setSessionJobId(resp.job_id);
                }

                // Update FPS calculation
                frameCounterRef.current += 1;
                const now = Date.now();
                if (now - lastFrameTimeRef.current >= 1000) {
                  setFps(frameCounterRef.current);
                  frameCounterRef.current = 0;
                  lastFrameTimeRef.current = now;
                }

                // Draw bounding boxes on live overlay
                drawOverlayBoxes(resp.results, vidW, vidH);

                // Update detected plates deduplication feed
                if (resp.results.length > 0) {
                  setDetectedPlates((prevMap) => {
                    const nextMap = new Map(prevMap);
                    resp.results.forEach((r) => {
                      const plateKey = r.plate_number || `unknown-${Date.now()}`;
                      const existing = nextMap.get(plateKey);

                      const historyRec: DetectionHistory = {
                        id: (existing?.seenCount ?? 0) + 1,
                        input_type: 'webcam',
                        image_path: null,
                        plate_image_path: r.plate_image_url,
                        plate_number: r.plate_number,
                        plate_display: r.plate_display,
                        raw_ocr_text: r.raw_ocr_text,
                        confidence: r.detection_confidence,
                        ocr_confidence: r.ocr_confidence,
                        plate_color: r.plate_color,
                        plate_color_confidence: r.plate_color_confidence,
                        plate_kind: r.plate_kind,
                        plate_line_count: r.plate_line_count,
                        is_valid_format: r.is_valid_format,
                        processing_time: r.processing_time ?? (latency / 1000),
                        bbox_x: r.bbox.x,
                        bbox_y: r.bbox.y,
                        bbox_w: r.bbox.width,
                        bbox_h: r.bbox.height,
                        bbox: r.bbox,
                        video_time_seconds: null,
                        detected_time: new Date().toISOString(),
                        created_at: new Date().toISOString(),
                        source_job_id: resp.job_id || '',
                      };

                      nextMap.set(plateKey, {
                        plateNumber: plateKey,
                        plateDisplay: r.plate_display,
                        plateImageUrl: r.plate_image_url,
                        confidence: r.detection_confidence,
                        ocrConfidence: r.ocr_confidence ?? 0,
                        plateColor: r.plate_color,
                        isValidFormat: r.is_valid_format,
                        seenCount: (existing?.seenCount ?? 0) + 1,
                        lastSeenTime: new Date(),
                        processingTimeMs: latency,
                        result: r,
                        historyRecord: historyRec,
                      });
                    });
                    return nextMap;
                  });
                }
              }
            } catch {
              // Silently continue live capture
            } finally {
              isProcessingRef.current = false;
            }
          },
          'image/jpeg',
          0.85,
        );
      } else {
        isProcessingRef.current = false;
      }
    }

    if (activeStreamActiveRef.current) {
      animationFrameIdRef.current = requestAnimationFrame(processLiveFrame);
    }
  }, [drawOverlayBoxes]);

  const startWebcam = async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'environment',
        },
        audio: false,
      });

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      setIsStreaming(true);
      activeStreamActiveRef.current = true;
      lastFrameTimeRef.current = Date.now();
      frameCounterRef.current = 0;

      // Start processing loop
      animationFrameIdRef.current = requestAnimationFrame(processLiveFrame);
    } catch {
      setError('Không thể truy cập camera. Vui lòng cấp quyền truy cập webcam trong trình duyệt.');
      setIsStreaming(false);
    }
  };

  const handleCopy = (text: string) => {
    void navigator.clipboard.writeText(text);
    setCopiedKey(text);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const plateList = Array.from(detectedPlates.values()).sort(
    (a, b) => b.lastSeenTime.getTime() - a.lastSeenTime.getTime(),
  );

  const totalValid = plateList.filter((p) => p.isValidFormat).length;

  return (
    <div className="space-y-4">
      {/* 2-Column Layout */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        {/* Left: Video Viewport & Controls (7 cols) */}
        <div className="space-y-3.5 lg:col-span-7">
          {/* Top Control Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border/80 bg-surface p-3.5 shadow-sm">
            <div className="flex items-center gap-2.5">
              <span className="relative flex h-3 w-3">
                {isStreaming ? (
                  <>
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                    <span className="relative inline-flex h-3 w-3 rounded-full bg-emerald-500" />
                  </>
                ) : (
                  <span className="inline-flex h-3 w-3 rounded-full bg-content-muted/40" />
                )}
              </span>
              <span className="text-xs font-bold text-content uppercase tracking-wider">
                {isStreaming ? 'Webcam Đang Hoạt Động' : 'Webcam Đang Tắt'}
              </span>
            </div>

            <div className="flex items-center gap-2">
              {isStreaming ? (
                <Button
                  variant="danger"
                  size="sm"
                  onClick={stopWebcam}
                  leftIcon={<CameraOff className="h-4 w-4" />}
                  className="h-8 text-xs font-semibold"
                >
                  Dừng Webcam
                </Button>
              ) : (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => void startWebcam()}
                  leftIcon={<Camera className="h-4 w-4" />}
                  className="h-8 text-xs font-semibold shadow-md"
                >
                  Bật Webcam Quét Biển Số
                </Button>
              )}
            </div>
          </div>

          {error && (
            <div className="flex items-center gap-2 rounded-xl border border-danger/40 bg-danger/10 px-4 py-3 text-xs font-semibold text-danger">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          {/* Live Video Frame with Overlay Canvas */}
          <div className="relative overflow-hidden rounded-2xl border border-border/80 bg-surface-raised/60 shadow-md min-h-[380px] max-h-[520px] flex items-center justify-center">
            {/* Hidden canvas for extracting JPEG frames */}
            <canvas ref={canvasRef} className="hidden" />

            {/* Video element */}
            <video
              ref={videoRef}
              playsInline
              muted
              className={cn(
                'h-full w-full max-h-[500px] object-contain rounded-xl',
                !isStreaming && 'hidden',
              )}
            />

            {/* Canvas overlay for drawing real-time bounding boxes */}
            <canvas
              ref={overlayCanvasRef}
              className={cn(
                'pointer-events-none absolute inset-0 h-full w-full object-contain',
                !isStreaming && 'hidden',
              )}
            />

            {!isStreaming && (
              <div className="flex flex-col items-center justify-center p-8 text-center space-y-3">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-surface border border-border text-primary shadow-sm">
                  <Camera className="h-8 w-8" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-content">Chế độ Nhận Dạng Thời Gian Thực Qua Webcam</p>
                  <p className="mt-1 text-xs text-content-muted max-w-sm">
                    Bật webcam laptop để quét và nhận diện biển số xe máy / ô tô trực tiếp theo thời gian thực (5+ FPS trên CPU).
                  </p>
                </div>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => void startWebcam()}
                  leftIcon={<Zap className="h-4 w-4" />}
                  className="mt-2"
                >
                  Bắt Đầu Quét
                </Button>
              </div>
            )}
          </div>

          {/* Live Performance HUD */}
          {isStreaming && (
            <div className="grid grid-cols-3 gap-2.5">
              <div className="flex items-center gap-2.5 rounded-xl border border-border/60 bg-surface px-3 py-2 text-xs">
                <Gauge className="h-4 w-4 text-primary" />
                <div>
                  <p className="text-[10px] uppercase font-bold text-content-muted">Tốc độ khung hình</p>
                  <p className="font-mono text-sm font-bold text-primary">{fps} FPS</p>
                </div>
              </div>

              <div className="flex items-center gap-2.5 rounded-xl border border-border/60 bg-surface px-3 py-2 text-xs">
                <Activity className="h-4 w-4 text-emerald-400" />
                <div>
                  <p className="text-[10px] uppercase font-bold text-content-muted">Độ trễ xử lý CPU</p>
                  <p className="font-mono text-sm font-bold text-emerald-400">{lastLatencyMs} ms</p>
                </div>
              </div>

              <div className="flex items-center gap-2.5 rounded-xl border border-border/60 bg-surface px-3 py-2 text-xs">
                <Sparkles className="h-4 w-4 text-amber-400" />
                <div>
                  <p className="text-[10px] uppercase font-bold text-content-muted">Khung hình đã quét</p>
                  <p className="font-mono text-sm font-bold text-amber-400">{totalFramesSent}</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right: Real-time Plate Feed & Inspection (5 cols) */}
        <div className="space-y-3.5 lg:col-span-5">
          {/* Summary Metric Cards */}
          <div className="grid grid-cols-2 gap-2.5">
            <div className="rounded-2xl border border-border/80 bg-surface p-3 shadow-sm">
              <p className="text-[11px] font-bold text-content-muted uppercase tracking-wider">Biển số phát hiện</p>
              <p className="mt-1 font-mono text-2xl font-extrabold text-sky-400">{plateList.length}</p>
              <p className="text-[10px] text-content-muted">Đã gộp trùng phiên</p>
            </div>

            <div className="rounded-2xl border border-border/80 bg-surface p-3 shadow-sm">
              <p className="text-[11px] font-bold text-content-muted uppercase tracking-wider">Hợp chuẩn TT 79</p>
              <p className="mt-1 font-mono text-2xl font-extrabold text-emerald-400">{totalValid}/{plateList.length}</p>
              <p className="text-[10px] text-content-muted">Đúng định dạng VN</p>
            </div>
          </div>

          {/* Live Feed List */}
          <div className="rounded-2xl border border-border/80 bg-surface p-3.5 shadow-sm space-y-3">
            <div className="flex items-center justify-between border-b border-border/60 pb-2.5">
              <span className="text-xs font-bold uppercase tracking-wider text-content">
                Danh Sách Biển Số Quét Được ({plateList.length})
              </span>
              {plateList.length > 0 && (
                <button
                  type="button"
                  onClick={() => setDetectedPlates(new Map())}
                  className="text-xs font-semibold text-danger hover:underline"
                >
                  Xoá danh sách
                </button>
              )}
            </div>

            {plateList.length === 0 ? (
              <div className="py-12">
                <EmptyState
                  icon={<Scan className="h-6 w-6" />}
                  title="Chưa có biển số nào"
                  description="Hướng camera về phía biển số xe — các biển số nhận dạng được sẽ tự động cập nhật tại đây."
                />
              </div>
            ) : (
              <div className="space-y-2.5 max-h-[460px] overflow-y-auto pr-1">
                {plateList.map((entry) => {
                  const isCopied = copiedKey === entry.plateNumber;
                  const cropUrl = fileUrl(entry.plateImageUrl);

                  return (
                    <div
                      key={entry.plateNumber}
                      onClick={() => setSelectedDetailRecord(entry.historyRecord)}
                      className={cn(
                        'group flex cursor-pointer items-center justify-between gap-3 rounded-xl border p-2.5 transition-all',
                        'border-border/80 bg-surface-raised/40 hover:border-primary/60 hover:bg-surface-raised/80 hover:shadow-sm',
                      )}
                    >
                      {/* Left: Plate Crop Image & Plate Monospace */}
                      <div className="flex items-center gap-3 min-w-0">
                        {cropUrl ? (
                          <img
                            src={cropUrl}
                            alt={entry.plateNumber}
                            className="h-10 w-16 rounded-lg border border-border bg-surface object-cover shadow-sm"
                          />
                        ) : (
                          <div className="flex h-10 w-16 items-center justify-center rounded-lg border border-dashed border-border bg-surface text-content-muted">
                            <Scan className="h-4 w-4" />
                          </div>
                        )}

                        <div className="min-w-0">
                          <div className="flex items-center gap-1.5">
                            <span className="font-mono text-sm font-extrabold tracking-wide text-primary">
                              {entry.plateDisplay || formatPlateNumber(entry.plateNumber)}
                            </span>
                            {entry.isValidFormat && (
                              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                            )}
                          </div>
                          <p className="text-[10px] text-content-muted">
                            OCR: {Math.round(entry.ocrConfidence * 100)}% · Xuất hiện {entry.seenCount} lần
                          </p>
                        </div>
                      </div>

                      {/* Right: Quick Copy & Detail trigger */}
                      <div className="flex items-center gap-1.5 shrink-0">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCopy(entry.plateNumber);
                          }}
                          className={cn(
                            'rounded-lg p-1.5 text-content-muted transition-colors',
                            'hover:bg-surface hover:text-content',
                            isCopied && 'text-emerald-400',
                          )}
                          title="Sao chép biển số"
                        >
                          <Copy className="h-3.5 w-3.5" />
                        </button>
                        <button
                          type="button"
                          className="rounded-lg p-1.5 text-content-muted transition-colors hover:bg-surface hover:text-primary"
                          title="Xem chi tiết"
                        >
                          <Maximize2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
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
