/** Reusable loading, empty and error state views. */

import type { ReactNode } from 'react';
import { AlertCircle, Inbox, Loader2, RefreshCw } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

/** Props for LoadingState component. */
export interface LoadingStateProps {
  message?: string;
}

/** Centred loading spinner view. */
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

/** Props for EmptyState component. */
export interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  action?: ReactNode;
}

/** Empty data state view. */
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

/** Props for ErrorState component. */
export interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
  requestId?: string;
}

/** Error state display view with optional retry action. */
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

/** Props for InlineError component. */
export interface InlineErrorProps {
  message: string;
  onDismiss?: () => void;
}

/** Compact inline error banner. */
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

/** Props for PageSection component. */
export interface PageSectionProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}

/** Card container with header for grouping page sections. */
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
