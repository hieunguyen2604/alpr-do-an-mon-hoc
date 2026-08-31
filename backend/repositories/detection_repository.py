"""Queries over the detection history table, including dashboard statistics."""

from __future__ import annotations

import datetime as dt
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Final

from sqlalchemy import ColumnElement, Select, case, func, select
from sqlalchemy.orm import InstrumentedAttribute

from backend.core.exceptions import ValidationError
from backend.models.detection import (
    DetectionHistory,
    DetectionJob,
    InputType,
    utcnow,
)
from backend.repositories.base import DEFAULT_PAGE_SIZE, BaseRepository

__all__ = [
    "HistoryFilter",
    "InputTypeCount",
    "DailyCount",
    "DetectionStatistics",
    "DetectionRepository",
    "HISTORY_SORT_COLUMNS",
    "DEFAULT_TREND_DAYS",
    "to_id_list",
]

DEFAULT_TREND_DAYS: Final[int] = 14
"""Days covered by the dashboard trend series when no window is given."""

MAX_TREND_DAYS: Final[int] = 365
"""Ceiling on the trend window.

A request for a ten-year series would build a list with thousands of entries,
almost all of them zero, and the chart would be unreadable long before the
response was large enough to matter.
"""

_LIKE_ESCAPE: Final[str] = "\\"
"""Escape character for ``LIKE`` patterns.

Required because a plate search is a substring match: a user typing ``%``
would otherwise inject a wildcard and match every row, and ``_`` would match
any single character. Both are plausible things to type by accident.
"""

_PLATE_SEPARATORS: Final[tuple[str, ...]] = ("-", ".", " ")
"""Characters stripped from both sides of a plate comparison.

Vietnamese plates are written ``51F-12345``, ``51F.12345`` or ``51F 12345``
depending on who is typing, and the stored value uses whichever form
normalisation produced. Comparing separator-free forms means a user searching
``51F12345`` finds ``51F-12345``, which is otherwise a "the search is broken"
bug report.
"""

HISTORY_SORT_COLUMNS: Final[dict[str, InstrumentedAttribute[Any]]] = {
    "detected_time": DetectionHistory.detected_time,
    "created_at": DetectionHistory.created_at,
    "confidence": DetectionHistory.confidence,
    "ocr_confidence": DetectionHistory.ocr_confidence,
    "processing_time": DetectionHistory.processing_time,
    "plate_number": DetectionHistory.plate_number,
    "input_type": DetectionHistory.input_type,
    "id": DetectionHistory.id,
}
"""Sort keys the history endpoint accepts, mapped to columns.

An allow-list rather than ``getattr``: the key arrives in a query string, and
an arbitrary attribute name would either raise inside the query builder or
resolve to a relationship and add an unintended join.
"""


@dataclass(frozen=True, slots=True)
class HistoryFilter:
    """Filter criteria for a history query."""

    plate_number: str | None = None
    input_type: str | None = None
    start_time: dt.datetime | None = None
    end_time: dt.datetime | None = None
    min_confidence: float | None = None
    min_ocr_confidence: float | None = None
    source_job_id: str | None = None
    is_valid_format: bool | None = None
    has_text: bool | None = None

    def __post_init__(self) -> None:
        """Reject criteria that cannot match anything."""
        if (
            self.start_time is not None
            and self.end_time is not None
            and self.end_time < self.start_time
        ):
            raise ValidationError(
                f"end_time {self.end_time!r} precedes start_time {self.start_time!r}",
                user_message=(
                    "Khoảng thời gian không hợp lệ: ngày kết thúc phải sau ngày bắt đầu."
                ),
            )

        for name, value in (
            ("min_confidence", self.min_confidence),
            ("min_ocr_confidence", self.min_ocr_confidence),
        ):
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValidationError(
                    f"{name} must be within [0.0, 1.0], got {value!r}",
                    user_message="Ngưỡng độ tin cậy phải nằm trong khoảng từ 0 đến 1.",
                    context={"field": name, "value": value},
                )

        if self.input_type is not None and self.input_type not in set(InputType):
            raise ValidationError(
                f"Unknown input_type {self.input_type!r}",
                user_message="Loại dữ liệu đầu vào không hợp lệ.",
                context={"input_type": self.input_type},
            )


@dataclass(frozen=True, slots=True)
class InputTypeCount:
    """Usage figures for one input type."""

    input_type: str
    job_count: int
    detection_count: int


@dataclass(frozen=True, slots=True)
class DailyCount:
    """Activity on one calendar day, in UTC."""

    date: dt.date
    job_count: int
    detection_count: int


