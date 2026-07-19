/**
 * Reusable loading, empty and error views.
 *
 * Every page has to handle the same three non-happy-path states. Centralising
 * them keeps the wording and spacing consistent, and means a page's own code
 * stays focused on its actual content.
 */

import type { ReactNode } from 'react';
import { AlertCircle, Inbox, Loader2, RefreshCw } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

/** Props for {@link LoadingState}. */
export interface LoadingStateProps {
  /** Message shown under the spinner. */
  message?: string;
}

/**
 * Centred spinner for a region that is waiting on data.
 *
 * @param props - Optional message override.
 * @returns The loading view.
 */
export function LoadingState({
  message = 'Đang tải dữ liệu…',
}: LoadingStateProps): JSX.Element {
  return (
    <div
      className="flex flex-col items-center justify-center gap-3 py-14 text-content-muted"
      role="status"
      aria-live="polite"
    >
      <Loader2 size={28} className="animate-spin text-primary" aria-hidden="true" />
      <p className="text-sm">{message}</p>
    </div>
  );
}

/** Props for {@link EmptyState}. */
export interface EmptyStateProps {
  /** Headline, e.g. "Chưa có dữ liệu". */
  title: string;
  /** Sentence explaining what to do next. */
  description?: string;
  /** Icon override; defaults to an inbox. */
  icon?: LucideIcon;
  /** Optional call-to-action, typically a button or a link. */
  action?: ReactNode;
}

/**
 * View shown when a request succeeded but returned nothing.
 *
 * Kept visually distinct from {@link ErrorState}: an empty result is a normal
 * outcome, and must not look like a failure.
 *
 * @param props - Title, description, icon and optional action.
 * @returns The empty view.
 */
export function EmptyState({
  title,
  description,
  icon: Icon = Inbox,
  action,
}: EmptyStateProps): JSX.Element {
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-6 py-14 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-surface-raised text-content-muted">
        <Icon size={22} aria-hidden="true" />
      </span>
      <div>
        <p className="text-sm font-medium text-content">{title}</p>
        {description && (
          <p className="mt-1 max-w-sm text-sm text-content-muted">{description}</p>
        )}
      </div>
      {action}
    </div>
  );
}

/** Props for {@link ErrorState}. */
export interface ErrorStateProps {
  /**
   * Display-ready Vietnamese message.
   *
   * Always comes from the API layer, which strips anything internal — a raw
   * exception must never be passed here.
   */
  message: string;
  /** Retry handler; the button is hidden when omitted. */
  onRetry?: () => void;
  /** Correlation id, shown so the user can quote it when reporting a problem. */
  requestId?: string;
}

/**
 * View shown when a request failed.
 *
 * @param props - Message, optional retry handler and request id.
 * @returns The error view.
 */
export function ErrorState({
  message,
  onRetry,
  requestId,
}: ErrorStateProps): JSX.Element {
  return (
    <div
      className="flex flex-col items-center justify-center gap-3 px-6 py-14 text-center"
      role="alert"
    >
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-danger/10 text-danger">
        <AlertCircle size={22} aria-hidden="true" />
      </span>
      <div>
        <p className="text-sm font-medium text-content">Không tải được dữ liệu</p>
        <p className="mt-1 max-w-md text-sm text-content-muted">{message}</p>
        {requestId && (
          <p className="mt-2 font-mono text-xs text-content-muted">
            Mã yêu cầu: {requestId}
          </p>
        )}
      </div>
      {onRetry && (
        <button type="button" onClick={onRetry} className="btn-secondary">
          <RefreshCw size={15} aria-hidden="true" />
          Thử lại
        </button>
      )}
    </div>
  );
}

/** Props for {@link InlineError}. */
export interface InlineErrorProps {
  /** Display-ready Vietnamese message. */
  message: string;
  /** Dismiss handler; the close button is hidden when omitted. */
  onDismiss?: () => void;
}

/**
 * Compact error banner for failures beside content that is still usable.
 *
 * Used where {@link ErrorState} would be too heavy — for example when an upload
 * fails but the form should stay on screen.
 *
 * @param props - Message and optional dismiss handler.
 * @returns The banner.
 */
export function InlineError({ message, onDismiss }: InlineErrorProps): JSX.Element {
  return (
    <div
      className="flex items-start gap-2.5 rounded-lg border border-danger/30 bg-danger/5 px-4 py-3"
      role="alert"
    >
      <AlertCircle size={17} className="mt-0.5 shrink-0 text-danger" aria-hidden="true" />
      <p className="flex-1 text-sm text-content">{message}</p>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="text-xs font-medium text-content-muted hover:text-content"
        >
          Đóng
        </button>
      )}
    </div>
  );
}

/** Props for {@link PageSection}. */
export interface PageSectionProps {
  /** Section heading. */
  title: string;
  /** Optional supporting line under the heading. */
  subtitle?: string;
  /** Controls rendered at the right of the header row. */
  actions?: ReactNode;
  /** Section body. */
  children: ReactNode;
  /** Extra classes for the wrapping card. */
  className?: string;
}

/**
 * Card with a titled header, used to group content on a page.
 *
 * @param props - Title, subtitle, actions and body.
 * @returns The section card.
 */
export function PageSection({
  title,
  subtitle,
  actions,
  children,
  className = '',
}: PageSectionProps): JSX.Element {
  return (
    <section className={`card ${className}`}>
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-3.5">
        <div className="min-w-0">
          <h2 className="text-sm font-semibold text-content">{title}</h2>
          {subtitle && (
            <p className="mt-0.5 text-xs text-content-muted">{subtitle}</p>
          )}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </header>
      <div className="p-5">{children}</div>
    </section>
  );
}
