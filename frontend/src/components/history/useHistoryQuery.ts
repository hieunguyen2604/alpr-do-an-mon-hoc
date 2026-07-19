/**
 * URL-backed state for the history page: filters, sorting and pagination.
 *
 * The query string is the single source of truth. Every filter the user sets is
 * written there, so reloading the page (F5), bookmarking it or sharing the link
 * reproduces exactly the same view — a filter kept only in component state
 * disappears on reload, which on a page whose whole purpose is narrowing down
 * 100 000 records is a real loss of work.
 *
 * Two inputs are debounced before reaching the URL: the plate search box and the
 * minimum-confidence slider. Both change on every keystroke or drag step, and
 * writing each intermediate value to the URL would issue a request per
 * character and fill the browser history with noise.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { useDebounce } from '@/hooks/useDebounce';
import {
  DEFAULT_DEBOUNCE_MS,
  DEFAULT_PAGE_SIZE,
  DEFAULT_SORT_OPTION,
  PAGE_SIZE_OPTIONS,
} from '@/lib/constants';
import type {
  HistoryQuery,
  HistorySortField,
  InputType,
  SortOrder,
} from '@/types';

// ---------------------------------------------------------------------------
// Query-string parameter names
// ---------------------------------------------------------------------------

/**
 * Names used in the query string.
 *
 * Deliberately identical to the API's own parameter names. A URL that reads
 * `?search=51F&min_confidence=80` can be compared with the request it produces
 * without a translation table in between.
 */
const PARAM = {
  search: 'search',
  inputType: 'input_type',
  dateFrom: 'date_from',
  dateTo: 'date_to',
  /** Held as a **percentage** (0-100) in the URL; sent as a ratio to the API. */
  minConfidence: 'min_confidence',
  sortBy: 'sort_by',
  order: 'order',
  page: 'page',
  pageSize: 'page_size',
} as const;

/** Sort fields this page offers. Must be values the API's `sort_by` accepts. */
const SORTABLE_FIELDS: readonly HistorySortField[] = [
  'detected_time',
  'confidence',
];

/** Input types accepted by the filter dropdown. */
const INPUT_TYPES: readonly InputType[] = ['image', 'video', 'webcam'];

// ---------------------------------------------------------------------------
// Parsing
// ---------------------------------------------------------------------------

/**
 * Whether a string is a sort field this page supports.
 *
 * Values reaching this come from the query string, which anyone can edit by
 * hand. An unknown `sort_by` makes the API answer 422, so it is filtered out
 * here and the default is used instead.
 *
 * @param value - Candidate value.
 * @returns `true` when the value is a supported sort field.
 */
export function isHistorySortField(value: string): value is HistorySortField {
  return (SORTABLE_FIELDS as readonly string[]).includes(value);
}

/**
 * Read the input-type filter from the query string.
 *
 * @param value - Raw parameter value, or `null` when absent.
 * @returns The input type, or an empty string meaning "all types".
 */
function parseInputType(value: string | null): InputType | '' {
  if (value && (INPUT_TYPES as readonly string[]).includes(value)) {
    return value as InputType;
  }
  return '';
}

/**
 * Read a calendar date from the query string.
 *
 * Only a `YYYY-MM-DD` value is accepted — the format a native date input
 * produces. Anything else is discarded rather than forwarded, so a hand-edited
 * URL cannot turn into a 422 from the API.
 *
 * @param value - Raw parameter value, or `null` when absent.
 * @returns The date, or an empty string when absent or malformed.
 */
function parseDate(value: string | null): string {
  return value && /^\d{4}-\d{2}-\d{2}$/.test(value) ? value : '';
}

/**
 * Read the minimum-confidence filter, as a percentage.
 *
 * @param value - Raw parameter value, or `null` when absent.
 * @returns A whole percentage clamped to 0-100; `0` means "no minimum".
 */
function parseConfidencePercent(value: string | null): number {
  if (!value) {
    return 0;
  }
  const parsed = Number.parseFloat(value);
  if (!Number.isFinite(parsed)) {
    return 0;
  }
  return Math.min(Math.max(Math.round(parsed), 0), 100);
}

/**
 * Read a 1-based page number from the query string.
 *
 * @param value - Raw parameter value, or `null` when absent.
 * @returns The page number, never below 1.
 */
function parsePage(value: string | null): number {
  const parsed = Number.parseInt(value ?? '', 10);
  return Number.isFinite(parsed) && parsed >= 1 ? parsed : 1;
}

/**
 * Read the page size from the query string.
 *
 * Restricted to the offered sizes: the API rejects anything above
 * `MAX_PAGE_SIZE` with a 422, and an arbitrary value would also make the page
 * selector show a size it cannot select.
 *
 * @param value - Raw parameter value, or `null` when absent.
 * @returns One of {@link PAGE_SIZE_OPTIONS}.
 */
function parsePageSize(value: string | null): number {
  const parsed = Number.parseInt(value ?? '', 10);
  return PAGE_SIZE_OPTIONS.includes(parsed) ? parsed : DEFAULT_PAGE_SIZE;
}

// ---------------------------------------------------------------------------
// Date bounds
// ---------------------------------------------------------------------------

