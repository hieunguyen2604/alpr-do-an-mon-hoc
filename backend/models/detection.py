"""SQLAlchemy ORM models for detection jobs and plate detection history records."""

from __future__ import annotations

import datetime as dt
import uuid
from enum import StrEnum
from typing import Final

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Dialect,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    TypeDecorator,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

__all__ = [
    "Base",
    "InputType",
    "JobStatus",
    "UtcDateTime",
    "DetectionHistory",
    "DetectionJob",
    "utcnow",
]

_UUID_LENGTH: Final[int] = 36
_PATH_LENGTH: Final[int] = 512
_PLATE_LENGTH: Final[int] = 32
_ENUM_LENGTH: Final[int] = 16


def utcnow() -> dt.datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return dt.datetime.now(dt.timezone.utc)


class UtcDateTime(TypeDecorator[dt.datetime]):
    """A datetime column that is always timezone-aware UTC in Python."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: dt.datetime | None, dialect: Dialect) -> dt.datetime | None:
        """Normalise a datetime to UTC before it is written."""
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=dt.timezone.utc)
        return value.astimezone(dt.timezone.utc)

    def process_result_value(
        self, value: dt.datetime | None, dialect: Dialect
    ) -> dt.datetime | None:
        """Re-attach UTC to a datetime loaded from the database."""
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=dt.timezone.utc)
        return value.astimezone(dt.timezone.utc)


class InputType(StrEnum):
    """How a detection entered the system."""

    IMAGE = "image"
    VIDEO = "video"
    WEBCAM = "webcam"


class JobStatus(StrEnum):
    """Lifecycle of a :class:`DetectionJob`."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        """Return ``True`` if no further transition is possible from this state."""
        return self in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model."""


