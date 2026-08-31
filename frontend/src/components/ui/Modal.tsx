/** Modal dialog rendered through a portal with focus management. */

import { useCallback, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import type { ReactNode } from 'react';

import { cn } from '@/lib/cn';

/** Width presets. */
export type ModalSize = 'sm' | 'md' | 'lg' | 'xl';

/** Props of {@link Modal}. */
export interface ModalProps {
  isOpen: boolean;
  /** Called on Escape, a backdrop click or the close button. */
  onClose: () => void;
  /** Heading, also used as the dialog's accessible name. */
  title?: ReactNode;
  description?: ReactNode;
  /** Footer content, typically the confirm and cancel buttons. */
  footer?: ReactNode;
  size?: ModalSize;
  /** Allow closing by clicking the backdrop. */
  closeOnBackdrop?: boolean;
  /** Allow closing with the Escape key. */
  closeOnEscape?: boolean;
  /** Show the close button in the header. */
  showCloseButton?: boolean;
  children?: ReactNode;
}

const SIZE_CLASS: Readonly<Record<ModalSize, string>> = {
  sm: 'max-w-sm',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
};

/** Selector matching everything focusable inside the dialog. */
const FOCUSABLE_SELECTOR = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',');

/** Render a modal dialog through a portal (returns `null` when closed). */
export function Modal({
  isOpen,
  onClose,
  title,
  description,
  footer,
  size = 'md',
  closeOnBackdrop = true,
  closeOnEscape = true,
  showCloseButton = true,
  children,
}: ModalProps): JSX.Element | null {
  const dialogRef = useRef<HTMLDivElement>(null);
  // The element that had focus before opening, so it can be restored on close.
  const triggerRef = useRef<HTMLElement | null>(null);

  // Held in a ref so the key handler does not need to be rebuilt — and the
  // listener re-registered — every time the parent passes a new arrow function.
  const onCloseRef = useRef(onClose);
  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  // Lock background scrolling. Without this the page behind the dialog scrolls
  // under the pointer, which on a long history list loses the user's place.
  useEffect(() => {
    if (!isOpen) {
      return;
    }
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      // Restores whatever was there before rather than clearing it, so two
      // stacked dialogs cannot unlock the page when the inner one closes.
      document.body.style.overflow = previousOverflow;
    };
  }, [isOpen]);

  // Move focus into the dialog on open, restore it on close.
  useEffect(() => {
    if (!isOpen) {
      return;
    }
    triggerRef.current = document.activeElement as HTMLElement | null;

    const firstFocusable = dialogRef.current?.querySelector<HTMLElement>(
      FOCUSABLE_SELECTOR,
    );
    (firstFocusable ?? dialogRef.current)?.focus();

    return () => {
      triggerRef.current?.focus();
    };
  }, [isOpen]);

  // Escape to close, Tab cycling kept inside the dialog.
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent): void => {
      if (event.key === 'Escape' && closeOnEscape) {
        event.stopPropagation();
        onCloseRef.current();
        return;
      }

      if (event.key !== 'Tab') {
        return;
      }

      // Focus trap: without it, Tab walks out of the dialog and into the page
      // behind it, where a keyboard user is then editing controls they cannot
      // see.
      const focusable = dialogRef.current?.querySelectorAll<HTMLElement>(
        FOCUSABLE_SELECTOR,
      );
      if (!focusable || focusable.length === 0) {
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (!first || !last) {
        return;
      }

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, closeOnEscape]);

  const handleBackdropClick = useCallback(() => {
    if (closeOnBackdrop) {
      onCloseRef.current();
    }
  }, [closeOnBackdrop]);

  if (!isOpen) {
    return null;
  }

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop. A plain div rather than a button: it is not a control a
          keyboard user should reach, since Escape already closes the dialog. */}
      <div
        aria-hidden="true"
        onClick={handleBackdropClick}
        className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm"
      />

      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label={typeof title === 'string' ? title : 'Hộp thoại'}
        tabIndex={-1}
        className={cn(
          'relative z-10 w-full overflow-hidden rounded-xl',
          'border border-border bg-surface shadow-xl',
          'animate-fade-in',
          SIZE_CLASS[size],
        )}
      >
        {(title ?? showCloseButton) && (
          <header className="flex items-start justify-between gap-3 border-b border-border px-5 py-4">
            <div className="min-w-0">
              {title && (
                <h2 className="text-base font-semibold text-content">
                  {title}
                </h2>
              )}
              {description && (
                <p className="mt-1 text-sm text-content-muted">{description}</p>
              )}
            </div>
            {showCloseButton && (
              <button
                type="button"
                onClick={onClose}
                aria-label="Đóng hộp thoại"
                className={cn(
                  'shrink-0 rounded-lg p-1.5 text-content-muted',
                  'transition-colors hover:bg-surface-raised hover:text-content',
                )}
              >
                <X className="h-5 w-5" aria-hidden="true" />
              </button>
            )}
          </header>
        )}

        <div className="max-h-[70vh] overflow-y-auto px-5 py-4">{children}</div>

        {footer && (
          <footer className="flex flex-wrap items-center justify-end gap-2 border-t border-border px-5 py-4">
            {footer}
          </footer>
        )}
      </div>
    </div>,
    document.body,
  );
}

export default Modal;
