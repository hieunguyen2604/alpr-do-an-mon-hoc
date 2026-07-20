"""Queries over the detection history table, including dashboard statistics.

Most of this module is ordinary filtering and pagination. The part worth
reading carefully is :meth:`DetectionRepository.get_statistics`, because it is
where the project's easiest serious bug lives.

The counting rule
-----------------
``detection_history`` holds **one row per license plate**, not one row per
upload. A photograph containing three vehicles produces three rows that share a
``source_job_id``. Two different questions therefore have two different answers,
and they must never be computed the same way:

======================================= ======================================
Question                                Correct computation
======================================= ======================================
"How many times was the system used?"   Count **jobs** -- one per upload.
"How many plates were recognised?"      Count **rows** in detection_history.
======================================= ======================================

Answering the first with ``SELECT COUNT(*) FROM detection_history`` inflates
usage by the average number of plates per image. The failure is quiet: the
number is plausible, monotonically increasing, and wrong by a factor nobody can
see without recomputing it. Every job-level figure produced here is therefore
named ``*_jobs`` or ``job_count`` and every plate-level figure ``*_detections``
or ``detection_count``, so that a mismatched assignment reads as wrong at the
call site.

Where the job counts come from
------------------------------
Job counts are read from the ``detection_job`` table rather than as
``COUNT(DISTINCT source_job_id)`` over ``detection_history``. The two agree on
every job that found at least one plate, and differ on the ones that found
none -- an upload of a photo containing no readable plate creates a job and
zero history rows, so the ``DISTINCT`` form cannot see it at all.

That difference is not an edge case to be waved away. Uploads that yield no
detection are exactly the negative cases the evaluation chapter needs, and a
dashboard tile reading "412 images processed" must include the image where
nothing was found -- the user did upload it. Counting the job table includes
them; counting distinct ids in the history table silently drops them and makes
the system look like it never fails to find a plate.

:meth:`DetectionRepository.count_distinct_job_ids` exposes the narrower
``COUNT(DISTINCT source_job_id)`` figure for the cases that genuinely want
"jobs that produced at least one detection", such as computing a hit rate.
Both are available and each is named for what it counts.
"""

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
    """Filter criteria for a history query.

    Grouped into one object rather than passed as eight keyword arguments so
    that the same criteria can be handed to the list query and to the count
    query without any chance of the two receiving different values -- which
    would produce a page of results whose total does not match it.

    Every field is optional; ``None`` means "do not filter on this". All
    supplied criteria are combined with ``AND``.

    Attributes:
        plate_number: Case-insensitive substring of the plate text. Separators
            are ignored on both sides, so ``51f12345`` matches ``51F-12345``.
        input_type: Restrict to ``image``, ``video`` or ``webcam``.
        start_time: Earliest ``detected_time``, inclusive.
        end_time: Latest ``detected_time``, exclusive. Exclusive so that
            consecutive windows tile the timeline without a row falling into
            two of them.
        min_confidence: Minimum **detector** confidence, in ``[0.0, 1.0]``.
        min_ocr_confidence: Minimum **OCR** confidence. Rows where OCR read
            nothing are excluded when this is set, since they have no value to
            compare.
        source_job_id: Restrict to the detections of one upload.
        is_valid_format: Restrict to plates that did or did not match a
            Vietnamese plate format.
        has_text: ``True`` keeps only rows OCR could read, ``False`` keeps only
            the ones it could not.
    """

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
        """Reject criteria that cannot match anything.

        A reversed date range or an out-of-range confidence returns an empty
        page, which looks identical to "no data yet". Failing loudly turns a
        confusing empty screen into a 400 that says what was wrong.

        Raises:
            ValidationError: If the time range ends before it starts, if a
                confidence bound falls outside ``[0.0, 1.0]``, or if
                ``input_type`` is not one of the three accepted values.
        """
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
    """Usage figures for one input type.

    Attributes:
        input_type: ``image``, ``video`` or ``webcam``.
        job_count: Uploads or sessions of this type.
        detection_count: Plates found across those uploads.
    """

    input_type: str
    job_count: int
    detection_count: int


