/**
 * REST client for the ALPR backend.
 *
 * This module is the only place in the frontend that knows about axios or HTTP
 * status codes. Components call the exported functions and receive either typed
 * data or a rejected promise carrying an {@link ApiError} — a normalised,
 * display-ready shape. That boundary is what keeps transport concerns out of
 * the pages.
 */

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

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const API_PREFIX = '/api';
const DEFAULT_TIMEOUT_MS = 60_000;

/**
 * Read the server origin from the build-time environment.
 *
 * Empty by default, which makes every request same-origin and relative: the
 * Vite dev server proxies them to the backend, and in production a reverse
 * proxy serves the bundle and the API from one host. No hostname is ever
 * hard-coded, so a deployment is configured rather than rebuilt.
 *
 * This is the **origin**, not the API base — the `/api` prefix is added
 * separately, because `GET /health` deliberately sits outside it.
 *
 * @returns The configured origin, without a trailing slash. May be empty.
 */
function resolveOrigin(): string {
  const configured = (
    import.meta.env.VITE_API_URL ??
    import.meta.env.VITE_API_BASE_URL ??
    ''
  ).trim();
  // A configured value ending in `/api` names the API base rather than the
  // origin. Strip the suffix so the health endpoint, which is not under it,
  // stays reachable.
  return configured.replace(/\/+$/, '').replace(/\/api$/, '');
}

/**
 * Read the request timeout from the build-time environment.
 *
 * Inference runs on CPU, so the default is generous. An unparsable or
 * non-positive value falls back to the default rather than disabling the
 * timeout, which would let a hung request spin forever.
 *
 * @returns Timeout in milliseconds.
 */
