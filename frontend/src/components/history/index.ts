/**
 * Components of the detection-history page.
 *
 * Re-exported so the page imports them in one statement:
 *
 * ```ts
 * import { HistoryFilters, HistoryTable } from '@/components/history';
 * ```
 */

export { DeleteHistoryDialog } from './DeleteHistoryDialog';
export type { DeleteHistoryDialogProps } from './DeleteHistoryDialog';

export { HistoryDetailModal } from './HistoryDetailModal';
export type { HistoryDetailModalProps } from './HistoryDetailModal';

export { HistoryFilters } from './HistoryFilters';
export type { HistoryFiltersProps } from './HistoryFilters';

export { HistoryTable } from './HistoryTable';
export type { HistoryTableProps } from './HistoryTable';

export { isHistorySortField, useHistoryQuery } from './useHistoryQuery';
export type { HistoryQueryState } from './useHistoryQuery';
