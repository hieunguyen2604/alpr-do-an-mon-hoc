"""Unit tests for :mod:`backend.repositories.job_repository`."""

from __future__ import annotations

import datetime as dt

import pytest
from sqlalchemy.orm import Session

from backend.core.exceptions import ValidationError
from backend.models.detection import InputType, JobStatus
from backend.repositories.detection_repository import DetectionRepository
from backend.repositories.job_repository import JobRepository

from .test_repositories import (  # noqa: F401 -- fixtures are used by name
    _NOW,
    detections,
    jobs,
    make_detection,
    make_job,
    session,
)


class TestJobListing:
    """The queries behind the dashboard's job list."""

    @pytest.fixture()
    def assorted(self, session: Session) -> None:
        """Jobs across several statuses and input types, spread over three days."""
        specification = [
            (InputType.IMAGE.value, JobStatus.COMPLETED.value, 0),
            (InputType.IMAGE.value, JobStatus.COMPLETED.value, 1),
            (InputType.VIDEO.value, JobStatus.PROCESSING.value, 1),
            (InputType.VIDEO.value, JobStatus.FAILED.value, 2),
            (InputType.WEBCAM.value, JobStatus.PENDING.value, 2),
        ]
        for input_type, status, offset in specification:
            make_job(
                session,
                input_type=input_type,
                status=status,
                created_at=_NOW + dt.timedelta(days=offset),
            )

    def test_lists_every_job_by_default(self, assorted: None, jobs: JobRepository) -> None:
        rows, total = jobs.list_paginated()
        assert total == 5
        assert len(rows) == 5

    def test_filters_by_status(self, assorted: None, jobs: JobRepository) -> None:
        _, total = jobs.list_paginated(status=JobStatus.COMPLETED)
        assert total == 2

    def test_filters_by_input_type(self, assorted: None, jobs: JobRepository) -> None:
        _, total = jobs.list_paginated(input_type=InputType.VIDEO)
        assert total == 2

    def test_filters_by_a_half_open_time_window(self, assorted: None, jobs: JobRepository) -> None:
        _, total = jobs.list_paginated(start_time=_NOW, end_time=_NOW + dt.timedelta(days=1))
        assert total == 1

    def test_combines_filters(self, assorted: None, jobs: JobRepository) -> None:
        _, total = jobs.list_paginated(input_type=InputType.IMAGE, status=JobStatus.COMPLETED)
        assert total == 2

    def test_paginates(self, assorted: None, jobs: JobRepository) -> None:
        rows, total = jobs.list_paginated(page=1, page_size=2)
        assert len(rows) == 2
        assert total == 5

    def test_sorts_newest_first_by_default(self, assorted: None, jobs: JobRepository) -> None:
        rows, _ = jobs.list_paginated()
        times = [row.created_at for row in rows]
        assert times == sorted(times, reverse=True)

    def test_an_unknown_sort_key_is_refused(self, assorted: None, jobs: JobRepository) -> None:
        with pytest.raises(ValidationError):
            jobs.list_paginated(sort_by="detections")

    def test_lists_only_unfinished_jobs(self, assorted: None, jobs: JobRepository) -> None:
        """Used at start-up to find jobs abandoned by a killed process."""
        active = jobs.list_active()
        assert {job.status for job in active} == {
            JobStatus.PENDING.value,
            JobStatus.PROCESSING.value,
        }
        assert len(active) == 2

    def test_counts_every_status_including_the_unused_ones(
        self, assorted: None, jobs: JobRepository
    ) -> None:
        """Zeros are present so a caller can index without a default, and a"""
        counts = jobs.count_by_status()
        assert set(counts) == {status.value for status in JobStatus}
        assert counts[JobStatus.COMPLETED.value] == 2
        assert counts[JobStatus.CANCELLED.value] == 0
        assert sum(counts.values()) == 5