function resolveTimeoutMs(): number {
  const raw = import.meta.env.VITE_API_TIMEOUT_MS?.trim();
  if (!raw) {
    return DEFAULT_TIMEOUT_MS;
  }
  const parsed = Number.parseInt(raw, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_TIMEOUT_MS;
}

// ---------------------------------------------------------------------------
// Error normalisation
// ---------------------------------------------------------------------------

/**
 * Vietnamese fallback messages, by HTTP status.
 *
 * Used only when the backend did not supply its own message. The backend is
 * the better source — it knows what actually failed — so its text always wins.
 */
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

/**
 * Convert any thrown value into the single {@link ApiError} shape.
 *
 * Deliberately never reads `error.stack` or any server-side traceback: user
 * feedback must not leak internals. The correlation id is carried through
 * instead, which is what makes a report traceable in the server log.
 *
 * @param error - The value rejected by axios, of unknown type.
 * @returns A normalised, display-ready error.
 */
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

/**
 * Type guard for {@link ApiError}, for use in `catch` blocks.
 *
 * @param value - The caught value.
 * @returns `true` if the value is a normalised API error.
 */
export function isApiError(value: unknown): value is ApiError {
  return (
    typeof value === 'object' &&
    value !== null &&
    'status' in value &&
    'message' in value
  );
}

/**
 * Extract a display-ready Vietnamese message from any caught value.
 *
 * @param error - The caught value.
 * @returns A message safe to render in the UI.
 */
export function getErrorMessage(error: unknown): string {
  if (isApiError(error)) {
    return error.message;
  }
  return UNKNOWN_ERROR_MESSAGE;
}

// ---------------------------------------------------------------------------
// Client instance
// ---------------------------------------------------------------------------

/**
 * Generate a correlation id for one request.
 *
 * Sent as `X-Request-ID` so a browser action can be matched to its server log
 * entry. `crypto.randomUUID` is unavailable on insecure non-localhost origins,
 * hence the fallback.
 *
 * @returns A unique request identifier.
 */
function createRequestId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `req-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

/** Server origin, without a trailing slash. Empty means same-origin. */
const ORIGIN = resolveOrigin();

const client: AxiosInstance = axios.create({
  // The `/api` prefix is part of each path rather than of the base URL, so that
  // `GET /health` — which the backend mounts at the root on purpose, since a
  // health check that moves with the API prefix is not much of a health check —
  // can be reached from this same instance.
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

// ---------------------------------------------------------------------------
// Endpoints
// ---------------------------------------------------------------------------

/** Callback reporting upload progress as a ratio from 0.0 to 1.0. */
export type UploadProgressHandler = (progress: number) => void;

/**
 * Build an axios config that reports upload progress.
 *
 * @param onProgress - Receives a ratio from 0.0 to 1.0.
 * @param signal - Optional abort signal for cancelling the upload.
 * @returns The axios request configuration.
 */
function uploadConfig(
  onProgress?: UploadProgressHandler,
  signal?: AbortSignal,
): AxiosRequestConfig {
  return {
    headers: { 'Content-Type': 'multipart/form-data' },
    signal,
    onUploadProgress: onProgress
      ? (event: AxiosProgressEvent) => {
          // `total` is absent when the body length is unknown; report nothing
          // rather than a misleading value.
          if (typeof event.total === 'number' && event.total > 0) {
            onProgress(event.loaded / event.total);
          }
        }
      : undefined,
  };
}

/**
 * Detect and recognise plates in a single uploaded image.
 *
 * @param file - The image file chosen by the user.
 * @param onProgress - Optional upload-progress callback, 0.0 to 1.0.
 * @param signal - Optional abort signal.
 * @returns Every plate found, together with the source dimensions needed to
 *   scale bounding-box overlays. An empty `results` array means no plate was
 *   present, which is a normal outcome rather than an error.
 * @throws {ApiError} If the upload is rejected or processing fails.
 */
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

/**
 * Queue a video for background processing.
 *
 * Returns as soon as the file is stored, without waiting for inference: a
 * 60-second clip takes roughly 200 seconds on CPU, far beyond a reasonable HTTP
 * timeout. Poll {@link getJob} with the returned id to follow progress.
 *
 * @param file - The video file chosen by the user.
 * @param onProgress - Optional *upload* progress callback, 0.0 to 1.0. This
 *   tracks the transfer only; inference progress comes from {@link getJob}.
 * @param signal - Optional abort signal.
 * @returns The freshly created job, initially in `pending` status.
 * @throws {ApiError} If the upload is rejected.
 */
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

/**
 * Fetch one page of detection history.
 *
 * Undefined query fields are dropped by axios, so callers can pass a partially
 * filled filter object without building the query string themselves.
 *
 * @param query - Pagination, search, filter and sort options.
 * @param signal - Optional abort signal.
 * @returns The matching page plus the total row count.
 * @throws {ApiError} If the request fails.
 */
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

/**
 * Fetch a single history record by id.
 *
 * @param id - Primary key of the record.
 * @param signal - Optional abort signal.
 * @returns The full record, including bounding box and both confidence scores.
 * @throws {ApiError} With status 404 if no such record exists.
 */
export async function getHistoryDetail(
  id: number,
  signal?: AbortSignal,
): Promise<DetectionHistory> {
  const response = await client.get<DetectionHistory>(`${API_PREFIX}/history/${id}`, {
    signal,
  });
  return response.data;
}

/**
 * Fetch the current state of an asynchronous job.
 *
 * Called on a timer by the video page until `status` reaches `completed` or
 * `failed`.
 *
 * @param jobId - The id returned by {@link detectVideo}.
 * @param signal - Optional abort signal.
 * @returns The job with its current status and progress.
 * @throws {ApiError} With status 404 if no such job exists.
 */
export async function getJob(
  jobId: string,
  signal?: AbortSignal,
): Promise<DetectionJob> {
  const response = await client.get<DetectionJob>(`${API_PREFIX}/jobs/${jobId}`, { signal });
  return response.data;
}

/**
 * Delete a history record and the image files it references.
 *
 * The backend removes the stored files alongside the row (FR-5.1) so no orphan
 * media is left behind.
 *
 * @param id - Primary key of the record to delete.
 * @param signal - Optional abort signal.
 * @throws {ApiError} With status 404 if no such record exists.
 */
export async function deleteHistory(
  id: number,
  signal?: AbortSignal,
): Promise<void> {
  await client.delete(`${API_PREFIX}/history/${id}`, { signal });
}

/**
 * Build the URL of the CSV export for a given set of filters.
 *
 * Returns a URL instead of fetching, because the download must be handed to the
 * browser rather than buffered in JavaScript. The export is unpaginated and the
 * table is specified to hold 100 000 records (NFR-SC2), so the file runs to tens
 * of megabytes; reading that into a blob to trigger a save would hold the whole
 * document in memory for no benefit. Navigating to this URL lets the browser
 * stream it straight to disk.
 *
 * Paging parameters are dropped on purpose: the export covers everything
 * matching the filters, not the page currently on screen.
 *
 * @param filters - The same filters used for the list view, so the file
 *   contains exactly what the user is looking at.
 * @returns An absolute or root-relative URL suitable for `window.location` or
 *   an anchor's `href`.
 */
export function exportHistoryUrl(filters: HistoryQuery = {}): string {
  const params = new URLSearchParams();

  for (const [key, value] of Object.entries(filters)) {
    // `page` and `page_size` are meaningless for an unpaginated export, and
    // sending them would suggest the file is a single page.
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

/**
 * Resolve a stored-file path from the API into a URL the browser can load.
 *
 * The API already returns `image_path` and `plate_image_path` as root-relative
 * `/files/...` URLs rather than as filesystem paths, so the server's directory
 * layout is never published (NFR-S2). This only prefixes the configured origin
 * when one is set, and tolerates an absolute URL or a bare relative path in
 * case either shows up.
 *
 * @param path - Path or URL from the API, or `null` when no file was stored.
 * @returns A loadable URL, or `null` when there is no file. Returning `null`
 *   rather than an empty string matters: an `<img src="">` re-requests the
 *   current page, which is a wasted round trip that renders as a broken image.
 */
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