class DetectionJob(Base):
    """One upload or capture session, and the state of processing it."""

    __tablename__ = "detection_job"

    id: Mapped[str] = mapped_column(
        String(_UUID_LENGTH),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    input_type: Mapped[str] = mapped_column(String(_ENUM_LENGTH), nullable=False)
    status: Mapped[str] = mapped_column(
        String(_ENUM_LENGTH),
        nullable=False,
        default=JobStatus.PENDING.value,
    )
    progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    source_path: Mapped[str | None] = mapped_column(String(_PATH_LENGTH))
    output_path: Mapped[str | None] = mapped_column(String(_PATH_LENGTH))
    error_message: Mapped[str | None] = mapped_column(Text)

    total_frames: Mapped[int | None] = mapped_column(Integer)
    processed_frames: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[dt.datetime] = mapped_column(UtcDateTime, nullable=False, default=utcnow)
    completed_at: Mapped[dt.datetime | None] = mapped_column(UtcDateTime)

    detections: Mapped[list[DetectionHistory]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        # DB-side cascade; requires the SQLite foreign_keys pragma (backend.models.database).
        passive_deletes=True,
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_detection_job_input_type", "input_type"),
        Index("ix_detection_job_status", "status"),
        # Dashboard "recent activity" lists are ordered by recency and often
        # filtered by status; one composite index serves both.
        Index("ix_detection_job_created_at", "created_at"),
        CheckConstraint(
            "input_type IN ('image', 'video', 'webcam')",
            name="ck_detection_job_input_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')",
            name="ck_detection_job_status",
        ),
        CheckConstraint(
            "progress >= 0.0 AND progress <= 1.0",
            name="ck_detection_job_progress_range",
        ),
    )

    @property
    def is_finished(self) -> bool:
        """Return ``True`` when the job has reached a terminal state."""
        return JobStatus(self.status).is_terminal

    def __repr__(self) -> str:
        """Return a concise developer-facing representation."""
        return (
            f"DetectionJob(id={self.id!r}, input_type={self.input_type!r}, "
            f"status={self.status!r}, progress={self.progress:.2f})"
        )


class DetectionHistory(Base):
    """One license plate found in one job."""

    __tablename__ = "detection_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    plate_number: Mapped[str | None] = mapped_column(String(_PLATE_LENGTH))
    raw_ocr_text: Mapped[str | None] = mapped_column(String(_PLATE_LENGTH))

    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    ocr_confidence: Mapped[float | None] = mapped_column(Float)

    input_type: Mapped[str] = mapped_column(String(_ENUM_LENGTH), nullable=False)

    image_path: Mapped[str | None] = mapped_column(String(_PATH_LENGTH))
    plate_image_path: Mapped[str | None] = mapped_column(String(_PATH_LENGTH))

    bbox_x: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_y: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_w: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_h: Mapped[int] = mapped_column(Integer, nullable=False)

    is_valid_format: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    plate_line_count: Mapped[int | None] = mapped_column(Integer)
    upper_char_count: Mapped[int | None] = mapped_column(Integer)

    # Read the two together — neither identifies a vehicle class alone:
    # plate_kind comes from the string, plate_color from the crop, and a yellow
    # business plate shares its exact layout with a white private one.
    plate_kind: Mapped[str | None] = mapped_column(String(_ENUM_LENGTH))
    plate_color: Mapped[str | None] = mapped_column(String(_ENUM_LENGTH))
    plate_color_confidence: Mapped[float | None] = mapped_column(Float)

    # Seconds, not a frame index: an index means nothing without the clip's
    # frame rate, which is neither stored nor constant across sources.
    video_time_seconds: Mapped[float | None] = mapped_column(Float)

    processing_time: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    detected_time: Mapped[dt.datetime] = mapped_column(UtcDateTime, nullable=False, default=utcnow)
    created_at: Mapped[dt.datetime] = mapped_column(UtcDateTime, nullable=False, default=utcnow)

    # Mandatory: usage statistics count distinct jobs, so an orphan row would
    # show in history yet be invisible to the counts — the two views would disagree.
    source_job_id: Mapped[str] = mapped_column(
        String(_UUID_LENGTH),
        ForeignKey("detection_job.id", ondelete="CASCADE"),
        nullable=False,
    )

    job: Mapped[DetectionJob] = relationship(back_populates="detections")

    __table_args__ = (
        Index("ix_detection_history_plate_number", "plate_number"),
        Index("ix_detection_history_detected_time", "detected_time"),
        Index("ix_detection_history_input_type", "input_type"),
        Index("ix_detection_history_source_job_id", "source_job_id"),
        # Composite index serves the default query (newest first + input-type filter)
        # from one structure — what keeps pagination inside NFR-P6 at 100k rows.
        Index(
            "ix_detection_history_input_type_detected_time",
            "input_type",
            "detected_time",
        ),
        CheckConstraint(
            "input_type IN ('image', 'video', 'webcam')",
            name="ck_detection_history_input_type",
        ),
        CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0",
            name="ck_detection_history_confidence_range",
        ),
        CheckConstraint(
            "ocr_confidence IS NULL OR (ocr_confidence >= 0.0 AND ocr_confidence <= 1.0)",
            name="ck_detection_history_ocr_confidence_range",
        ),
        CheckConstraint(
            "plate_line_count IS NULL OR plate_line_count IN (1, 2)",
            name="ck_detection_history_plate_line_count",
        ),
        # Upper line legally holds 3 (67C) or 4 (77H5) characters; anything else is
        # a miscomputed count and must not reach the display rule.
        CheckConstraint(
            "upper_char_count IS NULL OR upper_char_count IN (3, 4)",
            name="ck_detection_history_upper_char_count",
        ),
        CheckConstraint(
            "bbox_w > 0 AND bbox_h > 0",
            name="ck_detection_history_bbox_positive",
        ),
    )

    @property
    def has_text(self) -> bool:
        """Return ``True`` if OCR produced a non-empty plate string."""
        return bool(self.plate_number)

    @property
    def was_corrected(self) -> bool:
        """Return ``True`` if post-processing changed the raw OCR string."""
        if self.plate_number is None or self.raw_ocr_text is None:
            return False
        return self.plate_number != self.raw_ocr_text

    def __repr__(self) -> str:
        """Return a concise developer-facing representation."""
        return (
            f"DetectionHistory(id={self.id!r}, plate_number={self.plate_number!r}, "
            f"confidence={self.confidence:.3f}, input_type={self.input_type!r})"
        )