class TestJobProgress:
    """``update_progress``, which the video worker calls repeatedly."""

    def test_records_progress_and_frames(self, jobs: JobRepository) -> None:
        job = jobs.create_job(input_type=InputType.VIDEO, total_frames=100)
        jobs.update_progress(job.id, processed_frames=50)

        updated = jobs.get_by_id(job.id)
        assert updated.processed_frames == 50
        assert updated.progress == pytest.approx(0.5)

    def test_the_first_report_moves_the_job_out_of_pending(self, jobs: JobRepository) -> None:
        """The first progress report is proof the worker picked the job up."""
        job = jobs.create_job(input_type=InputType.VIDEO, total_frames=10)
        assert job.status == JobStatus.PENDING.value

        jobs.update_progress(job.id, processed_frames=1)
        assert jobs.get_by_id(job.id).status == JobStatus.PROCESSING.value

    @pytest.mark.parametrize("value", [1.0000001, 5.0, -0.5])
    def test_progress_is_clamped_rather_than_rejected(
        self, jobs: JobRepository, value: float
    ) -> None:
        """``processed / total`` gives ``1.0000001`` whenever the decoder"""
        job = jobs.create_job(input_type=InputType.VIDEO)
        jobs.update_progress(job.id, progress=value)
        assert 0.0 <= jobs.get_by_id(job.id).progress <= 1.0

    def test_a_terminal_job_is_not_dragged_back_out_of_its_final_state(
        self, jobs: JobRepository
    ) -> None:
        """The frontend stops polling on a terminal status, so a change made"""
        job = jobs.create_job(input_type=InputType.VIDEO, total_frames=100)
        jobs.mark_cancelled(job.id)
        jobs.update_progress(job.id, processed_frames=99)

        final = jobs.get_by_id(job.id)
        assert final.status == JobStatus.CANCELLED.value
        assert final.processed_frames == 0

    def test_updating_an_unknown_job_returns_none(self, jobs: JobRepository) -> None:
        """The worker reads ``None`` as "the job was deleted underneath me"."""
        assert jobs.update_progress("nope", progress=0.5) is None

    def test_a_revised_total_frame_count_is_accepted(self, jobs: JobRepository) -> None:
        """The true count is often only known once decoding has started."""
        job = jobs.create_job(input_type=InputType.VIDEO)
        jobs.update_progress(job.id, processed_frames=5, total_frames=50)

        updated = jobs.get_by_id(job.id)
        assert updated.total_frames == 50
        assert updated.progress == pytest.approx(0.1)

    def test_a_negative_frame_count_is_floored_at_zero(self, jobs: JobRepository) -> None:
        job = jobs.create_job(input_type=InputType.VIDEO)
        jobs.update_progress(job.id, processed_frames=-5)
        assert jobs.get_by_id(job.id).processed_frames == 0

    def test_marks_processing_and_cancelled(self, jobs: JobRepository) -> None:
        job = jobs.create_job(input_type=InputType.VIDEO)
        assert jobs.mark_processing(job.id).status == JobStatus.PROCESSING.value
        assert jobs.mark_cancelled(job.id).status == JobStatus.CANCELLED.value

    def test_a_completed_job_records_when_it_finished(self, jobs: JobRepository) -> None:
        job = jobs.create_job(input_type=InputType.VIDEO)
        jobs.mark_completed(job.id)

        finished = jobs.get_by_id(job.id)
        assert finished.completed_at is not None
        assert finished.is_finished is True

    def test_a_transition_on_an_unknown_job_returns_none(self, jobs: JobRepository) -> None:
        assert jobs.mark_processing("nope") is None
        assert jobs.mark_completed("nope") is None
        assert jobs.mark_failed("nope", "reason") is None
        assert jobs.mark_cancelled("nope") is None


class TestRetentionSweep:
    """``delete_older_than``, the maintenance job."""

    def test_removes_finished_jobs_before_the_cutoff(
        self, session: Session, jobs: JobRepository
    ) -> None:
        make_job(session, created_at=_NOW - dt.timedelta(days=10))
        make_job(session, created_at=_NOW - dt.timedelta(days=10))
        make_job(session, created_at=_NOW)

        assert jobs.delete_older_than(_NOW - dt.timedelta(days=1)) == 2
        assert jobs.count() == 1

    def test_leaves_a_running_job_alone_however_old(
        self, session: Session, jobs: JobRepository
    ) -> None:
        """Deleting a job a worker is still writing to would make every"""
        make_job(
            session,
            created_at=_NOW - dt.timedelta(days=30),
            status=JobStatus.PROCESSING.value,
        )
        assert jobs.delete_older_than(_NOW) == 0
        assert jobs.count() == 1

    def test_the_detections_go_with_the_job(
        self,
        session: Session,
        jobs: JobRepository,
        detections: DetectionRepository,
    ) -> None:
        """Through the foreign key's ``ON DELETE CASCADE``, which is only"""
        old = make_job(session, created_at=_NOW - dt.timedelta(days=10))
        make_detection(session, old)
        make_detection(session, old)
        session.commit()

        jobs.delete_older_than(_NOW - dt.timedelta(days=1))
        assert detections.count() == 0

    def test_a_sweep_that_matches_nothing_is_zero(
        self, session: Session, jobs: JobRepository
    ) -> None:
        make_job(session, created_at=_NOW)
        assert jobs.delete_older_than(_NOW - dt.timedelta(days=1)) == 0
