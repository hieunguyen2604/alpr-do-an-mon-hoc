/**
 * The history table itself (FR-4.6, FR-4.8).
 *
 * One row is one **license plate**, not one upload: an image holding three
 * plates produces three rows sharing a `source_job_id`. That is why this table
 * counts rows while the dashboard counts jobs, and the two figures are supposed
 * to differ.
 *
 * Sorting is delegated to the server — the column keys are the exact values the
 * API's `sort_by` accepts, so a header click becomes a query parameter with no
 * translation in between.
 */

import { useState } from 'react';
import { ImageOff, Trash2 } from 'lucide-react';

import { Badge, ConfidenceBar, PlateChip, Table } from '@/components/ui';
import type { BadgeVariant, TableColumn } from '@/components/ui';
import { cn } from '@/lib/cn';
import { INPUT_TYPE_LABELS } from '@/lib/constants';
import {
  formatDateTime,
  formatPlateNumber,
  formatProcessingTime,
} from '@/lib/format';
import { fileUrl } from '@/services/api';
import type {
  DetectionHistory,
  HistorySortField,
  InputType,
  SortOrder,
} from '@/types';

/** Badge colour per input type. Distinct hues make the column scannable. */
const INPUT_TYPE_VARIANT: Readonly<Record<InputType, BadgeVariant>> = {
  image: 'info',
  video: 'success',
  webcam: 'warning',
};

/** Props of {@link PlateThumbnail}. */
interface PlateThumbnailProps {
  /** URL of the cropped plate image, or `null` when the crop was not kept. */
  src: string | null;
  /** Plate text, used to describe the image. */
  plateNumber: string | null;
}

/**
 * Small preview of the cropped plate.
 *
 * A crop can be missing in two different ways — never stored, or stored and
 * since gone from disk — and both must land on the placeholder rather than on
 * the browser's broken-image icon, which in a dense table reads as a bug.
 *
 * @param props - Image URL and the plate text describing it.
 * @returns The thumbnail element.
 */
function PlateThumbnail({ src, plateNumber }: PlateThumbnailProps): JSX.Element {
  const [hasFailed, setHasFailed] = useState(false);

  if (!src || hasFailed) {
    return (
      <div
        title="Không có ảnh biển số"
        className={cn(
          'flex h-10 w-20 items-center justify-center rounded-md',
          'border border-dashed border-border bg-surface-raised text-content-muted',
        )}
      >
        <ImageOff className="h-4 w-4" aria-hidden="true" />
        <span className="sr-only">Không có ảnh biển số</span>
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={`Ảnh biển số ${formatPlateNumber(plateNumber)}`}
      onError={() => setHasFailed(true)}
      // Lazy so a page of 100 rows does not fire 100 image requests at once.
      loading="lazy"
      className="h-10 w-20 rounded-md border border-border bg-surface-raised object-cover"
    />
  );
}

/** Props of {@link HistoryTable}. */
export interface HistoryTableProps {
  records: readonly DetectionHistory[];
  /** Column currently sorted; matches the API's `sort_by`. */
  sortBy: HistorySortField;
  order: SortOrder;
  onSortChange: (key: string, order: SortOrder) => void;
  /** Open the detail dialog for a record. */
  onSelect: (record: DetectionHistory) => void;
  /** Ask to delete a record; confirmation happens in the page. */
  onDelete: (record: DetectionHistory) => void;
  /** Dim the body while a refresh is in flight. */
  isRefreshing?: boolean;
}

/**
 * Render the history table.
 *
 * @param props - Rows, sort state and row handlers.
 * @returns The table element.
 */
export function HistoryTable({
  records,
  sortBy,
  order,
  onSortChange,
  onSelect,
  onDelete,
  isRefreshing = false,
}: HistoryTableProps): JSX.Element {
  const columns: readonly TableColumn<DetectionHistory>[] = [
    {
      key: 'plate_image',
      header: 'Ảnh biển số',
      accessor: (record) => (
        <PlateThumbnail
          src={fileUrl(record.plate_image_path)}
          plateNumber={record.plate_number}
        />
      ),
    },
    {
      key: 'plate_number',
      header: 'Biển số',
      accessor: (record) => (
        <div className="space-y-1">
          {/* The formatted rendering, matching the image and video pages. The
              same plate shown three different ways across three screens reads
              as three different plates. */}
          <PlateChip
            plateNumber={record.plate_display ?? record.plate_number}
            isValidFormat={record.is_valid_format}
            size="sm"
          />
          {/* Surfacing the raw read next to the corrected one is what makes
              post-processing gain visible at a glance. */}
          {record.raw_ocr_text !== null &&
            record.raw_ocr_text !== record.plate_number && (
              <p className="text-xs text-content-muted">
                OCR thô:{' '}
                <span className="font-mono">{record.raw_ocr_text}</span>
              </p>
            )}
        </div>
      ),
    },
    {
      key: 'confidence',
      header: 'Độ tin cậy',
      sortable: true,
      className: 'min-w-40',
      accessor: (record) => (
        <ConfidenceBar value={record.confidence} size="sm" />
      ),
    },
    {
      key: 'input_type',
      header: 'Loại đầu vào',
      accessor: (record) => (
        <Badge variant={INPUT_TYPE_VARIANT[record.input_type]}>
          {INPUT_TYPE_LABELS[record.input_type]}
        </Badge>
      ),
    },
    {
      key: 'detected_time',
      header: 'Thời điểm',
      sortable: true,
      className: 'whitespace-nowrap tabular-nums',
      accessor: (record) => formatDateTime(record.detected_time),
    },
    {
      key: 'processing_time',
      header: 'Thời gian xử lý',
      align: 'right',
      className: 'whitespace-nowrap tabular-nums',
      accessor: (record) => formatProcessingTime(record.processing_time),
    },
    {
      key: 'actions',
      header: <span className="sr-only">Hành động</span>,
      align: 'right',
      accessor: (record) => (
        <button
          type="button"
          onClick={(event) => {
            // Without this the click also reaches the row and opens the detail
            // dialog behind the delete confirmation.
            event.stopPropagation();
            onDelete(record);
          }}
          aria-label={`Xoá bản ghi biển số ${formatPlateNumber(record.plate_number)}`}
          title="Xoá bản ghi"
          className={cn(
            'rounded-md p-2 text-content-muted transition-colors',
            'hover:bg-danger/10 hover:text-danger',
          )}
        >
          <Trash2 className="h-4 w-4" aria-hidden="true" />
        </button>
      ),
    },
  ];

  return (
    <Table<DetectionHistory>
      columns={columns}
      rows={records}
      getRowKey={(record) => record.id}
      sortKey={sortBy}
      sortOrder={order}
      onSortChange={onSortChange}
      onRowClick={onSelect}
      isLoading={isRefreshing}
      caption="Danh sách biển số đã nhận dạng. Mỗi dòng là một biển số; nhiều dòng có thể thuộc cùng một lần tải lên."
    />
  );
}

export default HistoryTable;