@dataclass(frozen=True, slots=True)
class DetectionStatistics:
    """Aggregate dashboard figures."""

    total_jobs: int = 0
    total_detections: int = 0
    unique_plates: int = 0
    valid_format_count: int = 0
    invalid_format_count: int = 0
    unreadable_count: int = 0
    average_confidence: float | None = None
    average_ocr_confidence: float | None = None
    average_processing_time: float | None = None
    jobs_today: int = 0
    detections_today: int = 0
    by_input_type: list[InputTypeCount] = field(default_factory=list)
    daily_counts: list[DailyCount] = field(default_factory=list)


class DetectionRepository(BaseRepository[DetectionHistory, int]):
    """Reads and writes rows of ``detection_history``."""

    model = DetectionHistory

    # -- Filtering --------------------------------------------------------

    def _apply_filters(
        self,
        stmt: Select[tuple[DetectionHistory]],
        filters: HistoryFilter | None,
    ) -> Select[tuple[DetectionHistory]]:
        """Add the ``WHERE`` clauses described by a filter object."""
        if filters is None:
            return stmt

        if filters.plate_number:
            condition = self._plate_match_condition(filters.plate_number)
            if condition is not None:
                stmt = stmt.where(condition)

        if filters.input_type is not None:
            stmt = stmt.where(DetectionHistory.input_type == filters.input_type)

        if filters.start_time is not None:
            stmt = stmt.where(DetectionHistory.detected_time >= filters.start_time)

        if filters.end_time is not None:
            stmt = stmt.where(DetectionHistory.detected_time < filters.end_time)

        if filters.min_confidence is not None:
            stmt = stmt.where(DetectionHistory.confidence >= filters.min_confidence)

        if filters.min_ocr_confidence is not None:
            stmt = stmt.where(
                DetectionHistory.ocr_confidence.is_not(None),
                DetectionHistory.ocr_confidence >= filters.min_ocr_confidence,
            )

        if filters.source_job_id is not None:
            stmt = stmt.where(DetectionHistory.source_job_id == filters.source_job_id)

        if filters.is_valid_format is not None:
            stmt = stmt.where(DetectionHistory.is_valid_format.is_(filters.is_valid_format))

        if filters.has_text is not None:
            has_text = DetectionHistory.plate_number.is_not(None) & (
                DetectionHistory.plate_number != ""
            )
            stmt = stmt.where(has_text if filters.has_text else ~has_text)

        return stmt

    @staticmethod
    def _plate_match_condition(term: str) -> ColumnElement[bool] | None:
        """Build a case- and separator-insensitive substring match on the plate."""
        normalized = term.upper()
        for separator in _PLATE_SEPARATORS:
            normalized = normalized.replace(separator, "")
        normalized = normalized.strip()
        if not normalized:
            return None

        pattern = (
            normalized.replace(_LIKE_ESCAPE, _LIKE_ESCAPE * 2)
            .replace("%", f"{_LIKE_ESCAPE}%")
            .replace("_", f"{_LIKE_ESCAPE}_")
        )

        column: ColumnElement[str] = func.upper(DetectionHistory.plate_number)
        for separator in _PLATE_SEPARATORS:
            column = func.replace(column, separator, "")

        return column.like(f"%{pattern}%", escape=_LIKE_ESCAPE)

    # -- Queries ----------------------------------------------------------

    def list_paginated(
        self,
        *,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        filters: HistoryFilter | None = None,
        sort_by: str | None = None,
        descending: bool = True,
    ) -> tuple[list[DetectionHistory], int]:
        """Return one page of detection records and the total matching count."""
        stmt = self._apply_filters(select(DetectionHistory), filters)
        return self.paginate(
            stmt,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_columns=HISTORY_SORT_COLUMNS,
            default_sort=DetectionHistory.detected_time,
            descending=descending,
        )

    def list_by_job(self, job_id: str) -> list[DetectionHistory]:
        """Return every plate found by one upload, in detection order."""
        stmt = (
            select(DetectionHistory)
            .where(DetectionHistory.source_job_id == job_id)
            .order_by(DetectionHistory.detected_time.asc(), DetectionHistory.id.asc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def count_distinct_job_ids(self, filters: HistoryFilter | None = None) -> int:
        """Count the distinct jobs that produced at least one detection."""
        stmt = self._apply_filters(select(DetectionHistory), filters)
        # Count distinct jobs from filtered subquery
        subquery = stmt.order_by(None).subquery()
        counted = select(func.count(func.distinct(subquery.c.source_job_id)))
        return int(self.session.execute(counted).scalar_one() or 0)

    def delete_by_job(self, job_id: str) -> int:
        """Delete every detection belonging to one job."""
        ids = list(
            self.session.execute(
                select(DetectionHistory.id).where(DetectionHistory.source_job_id == job_id)
            )
            .scalars()
            .all()
        )
        return self.bulk_delete(ids)

    # -- Statistics -------------------------------------------------------

    def get_statistics(
        self,
        *,
        start_time: dt.datetime | None = None,
        end_time: dt.datetime | None = None,
        input_type: str | None = None,
        trend_days: int = DEFAULT_TREND_DAYS,
    ) -> DetectionStatistics:
        """Compute the dashboard's aggregate figures."""
        # Reuse HistoryFilter for input validation
        HistoryFilter(input_type=input_type, start_time=start_time, end_time=end_time)
        if trend_days < 1:
            raise ValidationError(
                f"trend_days must be positive, got {trend_days}",
                user_message="Khoảng thống kê theo ngày phải lớn hơn 0.",
                context={"trend_days": trend_days},
            )
        trend_days = min(trend_days, MAX_TREND_DAYS)

        detection_totals = self._detection_totals(start_time, end_time, input_type)
        total_jobs = self._count_jobs(start_time, end_time, input_type)

        today_start = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + dt.timedelta(days=1)

        return DetectionStatistics(
            total_jobs=total_jobs,
            jobs_today=self._count_jobs(today_start, today_end, input_type),
            detections_today=self._count_detections(today_start, today_end, input_type),
            by_input_type=self._by_input_type(start_time, end_time),
            daily_counts=self._daily_counts(start_time, end_time, input_type, trend_days),
            **detection_totals,
        )

    def _detection_totals(
        self,
        start_time: dt.datetime | None,
        end_time: dt.datetime | None,
        input_type: str | None,
    ) -> dict[str, Any]:
        """Aggregate every plate-level figure in a single pass over the table."""
        has_text = DetectionHistory.plate_number.is_not(None) & (
            DetectionHistory.plate_number != ""
        )

        stmt = select(
            func.count().label("total_detections"),
            func.count(func.distinct(case((has_text, DetectionHistory.plate_number)))).label(
                "unique_plates"
            ),
            func.sum(
                case((has_text & DetectionHistory.is_valid_format.is_(True), 1), else_=0)
            ).label("valid_format_count"),
            func.sum(
                case((has_text & DetectionHistory.is_valid_format.is_(False), 1), else_=0)
            ).label("invalid_format_count"),
            func.sum(case((~has_text, 1), else_=0)).label("unreadable_count"),
            func.avg(DetectionHistory.confidence).label("average_confidence"),
            func.avg(DetectionHistory.ocr_confidence).label("average_ocr_confidence"),
            func.avg(DetectionHistory.processing_time).label("average_processing_time"),
        ).select_from(DetectionHistory)

        stmt = self._apply_time_window(stmt, DetectionHistory.detected_time, start_time, end_time)
        if input_type is not None:
            stmt = stmt.where(DetectionHistory.input_type == input_type)

        row = self.session.execute(stmt).one()
        return {
            "total_detections": int(row.total_detections or 0),
            "unique_plates": int(row.unique_plates or 0),
            "valid_format_count": int(row.valid_format_count or 0),
            "invalid_format_count": int(row.invalid_format_count or 0),
            "unreadable_count": int(row.unreadable_count or 0),
            "average_confidence": _as_float(row.average_confidence),
            "average_ocr_confidence": _as_float(row.average_ocr_confidence),
            "average_processing_time": _as_float(row.average_processing_time),
        }

    def _count_jobs(
        self,
        start_time: dt.datetime | None,
        end_time: dt.datetime | None,
        input_type: str | None,
    ) -> int:
        """Count uploads and capture sessions in a time window."""
        stmt = select(func.count(func.distinct(DetectionJob.id))).select_from(DetectionJob)
        stmt = self._apply_time_window(stmt, DetectionJob.created_at, start_time, end_time)
        if input_type is not None:
            stmt = stmt.where(DetectionJob.input_type == input_type)
        return int(self.session.execute(stmt).scalar_one() or 0)

    def _count_detections(
        self,
        start_time: dt.datetime | None,
        end_time: dt.datetime | None,
        input_type: str | None,
    ) -> int:
        """Count detected plates in a time window."""
        stmt = select(func.count()).select_from(DetectionHistory)
        stmt = self._apply_time_window(stmt, DetectionHistory.detected_time, start_time, end_time)
        if input_type is not None:
            stmt = stmt.where(DetectionHistory.input_type == input_type)
        return int(self.session.execute(stmt).scalar_one() or 0)

    def _by_input_type(
        self,
        start_time: dt.datetime | None,
        end_time: dt.datetime | None,
    ) -> list[InputTypeCount]:
        """Break usage down by input type."""
        job_stmt = select(
            DetectionJob.input_type, func.count(func.distinct(DetectionJob.id))
        ).group_by(DetectionJob.input_type)
        job_stmt = self._apply_time_window(job_stmt, DetectionJob.created_at, start_time, end_time)
        job_counts = {str(row[0]): int(row[1] or 0) for row in self.session.execute(job_stmt).all()}

        detection_stmt = select(DetectionHistory.input_type, func.count()).group_by(
            DetectionHistory.input_type
        )
        detection_stmt = self._apply_time_window(
            detection_stmt, DetectionHistory.detected_time, start_time, end_time
        )
        detection_counts = {
            str(row[0]): int(row[1] or 0) for row in self.session.execute(detection_stmt).all()
        }

        return [
            InputTypeCount(
                input_type=str(value),
                job_count=job_counts.get(str(value), 0),
                detection_count=detection_counts.get(str(value), 0),
            )
            for value in InputType
        ]

    def _daily_counts(
        self,
        start_time: dt.datetime | None,
        end_time: dt.datetime | None,
        input_type: str | None,
        trend_days: int,
    ) -> list[DailyCount]:
        """Build a continuous per-day activity series."""
        window_end = end_time or utcnow()
        last_day = (window_end - dt.timedelta(microseconds=1)).date()
        if start_time is not None:
            first_day = start_time.date()
            span = (last_day - first_day).days + 1
            if span > MAX_TREND_DAYS:
                first_day = last_day - dt.timedelta(days=MAX_TREND_DAYS - 1)
        else:
            first_day = last_day - dt.timedelta(days=trend_days - 1)

        if first_day > last_day:
            return []

        # Match SQL query time bounds with series time span
        bound_start = dt.datetime.combine(first_day, dt.time.min, tzinfo=dt.timezone.utc)
        bound_end = dt.datetime.combine(
            last_day, dt.time.min, tzinfo=dt.timezone.utc
        ) + dt.timedelta(days=1)

        job_stmt = select(
            func.date(DetectionJob.created_at), func.count(func.distinct(DetectionJob.id))
        ).group_by(func.date(DetectionJob.created_at))
        job_stmt = self._apply_time_window(
            job_stmt, DetectionJob.created_at, bound_start, bound_end
        )
        if input_type is not None:
            job_stmt = job_stmt.where(DetectionJob.input_type == input_type)
        jobs_by_day = {
            _as_date(row[0]): int(row[1] or 0) for row in self.session.execute(job_stmt).all()
        }

        detection_stmt = select(func.date(DetectionHistory.detected_time), func.count()).group_by(
            func.date(DetectionHistory.detected_time)
        )
        detection_stmt = self._apply_time_window(
            detection_stmt, DetectionHistory.detected_time, bound_start, bound_end
        )
        if input_type is not None:
            detection_stmt = detection_stmt.where(DetectionHistory.input_type == input_type)
        detections_by_day = {
            _as_date(row[0]): int(row[1] or 0) for row in self.session.execute(detection_stmt).all()
        }

        series: list[DailyCount] = []
        cursor = first_day
        while cursor <= last_day:
            series.append(
                DailyCount(
                    date=cursor,
                    job_count=jobs_by_day.get(cursor, 0),
                    detection_count=detections_by_day.get(cursor, 0),
                )
            )
            cursor += dt.timedelta(days=1)
        return series

    @staticmethod
    def _apply_time_window(
        stmt: Select[Any],
        column: InstrumentedAttribute[dt.datetime],
        start_time: dt.datetime | None,
        end_time: dt.datetime | None,
    ) -> Select[Any]:
        """Restrict a statement to a half-open time window."""
        if start_time is not None:
            stmt = stmt.where(column >= start_time)
        if end_time is not None:
            stmt = stmt.where(column < end_time)
        return stmt


def _as_float(value: Any) -> float | None:
    """Convert a SQL aggregate result to a float, preserving ``None``."""
    return None if value is None else float(value)


def _as_date(value: Any) -> dt.date:
    """Normalise whatever ``date()`` returned into a :class:`datetime.date`."""
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        return dt.date.fromisoformat(value[:10])
    raise ValueError(f"Cannot interpret {value!r} as a date")


def to_id_list(records: Sequence[DetectionHistory]) -> list[int]:
    """Extract the primary keys of a sequence of records."""
    return [record.id for record in records]
