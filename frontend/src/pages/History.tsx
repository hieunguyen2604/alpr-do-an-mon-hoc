/**
 * Detection history: search, filter, sort, inspect and delete stored results.
 *
 * Covers FR-4.3 to FR-4.8 (list, search, filter, sort, detail) and FR-5.1 to
 * FR-5.2 (delete a record with its media, export the current selection to CSV).
 *
 * Each row is one **license plate**, not one upload. Rows sharing a
 * `source_job_id` came from the same image or video — which is why the dashboard
 * headline counts jobs while this table lists plates, and why the two numbers
 * are expected to differ.
 *
 * All filter, sort and page state lives in the URL (see `useHistoryQuery`), so
 * the view survives a reload and can be shared as a link.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { FilterX, Inbox, RefreshCw, SearchX } from 'lucide-react';

import {
  DeleteHistoryDialog,
  HistoryDetailModal,
  HistoryFilters,
  HistoryTable,
  isHistorySortField,
  useHistoryQuery,
} from '@/components/history';
import {
  Button,
  Card,
  EmptyState,
  ErrorState,
  Pagination,
  SkeletonTable,
} from '@/components/ui';
import { formatNumber } from '@/lib/format';
import {
  deleteHistory,
  exportHistoryUrl,
  getErrorMessage,
  getHistory,
  isApiError,
} from '@/services/api';
import type { DetectionHistory, HistoryListResponse, SortOrder } from '@/types';

/** How long a transient confirmation stays on screen, in milliseconds. */
const NOTICE_TIMEOUT_MS = 4000;

/**
 * History page.
 *
 * @returns The history view.
 */
