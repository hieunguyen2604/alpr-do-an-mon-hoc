/**
 * Plates recognised during the current webcam session, one row per plate.
 *
 * Deduplicated by plate string rather than listed frame by frame: at 700 ms per
 * frame a car sitting at a barrier for fifteen seconds yields twenty identical
 * readings, and a raw log buries every other vehicle under them. Each row
 * therefore carries a sighting count and the best score seen, which says more
 * than the twenty rows it replaces.
 *
 * Sorting happens **in the browser**, unlike the history page where the server
 * orders the rows. The session log is a handful of entries held in memory and
 * never round-trips, so asking the API to sort it would be a request for data
 * the page already has.
 */

import { useMemo, useState } from 'react';
import { ScanLine } from 'lucide-react';

import { EmptyState } from '@/components/StateViews';
import { Table } from '@/components/ui';
import type { TableColumn } from '@/components/ui';
import type { SortOrder } from '@/types';
import { formatPercent, formatNumber } from '@/lib/format';

import type { SessionPlateRow, SessionSortKey } from './types';

/** Props of {@link SessionPlateTable}. */
export interface SessionPlateTableProps {
  rows: readonly SessionPlateRow[];
  /** Plates located but unreadable, reported as a footnote rather than as rows. */
  unreadableCount: number;
  /** Whether the camera is running, which changes the empty-state wording. */
  isStreaming: boolean;
}

/** Column keys that can be sorted, as a runtime-checkable set. */
const SORT_KEYS: readonly SessionSortKey[] = [
  'plateNumber',
  'occurrences',
  'bestConfidence',
  'lastSeenAt',
];

/**
 * Narrow a column key coming from the table into a sortable field.
 *
 * @param key - The key reported by the table.
 * @returns The matching sort field, or `null` if the column is not sortable.
 */
function toSortKey(key: string): SessionSortKey | null {
  return SORT_KEYS.find((candidate) => candidate === key) ?? null;
}

/**
 * Order the session rows.
 *
 * @param rows - The rows to order.
 * @param key - Field to order by.
 * @param order - Direction.
 * @returns A new, ordered array.
 */
function sortRows(
  rows: readonly SessionPlateRow[],
  key: SessionSortKey,
  order: SortOrder,
): SessionPlateRow[] {
  const direction = order === 'asc' ? 1 : -1;

  return [...rows].sort((left, right) => {
    switch (key) {
      case 'plateNumber':
        // Locale-aware so Vietnamese labels and digits order predictably.
        return left.plateNumber.localeCompare(right.plateNumber, 'vi-VN') * direction;
      case 'occurrences':
        return (left.occurrences - right.occurrences) * direction;
      case 'bestConfidence':
        return (left.bestConfidence - right.bestConfidence) * direction;
      case 'lastSeenAt':
        return (
          (left.lastSeenAt.getTime() - right.lastSeenAt.getTime()) * direction
        );
      default:
        return 0;
    }
  });
}

/**
 * Render the deduplicated session log.
 *
 * @param props - Rows, the unreadable tally and the stream state.
 * @returns The table, or an empty state when nothing has been recognised.
 */
export function SessionPlateTable({
  rows,
  unreadableCount,
  isStreaming,
}: SessionPlateTableProps): JSX.Element {
  // Newest sighting first: during a live capture the most recent vehicle is
  // almost always the one being looked at.
  const [sortKey, setSortKey] = useState<SessionSortKey>('lastSeenAt');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const sortedRows = useMemo(
    () => sortRows(rows, sortKey, sortOrder),
    [rows, sortKey, sortOrder],
  );

  const columns: readonly TableColumn<SessionPlateRow>[] = useMemo(
    () => [
      {
        key: 'plateNumber',
        header: 'Biển số',
        sortable: true,
        accessor: (row) => (
          <div className="flex flex-col gap-1">
            <span className="plate-text text-content">{row.plateNumber}</span>
            <span
              className={`badge w-fit ${
                row.isValidFormat
                  ? 'bg-success/10 text-success'
                  : 'bg-warning/10 text-warning'
              }`}
            >
              {row.isValidFormat ? 'Đúng định dạng' : 'Sai định dạng'}
            </span>
          </div>
        ),
      },
      {
        key: 'occurrences',
        header: 'Số lần',
        sortable: true,
        align: 'right',
        className: 'tabular-nums',
        accessor: (row) => formatNumber(row.occurrences),
      },
      {
        key: 'bestConfidence',
        header: 'Tin cậy cao nhất',
        sortable: true,
        align: 'right',
        className: 'tabular-nums',
        accessor: (row) => (
          <div className="flex flex-col items-end">
            <span className="font-medium text-content">
              {formatPercent(row.bestConfidence)}
            </span>
            <span className="text-xs text-content-muted">
              OCR {formatPercent(row.bestOcrConfidence)}
            </span>
          </div>
        ),
      },
      {
        key: 'lastSeenAt',
        header: 'Lần gần nhất',
        sortable: true,
        align: 'right',
        className: 'tabular-nums whitespace-nowrap',
        accessor: (row) => row.lastSeenAt.toLocaleTimeString('vi-VN'),
      },
    ],
    [],
  );

  return (
    <div className="space-y-3">
      <Table
        columns={columns}
        rows={sortedRows}
        getRowKey={(row) => row.key}
        sortKey={sortKey}
        sortOrder={sortOrder}
        onSortChange={(key, order) => {
          const next = toSortKey(key);
          if (next) {
            setSortKey(next);
            setSortOrder(order);
          }
        }}
        caption="Danh sách biển số đã nhận dạng trong phiên webcam hiện tại"
        emptyState={
          <EmptyState
            icon={ScanLine}
            title="Chưa nhận được biển số nào"
            description={
              isStreaming
                ? 'Hãy hướng camera về phía biển số xe. Mỗi biển số chỉ hiển thị một dòng, kèm số lần xuất hiện.'
                : 'Bật camera để bắt đầu nhận dạng biển số theo thời gian thực.'
            }
          />
        }
      />

      {unreadableCount > 0 && (
        <p className="text-xs text-content-muted">
          Ngoài ra có {formatNumber(unreadableCount)} lượt phát hiện được vùng biển số
          nhưng không đọc được ký tự nên không đưa vào bảng.
        </p>
      )}
    </div>
  );
}

export default SessionPlateTable;
