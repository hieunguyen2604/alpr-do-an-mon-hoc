"""Querying, exporting and deleting stored detection records."""

from __future__ import annotations

import csv
import datetime as dt
import io
from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from backend.core.exceptions import NotFoundError, ValidationError
from backend.core.logging import get_logger
from backend.models.detection import DetectionHistory
from backend.schemas.detection import DetectionHistoryResponse, HistoryListResponse
from backend.services.detection_service import display_text
from backend.services.storage_service import StorageService

__all__ = [
    "SortField",
    "SortOrder",
    "HistoryFilter",
    "HistoryService",
    "MAX_PAGE_SIZE",
]

logger = get_logger(__name__)

MAX_PAGE_SIZE: Final[int] = 100
"""Largest page a client may request."""

_EXPORT_BATCH_SIZE: Final[int] = 500
"""Rows fetched per round trip while streaming an export."""


class SortField(StrEnum):
    """Columns the history list may be ordered by."""

    DETECTED_TIME = "detected_time"
    CREATED_AT = "created_at"
    PLATE_NUMBER = "plate_number"
    CONFIDENCE = "confidence"
    OCR_CONFIDENCE = "ocr_confidence"
    PROCESSING_TIME = "processing_time"
    ID = "id"


class SortOrder(StrEnum):
    """Sort direction."""

    ASC = "asc"
    DESC = "desc"


@dataclass(frozen=True, slots=True)
class HistoryFilter:
    """The set of conditions narrowing a history query."""

    search: str | None = None
    input_type: str | None = None
    is_valid_format: bool | None = None
    date_from: dt.datetime | None = None
    date_to: dt.datetime | None = None
    min_confidence: float | None = None
    job_id: str | None = None

    def validate(self) -> None:
        """Check the filter for self-contradictory values."""
        if (
            self.date_from is not None
            and self.date_to is not None
            and self.date_from > self.date_to
        ):
            raise ValidationError(
                f"date_from ({self.date_from}) is after date_to ({self.date_to})",
                user_message=(
                    "Khoảng thời gian không hợp lệ: ngày bắt đầu phải trước ngày kết thúc."
                ),
            )
        if self.min_confidence is not None and not 0.0 <= self.min_confidence <= 1.0:
            raise ValidationError(
                f"min_confidence must be within [0.0, 1.0], got {self.min_confidence}",
                user_message="Ngưỡng độ tin cậy phải nằm trong khoảng từ 0 đến 1.",
            )


# Column headers of the CSV export (Vietnamese for end-user Excel export)
_CSV_HEADERS: Final[tuple[str, ...]] = (
    "ID",
    "Biển số",
    "Chuỗi OCR thô",
    "Độ tin cậy phát hiện",
    "Độ tin cậy OCR",
    "Loại đầu vào",
    "Đúng định dạng",
    "Số dòng",
    "Thời gian xử lý (giây)",
    "Thời điểm phát hiện (UTC)",
    "Mã lượt tải lên",
)