@dataclass(frozen=True, slots=True)
class DailyCount:
    """Activity on one calendar day, in UTC.

    Attributes:
        date: The day being reported.
        job_count: Uploads created that day.
        detection_count: Plates detected that day.
    """

    date: dt.date
    job_count: int
    detection_count: int


@dataclass(frozen=True, slots=True)
class DetectionStatistics:
    """Aggregate dashboard figures.

    Field names match :class:`~backend.schemas.detection.StatisticsResponse`
    exactly, so a router converts with
    ``StatisticsResponse.model_validate(stats)`` and no field-by-field copy --
    the copy being where ``total_jobs`` and ``total_detections`` would
    eventually get swapped.

    ``valid_format_count``, ``invalid_format_count`` and ``unreadable_count``
    are computed from mutually exclusive conditions and always sum to
    :attr:`total_detections`, so they can be charted as parts of a whole
    without the segments failing to add up.

    Attributes:
        total_jobs: Uploads and sessions. The usage figure.
        total_detections: Plates found. One upload may contribute several.
        unique_plates: Distinct non-empty plate strings recognised.
        valid_format_count: Detections whose text matched a Vietnamese format.
        invalid_format_count: Detections that produced text matching no format.
        unreadable_count: Detections OCR could not read at all.
        average_confidence: Mean detector confidence, or ``None`` if no rows.
        average_ocr_confidence: Mean OCR confidence over rows that produced
            text, or ``None``.
        average_processing_time: Mean seconds per detected plate, or ``None``.
        jobs_today: Uploads created today, UTC.
        detections_today: Plates detected today, UTC.
        by_input_type: Breakdown by input type; always all three entries.
        daily_counts: Continuous per-day series, oldest first.
    """

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
    """Reads and writes rows of ``detection_history``.

    Statistics also read ``detection_job``, because the job-level counters are
    only correct when taken from the table that has one row per job. That
    cross-table reach is deliberate and documented at module level; it is not
    an invitation to query unrelated tables from here.
    """

    model = DetectionHistory

    # -- Filtering --------------------------------------------------------

    def _apply_filters(
        self,
        stmt: Select[tuple[DetectionHistory]],
        filters: HistoryFilter | None,
    ) -> Select[tuple[DetectionHistory]]:
        """Add the ``WHERE`` clauses described by a filter object.

        Args:
            stmt: The statement to narrow.
            filters: Criteria to apply, or ``None`` for no filtering.

        Returns:
            The statement with every requested condition applied.
        """
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
        """Build a case- and separator-insensitive substring match on the plate.

        Both the column and the search term are upper-cased and stripped of
        ``-``, ``.`` and spaces before comparison, so every way a user might
        type a plate finds the same rows.

        ``%`` and ``_`` in the user's text are escaped. Left alone they are
        ``LIKE`` wildcards: a search for ``%`` would return the entire table,
        which reads as the filter having been ignored.

        Args:
            term: Raw search text from the caller.

        Returns:
            A boolean SQL expression, or ``None`` when the term consists only
            of separators and would therefore match every row -- in which case
            the filter is dropped rather than applied as a match-all.
        """
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
        """Return one page of detection records and the total matching count.

        Args:
            page: 1-based page number; values below 1 are clamped.
            page_size: Records per page, clamped to the repository maximum.
            filters: Criteria to narrow the result, or ``None`` for all rows.
            sort_by: A key of :data:`HISTORY_SORT_COLUMNS`. Defaults to
                ``detected_time``.
            descending: ``True`` returns newest first, the history screen's
                default.

        Returns:
            ``(records for this page, total records matching the filters)``.
            The total counts every match, not just this page, so the caller can
            build :class:`~backend.schemas.detection.HistoryListResponse`
            directly.

        Raises:
            ValidationError: If ``sort_by`` is not an accepted key.
        """
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
        """Return every plate found by one upload, in detection order.

        Args:
            job_id: Identifier of the job.

        Returns:
            The job's detections, oldest first.
        """
        stmt = (
            select(DetectionHistory)
            .where(DetectionHistory.source_job_id == job_id)
            .order_by(DetectionHistory.detected_time.asc(), DetectionHistory.id.asc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def count_distinct_job_ids(self, filters: HistoryFilter | None = None) -> int:
        """Count the distinct jobs that produced at least one detection.

        This is ``COUNT(DISTINCT source_job_id)`` over the filtered history
        rows. It is **not** the dashboard's usage figure: it cannot see an
        upload that produced no detection, because such a job has no row here.
        Use it as the numerator of a hit rate, paired with
        :attr:`DetectionStatistics.total_jobs` as the denominator.

        Args:
            filters: Criteria narrowing which detections are considered.

        Returns:
            The number of distinct ``source_job_id`` values.
        """
        stmt = self._apply_filters(select(DetectionHistory), filters)
        # Counted against the filtered statement wrapped as a subquery, so the
        # DISTINCT sees exactly the rows the filters selected -- rebuilding the
        # conditions a second time is how a count drifts away from its list.
        subquery = stmt.order_by(None).subquery()
        counted = select(func.count(func.distinct(subquery.c.source_job_id)))
        return int(self.session.execute(counted).scalar_one() or 0)

    def delete_by_job(self, job_id: str) -> int:
        """Delete every detection belonging to one job.

        Args:
            job_id: Identifier of the job whose detections should be removed.

        Returns:
            The number of rows deleted.
        """
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
        """Compute the dashboard's aggregate figures.

        Job-level counters come from ``detection_job`` and plate-level counters
        from ``detection_history``; see this module's docstring for why the two
        must not be taken from the same table. In short: one upload of a photo
        with three plates is **one** job and **three** detections, and an upload
        that found nothing is still one job.

        Args:
            start_time: Earliest timestamp to include, inclusive. ``None``
                means from the beginning of the data.
            end_time: Latest timestamp to include, exclusive. ``None`` means up
                to now.
            input_type: Restrict every figure to one input type, or ``None``
                for all of them.
            trend_days: Length of the per-day series, ending at ``end_time`` or
                today. Clamped to :data:`MAX_TREND_DAYS`.

        Returns:
            The populated statistics.

        Raises:
            ValidationError: If the time range is reversed, ``input_type`` is
                unknown, or ``trend_days`` is not positive.
        """
        # Reuses the filter object purely for its validation, so that the
        # statistics endpoint rejects the same bad input as the history one.
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
        """Aggregate every plate-level figure in a single pass over the table.

        One statement rather than eight: the history table may hold 100 000
        rows (NFR-SC2), and eight separate full scans is eight times the work
        for exactly the same answer.

        The three format counters use mutually exclusive, jointly exhaustive
        conditions, so ``valid + invalid + unreadable`` always equals the total
        and a stacked chart of them cannot show a gap. ``AVG`` ignores ``NULL``
        in SQL, which gives the OCR average the right denominator for free --
        rows OCR could not read are excluded rather than counted as zero, which
        would drag the mean down and misreport OCR quality.

        Args:
            start_time: Earliest ``detected_time``, inclusive, or ``None``.
            end_time: Latest ``detected_time``, exclusive, or ``None``.
            input_type: Input type to restrict to, or ``None``.

        Returns:
            Keyword arguments for :class:`DetectionStatistics`, covering the
            plate-level fields only.
        """
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
        """Count uploads and capture sessions in a time window.

        Counts rows of ``detection_job``, where the primary key is the job
        identifier -- so this is a count of distinct jobs by construction, and
        the number of plates each one found has no influence on it. That is the
        whole point: this is the "how much was the system used" figure.

        Args:
            start_time: Earliest ``created_at``, inclusive, or ``None``.
            end_time: Latest ``created_at``, exclusive, or ``None``.
            input_type: Input type to restrict to, or ``None``.

        Returns:
            The number of jobs in the window.
        """
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
        """Count detected plates in a time window.

        Args:
            start_time: Earliest ``detected_time``, inclusive, or ``None``.
            end_time: Latest ``detected_time``, exclusive, or ``None``.
            input_type: Input type to restrict to, or ``None``.

        Returns:
            The number of history rows in the window.
        """
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
        """Break usage down by input type.

        Two grouped queries, one per table, merged in Python. A single query
        joining the tables would multiply each job row by its number of
        detections and count a three-plate image as three uploads -- the exact
        error this module exists to prevent, and one that a ``JOIN`` makes
        almost automatic.

        All three input types are always present in the result, with zeros
        where nothing was recorded, so the dashboard renders a stable set of
        bars instead of a chart whose categories appear and disappear.

        Args:
            start_time: Earliest timestamp, inclusive, or ``None``.
            end_time: Latest timestamp, exclusive, or ``None``.

        Returns:
            One entry per input type, in the declaration order of
            :class:`~backend.models.detection.InputType`.
        """
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
        """Build a continuous per-day activity series.

        Days with no activity are emitted as zeros rather than omitted. A line
        chart fed only the days that had data draws a straight line across a
        quiet week, implying steady usage where there was none; and the x-axis
        spacing silently stops being uniform.

        As in :meth:`_by_input_type`, jobs and detections are counted in
        separate queries and merged, so a day's ``job_count`` is a count of
        uploads regardless of how many plates each contained.

        Args:
            start_time: Start of the window, inclusive. ``None`` derives it
                from ``trend_days`` counted back from the end.
            end_time: End of the window, exclusive. ``None`` means now.
            input_type: Input type to restrict to, or ``None``.
            trend_days: Series length used when ``start_time`` is ``None``.

        Returns:
            One entry per day, oldest first.
        """
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

        # Re-derive the bounds from the resolved days so the SQL window and the
        # emitted series cover exactly the same period. Deriving them
        # separately is how a chart ends up with a leading or trailing day that
        # is always zero.
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
        """Restrict a statement to a half-open time window.

        Half-open (``start <= t < end``) so consecutive windows tile without
        overlapping. A closed range double-counts any row landing exactly on a
        boundary, which for a per-day series is every row written at midnight.

        Args:
            stmt: The statement to narrow.
            column: The timestamp column to compare.
            start_time: Inclusive lower bound, or ``None``.
            end_time: Exclusive upper bound, or ``None``.

        Returns:
            The narrowed statement.
        """
        if start_time is not None:
            stmt = stmt.where(column >= start_time)
        if end_time is not None:
            stmt = stmt.where(column < end_time)
        return stmt


def _as_float(value: Any) -> float | None:
    """Convert a SQL aggregate result to a float, preserving ``None``.

    ``AVG`` over zero rows returns ``NULL``, which must stay ``None`` -- the
    statistics schema documents these fields as nullable precisely so that "no
    data yet" is distinguishable from "the average is 0.0". Coercing to zero
    would report a confidence of 0% on an empty database.

    Args:
        value: Raw aggregate value from the driver.

    Returns:
        The value as a float, or ``None``.
    """
    return None if value is None else float(value)


def _as_date(value: Any) -> dt.date:
    """Normalise whatever ``date()`` returned into a :class:`datetime.date`.

    The result type is dialect-dependent: SQLite has no date type and returns
    the ``YYYY-MM-DD`` string, while PostgreSQL returns a real ``date``. Both
    are normalised here so the merge keys in the per-day series compare equal
    -- a mixture of ``str`` and ``date`` keys would never match, and every day
    of the chart would come out zero.

    Args:
        value: Raw grouping key from the driver.

    Returns:
        The corresponding date.

    Raises:
        ValueError: If the value is neither a date, a datetime, nor an
            ISO-formatted string.
    """
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        return dt.date.fromisoformat(value[:10])
    raise ValueError(f"Cannot interpret {value!r} as a date")


def to_id_list(records: Sequence[DetectionHistory]) -> list[int]:
    """Extract the primary keys of a sequence of records.

    A small helper for the delete flow, where the caller has the rows of a page
    and needs their identifiers for :meth:`BaseRepository.bulk_delete`.

    Args:
        records: The records whose identifiers are wanted.

    Returns:
        The identifiers, in the order given.
    """
    return [record.id for record in records]
