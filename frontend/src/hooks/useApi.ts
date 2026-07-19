/**
 * Hooks for calling the API with managed loading and error state.
 *
 * Every page needs the same three pieces of state around a request — data,
 * "in flight", and a display-ready error — plus the same two safety rules:
 * never set state after unmount, and never let a slow response overwrite a
 * newer one. Writing that by hand in each page is where race conditions come
 * from, so it lives here once.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

import { getErrorMessage } from '@/services/api';

/** State tracked for a single API call. */
export interface UseApiState<TData> {
  /** The most recent successful result, or `null` before the first success. */
  data: TData | null;
  /** Whether a request is currently in flight. */
  isLoading: boolean;
  /** Display-ready Vietnamese error message, or `null` if the last call was fine. */
  error: string | null;
}

/** State plus the actions that drive it. */
export interface UseApiResult<TArgs extends unknown[], TData>
  extends UseApiState<TData> {
  /**
   * Alias of `isLoading`.
   *
   * Both spellings are exposed because both read naturally at a call site
   * (`if (loading)` versus `isLoading={...}`), and one alias is cheaper than
   * every consumer having to remember which one this hook chose.
   */
  loading: boolean;
  /**
   * Run the request.
   *
   * Resolves with the data on success, or `null` on failure — the error is put
   * into `error` rather than thrown, so callers may ignore the result and just
   * render from state.
   */
  run: (...args: TArgs) => Promise<TData | null>;
  /** Alias of `run`, for the read-and-reload case. */
  refetch: (...args: TArgs) => Promise<TData | null>;
  /** Clear data, error and loading back to their initial values. */
  reset: () => void;
  /** Clear only the error, e.g. when the user dismisses an alert. */
  clearError: () => void;
}

/**
 * Wrap an async API function with loading and error state.
 *
 * Results are applied only if the component is still mounted and the call is
 * still the newest one. Both guards matter here: a user who changes filters
 * quickly can easily have two `getHistory` calls in flight, and without the
 * sequence check the slower one would win and show stale rows.
 *
 * @typeParam TArgs - Argument tuple of the wrapped function.
 * @typeParam TData - Resolved data type of the wrapped function.
 * @param apiFunction - The API call to wrap. Must be referentially stable —
 *   either a module-level function or one wrapped in `useCallback`.
 * @param initialData - Value for `data` before the first successful call.
 * @returns The request state together with `run`, `reset` and `clearError`.
 *
 * @example
 * ```tsx
 * const { data, isLoading, error, run } = useApi(getStatistics);
 * useEffect(() => { void run(); }, [run]);
 * ```
 */
export function useApi<TArgs extends unknown[], TData>(
  apiFunction: (...args: TArgs) => Promise<TData>,
  initialData: TData | null = null,
): UseApiResult<TArgs, TData> {
  const [state, setState] = useState<UseApiState<TData>>({
    data: initialData,
    isLoading: false,
    error: null,
  });

  const isMountedRef = useRef(true);
  // Monotonic counter: only the newest call may write to state.
  const callSequenceRef = useRef(0);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const run = useCallback(
    async (...args: TArgs): Promise<TData | null> => {
      const callId = ++callSequenceRef.current;
      setState((previous) => ({ ...previous, isLoading: true, error: null }));

      try {
        const result = await apiFunction(...args);
        if (isMountedRef.current && callId === callSequenceRef.current) {
          setState({ data: result, isLoading: false, error: null });
        }
        return result;
      } catch (error) {
        if (isMountedRef.current && callId === callSequenceRef.current) {
          setState((previous) => ({
            ...previous,
            isLoading: false,
            error: getErrorMessage(error),
          }));
        }
        return null;
      }
    },
    [apiFunction],
  );

  const reset = useCallback(() => {
    // Invalidate any in-flight call so its result cannot land after the reset.
    callSequenceRef.current += 1;
    setState({ data: initialData, isLoading: false, error: null });
  }, [initialData]);

  const clearError = useCallback(() => {
    setState((previous) => ({ ...previous, error: null }));
  }, []);

  return {
    ...state,
    loading: state.isLoading,
    run,
    refetch: run,
    reset,
    clearError,
  };
}

/**
 * Run an API call once when the component mounts.
 *
 * A thin wrapper over {@link useApi} for the common read-on-load case, such as
 * the dashboard fetching its statistics.
 *
 * @typeParam TData - Resolved data type of the wrapped function.
 * @param apiFunction - A zero-argument API call. Must be referentially stable.
 * @returns The same shape as {@link useApi}; `run` re-fetches on demand.
 */
export function useApiOnMount<TData>(
  apiFunction: () => Promise<TData>,
): UseApiResult<[], TData> {
  const result = useApi<[], TData>(apiFunction);
  const { run } = result;

  useEffect(() => {
    void run();
  }, [run]);

  return result;
}
