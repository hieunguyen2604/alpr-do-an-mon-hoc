/**
 * Failure notice with a way to recover.
 *
 * The message shown here is always the Vietnamese text produced by the API
 * client's interceptor. Raw exception text, stack traces and status codes are
 * never rendered (NFR-U3, NFR-S4) — the correlation id is offered instead, so a
 * user can quote something that lets a developer find the server-side log entry
 * without any internals having been put on screen.
 */

import { AlertTriangle, RotateCcw } from 'lucide-react';
import type { ReactNode } from 'react';

import { cn } from '@/lib/cn';
import { Button } from './Button';

/** Props of {@link ErrorState}. */
export interface ErrorStateProps {
  /** Heading. Defaults to a generic Vietnamese failure title. */
  title?: string;
  /** Display-ready Vietnamese message from the API client. */
  message?: string | null;
  /** Correlation id, shown in small print for bug reports. */
  requestId?: string;
  /** Retry handler. The button is omitted when this is not supplied. */
  onRetry?: () => void;
  /** Label of the retry button. */
  retryLabel?: string;
  /** Whether a retry is currently running. */
  isRetrying?: boolean;
  /** Extra controls placed beside the retry button. */
  action?: ReactNode;
  className?: string;
}

const DEFAULT_MESSAGE =
  'Đã xảy ra lỗi khi tải dữ liệu. Vui lòng thử lại sau ít phút.';

/**
 * Render an error state.
 *
 * @param props - Title, message, retry handler and correlation id.
 * @returns The error-state element.
 */
export function ErrorState({
  title = 'Không tải được dữ liệu',
  message,
  requestId,
  onRetry,
  retryLabel = 'Thử lại',
  isRetrying = false,
  action,
  className,
}: ErrorStateProps): JSX.Element {
  return (
    <div
      // Announced as soon as it appears: a user who has just triggered an
      // action needs to hear that it failed, not discover it on the next tab
      // press.
      role="alert"
      className={cn(
        'flex flex-col items-center justify-center gap-3',
        'px-6 py-12 text-center',
        className,
      )}
    >
      <div
        aria-hidden="true"
        className={cn(
          'flex h-12 w-12 items-center justify-center rounded-full',
          'bg-danger/10 text-danger',
        )}
      >
        <AlertTriangle className="h-6 w-6" />
      </div>

      <h3 className="text-base font-semibold text-content">{title}</h3>
      <p className="max-w-md text-sm text-content-muted">
        {message ?? DEFAULT_MESSAGE}
      </p>

      {requestId && (
        <p className="text-xs text-content-muted">
          Mã tham chiếu:{' '}
          <code className="font-mono text-content">{requestId}</code>
        </p>
      )}

      <div className="mt-2 flex items-center gap-2">
        {onRetry && (
          <Button
            variant="secondary"
            onClick={onRetry}
            isLoading={isRetrying}
            loadingText="Đang thử lại…"
            leftIcon={<RotateCcw className="h-4 w-4" />}
          >
            {retryLabel}
          </Button>
        )}
        {action}
      </div>
    </div>
  );
}

export default ErrorState;