export default function History(): JSX.Element {
  const {
    query,
    exportQuery,
    searchInput,
    setSearchInput,
    confidencePercent,
    setConfidencePercent,
    inputType,
    setInputType,
    dateFrom,
    setDateFrom,
    dateTo,
    setDateTo,
    sortBy,
    order,
    setSort,
    page,
    setPage,
    pageSize,
    setPageSize,
    hasActiveFilters,
    resetFilters,
    isPendingInput,
  } = useHistoryQuery();

  const [response, setResponse] = useState<HistoryListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedRecord, setSelectedRecord] = useState<DetectionHistory | null>(
    null,
  );
  const [recordToDelete, setRecordToDelete] = useState<DetectionHistory | null>(
    null,
  );
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  // Monotonic counter: only the newest request may write to state. A user
  // changing two filters quickly has two requests in flight, and without this
  // the slower one can land last and show rows matching neither filter.
  const requestSequenceRef = useRef(0);
  const abortControllerRef = useRef<AbortController | null>(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      abortControllerRef.current?.abort();
    };
  }, []);

  /**
   * Fetch the page of history described by the current query.
   *
   * The previous request is aborted rather than merely ignored: while typing
   * into the search box the browser would otherwise hold several connections
   * open for answers that are already stale.
   */
  const loadHistory = useCallback(async (): Promise<void> => {
    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;
    const requestId = ++requestSequenceRef.current;

    setIsLoading(true);
    setError(null);

    try {
      const data = await getHistory(query, controller.signal);
      if (!isMountedRef.current || requestId !== requestSequenceRef.current) {
        return;
      }
      setResponse(data);
    } catch (caught) {
      if (!isMountedRef.current || requestId !== requestSequenceRef.current) {
        return;
      }
      // A cancellation is this page's own doing, not a failure the user needs
      // to see; the request that replaced it will report its own outcome.
      if (isApiError(caught) && caught.code === 'CANCELLED') {
        return;
      }
      setError(getErrorMessage(caught));
    } finally {
      if (isMountedRef.current && requestId === requestSequenceRef.current) {
        setIsLoading(false);
      }
    }
  }, [query]);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  // Clear the transient confirmation on its own, so it does not linger over an
  // unrelated action later.
  useEffect(() => {
    if (!notice) {
      return;
    }
    const timerId = window.setTimeout(() => setNotice(null), NOTICE_TIMEOUT_MS);
    return () => {
      window.clearTimeout(timerId);
    };
  }, [notice]);

  /**
   * Apply a sort asked for by a column header (FR-4.8).
   *
   * @param key - Column key, which is also the API's `sort_by` value.
   * @param nextOrder - Direction the table worked out.
   */
  const handleSortChange = useCallback(
    (key: string, nextOrder: SortOrder): void => {
      // The table reports a plain string; only fields the API accepts are
      // forwarded, so a future non-sortable column cannot cause a 422.
      if (isHistorySortField(key)) {
        setSort(key, nextOrder);
      }
    },
    [setSort],
  );

  /**
   * Ask to delete a record, from either the table or the detail dialog.
   *
   * @param record - The record to delete.
   */
  const requestDelete = useCallback((record: DetectionHistory): void => {
    setDeleteError(null);
    setRecordToDelete(record);
  }, []);

  /** Delete the confirmed record, then reload the list (FR-5.1). */
  const confirmDelete = useCallback(async (): Promise<void> => {
    if (!recordToDelete) {
      return;
    }
    setIsDeleting(true);
    setDeleteError(null);

    try {
      await deleteHistory(recordToDelete.id);
      if (!isMountedRef.current) {
        return;
      }

      const wasLastRowOfPage = response?.items.length === 1 && page > 1;
      setRecordToDelete(null);
      setSelectedRecord(null);
      setNotice('Đã xoá bản ghi cùng với ảnh liên quan trên máy chủ.');

      if (wasLastRowOfPage) {
        // Reloading in place would land on a page that no longer exists and
        // show an empty table; stepping back one page re-triggers the fetch.
        setPage(page - 1);
      } else {
        await loadHistory();
      }
    } catch (caught) {
      if (isMountedRef.current) {
        // Kept inside the dialog so the user can retry without hunting for the
        // row again.
        setDeleteError(getErrorMessage(caught));
      }
    } finally {
      if (isMountedRef.current) {
        setIsDeleting(false);
      }
    }
  }, [recordToDelete, response, page, setPage, loadHistory]);

  const records = response?.items ?? [];
  const total = response?.total ?? 0;
  const isInitialLoading = isLoading && response === null;
  const isRefreshing = isLoading && response !== null;

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-content">
            Lịch sử nhận dạng
          </h1>
          <p className="mt-1 text-sm text-content-muted">
            Mỗi dòng là một biển số. Nhiều dòng có thể thuộc cùng một lượt tải
            lên.
          </p>
        </div>

        <Button
          variant="secondary"
          onClick={() => void loadHistory()}
          isLoading={isRefreshing}
          loadingText="Đang tải…"
          leftIcon={<RefreshCw className="h-4 w-4" />}
        >
          Tải lại
        </Button>
      </header>

      <HistoryFilters
        searchInput={searchInput}
        onSearchInputChange={setSearchInput}
        inputType={inputType}
        onInputTypeChange={setInputType}
        dateFrom={dateFrom}
        onDateFromChange={setDateFrom}
        dateTo={dateTo}
        onDateToChange={setDateTo}
        confidencePercent={confidencePercent}
        onConfidencePercentChange={setConfidencePercent}
        hasActiveFilters={hasActiveFilters}
        onReset={resetFilters}
        exportUrl={exportHistoryUrl(exportQuery)}
        canExport={total > 0}
        isPendingInput={isPendingInput}
      />

      {notice && (
        // Announced politely so a keyboard or screen-reader user hears that the
        // deletion succeeded instead of only seeing a row disappear.
        <p
          role="status"
          aria-live="polite"
          className="rounded-lg border border-success/30 bg-success/10 px-4 py-3 text-sm text-success"
        >
          {notice}
        </p>
      )}

      <Card
        title="Kết quả"
        description={
          isInitialLoading
            ? 'Đang tải danh sách…'
            : `${formatNumber(total)} biển số khớp điều kiện hiện tại`
        }
        noPadding
      >
        {isInitialLoading ? (
          <div className="p-5">
            <p role="status" className="sr-only">
              Đang tải lịch sử nhận dạng…
            </p>
            <SkeletonTable rows={6} columns={6} />
          </div>
        ) : error ? (
          <ErrorState
            message={error}
            onRetry={() => void loadHistory()}
            isRetrying={isLoading}
          />
        ) : records.length === 0 ? (
          // The two empty cases are deliberately different. "Nothing matches
          // this filter" is a dead end unless the way out is offered with it,
          // whereas "nothing recorded yet" is a working system with no data.
          hasActiveFilters ? (
            <EmptyState
              icon={<SearchX className="h-6 w-6" />}
              title="Không có bản ghi nào khớp bộ lọc"
              description="Hãy nới lỏng điều kiện lọc, mở rộng khoảng thời gian hoặc hạ ngưỡng độ tin cậy."
              action={
                <Button
                  variant="secondary"
                  onClick={resetFilters}
                  leftIcon={<FilterX className="h-4 w-4" />}
                >
                  Xoá bộ lọc
                </Button>
              }
            />
          ) : (
            <EmptyState
              icon={<Inbox className="h-6 w-6" />}
              title="Chưa có dữ liệu nhận dạng"
              description="Mọi biển số nhận dạng được từ ảnh, video hoặc webcam sẽ tự động xuất hiện ở đây."
              action={
                <Link to="/" className="btn-primary">
                  Nhận dạng ảnh đầu tiên
                </Link>
              }
            />
          )
        ) : (
          <>
            <HistoryTable
              records={records}
              sortBy={sortBy}
              order={order}
              onSortChange={handleSortChange}
              onSelect={setSelectedRecord}
              onDelete={requestDelete}
              isRefreshing={isRefreshing}
            />

            <div className="border-t border-border px-5 py-4">
              <Pagination
                page={page}
                totalPages={response?.total_pages ?? 1}
                total={total}
                pageSize={pageSize}
                onPageChange={setPage}
                onPageSizeChange={setPageSize}
                disabled={isLoading}
              />
            </div>
          </>
        )}
      </Card>

      <HistoryDetailModal
        record={selectedRecord}
        onClose={() => setSelectedRecord(null)}
        onDelete={requestDelete}
      />

      <DeleteHistoryDialog
        record={recordToDelete}
        isDeleting={isDeleting}
        error={deleteError}
        onConfirm={() => void confirmDelete()}
        onCancel={() => {
          setRecordToDelete(null);
          setDeleteError(null);
        }}
      />
    </div>
  );
}
