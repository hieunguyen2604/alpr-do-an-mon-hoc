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
    """Return the current time as a timezone-aware UTC datetime.

    Used as the Python-side default for every timestamp column instead of
    SQLite's ``CURRENT_TIMESTAMP``. Two reasons: SQLite's version produces a
    *naive* string with one-second resolution, which is too coarse to order
    the detections coming out of a single video; and generating the value in
    Python keeps the behaviour identical if the database is ever moved to
    PostgreSQL.

    Returns:
        The current UTC time, with ``tzinfo`` set.
    """
    return dt.datetime.now(dt.timezone.utc)


class UtcDateTime(TypeDecorator[dt.datetime]):
    """A datetime column that is always timezone-aware UTC in Python.

    Exists because of a silent data-fidelity bug in the obvious approach.
    SQLite has no native datetime type: SQLAlchemy stores the value as a
    formatted string, and that format **drops the UTC offset**. A value written
    as ``2026-07-19 12:00:00+00:00`` therefore comes back as naive
    ``2026-07-19 12:00:00`` -- no error, no warning, just a timestamp that has
    quietly forgotten which timezone it is in. Two consequences follow, and
    neither announces itself:

    * ``utcnow() - row.created_at`` raises ``TypeError: can't subtract
      offset-naive and offset-aware datetimes``, at whatever future point
      someone computes a duration;
    * serialised to JSON, a naive timestamp has no ``Z`` suffix, so the browser
      reads it as **local** time. On a UTC+7 machine every timestamp in the
      history table would display seven hours off -- plausible enough to go
      unnoticed, wrong enough to invalidate any timing analysis.

    This decorator closes the gap at the type level, so that no individual
    model or query has to remember: values are normalised to UTC on the way in,
    and UTC is re-attached on the way out. A naive value read from a row
    written before this type existed is interpreted as UTC, which is what it
    is -- :func:`utcnow` has always been the only writer.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: dt.datetime | None, dialect: Dialect) -> dt.datetime | None:
        """Normalise a datetime to UTC before it is written.

        Args:
            value: The value being stored, aware or naive.
            dialect: The active SQLAlchemy dialect; unused.

        Returns:
            The equivalent instant expressed in UTC, or ``None``. A naive input
            is assumed to already be UTC rather than rejected, so that a plain
            ``datetime(2026, 1, 1)`` in a test fixture behaves predictably.
        """
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=dt.timezone.utc)
        return value.astimezone(dt.timezone.utc)

    def process_result_value(
        self, value: dt.datetime | None, dialect: Dialect
    ) -> dt.datetime | None:
        """Re-attach UTC to a datetime loaded from the database.

        Args:
            value: The raw value from the driver, naive on SQLite.
            dialect: The active SQLAlchemy dialect; unused.

        Returns:
            A timezone-aware UTC datetime, or ``None``.
        """
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=dt.timezone.utc)
        return value.astimezone(dt.timezone.utc)


class InputType(StrEnum):
    """How a detection entered the system.

    Stored as plain text rather than as a database enum: SQLite has no native
    enum type, and a ``CHECK`` constraint over strings gives the same integrity
    guarantee while keeping the column readable in any SQLite browser.
    """

    IMAGE = "image"
    VIDEO = "video"
    WEBCAM = "webcam"


class JobStatus(StrEnum):
    """Lifecycle of a :class:`DetectionJob`.

    Normal path::

        pending ──> processing ──> completed
                        │
                        ├──> failed      (error_message is set)
                        └──> cancelled   (user stopped it)

    ``pending`` exists as a distinct state from ``processing`` because a video
    upload returns ``202 Accepted`` immediately (decision AD-02) while the
    background worker may not have picked the job up yet. Collapsing the two
    would make a queued job indistinguishable from a stalled one.
    """

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        """Return ``True`` if no further transition is possible from this state.

        The frontend polls a job's progress and uses this to decide when to
        stop polling.
        """
        return self in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model.

    Alembic's autogenerate reads ``Base.metadata`` to diff the models against
    the live database, so every model must inherit from this one class -- a
    model on a second base would be invisible to migrations and its table would
    simply never be created.
    """