class HistoryService:
    """Reads, exports and deletes stored detection records."""

    def __init__(self, storage: StorageService) -> None:
        """Create the service."""
        self._storage = storage

    # -- Mapping ----------------------------------------------------------

    def _to_response(self, row: DetectionHistory) -> DetectionHistoryResponse:
        """Map one ORM row to its API representation."""
        return DetectionHistoryResponse(
            id=row.id,
            plate_number=row.plate_number,
            raw_ocr_text=row.raw_ocr_text,
            confidence=row.confidence,
            ocr_confidence=row.ocr_confidence,
            input_type=row.input_type,  # type: ignore[arg-type]
            image_path=self._storage.to_url(row.image_path),
            plate_image_path=self._storage.to_url(row.plate_image_path),
            bbox_x=row.bbox_x,
            bbox_y=row.bbox_y,
            bbox_w=row.bbox_w,
            bbox_h=row.bbox_h,
            is_valid_format=row.is_valid_format,
            # Explicit vehicle-class fields mapping
            plate_kind=row.plate_kind,
            plate_color=row.plate_color,
            plate_color_confidence=row.plate_color_confidence,
            plate_display=display_text(
                row.plate_number, row.plate_line_count, row.plate_kind, row.upper_char_count
            ),
            video_time_seconds=row.video_time_seconds,
            plate_line_count=row.plate_line_count,
            processing_time=row.processing_time,
            detected_time=row.detected_time,
            created_at=row.created_at,
            source_job_id=row.source_job_id,
        )

    # -- Query building ---------------------------------------------------

    @staticmethod
    def _apply_filter(
        statement: Select[tuple[DetectionHistory]], criteria: HistoryFilter
    ) -> Select[tuple[DetectionHistory]]:
        """Add every active condition of a filter to a query."""
        if criteria.search:
            # Escape LIKE wildcards to prevent unintended matches
            needle = criteria.search.strip().replace("\\", "\\\\")
            needle = needle.replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{needle}%"
            statement = statement.where(
                or_(
                    DetectionHistory.plate_number.ilike(pattern, escape="\\"),
                    DetectionHistory.raw_ocr_text.ilike(pattern, escape="\\"),
                )
            )
        if criteria.input_type:
            statement = statement.where(DetectionHistory.input_type == criteria.input_type)
        if criteria.is_valid_format is not None:
            statement = statement.where(
                DetectionHistory.is_valid_format.is_(criteria.is_valid_format)
            )
        if criteria.date_from is not None:
            statement = statement.where(DetectionHistory.detected_time >= criteria.date_from)
        if criteria.date_to is not None:
            statement = statement.where(DetectionHistory.detected_time <= criteria.date_to)
        if criteria.min_confidence is not None:
            statement = statement.where(DetectionHistory.confidence >= criteria.min_confidence)
        if criteria.job_id:
            statement = statement.where(DetectionHistory.source_job_id == criteria.job_id)
        return statement

    @staticmethod
    def _apply_sort(
        statement: Select[tuple[DetectionHistory]],
        sort_by: SortField,
        order: SortOrder,
    ) -> Select[tuple[DetectionHistory]]:
        """Add an ``ORDER BY`` clause, with a tiebreaker."""
        column = getattr(DetectionHistory, sort_by.value)
        if order is SortOrder.DESC:
            return statement.order_by(column.desc(), DetectionHistory.id.desc())
        return statement.order_by(column.asc(), DetectionHistory.id.asc())

    # -- Reading ----------------------------------------------------------

    def list_history(
        self,
        db: Session,
        *,
        page: int = 1,
        page_size: int = 20,
        criteria: HistoryFilter | None = None,
        sort_by: SortField = SortField.DETECTED_TIME,
        order: SortOrder = SortOrder.DESC,
    ) -> HistoryListResponse:
        """Return one page of detection records."""
        if page < 1:
            raise ValidationError(
                f"page must be >= 1, got {page}",
                user_message="Số trang phải lớn hơn hoặc bằng 1.",
            )
        if not 1 <= page_size <= MAX_PAGE_SIZE:
            raise ValidationError(
                f"page_size must be within [1, {MAX_PAGE_SIZE}], got {page_size}",
                user_message=f"Số bản ghi mỗi trang phải nằm trong khoảng 1 đến {MAX_PAGE_SIZE}.",
            )

        criteria = criteria or HistoryFilter()
        criteria.validate()

        # Count matching records without ORDER BY overhead
        count_statement = self._apply_filter(
            select(func.count()).select_from(DetectionHistory), criteria
        )
        total = int(db.execute(count_statement).scalar_one())

        statement = self._apply_filter(select(DetectionHistory), criteria)
        statement = self._apply_sort(statement, sort_by, order)
        statement = statement.offset((page - 1) * page_size).limit(page_size)
        rows = db.execute(statement).scalars().all()

        return HistoryListResponse.build(
            items=[self._to_response(row) for row in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_by_id(self, db: Session, detection_id: int) -> DetectionHistoryResponse:
        """Return one detection record."""
        row = db.get(DetectionHistory, detection_id)
        if row is None:
            raise NotFoundError.for_resource("detection", detection_id)
        return self._to_response(row)

    # -- Deleting ---------------------------------------------------------

    def delete(self, db: Session, detection_id: int) -> None:
        """Delete one detection record and the files that belong only to it."""
        row = db.get(DetectionHistory, detection_id)
        if row is None:
            raise NotFoundError.for_resource("detection", detection_id)

        plate_crop = row.plate_image_path
        source_image = row.image_path

        db.delete(row)
        db.flush()

        siblings = 0
        if source_image:
            siblings = int(
                db.execute(
                    select(func.count())
                    .select_from(DetectionHistory)
                    .where(DetectionHistory.image_path == source_image)
                ).scalar_one()
            )
        db.commit()

        self._storage.delete_file(plate_crop)
        if source_image and siblings == 0:
            self._storage.delete_file(source_image)

        logger.info(
            "detection record deleted",
            extra={
                "detection_id": detection_id,
                "source_image_kept": bool(source_image) and siblings > 0,
            },
        )

    # -- Exporting --------------------------------------------------------

    def export_csv(
        self,
        db: Session,
        *,
        criteria: HistoryFilter | None = None,
        sort_by: SortField = SortField.DETECTED_TIME,
        order: SortOrder = SortOrder.DESC,
    ) -> Iterator[str]:
        """Stream the matching records as CSV text."""
        criteria = criteria or HistoryFilter()
        criteria.validate()

        statement = self._apply_filter(select(DetectionHistory), criteria)
        statement = self._apply_sort(statement, sort_by, order)

        buffer = io.StringIO()
        # Use CRLF line terminators for Excel compatibility
        writer = csv.writer(buffer, lineterminator="\r\n")

        def flush() -> str:
            """Return everything written so far and reset the buffer."""
            chunk = buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            return chunk

        writer.writerow(_CSV_HEADERS)
        yield "﻿" + flush()

        exported = 0
        for row in db.execute(statement).scalars().yield_per(_EXPORT_BATCH_SIZE):
            writer.writerow(self._csv_row(row))
            exported += 1
            if exported % _EXPORT_BATCH_SIZE == 0:
                yield flush()

        remainder = flush()
        if remainder:
            yield remainder

        logger.info("history exported", extra={"row_count": exported})

    @staticmethod
    def _csv_row(row: DetectionHistory) -> tuple[str, ...]:
        """Render one record as CSV cells."""
        return (
            str(row.id),
            row.plate_number or "",
            row.raw_ocr_text or "",
            f"{row.confidence:.4f}",
            f"{row.ocr_confidence:.4f}" if row.ocr_confidence is not None else "",
            row.input_type,
            "Có" if row.is_valid_format else "Không",
            str(row.plate_line_count) if row.plate_line_count is not None else "",
            f"{row.processing_time:.4f}",
            row.detected_time.strftime("%Y-%m-%d %H:%M:%S"),
            row.source_job_id,
        )
