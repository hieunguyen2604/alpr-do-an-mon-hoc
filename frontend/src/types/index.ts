/** Input source type for detection. */
export type InputType = 'image' | 'video' | 'webcam';

/** Lifecycle status of an asynchronous job. */
export type JobStatus =
  | 'pending'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'cancelled';

/** Number of text lines on a plate: 1 for cars, 2 for motorcycles. */
export type PlateLineCount = 1 | 2;

/** Plate family inferred from character layout and rules. */
export type PlateKind =
  | 'car'
  | 'motorcycle_new'
  | 'motorcycle_old'
  | 'blue_car'
  | 'blue_motorcycle'
  | 'special'
  | 'diplomatic'
  | 'military'
  | 'unknown';

/** Background plate colour (white, yellow, blue, red, unknown). */
export type PlateColor = 'white' | 'yellow' | 'blue' | 'red' | 'unknown';

/** Sortable columns of the detection history table. */
export type HistorySortField =
  | 'detected_time'
  | 'created_at'
  | 'plate_number'
  | 'confidence';

/** Sort direction. */
export type SortOrder = 'asc' | 'desc';

/** Combined sort field and order option for UI dropdown. */
export interface SortOption {
  value: string;
  label: string;
  sort_by: HistorySortField;
  order: SortOrder;
}

/** Plate bounding box in image pixel coordinates. */
export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

/** Recognition result for a single detected license plate. */
export interface DetectionResult {
  plate_number: string | null;
  raw_ocr_text: string | null;
  detection_confidence: number;
  ocr_confidence: number | null;
  bbox: BoundingBox;
  is_valid_format: boolean;
  plate_kind: PlateKind | null;
  plate_color: PlateColor | null;
  plate_color_confidence: number | null;
  plate_display: string | null;
  plate_line_count: PlateLineCount | null;
  processing_time: number;
  plate_image_url: string | null;
}

/** API response payload for image and live frame detection endpoints. */
export interface DetectionResponse {
  job_id: string;
  input_type: InputType;
  image_url: string | null;
  image_width: number;
  image_height: number;
  processing_time: number;
  plate_count: number;
  results: DetectionResult[];
}

/** Stored license plate record in detection history. */
export interface DetectionHistory {
  id: number;
  plate_number: string | null;
  raw_ocr_text: string | null;
  confidence: number;
  ocr_confidence: number | null;
  input_type: InputType;
  image_path: string | null;
  plate_image_path: string | null;
  bbox_x: number;
  bbox_y: number;
  bbox_w: number;
  bbox_h: number;
  is_valid_format: boolean;
  plate_kind: PlateKind | null;
  plate_color: PlateColor | null;
  plate_color_confidence: number | null;
  plate_display: string | null;
  video_time_seconds: number | null;
  plate_line_count: PlateLineCount | null;
  processing_time: number;
  detected_time: string;
  created_at: string;
  source_job_id: string;
  bbox: BoundingBox;
}

/** Alias of DetectionHistory. */
export type DetectionRecord = DetectionHistory;

/** Query filter parameters for GET /api/history. */
export interface HistoryQuery {
  page?: number;
  page_size?: number;
  search?: string;
  input_type?: InputType;
  date_from?: string;
  date_to?: string;
  min_confidence?: number;
  is_valid_format?: boolean;
  job_id?: string;
  sort_by?: HistorySortField;
  order?: SortOrder;
}

/** UI filter state for history page. */
export type HistoryFilters = HistoryQuery;

/** Paginated list response for history query. */
export interface HistoryListResponse {
  items: DetectionHistory[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/** Async video detection job status. */
export interface DetectionJob {
  id: string;
  input_type: InputType;
  status: JobStatus;
  progress: number;
  output_url: string | null;
  total_frames: number | null;
  processed_frames: number;
  detection_count: number;
  created_at: string;
  completed_at: string | null;
}

/** Breakdown of jobs and detections by input type. */
export interface InputTypeBreakdown {
  input_type: InputType;
  job_count: number;
  detection_count: number;
}

/** Daily detection and job counts for trend chart. */
export interface DetectionsOverTimePoint {
  date: string;
  job_count: number;
  detection_count: number;
}

/** Dashboard aggregate statistics. */
export interface Statistics {
  total_jobs: number;
  total_detections: number;
  unique_plates: number;
  valid_format_count: number;
  invalid_format_count: number;
  unreadable_count: number;
  average_confidence: number | null;
  average_ocr_confidence: number | null;
  average_processing_time: number | null;
  jobs_today: number;
  detections_today: number;
  by_input_type: InputTypeBreakdown[];
  daily_counts: DetectionsOverTimePoint[];
}

/** Query parameters for statistics endpoint. */
export interface StatisticsQuery {
  days?: number;
}

/** System health check response. */
export interface HealthStatus {
  status: 'ok' | 'degraded';
  app_name: string;
  version: string;
  database_connected: boolean;
  model_loaded: boolean;
  uptime_seconds: number;
  timestamp: string;
}

/** API JSON error response structure. */
export interface ApiErrorResponse {
  error: string;
  message?: string;
  request_id?: string;
}

/** Normalised client-side API error. */
export interface ApiError {
  status: number;
  message: string;
  code?: string;
  request_id?: string;
}
