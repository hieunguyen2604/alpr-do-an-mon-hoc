"""Queries over detection_job: managing the lifecycle and progress of uploads and tasks (FR-2.6)."""

from __future__ import annotations

import datetime as dt
from typing import Any, Final

from sqlalchemy import Select, func, select
from sqlalchemy.orm import InstrumentedAttribute

from backend.core.exceptions import ValidationError
from backend.models.detection import DetectionJob, InputType, JobStatus, utcnow
from backend.repositories.base import DEFAULT_PAGE_SIZE, BaseRepository

__all__ = ["JobRepository", "JOB_SORT_COLUMNS"]

_PROGRESS_MIN: Final[float] = 0.0
_PROGRESS_MAX: Final[float] = 1.0

JOB_SORT_COLUMNS: Final[dict[str, InstrumentedAttribute[Any]]] = {
    "created_at": DetectionJob.created_at,
    "completed_at": DetectionJob.completed_at,
    "status": DetectionJob.status,
    "input_type": DetectionJob.input_type,
    "progress": DetectionJob.progress,
    "id": DetectionJob.id,
}
"""Allowed sort columns for job queries."""


class JobRepository(BaseRepository[DetectionJob, str]):
    """Reads and writes rows of ``detection_job``."""

    model = DetectionJob

    # -- Create -----------------------------------------------------------

    def create_job(
        self,
        *,
        input_type: str | InputType,
        source_path: str | None = None,
        total_frames: int | None = None,
    ) -> DetectionJob:
        """Create a job in the ``pending`` state."""
        value = str(input_type)
        if value not in set(InputType):
            raise ValidationError(
                f"Unknown input_type {value!r}",
                user_message="Loại dữ liệu đầu vào không hợp lệ.",
                context={"input_type": value},
            )
        return self.create(
            input_type=value,
            status=JobStatus.PENDING.value,
            progress=_PROGRESS_MIN,
            source_path=source_path,
            total_frames=total_frames,
            processed_frames=0,
        )

    # -- Read -------------------------------------------------------------

    def list_paginated(
        self,
        *,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        status: str | JobStatus | None = None,
        input_type: str | InputType | None = None,
        start_time: dt.datetime | None = None,
        end_time: dt.datetime | None = None,
        sort_by: str | None = None,
        descending: bool = True,
    ) -> tuple[list[DetectionJob], int]:
        """Return one page of jobs and the total matching count."""
        stmt: Select[tuple[DetectionJob]] = select(DetectionJob)
        if status is not None:
            stmt = stmt.where(DetectionJob.status == str(status))
        if input_type is not None:
            stmt = stmt.where(DetectionJob.input_type == str(input_type))
        if start_time is not None:
            stmt = stmt.where(DetectionJob.created_at >= start_time)
        if end_time is not None:
            stmt = stmt.where(DetectionJob.created_at < end_time)

        return self.paginate(
            stmt,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_columns=JOB_SORT_COLUMNS,
            default_sort=DetectionJob.created_at,
            descending=descending,
        )

    def list_active(self) -> list[DetectionJob]:
        """Return every job that has not reached a terminal state."""
        unfinished = [JobStatus.PENDING.value, JobStatus.PROCESSING.value]
        stmt = (
            select(DetectionJob)
            .where(DetectionJob.status.in_(unfinished))
            .order_by(DetectionJob.created_at.asc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def count_by_status(self) -> dict[str, int]:
        """Return the number of jobs in each lifecycle state."""
        stmt = select(DetectionJob.status, func.count()).group_by(DetectionJob.status)
        observed = {str(row[0]): int(row[1] or 0) for row in self.session.execute(stmt).all()}
        return {status.value: observed.get(status.value, 0) for status in JobStatus}

    def count_detections(self, job_id: str) -> int:
        """Return how many plates a job has produced so far."""
        # Lazy import to avoid circular dependency
        from backend.models.detection import DetectionHistory

        stmt = (
            select(func.count())
            .select_from(DetectionHistory)
            .where(DetectionHistory.source_job_id == job_id)
        )
        return int(self.session.execute(stmt).scalar_one() or 0)

    # -- State transitions ------------------------------------------------

    def update_progress(
        self,
        job_id: str,
        progress: float | None = None,
        *,
        processed_frames: int | None = None,
        total_frames: int | None = None,
    ) -> DetectionJob | None:
        """Advance a running job's progress."""
        job = self.get_by_id(job_id)
        if job is None:
            return None
        if job.is_finished:
            return job

        if total_frames is not None:
            job.total_frames = total_frames
        if processed_frames is not None:
            job.processed_frames = max(0, processed_frames)

        if progress is None and job.total_frames:
            progress = job.processed_frames / job.total_frames

        if progress is not None:
            job.progress = min(_PROGRESS_MAX, max(_PROGRESS_MIN, float(progress)))

        if job.status == JobStatus.PENDING.value:
            # The first progress report is proof the worker picked the job up.
            job.status = JobStatus.PROCESSING.value

        self.session.flush()
        return job

    def mark_processing(self, job_id: str) -> DetectionJob | None:
        """Move a job from ``pending`` to ``processing``."""
        return self._transition(job_id, JobStatus.PROCESSING)

    def mark_completed(self, job_id: str, *, output_path: str | None = None) -> DetectionJob | None:
        """Mark a job finished successfully."""
        job = self._transition(job_id, JobStatus.COMPLETED)
        if job is None:
            return None
        job.progress = _PROGRESS_MAX
        if output_path is not None:
            job.output_path = output_path
        self.session.flush()
        return job

    def mark_failed(self, job_id: str, error_message: str) -> DetectionJob | None:
        """Mark a job failed and record why, server-side only."""
        job = self._transition(job_id, JobStatus.FAILED)
        if job is None:
            return None
        job.error_message = error_message
        self.session.flush()
        return job

    def mark_cancelled(self, job_id: str) -> DetectionJob | None:
        """Mark a job cancelled by the user."""
        return self._transition(job_id, JobStatus.CANCELLED)

    def _transition(self, job_id: str, status: JobStatus) -> DetectionJob | None:
        """Move a job into a new state, setting ``completed_at`` when terminal."""
        job = self.get_by_id(job_id)
        if job is None:
            return None
        if job.is_finished:
            return job

        job.status = status.value
        if status.is_terminal:
            job.completed_at = utcnow()
        self.session.flush()
        return job

    # -- Maintenance ------------------------------------------------------

    def delete_older_than(self, cutoff: dt.datetime) -> int:
        """Delete finished jobs created before a cutoff."""
        terminal = [status.value for status in JobStatus if status.is_terminal]
        stmt = select(DetectionJob.id).where(
            DetectionJob.created_at < cutoff,
            DetectionJob.status.in_(terminal),
        )
        job_ids = list(self.session.execute(stmt).scalars().all())
        return self.bulk_delete(job_ids)
