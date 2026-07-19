/**
 * Drag-and-drop file picker with client-side validation.
 *
 * The checks here are a **convenience, not a control**. The backend validates
 * independently — it identifies a file by its magic bytes rather than by its
 * extension or `Content-Type` (NFR-S1) and enforces its own size ceiling — and
 * will reject a bad file with 413 or 415 whatever this component allows.
 * Checking in the browser only spares the user a pointless upload of a file
 * that was never going to be accepted.
 */

import { useCallback, useId, useRef, useState } from 'react';
import { Upload, X } from 'lucide-react';
import type { DragEvent, ReactNode } from 'react';

import { cn } from '@/lib/cn';
import { formatFileSize } from '@/lib/format';

/** Props of {@link FileDropzone}. */
export interface FileDropzoneProps {
  /** Called with a file that passed validation. */
  onFileSelect: (file: File) => void;
  /** MIME types to accept. */
  acceptedTypes: readonly string[];
  /** Largest accepted size, in megabytes. */
  maxSizeMb: number;
  /** Human-readable format list, e.g. `"JPG, PNG, WebP, BMP"`. */
  acceptedLabel: string;
  /** Currently selected file, shown as a summary. */
  selectedFile?: File | null;
  /** Called when the user clears the selection. */
  onClear?: () => void;
  /** Block interaction, e.g. while an upload is running. */
  disabled?: boolean;
  /** Main instruction. */
  label?: string;
  /** Replaces the default body, for a preview of the selected file. */
  children?: ReactNode;
  className?: string;
}

/**
 * Validate a file against the accepted types and size.
 *
 * @param file - The file to check.
 * @param acceptedTypes - Accepted MIME types.
 * @param maxSizeMb - Size ceiling in megabytes.
 * @param acceptedLabel - Human-readable format list, named in the message so
 *   the user is told what *is* accepted rather than only that this was not.
 * @returns A Vietnamese error message, or `null` when the file is acceptable.
 */
function validateFile(
  file: File,
  acceptedTypes: readonly string[],
  maxSizeMb: number,
  acceptedLabel: string,
): string | null {
  // Some browsers report an empty type for less common formats. Treated as
  // acceptable and left to the server, whose magic-byte check is authoritative
  // anyway — rejecting here would block a valid file on a browser quirk.
  if (file.type && !acceptedTypes.includes(file.type)) {
    return `Định dạng tệp không được hỗ trợ. Vui lòng chọn tệp ${acceptedLabel}.`;
  }

  const maxBytes = maxSizeMb * 1024 * 1024;
  if (file.size > maxBytes) {
    return `Tệp có dung lượng ${formatFileSize(
      file.size,
    )}, vượt quá giới hạn ${maxSizeMb} MB. Vui lòng chọn tệp nhỏ hơn.`;
  }

  if (file.size === 0) {
    return 'Tệp rỗng. Vui lòng chọn một tệp khác.';
  }

  return null;
}

/**
 * Render a dropzone.
 *
 * @param props - Selection handler, accepted types, size limit and state.
 * @returns The dropzone element.
 */
