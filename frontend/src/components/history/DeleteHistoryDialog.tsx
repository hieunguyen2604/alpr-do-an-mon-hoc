/**
 * Confirmation dialog for deleting a history record (FR-5.1).
 *
 * Deletion is irreversible and takes the stored media with it, so it is put
 * behind an explicit confirmation rather than behind a single click on a small
 * icon in a dense table. The dialog states plainly what else disappears — a
 * user who expects only the row to go would otherwise lose the source image
 * without ever being told.
 */

import { AlertTriangle, Trash2 } from 'lucide-react';

import { Button, Modal, PlateChip } from '@/components/ui';
import { formatDateTime } from '@/lib/format';
import type { DetectionHistory } from '@/types';

/** Props of {@link DeleteHistoryDialog}. */
export interface DeleteHistoryDialogProps {
  /** Record awaiting confirmation, or `null` when the dialog is closed. */
  record: DetectionHistory | null;
  /** Whether the delete request is in flight. */
  isDeleting: boolean;
  /**
   * Display-ready Vietnamese message from a failed attempt, or `null`.
   *
   * Shown inside the dialog rather than behind it: the dialog stays open on
   * failure so the user can simply try again, instead of having to find the row
   * a second time.
   */
  error: string | null;
  onConfirm: () => void;
  onCancel: () => void;
}

/**
 * Render the delete confirmation dialog.
 *
 * @param props - The record, the request state and the handlers.
 * @returns The dialog, or `null` when nothing is pending confirmation.
 */
export function DeleteHistoryDialog({
  record,
  isDeleting,
  error,
  onConfirm,
  onCancel,
}: DeleteHistoryDialogProps): JSX.Element | null {
  if (!record) {
    return null;
  }

  return (
    <Modal
      isOpen
      onClose={onCancel}
      size="md"
      title="Xoá bản ghi này?"
      // Closing mid-request would leave the user unsure whether the deletion
      // went through, so both escape routes are shut while it runs.
      closeOnBackdrop={!isDeleting}
      closeOnEscape={!isDeleting}
      showCloseButton={!isDeleting}
      footer={
        <>
          <Button variant="secondary" onClick={onCancel} disabled={isDeleting}>
            Huỷ
          </Button>
          <Button
            variant="danger"
            onClick={onConfirm}
            isLoading={isDeleting}
            loadingText="Đang xoá…"
            leftIcon={<Trash2 className="h-4 w-4" />}
          >
            Xoá bản ghi
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <div className="flex items-start gap-3">
          <span
            aria-hidden="true"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-danger/10 text-danger"
          >
            <AlertTriangle className="h-5 w-5" />
          </span>
          <div className="space-y-1">
            <p className="text-sm text-content">
              Thao tác này không thể hoàn tác. Ảnh gốc và ảnh biển số đã cắt
              cũng sẽ bị xoá khỏi máy chủ.
            </p>
            <p className="text-sm text-content-muted">
              Các biển số khác thuộc cùng lần tải lên sẽ không bị ảnh hưởng.
            </p>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-surface-raised p-4">
          <div className="flex flex-wrap items-center gap-3">
            <PlateChip
              plateNumber={record.plate_number}
              isValidFormat={record.is_valid_format}
              size="sm"
            />
            <span className="text-sm text-content-muted">
              {formatDateTime(record.detected_time)}
            </span>
          </div>
        </div>

        {error && (
          <p
            role="alert"
            className="rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger"
          >
            {error}
          </p>
        )}
      </div>
    </Modal>
  );
}

export default DeleteHistoryDialog;