class DetectionJob(Base):
    """One upload or capture session, and the state of processing it.

    A job is created the moment a file is accepted and lives until processing
    reaches a terminal state. Its purpose is twofold: it is the unit that
    dashboard usage statistics count, and it is what the frontend polls for
    progress while a video is being processed (FR-2.6).

    A webcam session is one job, not one job per frame. Frames arriving during
    the session raise :attr:`processed_frames` and attach their detections to
    the same job, which keeps "one usage event" meaning the same thing across
    all three input types.

    Attributes:
        id: UUID string primary key. A UUID rather than an auto-increment
            integer because the identifier is handed to the client and used in
            generated filenames, where a guessable sequential number would let
            one user enumerate another's uploads.
        input_type: Which of ``image``/``video``/``webcam`` produced this job.
        status: Current lifecycle state; see :class:`JobStatus`.
        progress: Completion fraction in ``[0.0, 1.0]``, for the progress bar.
        source_path: Where the uploaded file was stored.
        output_path: Where the annotated image or processed video was written.
        error_message: Technical reason the job failed. Server-side only --
            it is never returned to a user verbatim.
        total_frames: Frame count for a video, or ``None`` when not applicable
            or not yet known.
        processed_frames: Frames processed so far.
        created_at: When the job was accepted.
        completed_at: When it reached a terminal state, or ``None``.
        detections: Every plate found by this job.
    """

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
        # The database performs the cascade itself, so deleting a job does not
        # require loading its rows into memory first. This depends on SQLite
        # foreign keys being switched on -- see backend.models.database, which
        # enables the pragma on every connection.
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
    """One license plate found in one job.

    An image containing three plates produces three rows sharing a
    :attr:`source_job_id`. This is the record the history table and the
    accuracy reports are built from.

    Nullability follows one rule: **a detection is worth keeping even when OCR
    read nothing from it.** The detector's own output -- the box and its
    confidence -- is always present, so those columns are non-nullable. Every
    OCR-derived column is nullable, because a plate that was located but not
    read is a real and reportable outcome. Discarding those rows would remove
    precisely the failures the evaluation chapter needs to count, and would
    make recognition accuracy look perfect by construction.

    Attributes:
        id: Auto-increment primary key.
        plate_number: Normalised plate string after regex correction, e.g.
            ``"51F-12345"``. ``None`` when OCR read nothing.
        raw_ocr_text: The OCR engine's unmodified output. Kept so the effect of
            post-processing can be measured against ``plate_number``.
        confidence: **Detector** confidence in ``[0.0, 1.0]``. Always present.
        ocr_confidence: **OCR** confidence in ``[0.0, 1.0]``, kept in its own
            column so an uncertain reading is never mistaken for an uncertain
            detection. ``None`` when OCR read nothing.
        input_type: Which of ``image``/``video``/``webcam`` this came from.
            Denormalised from the parent job so history filtering does not
            require a join on every query.
        image_path: Stored source image, or the extracted frame for a video.
        plate_image_path: Stored crop of the plate itself.
        bbox_x: Left edge of the plate box, in source-image pixels.
        bbox_y: Top edge of the plate box.
        bbox_w: Box width.
        bbox_h: Box height.
        is_valid_format: Whether :attr:`plate_number` matches a known
            Vietnamese plate pattern. ``False`` flags the row rather than
            rejecting it.
        plate_line_count: ``1`` or ``2``. Lets accuracy be reported separately
            for single-line and two-line plates, which behave very differently.
        upper_char_count: For a two-line plate, how many characters were read
            from the **upper** line; ``NULL`` when unknown or single-line.

            Stored because it is *evidence*, not presentation. Separators are
            still derived on read (see
            :func:`~backend.services.detection_service.display_text`), but that
            derivation cannot succeed without this: an eight-character two-line
            string is genuinely ambiguous, and ``67C10815`` is ``67C-108.15``
            when the upper line read ``67C`` and ``67C1-0815`` when it read
            ``67C1``. Both are legal Vietnamese plates, so no rule over the
            flat string can separate them -- only the image can, and this
            column is where that observation survives.
        processing_time: Seconds spent on this plate, detection plus OCR.
        detected_time: When the plate was detected. For a video this is the
            moment of processing, not a position within the video.
        created_at: When the row was written.
        source_job_id: The job this plate belongs to.
        job: The parent job.
    """

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

    # Vehicle-class attributes, added 2026-07-20. Both were already computed
    # during recognition and then discarded before reaching this table, which
    # meant an army plate was stored indistinguishable from an unreadable one:
    # `is_valid_format = false` and nothing to say why. Read the two together --
    # neither identifies a vehicle class alone. `plate_kind` comes from the
    # character string and cannot see that a business vehicle's yellow plate
    # carries the same layout as a private vehicle's white one; `plate_color`
    # comes from the pixels and cannot tell a diplomatic plate from a private
    # one, both being white.
    plate_kind: Mapped[str | None] = mapped_column(String(_ENUM_LENGTH))
    plate_color: Mapped[str | None] = mapped_column(String(_ENUM_LENGTH))
    plate_color_confidence: Mapped[float | None] = mapped_column(Float)

    # Where in the source clip this plate was found, in seconds. NULL for images
    # and realtime frames, which have no "when" to record. Stored as a timestamp
    # rather than a frame index because an index means nothing without the clip's
    # frame rate, and that is neither stored nor constant across sources.
    video_time_seconds: Mapped[float | None] = mapped_column(Float)

    processing_time: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    detected_time: Mapped[dt.datetime] = mapped_column(UtcDateTime, nullable=False, default=utcnow)
    created_at: Mapped[dt.datetime] = mapped_column(UtcDateTime, nullable=False, default=utcnow)

    # Non-nullable on purpose. Every detection must belong to a job, because
    # usage statistics are defined as a count of distinct jobs; a row with no
    # job would be invisible to those counts while still appearing in the
    # history list, so the two views of the same data would disagree. Making
    # the column mandatory turns that inconsistency into an insert-time error
    # instead of a silently wrong dashboard number.
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
        # The history screen's default query is "newest first, optionally
        # filtered by input type". A composite index lets SQLite satisfy the
        # filter and the ordering from one structure, which is what keeps the
        # paginated query inside NFR-P6 at 100k rows.
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
        # A Vietnamese two-line plate carries province + serial on the upper
        # line: three characters (`67C`) or four (`77H5`). Nothing else is a
        # legal reading, so a value outside that range means the count was
        # miscomputed rather than observed, and it must not reach the
        # display rule.
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
        """Return ``True`` if post-processing changed the raw OCR string.

        This is the per-row form of the measurement ``raw_ocr_text`` exists
        for: aggregated over the test set it gives the share of readings the
        correction step altered, which the evaluation report pairs with the
        change in accuracy.
        """
        if self.plate_number is None or self.raw_ocr_text is None:
            return False
        return self.plate_number != self.raw_ocr_text

    def __repr__(self) -> str:
        """Return a concise developer-facing representation."""
        return (
            f"DetectionHistory(id={self.id!r}, plate_number={self.plate_number!r}, "
            f"confidence={self.confidence:.3f}, input_type={self.input_type!r})"
        )
