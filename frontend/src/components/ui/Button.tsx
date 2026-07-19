/**
 * The application's button.
 */

import { forwardRef } from 'react';
import type { ButtonHTMLAttributes, ReactNode } from 'react';

import { cn } from '@/lib/cn';
import { Spinner } from './Spinner';

/** Visual weight of a button. */
export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';

/** Size presets. */
export type ButtonSize = 'sm' | 'md' | 'lg';

/** Props of {@link Button}. */
export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /**
   * Show a spinner and block interaction.
   *
   * Required for anything that can take more than 500 ms (NFR-U2): without it
   * a user who sees no reaction clicks again, and a second upload is submitted.
   */
  isLoading?: boolean;
  /** Text shown while `isLoading`. Falls back to the normal children. */
  loadingText?: string;
  /** Icon placed before the label. */
  leftIcon?: ReactNode;
  /** Icon placed after the label. */
  rightIcon?: ReactNode;
  /** Stretch to the full width of the container. */
  fullWidth?: boolean;
  children?: ReactNode;
}

/**
 * Variant styles.
 *
 * In dark mode the primary and danger fills become light (blue-400, red-400),
 * where white text would fall to roughly 2.7:1. Those variants therefore switch
 * to near-black text in the dark theme to hold the 4.5:1 that NFR-U5 requires.
 */
const VARIANT_CLASS: Readonly<Record<ButtonVariant, string>> = {
  primary:
    'bg-primary text-white hover:bg-primary-hover dark:text-slate-950 ' +
    'focus-visible:ring-primary',
  secondary:
    'border border-border bg-surface text-content hover:bg-surface-raised ' +
    'focus-visible:ring-primary',
  danger:
    'bg-danger text-white hover:brightness-110 dark:text-slate-950 ' +
    'focus-visible:ring-danger',
  ghost:
    'bg-transparent text-content hover:bg-surface-raised ' +
    'focus-visible:ring-primary',
};

const SIZE_CLASS: Readonly<Record<ButtonSize, string>> = {
  sm: 'px-3 py-1.5 text-xs gap-1.5',
  md: 'px-4 py-2 text-sm gap-2',
  lg: 'px-5 py-2.5 text-base gap-2',
};

/**
 * Render a button.
 *
 * Forwards its ref so a parent can focus it — a modal returning focus to the
 * control that opened it, for instance.
 *
 * @param props - Variant, size, loading state and native button attributes.
 * @returns The button element.
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  function Button(
    {
      variant = 'primary',
      size = 'md',
      isLoading = false,
      loadingText,
      leftIcon,
      rightIcon,
      fullWidth = false,
      className,
      children,
      disabled,
      type = 'button',
      ...rest
    },
    ref,
  ) {
    // A loading button must not be clickable, whatever `disabled` says.
    const isDisabled = disabled === true || isLoading;

    return (
      <button
        ref={ref}
        // Defaults to "button": an unspecified type inside a form is "submit",
        // so a stray action button would submit the form it happens to sit in.
        type={type}
        disabled={isDisabled}
        // Announces the pending state; `disabled` alone tells a screen reader
        // the control is unavailable, not that it is working.
        aria-busy={isLoading}
        className={cn(
          'inline-flex items-center justify-center rounded-lg font-medium',
          'transition-colors focus-visible:outline-none focus-visible:ring-2',
          'focus-visible:ring-offset-2 focus-visible:ring-offset-surface',
          'disabled:cursor-not-allowed disabled:opacity-50',
          VARIANT_CLASS[variant],
          SIZE_CLASS[size],
          fullWidth && 'w-full',
          className,
        )}
        {...rest}
      >
        {isLoading ? (
          <Spinner size="sm" className="text-current" label="" />
        ) : (
          leftIcon
        )}
        {isLoading && loadingText ? loadingText : children}
        {!isLoading && rightIcon}
      </button>
    );
  },
);

export default Button;
