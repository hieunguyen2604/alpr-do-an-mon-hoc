/**
 * Debouncing hooks, for the history search box.
 *
 * Typing "51F-12345" is nine keystrokes. Querying on each of them sends nine
 * requests for a result the user only wants once, and — because responses can
 * arrive out of order — the list may settle on the answer to a prefix rather
 * than to the finished query. Waiting for a pause in typing fixes both.
 */

import { useEffect, useRef, useState } from 'react';

import { DEFAULT_DEBOUNCE_MS } from '@/lib/constants';

/**
 * Track a value, but only report it once it has stopped changing.
 *
 * @typeParam TValue - Type of the debounced value.
 * @param value - The value that changes on every keystroke.
 * @param delayMs - Quiet period to wait for, in milliseconds.
 * @returns The value as it stood `delayMs` after the last change.
 *
 * @example
 * ```tsx
 * const [search, setSearch] = useState('');
 * const debouncedSearch = useDebounce(search);
 * useEffect(() => { void run({ search: debouncedSearch }); }, [debouncedSearch]);
 * ```
 */
export function useDebounce<TValue>(
  value: TValue,
  delayMs: number = DEFAULT_DEBOUNCE_MS,
): TValue {
  const [debouncedValue, setDebouncedValue] = useState<TValue>(value);

  useEffect(() => {
    const timerId = window.setTimeout(() => {
      setDebouncedValue(value);
    }, delayMs);

    // Clearing on every change is what makes this a debounce rather than a
    // delay: a new keystroke cancels the pending update instead of queueing a
    // second one behind it.
    return () => {
      window.clearTimeout(timerId);
    };
  }, [value, delayMs]);

  return debouncedValue;
}

/**
 * Wrap a callback so it runs only after calls have stopped for `delayMs`.
 *
 * The returned function is referentially stable, so it can be passed to a
 * memoised child or listed in a dependency array without causing a re-render
 * loop. The latest `callback` is always the one invoked — it is held in a ref
 * rather than captured, so a stale closure cannot fire with outdated state.
 *
 * @typeParam TArgs - Argument tuple of the callback.
 * @param callback - The function to defer.
 * @param delayMs - Quiet period to wait for, in milliseconds.
 * @returns A debounced version of the callback.
 */
export function useDebouncedCallback<TArgs extends unknown[]>(
  callback: (...args: TArgs) => void,
  delayMs: number = DEFAULT_DEBOUNCE_MS,
): (...args: TArgs) => void {
  const callbackRef = useRef(callback);
  const delayRef = useRef(delayMs);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  // Kept in a ref for the same reason as the callback: the returned function is
  // created once, so reading `delayMs` from the closure would pin it to the
  // value it had on the first render.
  useEffect(() => {
    delayRef.current = delayMs;
  }, [delayMs]);

  useEffect(
    () => () => {
      if (timerRef.current !== null) {
        window.clearTimeout(timerRef.current);
      }
    },
    [],
  );

  const debouncedRef = useRef((...args: TArgs) => {
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current);
    }
    timerRef.current = window.setTimeout(() => {
      timerRef.current = null;
      callbackRef.current(...args);
    }, delayRef.current);
  });

  return debouncedRef.current;
}