export function FileDropzone({
  onFileSelect,
  acceptedTypes,
  maxSizeMb,
  acceptedLabel,
  selectedFile,
  onClear,
  disabled = false,
  label = 'Kéo thả tệp vào đây hoặc bấm để chọn',
  children,
  className,
}: FileDropzoneProps): JSX.Element {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const inputId = useId();
  const errorId = `${inputId}-error`;

  // Drag events fire on every child element too, so a plain boolean would
  // flicker as the pointer crosses the inner text. Counting enter and leave
  // events keeps the highlight steady.
  const dragDepthRef = useRef(0);

  const handleFile = useCallback(
    (file: File | undefined) => {
      if (!file) {
        return;
      }
      const validationError = validateFile(
        file,
        acceptedTypes,
        maxSizeMb,
        acceptedLabel,
      );
      if (validationError) {
        setError(validationError);
        return;
      }
      setError(null);
      onFileSelect(file);
    },
    [acceptedTypes, maxSizeMb, acceptedLabel, onFileSelect],
  );

  const handleDrop = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      dragDepthRef.current = 0;
      setIsDragging(false);
      if (disabled) {
        return;
      }
      handleFile(event.dataTransfer.files[0]);
    },
    [disabled, handleFile],
  );

  const handleDragEnter = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      if (disabled) {
        return;
      }
      dragDepthRef.current += 1;
      setIsDragging(true);
    },
    [disabled],
  );

  const handleDragLeave = useCallback((event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    dragDepthRef.current -= 1;
    if (dragDepthRef.current <= 0) {
      dragDepthRef.current = 0;
      setIsDragging(false);
    }
  }, []);

  const openPicker = useCallback(() => {
    if (!disabled) {
      inputRef.current?.click();
    }
  }, [disabled]);

  return (
    <div className={className}>
      <div
        onDrop={handleDrop}
        onDragOver={(event) => event.preventDefault()}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onClick={openPicker}
        onKeyDown={(event) => {
          // Drag and drop is unusable from a keyboard, so the zone must also
          // work as a plain button.
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            openPicker();
          }
        }}
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label={label}
        aria-disabled={disabled}
        aria-describedby={error ? errorId : undefined}
        className={cn(
          'flex flex-col items-center justify-center gap-3 rounded-xl',
          'border-2 border-dashed px-6 py-10 text-center transition-colors',
          disabled
            ? 'cursor-not-allowed border-border bg-surface-muted opacity-60'
            : 'cursor-pointer border-border bg-surface hover:border-primary hover:bg-primary/5',
          isDragging && !disabled && 'border-primary bg-primary/10',
          error && 'border-danger',
        )}
      >
        {children ?? (
          <>
            <div
              aria-hidden="true"
              className={cn(
                'flex h-12 w-12 items-center justify-center rounded-full',
                'bg-surface-raised text-content-muted',
              )}
            >
              <Upload className="h-6 w-6" />
            </div>

            <div>
              <p className="text-sm font-medium text-content">{label}</p>
              <p className="mt-1 text-xs text-content-muted">
                Hỗ trợ {acceptedLabel} · Tối đa {maxSizeMb} MB
              </p>
            </div>
          </>
        )}

        <input
          ref={inputRef}
          id={inputId}
          type="file"
          className="sr-only"
          accept={acceptedTypes.join(',')}
          disabled={disabled}
          // Cleared after each pick so that choosing the same file twice in a
          // row still fires a change event.
          onChange={(event) => {
            handleFile(event.target.files?.[0]);
            event.target.value = '';
          }}
          // The click is delegated from the wrapper; without this a click on
          // the input would bubble back up and reopen the picker.
          onClick={(event) => event.stopPropagation()}
        />
      </div>

      {selectedFile && (
        <div
          className={cn(
            'mt-3 flex items-center justify-between gap-3 rounded-lg',
            'border border-border bg-surface px-3 py-2',
          )}
        >
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-content">
              {selectedFile.name}
            </p>
            <p className="text-xs text-content-muted">
              {formatFileSize(selectedFile.size)}
            </p>
          </div>
          {onClear && (
            <button
              type="button"
              onClick={onClear}
              disabled={disabled}
              aria-label="Bỏ chọn tệp"
              className={cn(
                'shrink-0 rounded-lg p-1.5 text-content-muted transition-colors',
                'hover:bg-surface-raised hover:text-content',
                'disabled:cursor-not-allowed disabled:opacity-50',
              )}
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
          )}
        </div>
      )}

      {error && (
        <p
          id={errorId}
          role="alert"
          className="mt-2 text-sm text-danger"
        >
          {error}
        </p>
      )}
    </div>
  );
}

export default FileDropzone;
