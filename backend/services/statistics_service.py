"""Aggregate figures and metrics for dashboard statistics."""

from __future__ import annotations

import datetime as dt
from typing import Final

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from backend.core.exceptions import ValidationError
from backend.core.logging import get_logger
from backend.models.detection import DetectionHistory, DetectionJob, InputType, utcnow
from backend.schemas.detection import (
    DailyCountSchema,
    InputTypeCountSchema,
    StatisticsResponse,
)

__all__ = ["StatisticsService", "DEFAULT_TREND_DAYS", "MAX_TREND_DAYS"]

logger = get_logger(__name__)

DEFAULT_TREND_DAYS: Final[int] = 7
"""Length of the dashboard trend window when the client does not ask."""

MAX_TREND_DAYS: Final[int] = 365
"""Longest trend window a client may request.

Bounded because the response carries one object per day: an unbounded window
would let a single query return an arbitrarily large payload.
"""


class StatisticsService:
    """Computes the dashboard's aggregate figures."""

    def get_statistics(
        self,
        db: Session,
        *,
        days: int = DEFAULT_TREND_DAYS,
    ) -> StatisticsResponse:
        """Compute every dashboard figure in one pass."""
        if not 1 <= days <= MAX_TREND_DAYS:
            raise ValidationError(
                f"days must be within [1, {MAX_TREND_DAYS}], got {days}",
                user_message=(f"Số ngày thống kê phải nằm trong khoảng 1 đến {MAX_TREND_DAYS}."),
            )

        today = utcnow().date()
        start_of_today = self._start_of_day(today)

        # -- Usage, from the job table --------------------------------------
        total_jobs = self._scalar_count(db, select(func.count()).select_from(DetectionJob))
        jobs_today = self._scalar_count(
            db,
            select(func.count())
            .select_from(DetectionJob)
            .where(DetectionJob.created_at >= start_of_today),
        )

        # -- Recognition, from the history table -----------------------------
        total_detections = self._scalar_count(
            db, select(func.count()).select_from(DetectionHistory)
        )
        detections_today = self._scalar_count(
            db,
            select(func.count())
            .select_from(DetectionHistory)
            .where(DetectionHistory.detected_time >= start_of_today),
        )

        unique_plates = self._scalar_count(
            db,
            select(func.count(func.distinct(DetectionHistory.plate_number))).where(
                DetectionHistory.plate_number.is_not(None)
            ),
        )

        unreadable_count = self._scalar_count(
            db,
            select(func.count())
            .select_from(DetectionHistory)
            .where(DetectionHistory.plate_number.is_(None)),
        )
        valid_format_count = self._scalar_count(
            db,
            select(func.count())
            .select_from(DetectionHistory)
            .where(DetectionHistory.is_valid_format.is_(True)),
        )
        # Read but unrecognised: text present, pattern not matched
        invalid_format_count = self._scalar_count(
            db,
            select(func.count())
            .select_from(DetectionHistory)
            .where(
                DetectionHistory.is_valid_format.is_(False),
                DetectionHistory.plate_number.is_not(None),
            ),
        )

        averages = db.execute(
            select(
                func.avg(DetectionHistory.confidence),
                func.avg(DetectionHistory.ocr_confidence),
                func.avg(DetectionHistory.processing_time),
            )
        ).one()
        average_confidence = self._as_optional_float(averages[0])
        # AVG over readings with valid text (NULLs ignored by SQL AVG)
        average_ocr_confidence = self._as_optional_float(averages[1])
        average_processing_time = self._as_optional_float(averages[2])

        response = StatisticsResponse(
            total_jobs=total_jobs,
            total_detections=total_detections,
            unique_plates=unique_plates,
            valid_format_count=valid_format_count,
            invalid_format_count=invalid_format_count,
            unreadable_count=unreadable_count,
            average_confidence=average_confidence,
            average_ocr_confidence=average_ocr_confidence,
            average_processing_time=average_processing_time,
            jobs_today=jobs_today,
            detections_today=detections_today,
            by_input_type=self._by_input_type(db),
            daily_counts=self._daily_counts(db, days=days, today=today),
        )

        logger.debug(
            "statistics computed",
            extra={
                "total_jobs": total_jobs,
                "total_detections": total_detections,
                "trend_days": days,
            },
        )
        return response

    # -- Breakdowns -------------------------------------------------------

    def _by_input_type(self, db: Session) -> list[InputTypeCountSchema]:
        """Count uploads and plates for each input type."""
        job_counts = dict(
            db.execute(
                select(DetectionJob.input_type, func.count()).group_by(DetectionJob.input_type)
            ).all()
        )
        detection_counts = dict(
            db.execute(
                select(DetectionHistory.input_type, func.count()).group_by(
                    DetectionHistory.input_type
                )
            ).all()
        )

        return [
            InputTypeCountSchema(
                input_type=kind.value,  # type: ignore[arg-type]
                job_count=int(job_counts.get(kind.value, 0)),
                detection_count=int(detection_counts.get(kind.value, 0)),
            )
            for kind in InputType
        ]

    def _daily_counts(self, db: Session, *, days: int, today: dt.date) -> list[DailyCountSchema]:
        """Build the per-day activity series for the trend chart."""
        window_start = self._start_of_day(today - dt.timedelta(days=days - 1))

        job_rows = db.execute(
            select(func.date(DetectionJob.created_at), func.count())
            .where(DetectionJob.created_at >= window_start)
            .group_by(func.date(DetectionJob.created_at))
        ).all()
        detection_rows = db.execute(
            select(func.date(DetectionHistory.detected_time), func.count())
            .where(DetectionHistory.detected_time >= window_start)
            .group_by(func.date(DetectionHistory.detected_time))
        ).all()

        jobs_by_day = {self._as_date(key): int(count) for key, count in job_rows}
        detections_by_day = {self._as_date(key): int(count) for key, count in detection_rows}

        series: list[DailyCountSchema] = []
        for offset in range(days - 1, -1, -1):
            day = today - dt.timedelta(days=offset)
            series.append(
                DailyCountSchema(
                    date=day,
                    job_count=jobs_by_day.get(day, 0),
                    detection_count=detections_by_day.get(day, 0),
                )
            )
        return series

    # -- Small helpers ----------------------------------------------------

    @staticmethod
    def _start_of_day(day: dt.date) -> dt.datetime:
        """Return midnight UTC at the start of a date."""
        return dt.datetime.combine(day, dt.time.min, tzinfo=dt.timezone.utc)

    @staticmethod
    def _as_date(value: object) -> dt.date:
        """Coerce a grouped ``DATE()`` result into a :class:`datetime.date`."""
        if isinstance(value, dt.datetime):
            return value.date()
        if isinstance(value, dt.date):
            return value
        return dt.date.fromisoformat(str(value)[:10])

    @staticmethod
    def _as_optional_float(value: object) -> float | None:
        """Convert an aggregate result to a float, preserving ``NULL``."""
        return None if value is None else float(value)

    @staticmethod
    def _scalar_count(db: Session, statement: Select[tuple[int]]) -> int:
        """Execute a counting query and return the result as an ``int``."""
        return int(db.execute(statement).scalar_one())
