/** Polling hook for async background video jobs (stops on terminal status or unmount). */

import { useCallback, useEffect, useRef, useState } from 'react';

import { DEFAULT_POLL_INTERVAL_MS, isTerminalStatus } from '@/lib/constants';
import { getErrorMessage, getJob } from '@/services/api';
import type { DetectionJob } from '@/types';

/** Options accepted by {@link useJobPolling}. */
export interface UseJobPollingOptions {
  /** Milliseconds between polls. */
  intervalMs?: number;
  /** Called once when the job reaches a terminal status (completed/failed/cancelled). */
  onSettled?: (job: DetectionJob) => void;
  /** How many consecutive failed polls to tolerate before giving up. */
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

/** Follow a background job until it finishes. */
export function useJobPolling(
  jobId: string | null,
  options: UseJobPollingOptions = {},
): UseJobPollingResult {
  const {
    intervalMs = DEFAULT_POLL_INTERVAL_MS,
    onSettled,
    maxConsecutiveErrors = 10,
  } = options;

  const [job, setJob] = useState<DetectionJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  const isMountedRef = useRef(true);
  const errorCountRef = useRef(0);
  // Guards onSettled against duplicate executions
  const settledRef = useRef(false);
  // Stable ref callback prevents interval teardown on re-render
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

  /** Fetch the job once and apply the result; returns whether polling should continue. */
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
        // Silently tolerate transient polling errors up to threshold
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

    // Reset state on job ID change
    settledRef.current = false;
    errorCountRef.current = 0;
    setJob(null);
    setError(null);
    setIsPolling(true);

    const controller = new AbortController();
    let timerId: number | null = null;
    let stopped = false;

    /** Poll, then schedule the next one only if polling should continue (chained timeouts to avoid overlap). */
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
