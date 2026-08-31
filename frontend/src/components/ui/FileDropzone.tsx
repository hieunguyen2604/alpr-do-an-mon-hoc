/** Drag-and-drop file picker with client-side validation and multi-file support. */

import { useCallback, useId, useRef, useState } from 'react';
import { Upload, X } from 'lucide-react';
import type { DragEvent, ReactNode } from 'react';

import { cn } from '@/lib/cn';
import { formatFileSize } from '@/lib/format';

export interface FileDropzoneProps {
  /** Called with a file that passed validation (single mode). */
  onFileSelect?: (file: File) => void;
  /** Called with multiple valid files (multiple mode). */
  onFilesSelect?: (files: File[]) => void;
  /** Whether multiple files can be selected simultaneously. */
  multiple?: boolean;
  acceptedTypes: readonly string[];
  maxSizeMb: number;
  acceptedLabel: string;
  selectedFile?: File | null;
  onClear?: () => void;
  disabled?: boolean;
  label?: string;
  children?: ReactNode;
  className?: string;
}

function validateFile(
  file: File,
  acceptedTypes: readonly string[],
  maxSizeMb: number,
  acceptedLabel: string,
): string | null {
  if (file.type && !acceptedTypes.includes(file.type)) {
    return `Định dạng tệp không được hỗ trợ. Vui lòng chọn tệp ${acceptedLabel}.`;
  }

  const maxBytes = maxSizeMb * 1024 * 1024;
  if (file.size > maxBytes) {
    return `Tệp có dung lượng ${formatFileSize(
      file.size,
    )}, vượt quá giới hạn ${maxSizeMb} MB.`;
  }

  if (file.size === 0) {
    return 'Tệp rỗng. Vui lòng chọn một tệp khác.';
  }

  return null;
}

export function FileDropzone({
  onFileSelect,
  onFilesSelect,
  multiple = false,
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
  const dragDepthRef = useRef(0);

  const handleFiles = useCallback(
    (fileList: FileList | null | undefined) => {
      if (!fileList || fileList.length === 0) return;
      const validFiles: File[] = [];
      let firstError: string | null = null;

      for (let i = 0; i < fileList.length; i++) {
        const f = fileList[i];
        if (!f) continue;
        const err = validateFile(f, acceptedTypes, maxSizeMb, acceptedLabel);
        if (err) {
          if (!firstError) firstError = `${f.name}: ${err}`;
        } else {
          validFiles.push(f);
        }
      }

      if (firstError && validFiles.length === 0) {
        setError(firstError);
        return;
      }

      setError(null);
      if (multiple && onFilesSelect && validFiles.length > 0) {
        onFilesSelect(validFiles);
      } else if (validFiles[0] && onFileSelect) {
        onFileSelect(validFiles[0]);
      }
    },
    [acceptedTypes, maxSizeMb, acceptedLabel, multiple, onFileSelect, onFilesSelect],
  );

  const handleDrop = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      dragDepthRef.current = 0;
      setIsDragging(false);
      if (disabled) return;
      handleFiles(event.dataTransfer.files);
    },
    [disabled, handleFiles],
  );

  const handleDragEnter = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      if (disabled) return;
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
          'flex flex-col items-center justify-center gap-3 rounded-2xl',
          'border-2 border-dashed px-6 py-10 text-center transition-all',
          disabled
            ? 'cursor-not-allowed border-border bg-surface-muted opacity-60'
            : 'cursor-pointer border-border bg-surface hover:border-primary hover:bg-primary/5 shadow-sm',
          isDragging && !disabled && 'border-primary bg-primary/10 scale-[0.99]',
          error && 'border-danger',
        )}
      >
        {children ?? (
          <>
            <div
              aria-hidden="true"
              className={cn(
                'flex h-12 w-12 items-center justify-center rounded-2xl font-bold',
                'bg-primary/10 text-primary border border-primary/20 shadow-sm',
              )}
            >
              <Upload className="h-6 w-6" />
            </div>

            <div>
              <p className="text-sm font-semibold text-content">{label}</p>
              <p className="mt-1 text-xs text-content-muted">
                Hỗ trợ {acceptedLabel} · Tối đa {maxSizeMb} MB {multiple && '· Chọn nhiều ảnh cùng lúc'}
              </p>
            </div>
          </>
        )}

        <input
          ref={inputRef}
          id={inputId}
          type="file"
          multiple={multiple}
          className="sr-only"
          accept={acceptedTypes.join(',')}
          disabled={disabled}
          onChange={(event) => {
            handleFiles(event.target.files);
            event.target.value = '';
          }}
          onClick={(event) => event.stopPropagation()}
        />
      </div>

      {selectedFile && !multiple && (
        <div
          className={cn(
            'mt-3 flex items-center justify-between gap-3 rounded-xl',
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
          className="mt-2 text-sm text-danger font-medium"
        >
          {error}
        </p>
      )}
    </div>
  );
}

export default FileDropzone;
