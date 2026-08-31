/** REST client for the ALPR backend — the only module that knows about axios/HTTP. */

import axios, {
  AxiosError,
  type AxiosInstance,
  type AxiosProgressEvent,
  type AxiosRequestConfig,
} from 'axios';

import type {
  ApiError,
  ApiErrorResponse,
  DetectionJob,
  DetectionResponse,
  DetectionHistory,
  HistoryListResponse,
  HistoryQuery,
} from '@/types';

const API_PREFIX = '/api';
const DEFAULT_TIMEOUT_MS = 60_000;

/** Read the server origin from build-time env (empty = same-origin). */
function resolveOrigin(): string {
  const configured = (
    import.meta.env.VITE_API_URL ??
    import.meta.env.VITE_API_BASE_URL ??
    ''
  ).trim();
  // Strip /api suffix if present so root /health stays reachable
  return configured.replace(/\/+$/, '').replace(/\/api$/, '');
}

/** Read request timeout from build-time env (default: 60s). */
function resolveTimeoutMs(): number {
  const raw = import.meta.env.VITE_API_TIMEOUT_MS?.trim();
  if (!raw) {
    return DEFAULT_TIMEOUT_MS;
  }
  const parsed = Number.parseInt(raw, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_TIMEOUT_MS;
}

/** Vietnamese fallback messages by HTTP status (used when backend has no message). */
const STATUS_MESSAGES: Readonly<Record<number, string>> = {
  400: 'Dữ liệu gửi lên không hợp lệ. Vui lòng kiểm tra lại tệp và thử lại.',
  401: 'Phiên làm việc đã hết hạn. Vui lòng đăng nhập lại.',
  403: 'Bạn không có quyền thực hiện thao tác này.',
  404: 'Không tìm thấy dữ liệu yêu cầu.',
  409: 'Thao tác xung đột với trạng thái hiện tại của dữ liệu.',
  413: 'Tệp tải lên vượt quá dung lượng cho phép.',
  415: 'Định dạng tệp không được hỗ trợ.',
  422: 'Dữ liệu gửi lên không đúng định dạng yêu cầu.',
  429: 'Bạn đang gửi quá nhiều yêu cầu. Vui lòng chờ một lát rồi thử lại.',
  500: 'Máy chủ gặp sự cố khi xử lý yêu cầu. Vui lòng thử lại sau.',
  502: 'Không kết nối được tới dịch vụ xử lý. Vui lòng thử lại sau.',
  503: 'Dịch vụ đang tạm thời quá tải. Vui lòng thử lại sau.',
  504: 'Máy chủ xử lý quá lâu và đã hết thời gian chờ.',
};

const NETWORK_ERROR_MESSAGE =
  'Không kết nối được tới máy chủ. Vui lòng kiểm tra backend có đang chạy ở http://localhost:8000 hay không.';
const TIMEOUT_ERROR_MESSAGE =
  'Yêu cầu xử lý quá lâu và đã hết thời gian chờ. Ảnh hoặc video có thể quá lớn.';
const CANCELLED_ERROR_MESSAGE = 'Yêu cầu đã bị huỷ.';
const UNKNOWN_ERROR_MESSAGE = 'Đã xảy ra lỗi không xác định. Vui lòng thử lại.';

/** Normalise any thrown value into a display-ready ApiError. */
function normalizeError(error: unknown): ApiError {
  if (axios.isCancel(error)) {
    return { status: 0, message: CANCELLED_ERROR_MESSAGE, code: 'CANCELLED' };
  }

  if (error instanceof AxiosError) {
    const requestId =
      (error.response?.headers?.['x-request-id'] as string | undefined) ??
      undefined;

    // No response at all: the request never reached the server.
    if (!error.response) {
      const isTimeout =
        error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT';
      return {
        status: 0,
        message: isTimeout ? TIMEOUT_ERROR_MESSAGE : NETWORK_ERROR_MESSAGE,
        code: error.code ?? 'NETWORK_ERROR',
        request_id: requestId,
      };
    }

    const { status } = error.response;
    const body = error.response.data as Partial<ApiErrorResponse> | undefined;

    return {
      status,
      message:
        body?.message ??
        STATUS_MESSAGES[status] ??
        `Yêu cầu thất bại với mã lỗi ${status}.`,
      code: body?.error,
      request_id: body?.request_id ?? requestId,
    };
  }

  return { status: 0, message: UNKNOWN_ERROR_MESSAGE };
}

/** Type guard for ApiError. */
export function isApiError(value: unknown): value is ApiError {
  return (
    typeof value === 'object' &&
    value !== null &&
    'status' in value &&
    'message' in value
  );
}

/** Extract a display-ready Vietnamese message from any caught value. */
export function getErrorMessage(error: unknown): string {
  if (isApiError(error)) {
    return error.message;
  }
  return UNKNOWN_ERROR_MESSAGE;
}

/** Generate a per-request correlation id (X-Request-ID). */
function createRequestId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `req-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

/** Server origin, without a trailing slash. Empty means same-origin. */
const ORIGIN = resolveOrigin();

const client: AxiosInstance = axios.create({
  // Base URL set to origin; /api prefix attached per endpoint
  baseURL: ORIGIN,
  timeout: resolveTimeoutMs(),
  headers: { Accept: 'application/json' },
});

// Attach a correlation id to every outgoing request.
client.interceptors.request.use((config) => {
  config.headers.set('X-Request-ID', createRequestId());
  return config;
});

// Unwrap successful responses; normalise every failure into an ApiError.
client.interceptors.response.use(
  (response) => response,
  (error: unknown) => Promise.reject(normalizeError(error)),
);

/** Callback reporting upload progress as a ratio from 0.0 to 1.0. */
export type UploadProgressHandler = (progress: number) => void;

/** Build an axios config that reports upload progress. */
function uploadConfig(
  onProgress?: UploadProgressHandler,
  signal?: AbortSignal,
): AxiosRequestConfig {
  return {
    headers: { 'Content-Type': 'multipart/form-data' },
    signal,
    onUploadProgress: onProgress
      ? (event: AxiosProgressEvent) => {
          // Check total exists before calculating ratio
          if (typeof event.total === 'number' && event.total > 0) {
            onProgress(event.loaded / event.total);
          }
        }
      : undefined,
  };
}

/** Detect and recognise plates in a single uploaded image. */
export async function detectImage(
  file: File,
  onProgress?: UploadProgressHandler,
  signal?: AbortSignal,
): Promise<DetectionResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await client.post<DetectionResponse>(
    `${API_PREFIX}/detect/image`,
    formData,
    uploadConfig(onProgress, signal),
  );
  return response.data;
}

/** Queue a video for async background processing; poll getJob for progress. */
export async function detectVideo(
  file: File,
  onProgress?: UploadProgressHandler,
  signal?: AbortSignal,
): Promise<DetectionJob> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await client.post<DetectionJob>(
    `${API_PREFIX}/detect/video`,
    formData,
    uploadConfig(onProgress, signal),
  );
  return response.data;
}

/** Detect plates in a single frame synchronously (live preview). */
export async function detectFrame(
  frame: Blob,
  jobId?: string | null,
  signal?: AbortSignal,
  readText = true,
): Promise<DetectionResponse> {
  const formData = new FormData();
  formData.append('file', frame, 'frame.jpg');
  if (jobId) {
    formData.append('job_id', jobId);
  }
  if (!readText) {
    formData.append('read_text', 'false');
  }

  const response = await client.post<DetectionResponse>(
    `${API_PREFIX}/detect/frame`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' }, signal },
  );
  return response.data;
}

/** Fetch one page of detection history. */
export async function getHistory(
  query: HistoryQuery = {},
  signal?: AbortSignal,
): Promise<HistoryListResponse> {
  const response = await client.get<HistoryListResponse>(`${API_PREFIX}/history`, {
    params: query,
    signal,
  });
  return response.data;
}

/** Fetch a single history record by id. */
export async function getHistoryDetail(
  id: number,
  signal?: AbortSignal,
): Promise<DetectionHistory> {
  const response = await client.get<DetectionHistory>(`${API_PREFIX}/history/${id}`, {
    signal,
  });
  return response.data;
}

/** Fetch current state of an async job (poll until completed/failed). */
export async function getJob(
  jobId: string,
  signal?: AbortSignal,
): Promise<DetectionJob> {
  const response = await client.get<DetectionJob>(`${API_PREFIX}/jobs/${jobId}`, { signal });
  return response.data;
}

/** Delete a history record and its associated image files (FR-5.1). */
export async function deleteHistory(
  id: number,
  signal?: AbortSignal,
): Promise<void> {
  await client.delete(`${API_PREFIX}/history/${id}`, { signal });
}

/** Build the URL for CSV export with the given filters (streams to disk). */
export function exportHistoryUrl(filters: HistoryQuery = {}): string {
  const params = new URLSearchParams();

  for (const [key, value] of Object.entries(filters)) {
    // Omit pagination params for complete CSV export
    if (key === 'page' || key === 'page_size') {
      continue;
    }
    if (value === undefined || value === null || value === '') {
      continue;
    }
    params.append(key, String(value));
  }

  const query = params.toString();
  return `${ORIGIN}${API_PREFIX}/history/export${query ? `?${query}` : ''}`;
}

/** Resolve a stored-file path into a loadable URL (NFR-S2). */
export function fileUrl(path: string | null | undefined): string | null {
  if (!path) {
    return null;
  }
  if (/^https?:\/\//i.test(path)) {
    return path;
  }
  const rooted = path.startsWith('/') ? path : `/${path}`;
  return `${ORIGIN}${rooted}`;
}

export { client as apiClient };
