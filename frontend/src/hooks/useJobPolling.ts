/**
 * Polling for background video jobs.
 *
 * Video is processed asynchronously because it cannot be processed inline:
 * roughly 200 seconds of CPU per 60 seconds of footage (NFR-SC3), far past any
 * HTTP timeout. `POST /api/detect/video` answers 202 with a job id and the
 * frontend follows progress from here (decision AD-02).
 *
 * Two rules matter and are easy to get wrong by hand:
 *
 * 1. **Stop at a terminal status.** `completed`, `failed` and `cancelled` are
 *    final. Polling past one is a request every 1.5 seconds, forever, for an
 *    answer that will never change.
 * 2. **Stop on unmount.** A timer left running holds the component alive and
 *    sets state on something React has already discarded.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

import { DEFAULT_POLL_INTERVAL_MS, isTerminalStatus } from '@/lib/constants';
import { getErrorMessage, getJob } from '@/services/api';
import type { DetectionJob } from '@/types';

/** Options accepted by {@link useJobPolling}. */
export interface UseJobPollingOptions {
  /** Milliseconds between polls. */
  intervalMs?: number;
  /**
   * Called once when the job reaches a terminal status.
   *
   * Fires for `failed` and `cancelled` as well as `completed` — inspect
   * `job.status` rather than assuming success.
   */
  onSettled?: (job: DetectionJob) => void;
  /**
   * How many consecutive failed polls to tolerate before giving up.
   *
   * Not zero, because a single dropped request is not a dead job: aborting on
   * the first failure would discard a run that is still progressing fine on the
   * server, and the user would have no way to recover it.
   */
  maxConsecutiveErrors?: number;
}

/** What {@link useJobPolling} returns. */
export interface UseJobPollingResult {
  /** Latest job state, or `null` before the first successful poll. */
  job: DetectionJob | null;
  /** Whether the hook is actively polling. */
  isPolling: boolean;
  /** Display-ready Vietnamese error, or `null`. */
  error: string | null;
  /** Progress from 0.0 to 1.0, `0` before the first poll. */
  progress: number;
  /** Whether the job has reached a terminal status. */
  isSettled: boolean;
  /** Poll once immediately, without waiting for the next tick. */
  refresh: () => Promise<void>;
}

/**
 * Follow a background job until it finishes.
 *
 * Polling starts when `jobId` becomes non-null and stops on its own at a
 * terminal status, on unmount, or after too many consecutive failures.
 *
 * @param jobId - Job to watch, or `null` to poll nothing. Passing `null` is the
 *   normal idle state, not an error.
 * @param options - Interval, completion callback and error tolerance.
 * @returns The job state, progress and a manual refresh.
 *
 * @example
 * ```tsx
 * const { job, progress, error } = useJobPolling(jobId, {
 *   onSettled: (finished) => {
 *     if (finished.status === 'completed') void reloadHistory();
 *   },
 * });
 * ```
 */
export function useJobPolling(
  jobId: string | null,
  options: UseJobPollingOptions = {},
): UseJobPollingResult {
  const {
    intervalMs = DEFAULT_POLL_INTERVAL_MS,
    onSettled,
    maxConsecutiveErrors = 3,
  } = options;

  const [job, setJob] = useState<DetectionJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  const isMountedRef = useRef(true);
  const errorCountRef = useRef(0);
  // Guards `onSettled` against firing twice, which would otherwise happen when
  // a manual `refresh` and a scheduled tick both observe the terminal status.
  const settledRef = useRef(false);
  // Held in a ref so that changing the callback does not restart the interval:
  // an inline arrow function is a new reference on every render, and in a
  // dependency array it would tear the timer down and rebuild it each time.
  const onSettledRef = useRef(onSettled);

  useEffect(() => {
    onSettledRef.current = onSettled;
  }, [onSettled]);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  /**
   * Fetch the job once and apply the result.
   *
   * @param signal - Abort signal tied to the current polling session.
   * @returns Whether polling should continue.
   */
  const poll = useCallback(
    async (signal?: AbortSignal): Promise<boolean> => {
      try {
        const next = await getJob(jobId ?? '', signal);
        if (!isMountedRef.current) {
          return false;
        }

        errorCountRef.current = 0;
        setJob(next);
        setError(null);

        if (isTerminalStatus(next.status)) {
          if (!settledRef.current) {
            settledRef.current = true;
            onSettledRef.current?.(next);
          }
          return false;
        }
        return true;
      } catch (caught) {
        if (!isMountedRef.current || signal?.aborted) {
          return false;
        }

        errorCountRef.current += 1;
        // A transient failure is tolerated silently: reporting the first
        // dropped request as an error would flash a message on a job that is
        // still running normally.
        if (errorCountRef.current >= maxConsecutiveErrors) {
          setError(getErrorMessage(caught));
          return false;
        }
        return true;
      }
    },
    [jobId, maxConsecutiveErrors],
  );

  useEffect(() => {
    if (!jobId) {
      setIsPolling(false);
      return;
    }

    // A new job starts with a clean slate, otherwise the previous job's final
    // state would be shown as this one's opening state.
    settledRef.current = false;
    errorCountRef.current = 0;
    setJob(null);
    setError(null);
    setIsPolling(true);

    const controller = new AbortController();
    let timerId: number | null = null;
    let stopped = false;

    /**
     * Poll, then schedule the next one only if polling should continue.
     *
     * Chained timeouts rather than `setInterval`: an interval fires on a fixed
     * schedule regardless of whether the previous request has returned, so a
     * slow response would let calls pile up and overlap.
     */
    const tick = async (): Promise<void> => {
      const shouldContinue = await poll(controller.signal);

      if (stopped || !isMountedRef.current) {
        return;
      }
      if (!shouldContinue) {
        setIsPolling(false);
        return;
      }
      timerId = window.setTimeout(() => {
        void tick();
      }, intervalMs);
    };

    void tick();

    return () => {
      stopped = true;
      controller.abort();
      if (timerId !== null) {
        window.clearTimeout(timerId);
      }
    };
  }, [jobId, intervalMs, poll]);

  const refresh = useCallback(async (): Promise<void> => {
    if (!jobId) {
      return;
    }
    await poll();
  }, [jobId, poll]);

  return {
    job,
    isPolling,
    error,
    progress: job?.progress ?? 0,
    isSettled: job ? isTerminalStatus(job.status) : false,
    refresh,
  };
}
