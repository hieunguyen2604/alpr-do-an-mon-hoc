import { useEffect, useRef, useState } from 'react';

import { DEFAULT_DEBOUNCE_MS } from '@/lib/constants';

/** Track a value and report it after it stops changing for delayMs. */
export function useDebounce<TValue>(
  value: TValue,
  delayMs: number = DEFAULT_DEBOUNCE_MS,
): TValue {
  const [debouncedValue, setDebouncedValue] = useState<TValue>(value);

  useEffect(() => {
    const timerId = window.setTimeout(() => {
      setDebouncedValue(value);
    }, delayMs);

    // Cancel pending update on new change
    return () => {
      window.clearTimeout(timerId);
    };
  }, [value, delayMs]);

  return debouncedValue;
}

/** Wrap a callback so it runs only after calls stop for delayMs. */
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

  // Keep latest delay in ref without triggering re-render
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
