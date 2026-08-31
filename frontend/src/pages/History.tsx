/** Detection history: search, filter, sort, inspect, delete, and export (FR-4.3 to FR-4.8, FR-5.1 to FR-5.2). */

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

/** History page view. */
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

  // Monotonic request counter ensures latest query result wins
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

  /** Fetch the page of history described by the current query (aborts stale requests). */
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
      // Silently ignore aborted requests
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

  // Auto-clear transient feedback messages
  useEffect(() => {
    if (!notice) {
      return;
    }
    const timerId = window.setTimeout(() => setNotice(null), NOTICE_TIMEOUT_MS);
    return () => {
      window.clearTimeout(timerId);
    };
  }, [notice]);

  /** Apply a sort asked for by a column header (FR-4.8). */
  const handleSortChange = useCallback(
    (key: string, nextOrder: SortOrder): void => {
      // Forward only valid sortable fields
      if (isHistorySortField(key)) {
        setSort(key, nextOrder);
      }
    },
    [setSort],
  );

  /** Ask to delete a record, from either the table or the detail dialog. */
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

      // Step back one page if current page becomes empty after deletion
      if (wasLastRowOfPage) {
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
    <div className="space-y-4">
      {/* Compact Filters Toolbar */}
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
        <p
          role="status"
          aria-live="polite"
          className="rounded-xl border border-success/30 bg-success/10 px-4 py-2.5 text-xs font-semibold text-success"
        >
          {notice}
        </p>
      )}

      {/* Main Records Table Card */}
      <Card
        title="Danh sách biển số đã lưu"
        description={
          isInitialLoading
            ? 'Đang tải danh sách…'
            : `${formatNumber(total)} biển số khớp điều kiện`
        }
        actions={
          <Button
            variant="ghost"
            size="sm"
            onClick={() => void loadHistory()}
            isLoading={isRefreshing}
            loadingText="Đang tải…"
            className="h-8 text-xs font-semibold text-content-muted hover:text-content"
            leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
          >
            Làm mới
          </Button>
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
          // Distinguish between filtered empty state and clean empty database
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