/**
 * Expand a `YYYY-MM-DD` day into the start of that day.
 *
 * @param date - Calendar date from the date input.
 * @returns An ISO 8601 timestamp, or `undefined` when no date was chosen.
 */
function startOfDay(date: string): string | undefined {
  return date ? `${date}T00:00:00` : undefined;
}

/**
 * Expand a `YYYY-MM-DD` day into the last instant of that day.
 *
 * The time component is not cosmetic. `date_to` is compared against
 * `detected_time`, which is a timestamp: sending the bare date sends midnight,
 * and every record made during that day falls after the bound. Verified against
 * the running API — `date_to=2026-07-19` returns zero rows for a record
 * detected at 07:00 that same day, while `2026-07-19T23:59:59` returns it.
 *
 * @param date - Calendar date from the date input.
 * @returns An ISO 8601 timestamp, or `undefined` when no date was chosen.
 */
function endOfDay(date: string): string | undefined {
  return date ? `${date}T23:59:59` : undefined;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

/** Patch applied to the query string; `null` removes a parameter. */
type ParamPatch = Readonly<Record<string, string | null>>;

/** Everything the history page needs to drive its filters and its request. */
export interface HistoryQueryState {
  /** Parameters for `getHistory`, derived from the URL. */
  query: HistoryQuery;
  /** The same filters without paging, for the CSV export. */
  exportQuery: HistoryQuery;

  /** Live value of the search box, updated on every keystroke. */
  searchInput: string;
  setSearchInput: (value: string) => void;
  /** Live value of the confidence slider, as a whole percentage. */
  confidencePercent: number;
  setConfidencePercent: (value: number) => void;

  inputType: InputType | '';
  setInputType: (value: InputType | '') => void;
  dateFrom: string;
  setDateFrom: (value: string) => void;
  dateTo: string;
  setDateTo: (value: string) => void;

  sortBy: HistorySortField;
  order: SortOrder;
  setSort: (sortBy: HistorySortField, order: SortOrder) => void;

  page: number;
  setPage: (page: number) => void;
  pageSize: number;
  setPageSize: (pageSize: number) => void;

  /** Whether any narrowing filter is currently applied. */
  hasActiveFilters: boolean;
  /** Clear every filter, keeping the sort and the page size. */
  resetFilters: () => void;
  /**
   * Whether a debounced input has been changed but not yet applied.
   *
   * Drives the "đang chờ nhập xong" hint, so a user who has typed and sees no
   * change knows the request is coming rather than assuming nothing happened
   * (NFR-U2).
   */
  isPendingInput: boolean;
}

/**
 * Manage the history page's filters, sort and pagination in the URL.
 *
 * @returns The current query plus the setters that update it.
 */
export function useHistoryQuery(): HistoryQueryState {
  const [searchParams, setSearchParams] = useSearchParams();

  // ---- Values as they currently stand in the URL --------------------------
  const urlSearch = searchParams.get(PARAM.search) ?? '';
  const urlConfidence = parseConfidencePercent(
    searchParams.get(PARAM.minConfidence),
  );
  const inputType = parseInputType(searchParams.get(PARAM.inputType));
  const dateFrom = parseDate(searchParams.get(PARAM.dateFrom));
  const dateTo = parseDate(searchParams.get(PARAM.dateTo));
  const page = parsePage(searchParams.get(PARAM.page));
  const pageSize = parsePageSize(searchParams.get(PARAM.pageSize));

  const rawSortBy = searchParams.get(PARAM.sortBy);
  const sortBy: HistorySortField =
    rawSortBy && isHistorySortField(rawSortBy)
      ? rawSortBy
      : DEFAULT_SORT_OPTION.sort_by;
  const order: SortOrder =
    searchParams.get(PARAM.order) === 'asc' ? 'asc' : 'desc';

  /**
   * Write a patch into the query string.
   *
   * Uses `replace` so that typing into a filter does not push a history entry
   * per keystroke — the Back button should leave the page, not undo one
   * character at a time.
   */
  const applyParams = useCallback(
    (patch: ParamPatch): void => {
      setSearchParams(
        (current) => {
          const next = new URLSearchParams(current);
          for (const [key, value] of Object.entries(patch)) {
            if (value === null || value === '') {
              next.delete(key);
            } else {
              next.set(key, value);
            }
          }
          return next;
        },
        { replace: true },
      );
    },
    [setSearchParams],
  );

  // ---- Debounced inputs ---------------------------------------------------
  // Held locally so the control stays responsive while the URL — and therefore
  // the request — waits for the user to stop.
  const [searchInput, setSearchInput] = useState<string>(urlSearch);
  const [confidencePercent, setConfidencePercent] =
    useState<number>(urlConfidence);

  const debouncedSearch = useDebounce(searchInput, DEFAULT_DEBOUNCE_MS);
  const debouncedConfidence = useDebounce(confidencePercent, DEFAULT_DEBOUNCE_MS);

  // Tracks the URL values this hook last observed, so a change made *elsewhere*
  // — "Xoá bộ lọc", or a Back navigation — can be told apart from one this hook
  // just wrote, and pushed back down into the local inputs.
  const lastSeenSearchRef = useRef(urlSearch);
  const lastSeenConfidenceRef = useRef(urlConfidence);

  useEffect(() => {
    if (lastSeenSearchRef.current !== urlSearch) {
      lastSeenSearchRef.current = urlSearch;
      setSearchInput(urlSearch);
    }
  }, [urlSearch]);

  useEffect(() => {
    if (lastSeenConfidenceRef.current !== urlConfidence) {
      lastSeenConfidenceRef.current = urlConfidence;
      setConfidencePercent(urlConfidence);
    }
  }, [urlConfidence]);

  // Push the settled search value into the URL.
  //
  // The `debouncedSearch === searchInput` guard is what keeps an external reset
  // from being undone: right after one, the input already holds the new value
  // while the debounce still holds the old one, and writing that stale value
  // back would resurrect the filter the user just cleared.
  useEffect(() => {
    if (debouncedSearch !== searchInput || debouncedSearch === urlSearch) {
      return;
    }
    lastSeenSearchRef.current = debouncedSearch;
    applyParams({
      [PARAM.search]: debouncedSearch || null,
      // A narrower search almost never has as many pages; staying on page 7
      // would show an empty table that looks like a bug.
      [PARAM.page]: null,
    });
  }, [debouncedSearch, searchInput, urlSearch, applyParams]);

  useEffect(() => {
    if (
      debouncedConfidence !== confidencePercent ||
      debouncedConfidence === urlConfidence
    ) {
      return;
    }
    lastSeenConfidenceRef.current = debouncedConfidence;
    applyParams({
      [PARAM.minConfidence]:
        debouncedConfidence > 0 ? String(debouncedConfidence) : null,
      [PARAM.page]: null,
    });
  }, [debouncedConfidence, confidencePercent, urlConfidence, applyParams]);

  const isPendingInput =
    debouncedSearch !== searchInput || debouncedConfidence !== confidencePercent;

  // ---- Setters ------------------------------------------------------------

  const setInputType = useCallback(
    (value: InputType | ''): void => {
      applyParams({ [PARAM.inputType]: value || null, [PARAM.page]: null });
    },
    [applyParams],
  );

  const setDateFrom = useCallback(
    (value: string): void => {
      applyParams({ [PARAM.dateFrom]: value || null, [PARAM.page]: null });
    },
    [applyParams],
  );

  const setDateTo = useCallback(
    (value: string): void => {
      applyParams({ [PARAM.dateTo]: value || null, [PARAM.page]: null });
    },
    [applyParams],
  );

  const setSort = useCallback(
    (nextSortBy: HistorySortField, nextOrder: SortOrder): void => {
      // Re-sorting reorders the whole result set, so the rows on page 7 are no
      // longer the ones the user was looking at. Returning to page 1 is the
      // only position that stays meaningful.
      applyParams({
        [PARAM.sortBy]: nextSortBy,
        [PARAM.order]: nextOrder,
        [PARAM.page]: null,
      });
    },
    [applyParams],
  );

  const setPage = useCallback(
    (nextPage: number): void => {
      applyParams({ [PARAM.page]: nextPage > 1 ? String(nextPage) : null });
    },
    [applyParams],
  );

  const setPageSize = useCallback(
    (nextPageSize: number): void => {
      applyParams({
        [PARAM.pageSize]:
          nextPageSize === DEFAULT_PAGE_SIZE ? null : String(nextPageSize),
        [PARAM.page]: null,
      });
    },
    [applyParams],
  );

  const resetFilters = useCallback((): void => {
    setSearchInput('');
    setConfidencePercent(0);
    lastSeenSearchRef.current = '';
    lastSeenConfidenceRef.current = 0;
    applyParams({
      [PARAM.search]: null,
      [PARAM.inputType]: null,
      [PARAM.dateFrom]: null,
      [PARAM.dateTo]: null,
      [PARAM.minConfidence]: null,
      [PARAM.page]: null,
    });
  }, [applyParams]);

  const hasActiveFilters =
    urlSearch !== '' ||
    inputType !== '' ||
    dateFrom !== '' ||
    dateTo !== '' ||
    urlConfidence > 0;

  // ---- Derived request ----------------------------------------------------

  const exportQuery = useMemo<HistoryQuery>(() => {
    const built: HistoryQuery = { sort_by: sortBy, order };
    if (urlSearch) {
      built.search = urlSearch;
    }
    if (inputType) {
      built.input_type = inputType;
    }
    const from = startOfDay(dateFrom);
    if (from) {
      built.date_from = from;
    }
    const to = endOfDay(dateTo);
    if (to) {
      built.date_to = to;
    }
    if (urlConfidence > 0) {
      // The slider speaks percent; the API speaks a 0.0-1.0 ratio.
      built.min_confidence = urlConfidence / 100;
    }
    return built;
  }, [urlSearch, inputType, dateFrom, dateTo, urlConfidence, sortBy, order]);

  const query = useMemo<HistoryQuery>(
    () => ({ ...exportQuery, page, page_size: pageSize }),
    [exportQuery, page, pageSize],
  );

  return {
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
  };
}
