/**
 * The five most recent recognitions, with a link through to the full history.
 *
 * One row is one **license plate**, not one upload — several rows can share a
 * `source_job_id`. The section subtitle says so, because next to a tile reading
 * "Lượt nhận dạng" a five-row list could otherwise be read as five uploads.
 */

import { Link } from 'react-router-dom';
import { ArrowRight, ScanLine } from 'lucide-react';

import { EmptyState, PageSection } from '@/components/StateViews';
import { Badge, PlateChip, SkeletonTable, Table } from '@/components/ui';
import type { TableColumn } from '@/components/ui';
import {
  confidenceColorClass,
  formatConfidence,
  formatDateTime,
  formatInputType,
} from '@/lib/format';
import type { DetectionHistory } from '@/types';

/** Props of {@link RecentDetections}. */
export interface RecentDetectionsProps {
  /** The most recent records, newest first. */
  records: readonly DetectionHistory[];
  isLoading?: boolean;
}

/**
 * Render the recent-detections section.
 *
 * @param props - The records and the loading flag.
 * @returns The section.
 */
export function RecentDetections({
  records,
  isLoading = false,
}: RecentDetectionsProps): JSX.Element {
  const columns: readonly TableColumn<DetectionHistory>[] = [
    {
      key: 'plate_number',
      header: 'Biển số',
      accessor: (row) => (
        <PlateChip
          plateNumber={row.plate_number}
          isValidFormat={row.is_valid_format}
          size="sm"
        />
      ),
    },
    {
      key: 'input_type',
      header: 'Nguồn',
      accessor: (row) => (
        <Badge variant="neutral">{formatInputType(row.input_type)}</Badge>
      ),
    },
    {
      key: 'confidence',
      header: 'Độ tin cậy',
      align: 'right',
      accessor: (row) => (
        <span
          className={`inline-block rounded px-1.5 py-0.5 text-xs font-medium tabular-nums ${confidenceColorClass(
            row.confidence,
          )}`}
        >
          {formatConfidence(row.confidence)}
        </span>
      ),
    },
    {
      key: 'detected_time',
      header: 'Thời điểm',
      align: 'right',
      className: 'whitespace-nowrap tabular-nums text-content-muted',
      accessor: (row) => formatDateTime(row.detected_time),
    },
  ];

  return (
    <PageSection
      title="Nhận dạng gần đây"
      subtitle="5 biển số được ghi nhận gần nhất — một lượt tải lên có thể sinh ra nhiều dòng"
      actions={
        <Link
          to="/history"
          className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs
                     font-medium text-primary transition-colors hover:bg-surface-raised"
        >
          Xem tất cả lịch sử
          <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
        </Link>
      }
    >
      {isLoading ? (
        <SkeletonTable rows={5} columns={4} />
      ) : (
        <Table
          columns={columns}
          rows={records}
          getRowKey={(row) => row.id}
          caption="Năm biển số được nhận dạng gần đây nhất"
          emptyState={
            <EmptyState
              icon={ScanLine}
              title="Chưa có biển số nào được ghi nhận"
              description="Kết quả sẽ xuất hiện tại đây ngay sau lần nhận dạng đầu tiên."
              action={
                <Link to="/image" className="btn-primary mt-1">
                  Nhận dạng ảnh đầu tiên
                </Link>
              }
            />
          }
        />
      )}
    </PageSection>
  );
}

export default RecentDetections;
