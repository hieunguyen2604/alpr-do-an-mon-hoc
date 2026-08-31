"""Unit tests for the repository layer."""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from backend.core.exceptions import NotFoundError, ValidationError
from backend.models.detection import (
    Base,
    DetectionHistory,
    DetectionJob,
    InputType,
    JobStatus,
)
from backend.repositories.detection_repository import (
    DetectionRepository,
    HistoryFilter,
    to_id_list,
)
from backend.repositories.job_repository import JobRepository

_NOW = dt.datetime(2026, 7, 19, 12, 0, 0, tzinfo=dt.timezone.utc)


@pytest.fixture()
def session() -> Iterator[Session]:
    """A session on a fresh in-memory database with foreign keys enforced."""
    engine = create_engine("sqlite:///:memory:", future=True)

    @event.listens_for(engine, "connect")
    def _pragmas(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    db = factory()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


@pytest.fixture()
def detections(session: Session) -> DetectionRepository:
    """A repository over the detection history table."""
    return DetectionRepository(session)


@pytest.fixture()
def jobs(session: Session) -> JobRepository:
    """A repository over the job table."""
    return JobRepository(session)


def make_job(
    session: Session,
    *,
    input_type: str = InputType.IMAGE.value,
    created_at: dt.datetime | None = None,
    status: str = JobStatus.COMPLETED.value,
) -> DetectionJob:
    """Insert one job row."""
    job = DetectionJob(
        input_type=input_type,
        status=status,
        progress=1.0,
        created_at=created_at or _NOW,
    )
    session.add(job)
    session.flush()
    return job


def make_detection(
    session: Session,
    job: DetectionJob,
    *,
    plate_number: str | None = "51F-12345",
    raw_ocr_text: str | None = "51FI2345",
    confidence: float = 0.9,
    ocr_confidence: float | None = 0.8,
    is_valid_format: bool = True,
    detected_time: dt.datetime | None = None,
    processing_time: float = 0.4,
    input_type: str | None = None,
) -> DetectionHistory:
    """Insert one detection row belonging to a job."""
    row = DetectionHistory(
        plate_number=plate_number,
        raw_ocr_text=raw_ocr_text,
        confidence=confidence,
        ocr_confidence=ocr_confidence,
        input_type=input_type or job.input_type,
        bbox_x=10,
        bbox_y=20,
        bbox_w=100,
        bbox_h=40,
        is_valid_format=is_valid_format,
        plate_line_count=1,
        processing_time=processing_time,
        detected_time=detected_time or _NOW,
        source_job_id=job.id,
    )
    session.add(row)
    session.flush()
    return row


class TestBaseCrud:
    """The generic operations every repository inherits."""

    def test_creates_and_reads_back(self, session: Session, jobs: JobRepository) -> None:
        job = jobs.create_job(input_type=InputType.IMAGE)
        assert job.id
        assert jobs.get_by_id(job.id) is job

    def test_a_new_job_starts_pending(self, jobs: JobRepository) -> None:
        """Not ``processing``: nothing has touched it yet."""
        assert jobs.create_job(input_type=InputType.VIDEO).status == JobStatus.PENDING.value

    def test_rejects_an_unknown_input_type(self, jobs: JobRepository) -> None:
        """Checked in Python so the error names a field, not a constraint."""
        with pytest.raises(ValidationError):
            jobs.create_job(input_type="satellite")

    def test_get_by_id_returns_none_for_a_missing_row(self, jobs: JobRepository) -> None:
        assert jobs.get_by_id("nope") is None

    def test_get_or_raise_raises_for_a_missing_row(self, jobs: JobRepository) -> None:
        with pytest.raises(NotFoundError):
            jobs.get_or_raise("nope")

    def test_exists_and_count(self, session: Session, jobs: JobRepository) -> None:
        assert jobs.count() == 0
        job = make_job(session)
        assert jobs.exists(job.id) is True
        assert jobs.exists("other") is False
        assert jobs.count() == 1

    def test_update_rejects_an_unknown_field(self, session: Session, jobs: JobRepository) -> None:
        """A typo would otherwise attach a stray attribute and change nothing."""
        job = make_job(session)
        with pytest.raises(ValidationError):
            jobs.update(job, statuss=JobStatus.FAILED.value)

    def test_update_applies_a_known_field(self, session: Session, jobs: JobRepository) -> None:
        job = make_job(session)
        jobs.update(job, status=JobStatus.FAILED.value)
        assert jobs.get_by_id(job.id).status == JobStatus.FAILED.value

    def test_delete_reports_whether_a_row_was_removed(
        self, session: Session, jobs: JobRepository
    ) -> None:
        job = make_job(session)
        assert jobs.delete(job.id) is True
        assert jobs.delete(job.id) is False

    def test_bulk_delete_ignores_duplicate_identifiers(
        self, session: Session, detections: DetectionRepository
    ) -> None:
        """A client sending the same id twice must not inflate the count."""
        job = make_job(session)
        first = make_detection(session, job)
        second = make_detection(session, job)
        removed = detections.bulk_delete([first.id, first.id, second.id])
        assert removed == 2

    def test_bulk_delete_of_nothing_is_zero(self, detections: DetectionRepository) -> None:
        assert detections.bulk_delete([]) == 0

    def test_to_id_list_extracts_primary_keys(self, session: Session) -> None:
        job = make_job(session)
        rows = [make_detection(session, job) for _ in range(3)]
        assert to_id_list(rows) == [row.id for row in rows]


class TestCascadingDelete:
    """Deleting a job must take its detections with it."""

    def test_removing_a_job_removes_its_detections(
        self, session: Session, jobs: JobRepository, detections: DetectionRepository
    ) -> None:
        job = make_job(session)
        make_detection(session, job)
        make_detection(session, job)
        assert detections.count() == 2

        jobs.delete(job.id)
        session.flush()
        assert detections.count() == 0

    def test_delete_by_job_removes_only_that_jobs_rows(
        self, session: Session, detections: DetectionRepository
    ) -> None:
        kept = make_job(session)
        removed = make_job(session)
        make_detection(session, kept)
        make_detection(session, removed)
        make_detection(session, removed)

        assert detections.delete_by_job(removed.id) == 2
        assert detections.count() == 1


class TestPagination:
    """Paging must be stable and its total must match its filters."""

    @pytest.fixture()
    def populated(self, session: Session) -> DetectionJob:
        """25 detections under one job, all sharing a timestamp."""
        job = make_job(session)
        for index in range(25):
            make_detection(session, job, plate_number=f"51F-{index:05d}")
        return job

    def test_returns_the_requested_page_size(
        self, populated: DetectionJob, detections: DetectionRepository
    ) -> None:
        rows, total = detections.list_paginated(page=1, page_size=10)
        assert len(rows) == 10
        assert total == 25

    def test_the_total_counts_all_matches_not_the_page(
        self, populated: DetectionJob, detections: DetectionRepository
    ) -> None:
        _, total = detections.list_paginated(page=2, page_size=10)
        assert total == 25

    def test_the_last_page_is_partial(
        self, populated: DetectionJob, detections: DetectionRepository
    ) -> None:
        rows, _ = detections.list_paginated(page=3, page_size=10)
        assert len(rows) == 5

    def test_a_page_past_the_end_is_empty_not_an_error(
        self, populated: DetectionJob, detections: DetectionRepository
    ) -> None:
        rows, total = detections.list_paginated(page=99, page_size=10)
        assert rows == []
        assert total == 25

    def test_pages_do_not_overlap_or_lose_a_row(
        self, populated: DetectionJob, detections: DetectionRepository
    ) -> None:
        """The property the primary-key tie-breaker exists to guarantee."""
        seen: list[int] = []
        for page in (1, 2, 3):
            rows, _ = detections.list_paginated(page=page, page_size=10)
            seen.extend(row.id for row in rows)
        assert len(seen) == 25
        assert len(set(seen)) == 25

    def test_page_zero_is_clamped_to_the_first_page(
        self, populated: DetectionJob, detections: DetectionRepository
    ) -> None:
        clamped, _ = detections.list_paginated(page=0, page_size=5)
        first, _ = detections.list_paginated(page=1, page_size=5)
        assert [row.id for row in clamped] == [row.id for row in first]

    def test_an_excessive_page_size_is_clamped_not_rejected(
        self, populated: DetectionJob, detections: DetectionRepository
    ) -> None:
        """``?page_size=1000000`` must not load the whole table."""
        rows, _ = detections.list_paginated(page=1, page_size=1_000_000)
        assert len(rows) <= 200


class TestSorting:
    """Sort keys resolve through an allow-list, never through ``getattr``."""

    @pytest.fixture()
    def spread(self, session: Session) -> None:
        job = make_job(session)
        for index, confidence in enumerate((0.5, 0.9, 0.7)):
            make_detection(
                session,
                job,
                confidence=confidence,
                plate_number=f"51F-{index:05d}",
                detected_time=_NOW + dt.timedelta(minutes=index),
            )

    def test_sorts_descending_by_default(
        self, spread: None, detections: DetectionRepository
    ) -> None:
        rows, _ = detections.list_paginated(sort_by="confidence")
        assert [row.confidence for row in rows] == [0.9, 0.7, 0.5]

    def test_sorts_ascending_when_asked(
        self, spread: None, detections: DetectionRepository
    ) -> None:
        rows, _ = detections.list_paginated(sort_by="confidence", descending=False)
        assert [row.confidence for row in rows] == [0.5, 0.7, 0.9]

    def test_sorts_by_time(self, spread: None, detections: DetectionRepository) -> None:
        rows, _ = detections.list_paginated(sort_by="detected_time", descending=False)
        assert [row.detected_time for row in rows] == sorted(row.detected_time for row in rows)

    def test_an_unknown_sort_key_is_a_clean_validation_error(
        self, spread: None, detections: DetectionRepository
    ) -> None:
        """Not an ``AttributeError``-shaped 500, and not an unintended join."""
        with pytest.raises(ValidationError):
            detections.list_paginated(sort_by="job")

    def test_a_sort_key_naming_a_relationship_is_refused(
        self, spread: None, detections: DetectionRepository
    ) -> None:
        with pytest.raises(ValidationError):
            detections.list_paginated(sort_by="metadata")


class TestPlateSearch:
    """Substring matching that survives how people actually type a plate."""

    @pytest.fixture()
    def plates(self, session: Session) -> None:
        job = make_job(session)
        for text in ("51F-12345", "29A1-234.56", "30G 99999", "51F-54321"):
            make_detection(session, job, plate_number=text)

    def test_finds_a_plain_substring(self, plates: None, detections: DetectionRepository) -> None:
        rows, total = detections.list_paginated(filters=HistoryFilter(plate_number="51F"))
        assert total == 2

    def test_matching_is_case_insensitive(
        self, plates: None, detections: DetectionRepository
    ) -> None:
        rows, total = detections.list_paginated(filters=HistoryFilter(plate_number="51f"))
        assert total == 2

    def test_separators_are_ignored_on_both_sides(
        self, plates: None, detections: DetectionRepository
    ) -> None:
        """``51F12345`` must find ``51F-12345``."""
        _, total = detections.list_paginated(filters=HistoryFilter(plate_number="51F12345"))
        assert total == 1

    def test_a_dotted_query_finds_a_hyphenated_plate(
        self, plates: None, detections: DetectionRepository
    ) -> None:
        _, total = detections.list_paginated(filters=HistoryFilter(plate_number="51F.12345"))
        assert total == 1

    def test_a_percent_sign_is_escaped_not_treated_as_a_wildcard(
        self, plates: None, detections: DetectionRepository
    ) -> None:
        """Left alone it would match every row, which reads as an ignored filter."""
        _, total = detections.list_paginated(filters=HistoryFilter(plate_number="%"))
        assert total == 0

    def test_an_underscore_is_escaped_too(
        self, plates: None, detections: DetectionRepository
    ) -> None:
        _, total = detections.list_paginated(filters=HistoryFilter(plate_number="51F_2345"))
        assert total == 0

    def test_a_query_of_only_separators_is_dropped_not_applied(
        self, plates: None, detections: DetectionRepository
    ) -> None:
        """Applying it as a match-all would be worse than not filtering."""
        _, total = detections.list_paginated(filters=HistoryFilter(plate_number="---"))
        assert total == 4


class TestFiltering:
    """Every criterion, and their combination."""

    @pytest.fixture()
    def mixed(self, session: Session) -> None:
        image_job = make_job(session, input_type=InputType.IMAGE.value)
        video_job = make_job(session, input_type=InputType.VIDEO.value)

        make_detection(
            session,
            image_job,
            plate_number="51F-11111",
            confidence=0.95,
            ocr_confidence=0.9,
            is_valid_format=True,
        )
        make_detection(
            session,
            image_job,
            plate_number="ZZ-00000",
            confidence=0.60,
            ocr_confidence=0.4,
            is_valid_format=False,
        )
        make_detection(
            session,
            image_job,
            plate_number=None,
            raw_ocr_text=None,
            confidence=0.55,
            ocr_confidence=None,
            is_valid_format=False,
        )
        make_detection(
            session,
            video_job,
            plate_number="29A1-22222",
            confidence=0.80,
            ocr_confidence=0.75,
            is_valid_format=True,
            detected_time=_NOW + dt.timedelta(days=2),
        )

    def test_filters_by_input_type(self, mixed: None, detections: DetectionRepository) -> None:
        _, total = detections.list_paginated(
            filters=HistoryFilter(input_type=InputType.VIDEO.value)
        )
        assert total == 1

    def test_filters_by_minimum_detection_confidence(
        self, mixed: None, detections: DetectionRepository
    ) -> None:
        _, total = detections.list_paginated(filters=HistoryFilter(min_confidence=0.75))
        assert total == 2

    def test_filtering_by_ocr_confidence_excludes_unread_rows(
        self, mixed: None, detections: DetectionRepository
    ) -> None:
        """A row with no OCR value has nothing to compare, so it is excluded."""
        _, total = detections.list_paginated(filters=HistoryFilter(min_ocr_confidence=0.0))
        assert total == 3

    def test_filters_by_format_validity(self, mixed: None, detections: DetectionRepository) -> None:
        _, valid = detections.list_paginated(filters=HistoryFilter(is_valid_format=True))
        _, invalid = detections.list_paginated(filters=HistoryFilter(is_valid_format=False))
        assert valid == 2
        assert invalid == 2

    def test_filters_by_whether_text_was_read(
        self, mixed: None, detections: DetectionRepository
    ) -> None:
        _, with_text = detections.list_paginated(filters=HistoryFilter(has_text=True))
        _, without = detections.list_paginated(filters=HistoryFilter(has_text=False))
        assert with_text == 3
        assert without == 1

    def test_the_time_window_is_half_open(
        self, mixed: None, detections: DetectionRepository
    ) -> None:
        """``start <= t < end``, so consecutive windows tile without overlap."""
        _, total = detections.list_paginated(
            filters=HistoryFilter(start_time=_NOW, end_time=_NOW + dt.timedelta(days=1))
        )
        assert total == 3

    def test_combines_several_criteria_with_and(
        self, mixed: None, detections: DetectionRepository
    ) -> None:
        _, total = detections.list_paginated(
            filters=HistoryFilter(
                input_type=InputType.IMAGE.value,
                is_valid_format=True,
                min_confidence=0.9,
            )
        )
        assert total == 1

    def test_combined_criteria_can_select_nothing(
        self, mixed: None, detections: DetectionRepository
    ) -> None:
        _, total = detections.list_paginated(
            filters=HistoryFilter(input_type=InputType.VIDEO.value, min_confidence=0.99)
        )
        assert total == 0

    def test_no_filter_returns_everything(
        self, mixed: None, detections: DetectionRepository
    ) -> None:
        _, total = detections.list_paginated(filters=None)
        assert total == 4


class TestHistoryFilterValidation:
    """Criteria that cannot match anything must fail loudly."""

    def test_a_reversed_time_range_is_refused(self) -> None:
        """An empty page looks identical to "no data yet"."""
        with pytest.raises(ValidationError):
            HistoryFilter(start_time=_NOW, end_time=_NOW - dt.timedelta(days=1))

    def test_an_equal_time_range_is_allowed(self) -> None:
        assert HistoryFilter(start_time=_NOW, end_time=_NOW) is not None

    @pytest.mark.parametrize("value", [-0.1, 1.1, 5.0])
    def test_an_out_of_range_confidence_is_refused(self, value: float) -> None:
        with pytest.raises(ValidationError):
            HistoryFilter(min_confidence=value)

    def test_an_unknown_input_type_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            HistoryFilter(input_type="satellite")

    @pytest.mark.parametrize("value", ["image", "video", "webcam"])
    def test_the_three_accepted_input_types(self, value: str) -> None:
        assert HistoryFilter(input_type=value).input_type == value


class TestJobsVersusDetections:
    """The counting rule: one image with three plates is ONE use of the system."""

    @pytest.fixture()
    def one_image_three_plates(self, session: Session) -> DetectionJob:
        job = make_job(session)
        for index in range(3):
            make_detection(session, job, plate_number=f"51F-{index:05d}")
        return job

    def test_three_plates_in_one_image_are_one_job(
        self,
        one_image_three_plates: DetectionJob,
        detections: DetectionRepository,
    ) -> None:
        stats = detections.get_statistics()
        assert stats.total_detections == 3
        assert stats.total_jobs == 1

    def test_count_distinct_job_ids_collapses_the_three_rows(
        self,
        one_image_three_plates: DetectionJob,
        detections: DetectionRepository,
    ) -> None:
        """``COUNT(DISTINCT source_job_id)`` over the history table."""
        assert detections.count() == 3
        assert detections.count_distinct_job_ids() == 1

    def test_three_separate_images_are_three_jobs(
        self, session: Session, detections: DetectionRepository
    ) -> None:
        for _ in range(3):
            make_detection(session, make_job(session))
        stats = detections.get_statistics()
        assert stats.total_jobs == 3
        assert stats.total_detections == 3

    def test_usage_and_recognition_diverge_as_soon_as_they_can(
        self, session: Session, detections: DetectionRepository
    ) -> None:
        """Two uploads, five plates. The two figures must not be equal."""
        first = make_job(session)
        second = make_job(session)
        for index in range(3):
            make_detection(session, first, plate_number=f"51F-0000{index}")
        for index in range(2):
            make_detection(session, second, plate_number=f"29A-0000{index}")

        stats = detections.get_statistics()
        assert stats.total_jobs == 2
        assert stats.total_detections == 5
        assert detections.count_distinct_job_ids() == 2

    def test_an_upload_that_found_nothing_still_counts_as_usage(
        self, session: Session, detections: DetectionRepository
    ) -> None:
        """The difference between the two job figures, made explicit."""
        productive = make_job(session)
        make_detection(session, productive)
        make_job(session)  # an upload in which no plate was found

        stats = detections.get_statistics()
        assert stats.total_jobs == 2
        assert detections.count_distinct_job_ids() == 1
        assert stats.total_detections == 1

    def test_the_job_count_ignores_how_many_plates_each_upload_found(
        self, session: Session, detections: DetectionRepository
    ) -> None:
        job = make_job(session)
        for index in range(20):
            make_detection(session, job, plate_number=f"51F-{index:05d}")
        stats = detections.get_statistics()
        assert stats.total_jobs == 1
        assert stats.total_detections == 20

    def test_the_breakdown_by_input_type_counts_jobs_and_rows_separately(
        self, session: Session, detections: DetectionRepository
    ) -> None:
        """A join would multiply each job by its detections -- the same error."""
        job = make_job(session, input_type=InputType.IMAGE.value)
        for index in range(4):
            make_detection(session, job, plate_number=f"51F-{index:05d}")

        stats = detections.get_statistics()
        by_type = {entry.input_type: entry for entry in stats.by_input_type}
        assert by_type["image"].job_count == 1
        assert by_type["image"].detection_count == 4

    def test_every_input_type_appears_even_with_no_activity(
        self, session: Session, detections: DetectionRepository
    ) -> None:
        """A bar chart whose categories vanish looks like a rendering fault."""
        make_detection(session, make_job(session))
        stats = detections.get_statistics()
        assert {entry.input_type for entry in stats.by_input_type} == {
            "image",
            "video",
            "webcam",
        }


class TestStatisticsFigures:
    """The remaining aggregate values."""

    @pytest.fixture()
    def population(self, session: Session) -> None:
        job = make_job(session)
        make_detection(
            session,
            job,
            plate_number="51F-12345",
            is_valid_format=True,
            confidence=0.9,
            ocr_confidence=0.8,
            processing_time=0.4,
        )
        make_detection(
            session,
            job,
            plate_number="51F-12345",
            is_valid_format=True,
            confidence=0.7,
            ocr_confidence=0.6,
            processing_time=0.6,
        )
        make_detection(
            session,
            job,
            plate_number="XX-99999",
            is_valid_format=False,
            confidence=0.5,
            ocr_confidence=0.5,
            processing_time=0.5,
        )
        make_detection(
            session,
            job,
            plate_number=None,
            raw_ocr_text=None,
            is_valid_format=False,
            confidence=0.5,
            ocr_confidence=None,
            processing_time=0.5,
        )

    def test_unique_plates_counts_distinct_text(
        self, population: None, detections: DetectionRepository
    ) -> None:
        """Four rows, one duplicate, one unreadable -> two distinct plates."""
        assert detections.get_statistics().unique_plates == 2

    def test_the_three_format_counters_partition_the_detections(
        self, population: None, detections: DetectionRepository
    ) -> None:
        """They must sum to the total, or a stacked chart shows a gap."""
        stats = detections.get_statistics()
        total = stats.valid_format_count + stats.invalid_format_count + stats.unreadable_count
        assert total == stats.total_detections
        assert stats.valid_format_count == 2
        assert stats.invalid_format_count == 1
        assert stats.unreadable_count == 1

    def test_the_ocr_average_ignores_unread_rows(
        self, population: None, detections: DetectionRepository
    ) -> None:
        """Counting them as zero would misreport OCR quality downwards."""
        stats = detections.get_statistics()
        assert stats.average_ocr_confidence == pytest.approx((0.8 + 0.6 + 0.5) / 3)

    def test_the_detection_average_covers_every_row(
        self, population: None, detections: DetectionRepository
    ) -> None:
        stats = detections.get_statistics()
        assert stats.average_confidence == pytest.approx((0.9 + 0.7 + 0.5 + 0.5) / 4)

    def test_averages_are_none_on_an_empty_database(self, detections: DetectionRepository) -> None:
        """``None`` distinguishes "no data yet" from "the average is 0.0"."""
        stats = detections.get_statistics()
        assert stats.total_detections == 0
        assert stats.average_confidence is None
        assert stats.average_ocr_confidence is None
        assert stats.average_processing_time is None

    def test_the_daily_series_is_continuous(
        self, population: None, detections: DetectionRepository
    ) -> None:
        """Days with no activity are zeros, not omissions."""
        stats = detections.get_statistics(trend_days=7)
        assert len(stats.daily_counts) == 7
        dates = [entry.date for entry in stats.daily_counts]
        assert dates == sorted(dates)
        for earlier, later in zip(dates, dates[1:]):
            assert (later - earlier).days == 1

    def test_a_non_positive_trend_window_is_refused(self, detections: DetectionRepository) -> None:
        with pytest.raises(ValidationError):
            detections.get_statistics(trend_days=0)

    def test_the_trend_window_is_capped(self, detections: DetectionRepository) -> None:
        """An unbounded window would build thousands of mostly-zero entries."""
        stats = detections.get_statistics(trend_days=10_000)
        assert len(stats.daily_counts) <= 365

    def test_statistics_reject_a_reversed_time_range(self, detections: DetectionRepository) -> None:
        """The same validation as the history endpoint, deliberately shared."""
        with pytest.raises(ValidationError):
            detections.get_statistics(start_time=_NOW, end_time=_NOW - dt.timedelta(days=1))


class TestListByJob:
    """Retrieving the plates of one upload."""

    def test_returns_only_that_jobs_detections(
        self, session: Session, detections: DetectionRepository
    ) -> None:
        wanted = make_job(session)
        other = make_job(session)
        make_detection(session, wanted)
        make_detection(session, wanted)
        make_detection(session, other)

        rows = detections.list_by_job(wanted.id)
        assert len(rows) == 2
        assert {row.source_job_id for row in rows} == {wanted.id}

    def test_an_unknown_job_yields_an_empty_list(self, detections: DetectionRepository) -> None:
        assert detections.list_by_job("nope") == []


class TestJobStateTransitions:
    """The job lifecycle, as the polling client observes it."""

    def test_marks_a_job_completed(self, session: Session, jobs: JobRepository) -> None:
        job = jobs.create_job(input_type=InputType.VIDEO)
        jobs.mark_completed(job.id)
        assert jobs.get_by_id(job.id).status == JobStatus.COMPLETED.value

    def test_marks_a_job_failed_and_records_the_reason(
        self, session: Session, jobs: JobRepository
    ) -> None:
        job = jobs.create_job(input_type=InputType.VIDEO)
        jobs.mark_failed(job.id, "codec exploded")
        stored = jobs.get_by_id(job.id)
        assert stored.status == JobStatus.FAILED.value
        assert "codec exploded" in (stored.error_message or "")

    @pytest.mark.parametrize(
        ("status", "terminal"),
        [
            (JobStatus.PENDING, False),
            (JobStatus.PROCESSING, False),
            (JobStatus.COMPLETED, True),
            (JobStatus.FAILED, True),
            (JobStatus.CANCELLED, True),
        ],
    )
    def test_terminal_states_are_declared_correctly(
        self, status: JobStatus, terminal: bool
    ) -> None:
        """The frontend stops polling on exactly these three."""
        assert status.is_terminal is terminal

    def test_counts_a_jobs_detections_without_loading_them(
        self, session: Session, jobs: JobRepository
    ) -> None:
        job = make_job(session)
        for _ in range(4):
            make_detection(session, job)
        assert jobs.count_detections(job.id) == 4

    def test_counting_an_unknown_job_is_zero(self, jobs: JobRepository) -> None:
        assert jobs.count_detections("nope") == 0


class TestModelProperties:
    """Small derived values on the ORM models."""

    def test_has_text_reflects_the_plate_number(self, session: Session) -> None:
        job = make_job(session)
        assert make_detection(session, job, plate_number="51F-1").has_text is True
        assert make_detection(session, job, plate_number=None).has_text is False

    def test_was_corrected_compares_raw_against_normalised(self, session: Session) -> None:
        """The per-row form of the measurement ``raw_ocr_text`` exists for."""
        job = make_job(session)
        changed = make_detection(session, job, plate_number="51F-12345", raw_ocr_text="51FI2345")
        unchanged = make_detection(session, job, plate_number="51F-12345", raw_ocr_text="51F-12345")
        missing = make_detection(session, job, plate_number=None, raw_ocr_text=None)

        assert changed.was_corrected is True
        assert unchanged.was_corrected is False
        assert missing.was_corrected is False

    def test_a_timestamp_survives_the_round_trip_as_aware_utc(self, session: Session) -> None:
        """SQLite drops the offset; ``UtcDateTime`` puts it back."""
        job = make_job(session)
        row = make_detection(session, job, detected_time=_NOW)
        session.commit()
        session.expire_all()

        reloaded = session.get(DetectionHistory, row.id)
        assert reloaded.detected_time.tzinfo is not None
        assert reloaded.detected_time == _NOW

    def test_a_naive_timestamp_written_in_is_read_back_as_utc(self, session: Session) -> None:
        job = make_job(session)
        naive = dt.datetime(2026, 7, 19, 12, 0, 0)
        row = make_detection(session, job, detected_time=naive)
        session.commit()
        session.expire_all()

        reloaded = session.get(DetectionHistory, row.id)
        assert reloaded.detected_time == naive.replace(tzinfo=dt.timezone.utc)
