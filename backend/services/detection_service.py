"""Orchestration of the recognition pipeline, storage and persistence.

This service is the only place where the three sides of a detection meet: the
AI pipeline that reads the plate, the storage service that keeps the pixels,
and the database that records what happened. Routers call it and translate
nothing; the pipeline knows nothing about either of the other two.

Dependency injection, and why it is not optional here
-----------------------------------------------------
The pipeline arrives as a **constructor argument**. The service never imports a
detector, never reads ``model_path`` and never calls a factory. That is what
makes NFR-M5 real rather than aspirational: swapping PaddleOCR for EasyOCR, or
the whole pipeline for the :class:`StubPipeline` below, changes one line in
``backend.main`` and nothing in this file, in the routers, or in the tests --
which inject a stub precisely so that the suite runs in a second and without
2 GB of model weights.

The pipeline contract is expressed as a :class:`typing.Protocol` rather than as
an abstract base class, and the direction of that choice matters. An ABC would
have to live in ``backend`` and be *inherited* by the pipeline in ``ai``, which
would make ``ai`` import from ``backend`` -- the arrow NFR-M1 forbids. A
Protocol is structural: Phase 4's ``ALPRPipeline`` satisfies it by having the
right methods, while remaining entirely unaware that this file exists.

.. important::
   :class:`StubPipeline` fabricates results. It existed so the API, the
   database and the frontend could be built and demonstrated end to end before
   the model was trained; since Phase 4 wired the real
   ``ai.inference.pipeline.ALPRPipeline`` into
   :func:`backend.main.build_pipeline`, the stub is installed **only on
   explicit opt-in** (``ALPR_USE_STUB``). When the weights are missing the
   composition root installs :class:`UnavailablePipeline` instead, which fails
   every request cleanly rather than inventing plates. The stub reports
   ``is_ready = False``, so ``/health`` answers ``"degraded"`` and no
   demonstration can silently pass off fabricated plates as real ones.
"""

from __future__ import annotations

import time
from typing import Final, Protocol, runtime_checkable

import cv2
import numpy as np
from sqlalchemy.orm import Session

from ai.inference.exceptions import ALPRError
from ai.inference.normalizer import VietnamesePlateNormalizer
from ai.inference.plate_rules import PlateKind
from ai.inference.types import (
    BoundingBox,
    DetectionResult,
    ImageArray,
    PipelineResult,
    PlateDetection,
    PlateRecognition,
)
from backend.core.config import Settings
from backend.core.exceptions import NotFoundError, ProcessingError, ValidationError
from backend.core.logging import get_logger, request_context
from backend.models.detection import DetectionHistory, DetectionJob, InputType, JobStatus, utcnow
from backend.schemas.detection import (
    BoundingBoxSchema,
    DetectionJobResponse,
    DetectionResponse,
    DetectionResultSchema,
)
from backend.services.storage_service import MediaKind, StorageService

__all__ = [
    "PlatePipeline",
    "StubPipeline",
    "UnavailablePipeline",
    "DetectionService",
    "to_job_response",
    "display_text",
]

logger = get_logger(__name__)

_NORMALIZER = VietnamesePlateNormalizer()
"""Shared, stateless formatter for the display rendering of a stored plate.

Module-level because it holds no per-request state and constructing one per
response would recompile the same regular expressions on every history page.
"""

_PROGRESS_COMMIT_EVERY: Final[int] = 10
"""Processed frames between two progress writes.

Committing on every frame turns a two-minute video into thousands of write
transactions competing with the dashboard's reads. Committing only at the end
would leave the progress bar frozen at zero for the whole job, which is exactly
what the endpoint exists to prevent. Ten is the compromise: at the configured
frame stride it refreshes several times a second of video.
"""

_MIN_UNCLASSIFIED_TEXT_LEN: Final[int] = 7
"""Shortest OCR string worth persisting from a video when nothing matched it.

Every legal civil layout is at least 7 characters (2 province + 1 serial +
4 order digits), so an *unclassified* string shorter than this cannot be a
complete plate -- it is a fragment read off a blurred frame. The guard applies
only when the classifier found no family at all: a recognised-but-invalid kind
such as ``military`` passes at any length, because "recognise and exclude" is
a finding the operator must see, not noise.

Measured motivation: the 14-second demo video produced 27 history rows of
which 12 were fragments like ``S``, ``BEK`` and ``187`` -- rows nobody can act
on, polluting the history page one upload at a time.
"""

_VARIANT_MERGE_WINDOW_SECONDS: Final[float] = 3.5
"""How close in time two readings must be to count as variants of one plate.

One physical plate read across consecutive sampled frames sometimes yields
strings differing in 1-2 characters (e.g. ``52Z1513`` next to ``52Z20513``
due to glare or shadow). Merging on string distance alone would be unsafe,
so the merge additionally requires the sightings to be near-simultaneous (<=3.5s)
and share province prefix / suffix digits.
"""


def _within_one_edit(a: str, b: str) -> bool:
    """Return whether two strings differ by at most one edit operation."""
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) > len(b):
        a, b = b, a
    i = 0
    while i < len(a) and a[i] == b[i]:
        i += 1
    if i == len(a):
        return True
    if len(a) == len(b):
        return a[i + 1 :] == b[i + 1 :]
    return a[i:] == b[i + 1 :]


def _levenshtein_distance(a: str, b: str) -> int:
    """Compute standard Levenshtein distance between two short strings."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    dp = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        new_dp = [i + 1] * (len(b) + 1)
        for j, cb in enumerate(b):
            cost = 0 if ca == cb else 1
            new_dp[j + 1] = min(dp[j + 1] + 1, new_dp[j] + 1, dp[j] + cost)
        dp = new_dp
    return dp[len(b)]


def _is_fuzzy_duplicate_plate(a: str, b: str) -> bool:
    """Return whether two plate strings describe the same physical vehicle.

    Handles 1-edit substitutions/insertions, and 2-edit variations where the
    same vehicle has common province prefix (e.g. '52Z') and trailing digits ('513').
    """
    if not a or not b:
        return False
    if a == b or _within_one_edit(a, b):
        return True

    dist = _levenshtein_distance(a, b)
    if dist <= 2:
        # Require shared 2-digit province code (e.g. '52', '67', '79')
        if len(a) >= 3 and len(b) >= 3 and a[:2] == b[:2]:
            # Shared series letter (e.g. 52Z...)
            if a[2] == b[2]:
                return True
            # Or shared trailing digits (e.g. ...513)
            if len(a) >= 4 and len(b) >= 4 and a[-3:] == b[-3:]:
                return True
    return False


# ---------------------------------------------------------------------------
# The pipeline contract
# ---------------------------------------------------------------------------


@runtime_checkable
class PlatePipeline(Protocol):
    """What this service requires of a recognition pipeline.

    Deliberately tiny. A larger interface would tie the service to details of
    how recognition is staged internally -- detector, crop, OCR, normalise --
    and those are exactly the details Phase 4 is free to rearrange.

    Implementations must be safe to call from the request thread pool and from
    a background video job, potentially at the same time.
    """

    @property
    def name(self) -> str:
        """Return a short engine identifier, e.g. ``"yolo11n+paddleocr"``.

        Recorded in logs so a stored result can be traced back to the engine
        that produced it -- and so a result produced by the stub is obvious in
        hindsight.
        """
        ...

    @property
    def is_ready(self) -> bool:
        """Return whether the pipeline can produce genuine results.

        ``False`` for the stub and for a real pipeline whose weights failed to
        load. ``/health`` reports it as ``model_loaded`` and downgrades its
        status accordingly, so a misconfigured deployment is visible from the
        outside instead of quietly returning fabricated data.
        """
        ...

    def process(self, image: ImageArray, *, read_text: bool = True) -> PipelineResult:
        """Find and read every license plate in one image or video frame.

        Args:
            image: Source image as a BGR ``uint8`` array of shape
                ``(height, width, 3)`` -- what ``cv2.imread`` returns.
            read_text: Whether to read the characters. ``False`` asks for boxes
                only, which the live preview uses on the frames between reads.

        Returns:
            A :class:`~ai.inference.types.PipelineResult`. An image containing
            no plate yields an empty result list, which is a normal outcome and
            never an error.

        Raises:
            ai.inference.exceptions.ALPRError: If inference itself fails.
        """
        ...


class StubPipeline:
    """A placeholder pipeline that fabricates structurally valid results.

    **This class recognises nothing.** It exists for one reason: the API, the
    database schema, the statistics and the frontend all need something to
    exchange before Phase 3 finishes training a model, and building them
    against a pipeline that does not exist yet would mean discovering every
    integration mistake at the end, all at once.

    What it guarantees is *shape*, not truth. Every field the real pipeline
    fills is filled here, in the right type and the right range: two separate
    confidences, a raw OCR string that differs from the corrected one, a
    plausible bounding box inside the image, a line count, a validity flag. Code
    written against it therefore exercises every branch that the real pipeline
    will exercise.

    Output is deterministic for a given image, derived from a hash of its
    pixels. Two calls with the same image return the same plate, so a test can
    assert on it; two different images return different plates, so a
    demonstration does not look obviously canned.

    .. warning::
       :attr:`is_ready` is ``False`` and :attr:`name` is ``"stub"``. Both are
       surfaced by ``/health``, which reports ``"degraded"`` while this class is
       installed. Do not "fix" that by hard-coding ``True``: the whole point is
       that a deployment running on fabricated data cannot look healthy.
    """

    _LETTERS: Final[str] = "ABCDEFGHKLMNPSTVXYZ"
    """Series letters that appear on Vietnamese plates, roughly."""

    @property
    def name(self) -> str:
        """Return the engine identifier, ``"stub"``."""
        return "stub"

    @property
    def is_ready(self) -> bool:
        """Return ``False``: fabricated results are never a ready service."""
        return False

    def process(self, image: ImageArray, *, read_text: bool = True) -> PipelineResult:
        """Fabricate one detection positioned inside the given image.

        Args:
            image: Source image as a BGR ``uint8`` array. Only its shape and a
                cheap hash of its contents are used.
            read_text: Honoured rather than ignored: with ``False`` the fake
                plate comes back without a string, the same shape the real
                pipeline returns. A stub that answered differently from the
                thing it stands in for would let the detection-only path pass
                its tests and fail in production.

        Returns:
            A result carrying exactly one plate, with the source dimensions
            filled in so bounding-box scaling can be tested.

        Raises:
            ai.inference.exceptions.InvalidImageError: Never raised by the
                stub; declared because callers must handle it from the real
                pipeline.
        """
        started = time.perf_counter()
        height, width = int(image.shape[0]), int(image.shape[1])

        # A box in the lower-middle of the frame, where a plate usually sits,
        # sized as a realistic single-line plate. Clamped so that a very small
        # image still produces a box with positive width and height, which
        # BoundingBox requires.
        box_width = max(32, width // 5)
        box_height = max(12, box_width // 4)
        left = max(0, (width - box_width) // 2)
        top = max(0, min(height - box_height, (height * 2) // 3))
        bbox = BoundingBox(
            x=left,
            y=top,
            width=min(box_width, max(1, width - left)),
            height=min(box_height, max(1, height - top)),
        )

        seed = int(np.sum(image[::17, ::17], dtype=np.int64) % 100_000)
        province = 10 + seed % 90
        letter = self._LETTERS[seed % len(self._LETTERS)]
        serial = f"{seed % 100000:05d}"
        text = f"{province}{letter}-{serial}"
        # The raw string differs from the corrected one, so that every consumer
        # of `raw_ocr_text` is exercised rather than seeing two equal strings.
        raw_text = text.replace("-", "").replace("0", "O", 1)

        recognition = (
            PlateRecognition(
                text=text,
                raw_text=raw_text,
                confidence=0.50 + (seed % 45) / 100.0,
                line_count=1 if bbox.aspect_ratio >= 2.5 else 2,
                is_valid_format=True,
            )
            if read_text
            else None
        )
        detection = PlateDetection(bbox=bbox, confidence=0.60 + (seed % 35) / 100.0)

        crop = image[bbox.y : bbox.y2, bbox.x : bbox.x2]
        elapsed = time.perf_counter() - started

        return PipelineResult(
            results=[
                DetectionResult(
                    detection=detection,
                    recognition=recognition,
                    plate_image=crop if crop.size else None,
                    processing_time=elapsed,
                )
            ],
            total_time=elapsed,
            image_width=width,
            image_height=height,
        )

    def warmup(self) -> None:
        """Do nothing; the stub has no model to prime."""
        return None


class UnavailablePipeline:
    """The pipeline that is installed when the real one could not be built.

    It is **not** a stub. :class:`StubPipeline` fabricates plausible results and
    is therefore only safe when a human asked for it explicitly; this class
    fabricates nothing and refuses every request. That difference is the whole
    reason it exists: when the weights are missing or PaddleOCR fails to load,
    the correct behaviour is a service that starts, reports ``model_loaded =
    false`` on ``/health``, and returns a clean error for each detection --
    never one that quietly answers with invented plate numbers.

    Args:
        reason: Why the real pipeline is unavailable. Recorded in the log and in
            the raised error's technical detail; it never reaches a user.
    """

    def __init__(self, reason: str) -> None:
        """Store the reason the real pipeline could not be constructed."""
        self._reason = reason

    @property
    def name(self) -> str:
        """Return the engine identifier, ``"unavailable"``."""
        return "unavailable"

    @property
    def is_ready(self) -> bool:
        """Return ``False``: there is no model behind this object."""
        return False

    @property
    def reason(self) -> str:
        """Return why the real pipeline could not be built."""
        return self._reason

    def process(self, image: ImageArray, *, read_text: bool = True) -> PipelineResult:
        """Refuse the request.

        Args:
            image: Ignored.
            read_text: Ignored; there is no pipeline to ask.

        Returns:
            Never returns.

        Raises:
            ai.inference.exceptions.ALPRError: Always. The service layer turns
                this into a ``ProcessingError`` with a Vietnamese user message.
        """
        raise ALPRError(f"Recognition pipeline is not available: {self._reason}")

    def warmup(self) -> None:
        """Do nothing; there is no model to prime."""
        return None


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------


def to_job_response(job: DetectionJob, storage: StorageService) -> DetectionJobResponse:
    """Map a job row to its API representation.

    Two fields cannot come straight from the ORM object and are the reason this
    function exists: ``output_url`` is derived from the stored relative path so
    the server's directory layout stays private, and ``detection_count`` is a
    count of the related rows. ``error_message`` is deliberately **not**
    carried across -- it holds the technical failure text and belongs in the log
    (NFR-S4).

    Args:
        job: The job row to convert.
        storage: Used to turn a stored path into a public URL.

    Returns:
        The response model for this job.
    """
    return DetectionJobResponse(
        id=job.id,
        input_type=job.input_type,  # type: ignore[arg-type]
        status=job.status,  # type: ignore[arg-type]
        progress=job.progress,
        output_url=storage.to_url(job.output_path),
        total_frames=job.total_frames,
        processed_frames=job.processed_frames,
        detection_count=len(job.detections),
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


def display_text(
    plate_number: str | None,
    line_count: int | None,
    kind: str | None = None,
    upper_char_count: int | None = None,
) -> str | None:
    """Render a stored plate number with the separators the real plate carries.

    Derived on read rather than stored: the separators are a pure function of
    the plate string AND its established family, so persisting them would be a
    second copy of the same fact -- one that could drift, and one that
    historical rows written before this feature would be missing anyway.

    Args:
        plate_number: The bare stored string, e.g. ``"29E01566"``.
        line_count: Lines on the plate, used to disambiguate layouts when no
            ``kind`` is available.
        kind: The stored plate family (``row.plate_kind``). Forwarding it is
            what keeps the response's grouping consistent with its own
            ``plate_kind`` field: the pipeline may have classified
            ``51H60969`` as a car from the printed-dot evidence, and
            re-deriving here without that evidence used to regroup it as the
            motorcycle ``51H6-0969`` while the badge said car (field bug,
            24/07/2026; rules in ``docs/reports/23-display-format-rules.md``).
        upper_char_count: ``row.upper_char_count`` -- how many characters the
            recogniser read from the upper line of a two-line plate, or
            ``None``.

            Outranks ``kind`` when present, because it is an observation of the
            image rather than an inference from the string. ``kind`` cannot
            settle ``67C10815``: both ``67C-108.15`` (serial ``C``) and
            ``67C1-0815`` (serial ``C1``) are legal, and the flat string
            carries no evidence either way. The upper line does.

    Returns:
        The formatted string, e.g. ``"29E-015.66"``; ``None`` when there is no
        plate number; or the input unchanged if it matches no known layout --
        an unrecognised string is shown exactly as read, never dressed up to
        look like a valid plate.
    """
    if not plate_number:
        return None
    try:
        return _NORMALIZER.format_for_display(
            plate_number,
            line_count=line_count,
            kind=kind or None,
            upper_char_count=upper_char_count or 0,
        )
    except Exception:  # noqa: BLE001 - presentation must never break a response
        logger.debug("format_for_display failed for %r", plate_number)
        return plate_number


def _to_result_schema(row: DetectionHistory, storage: StorageService) -> DetectionResultSchema:
    """Map a persisted detection row to the per-plate response model.

    Args:
        row: The stored detection.
        storage: Used to turn the stored crop path into a public URL.

    Returns:
        The response model for one detected plate.
    """
    return DetectionResultSchema(
        plate_number=row.plate_number,
        raw_ocr_text=row.raw_ocr_text,
        detection_confidence=row.confidence,
        ocr_confidence=row.ocr_confidence,
        bbox=BoundingBoxSchema(x=row.bbox_x, y=row.bbox_y, width=row.bbox_w, height=row.bbox_h),
        is_valid_format=row.is_valid_format,
        plate_kind=row.plate_kind,
        plate_color=row.plate_color,
        plate_color_confidence=row.plate_color_confidence,
        plate_display=display_text(
            row.plate_number, row.plate_line_count, row.plate_kind, row.upper_char_count
        ),
        video_time_seconds=row.video_time_seconds,
        plate_line_count=row.plate_line_count,
        processing_time=row.processing_time,
        plate_image_url=storage.to_url(row.plate_image_path),
    )


def _to_unstored_result_schema(result: DetectionResult) -> DetectionResultSchema:
    """Map a pipeline result to the response model **without** storing it.

    Used only by the detection-only frame path, where there is deliberately no
    database row to map from. A box with no characters is not a detection
    record: the live preview asks for several of these every second, and
    writing them would bury the history under empty rows and inflate every
    count derived from it.

    Args:
        result: One plate straight from the pipeline.

    Returns:
        The response model, carrying the box and its colour but no text.
    """
    box = result.detection.bbox
    return DetectionResultSchema(
        plate_number=None,
        raw_ocr_text=None,
        detection_confidence=result.detection.confidence,
        ocr_confidence=None,
        bbox=BoundingBoxSchema(x=box.x, y=box.y, width=box.width, height=box.height),
        is_valid_format=False,
        plate_kind=None,
        plate_color=result.plate_color or None,
        plate_color_confidence=result.plate_color_confidence,
        plate_display=None,
        video_time_seconds=None,
        plate_line_count=None,
        processing_time=result.processing_time,
        plate_image_url=None,
    )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class DetectionService:
    """Runs detections and records them.

    One instance is built per request from injected collaborators; it holds no
    mutable state of its own, so the same pipeline object is shared while each
    request keeps its own database session.
    """

    def __init__(
        self,
        *,
        pipeline: PlatePipeline,
        storage: StorageService,
        settings: Settings,
    ) -> None:
        """Create the service.

        Args:
            pipeline: The recognition pipeline. Injected, never constructed
                here -- see the module docstring for why that is load-bearing.
            storage: Handles every file this service reads or writes.
            settings: Supplies the video frame stride and the upload limits.
        """
        self._pipeline = pipeline
        self._storage = storage
        self._settings = settings

    @property
    def pipeline_name(self) -> str:
        """Return the identifier of the installed pipeline."""
        return self._pipeline.name

    @property
    def pipeline_ready(self) -> bool:
        """Return whether the installed pipeline can produce genuine results."""
        return self._pipeline.is_ready

    # -- Image ------------------------------------------------------------

    def detect_image(
        self,
        db: Session,
        *,
        data: bytes,
        original_filename: str | None = None,
    ) -> DetectionResponse:
        """Detect and recognise every plate in an uploaded image.

        The whole operation is one job. An image containing three plates
        produces three ``detection_history`` rows sharing one ``source_job_id``,
        which is what lets the dashboard report one upload rather than three.

        Args:
            db: Session for this request. Committed here, once, when the unit
                of work is complete.
            data: The raw uploaded bytes.
            original_filename: Client-supplied name, used only for logging.

        Returns:
            The detection response, including the job identifier and one entry
            per plate. **An image with no plate is a success**: the response
            carries an empty list and HTTP 200, because a 4xx would erase every
            negative case from the statistics.

        Raises:
            ValidationError: If the bytes cannot be decoded as an image.
            FileTooLargeError: If the upload exceeds the configured ceiling.
            UnsupportedMediaTypeError: If its true type is not an accepted image.
            ProcessingError: If the pipeline or storage fails.
        """
        stored = self._storage.save_upload(
            data, kind=MediaKind.IMAGE, original_filename=original_filename
        )
        job = self._create_job(db, input_type=InputType.IMAGE, source_path=stored.relative_path)

        try:
            image = self._decode_image(data)
            result = self._run_pipeline(image, job_id=job.id)
            rows = self._persist_results(
                db,
                job=job,
                result=result,
                input_type=InputType.IMAGE,
                image_path=stored.relative_path,
            )
            self._finish_job(job, status=JobStatus.COMPLETED)
            db.commit()
        except Exception as error:
            self._fail_job(db, job, error)
            raise

        logger.info(
            "image detection completed",
            extra={
                "job_id": job.id,
                "plate_count": len(rows),
                "engine": self._pipeline.name,
                "total_time": result.total_time,
            },
        )
        return DetectionResponse(
            job_id=job.id,
            input_type=InputType.IMAGE.value,
            results=[_to_result_schema(row, self._storage) for row in rows],
            plate_count=len(rows),
            processing_time=result.total_time,
            image_url=stored.url,
            image_width=result.image_width,
            image_height=result.image_height,
        )

    # -- Webcam frame -----------------------------------------------------

    def detect_frame(
        self,
        db: Session,
        *,
        data: bytes,
        job_id: str | None = None,
        read_text: bool = True,
    ) -> DetectionResponse:
        """Detect plates in a single webcam frame.

        A webcam **session** is one job, not one job per frame: the client
        passes the ``job_id`` it received from the first frame back with every
        subsequent one, and the frames accumulate against that job. Creating a
        job per frame would count a thirty-second session as hundreds of
        uploads and make the usage figures meaningless.

        Frames are not kept on disk. A session produces frames at several per
        second, all nearly identical, and storing them would fill the disk to
        record nothing -- only the plate crop, which is what a user actually
        looks at afterwards, is saved.

        Args:
            db: Session for this request.
            data: The raw frame bytes, normally a JPEG from the browser canvas.
            job_id: Identifier of an ongoing webcam session. A new session is
                started when omitted or unknown.
            read_text: Whether to read the characters. ``False`` returns boxes
                and colours only, and **stores nothing**.

                A live preview re-detects the same vehicles several times a
                second, and OCR is 55% of the per-frame cost while producing
                the same string every time. A client that tracks boxes between
                frames can read each plate once and ask for detection alone in
                between. Nothing is written for those frames because a box with
                no characters is not a record worth keeping, and the session
                would otherwise accumulate empty rows at several per second.

        Returns:
            The detection response for this frame, carrying the session's job
            identifier so the caller can send it with the next frame. With
            ``read_text=False`` every entry has a ``null`` plate number.

        Raises:
            ValidationError: If the frame cannot be decoded, is empty, or
                exceeds the image size ceiling.
            ProcessingError: If the pipeline fails.
        """
        # Validated as an image -- a webcam frame arrives as a JPEG or PNG and
        # is subject to the same magic-byte and size rules as an upload
        # (NFR-S1, NFR-S3). It is simply not written to disk afterwards.
        self._storage.validate_upload(data, kind=MediaKind.IMAGE)

        job = self._resume_or_create_webcam_job(db, job_id)

        try:
            image = self._decode_image(data)
            result = self._run_pipeline(image, job_id=job.id, read_text=read_text)

            if read_text:
                rows = self._persist_results(
                    db,
                    job=job,
                    result=result,
                    input_type=InputType.WEBCAM,
                    image_path=None,
                )
                entries = [_to_result_schema(row, self._storage) for row in rows]
            else:
                entries = [_to_unstored_result_schema(item) for item in result.results]

            # The frame counter still advances: the frame was processed, and a
            # progress figure that ignored the cheap frames would understate how
            # much of the session the system actually looked at.
            job.processed_frames += 1
            job.status = JobStatus.PROCESSING.value
            db.commit()
        except Exception as error:
            self._fail_job(db, job, error)
            raise

        return DetectionResponse(
            job_id=job.id,
            input_type=InputType.WEBCAM.value,
            results=entries,
            plate_count=len(entries),
            processing_time=result.total_time,
            image_url=None,
            image_width=result.image_width,
            image_height=result.image_height,
        )

    # -- Video ------------------------------------------------------------

    def create_video_job(
        self,
        db: Session,
        *,
        data: bytes,
        original_filename: str | None = None,
    ) -> DetectionJob:
        """Accept a video upload and queue it, without processing it.

        Returns as soon as the bytes are on disk. Processing happens later in
        :meth:`process_video_job`, because a sixty-second video takes roughly
        200 seconds on CPU (NFR-SC3) and no HTTP client waits that long -- the
        request would time out somewhere in the middle with the work half done
        and no way to find out how it ended.

        Args:
            db: Session for this request; committed before returning so the job
                is visible to the background task and to a status poll that may
                arrive first.
            data: The raw uploaded bytes.
            original_filename: Client-supplied name, used only for logging.

        Returns:
            The persisted job in state ``pending``.

        Raises:
            FileTooLargeError: If the upload exceeds the video ceiling.
            UnsupportedMediaTypeError: If its true type is not an accepted video.
            ProcessingError: If the file could not be written.
        """
        stored = self._storage.save_upload(
            data, kind=MediaKind.VIDEO, original_filename=original_filename
        )
        # _create_job commits, so the job is visible to the background task and
        # to a status poll that may arrive first. That used to be an extra
        # `db.commit()` here, needed only because _create_job did not commit.
        job = self._create_job(
            db,
            input_type=InputType.VIDEO,
            source_path=stored.relative_path,
            status=JobStatus.PENDING,
        )

        logger.info(
            "video job queued",
            extra={"job_id": job.id, "source": stored.relative_path},
        )
        return job

    def process_video_job(self, job_id: str) -> None:
        """Process a queued video to completion.

        Runs outside any request, so it opens its own session
        (:func:`~backend.models.database.session_scope` semantics via an
        explicit session) and its own log correlation context -- the request
        that queued the job returned ``202`` and closed its session long before
        this starts.

        Frames are sampled every ``frame_stride`` frames rather than processed
        exhaustively. At 30 fps a plate is visible across dozens of consecutive
        frames, so full processing multiplies the cost by the stride and adds
        nothing but duplicates.

        Results are **de-duplicated before they are written**, not after. The
        same plate seen in forty sampled frames must become one history row: it
        was one plate. Rows are keyed by the recognised text, keeping the
        highest-confidence reading; a plate the OCR could not read is keyed by
        its position in the frame instead, so a stationary unreadable plate
        collapses to one row rather than one per frame.

        This method never raises: it is a background task with nobody to catch
        it. Failures are recorded on the job, where the polling client sees
        them as ``status = "failed"``.

        Args:
            job_id: Identifier of the job to process.
        """
        from backend.models.database import SessionLocal  # local: avoids an import cycle

        with request_context() as trace_id:
            session = SessionLocal()
            try:
                job = session.get(DetectionJob, job_id)
                if job is None:
                    logger.error("video job vanished before processing", extra={"job_id": job_id})
                    return
                logger.info(
                    "video job started",
                    extra={"job_id": job_id, "trace_id": trace_id},
                )
                self._process_video(session, job)
            except Exception as error:  # noqa: BLE001 -- background tasks swallow everything
                logger.exception(
                    "video job failed",
                    extra={"job_id": job_id, "error_type": type(error).__name__},
                )
                session.rollback()
                self._mark_job_failed(session, job_id, error)
            finally:
                session.close()

    def _process_video(self, db: Session, job: DetectionJob) -> None:
        """Run the sampling loop over one video.

        Args:
            db: Session owned by the background task.
            job: The job to process; mutated and committed as it progresses.

        Raises:
            ProcessingError: If the video cannot be opened or decoded.
        """
        if not job.source_path:
            raise ProcessingError(
                "Video job has no source file recorded",
                context={"job_id": job.id},
            )

        source = self._storage.get_path(job.source_path)
        capture = cv2.VideoCapture(str(source))
        if not capture.isOpened():
            raise ProcessingError(
                f"OpenCV could not open video {source}",
                context={"job_id": job.id},
            )

        job.status = JobStatus.PROCESSING.value
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        job.total_frames = total_frames if total_frames > 0 else None
        db.commit()

        stride = max(1, self._settings.frame_stride)
        best_by_key: dict[str, tuple[DetectionResult, int, int]] = {}
        frame_index = 0
        processed = 0

        # Read while the capture is still open. Querying these properties after
        # ``capture.release()`` returns 0 on every backend, which would report a
        # video of size 0x0 and make any bounding box the frontend scales
        # against it collapse.
        frame_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        frame_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        # Needed to turn a frame index into a timestamp. Read here for the same
        # reason as the dimensions above: it reports 0 once the capture is
        # released, and a frame rate of 0 would put every plate at second zero.
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)

        try:
            while True:
                grabbed, frame = capture.read()
                if not grabbed:
                    break
                if frame_index % stride == 0:
                    result = self._run_pipeline(frame, job_id=job.id)
                    self._merge_frame_results(best_by_key, result, frame_index)
                    processed += 1

                    if processed % _PROGRESS_COMMIT_EVERY == 0:
                        job.processed_frames = processed
                        job.progress = self._progress(frame_index, total_frames)
                        db.commit()
                        if self._is_cancelled(db, job):
                            logger.info("video job cancelled", extra={"job_id": job.id})
                            return
                frame_index += 1
        finally:
            capture.release()

        # An unknown frame rate disables the variant merge (a window of "0
        # frames apart" can never hold), which fails safe: no merge is better
        # than a merge whose time window was guessed.
        max_frame_gap = int(_VARIANT_MERGE_WINDOW_SECONDS * fps) if fps > 0 else 0
        sightings = self._collapse_variants(best_by_key, max_frame_gap=max_frame_gap)
        merged = [entry for entry, _ in sightings]
        # Where each plate was found, in seconds. The frame index was already
        # tracked and then discarded; keeping it lets the interface say *when* a
        # plate passed and lets a reviewer seek to that moment in the source to
        # check a doubtful reading. ``None`` when the container reports no frame
        # rate -- an unknown timestamp is better left absent than reported as
        # second zero.
        video_times = [(index / fps if fps > 0 else None) for _, index in sightings]
        pseudo = PipelineResult(
            results=merged,
            total_time=0.0,
            image_width=frame_width,
            image_height=frame_height,
        )
        self._persist_results(
            db,
            job=job,
            result=pseudo,
            input_type=InputType.VIDEO,
            image_path=job.source_path,
            video_times=video_times,
        )

        job.processed_frames = processed
        # TODO: render an annotated copy of the video and set
        # ``job.output_path`` to it, so the client can download a result video
        # rather than only the per-plate rows. Known limitation, deliberately
        # kept out of scope: on the CPU-only target machine re-encoding every
        # frame with boxes drawn on it would multiply the processing time of a
        # job, and the dashboard already exposes the per-plate crops that the
        # pipeline persisted for verification.
        self._finish_job(job, status=JobStatus.COMPLETED)
        db.commit()

        logger.info(
            "video job completed",
            extra={
                "job_id": job.id,
                "frames_processed": processed,
                "unique_plates": len(merged),
            },
        )

    @staticmethod
    def _merge_frame_results(
        best_by_key: dict[str, tuple[DetectionResult, int, int]],
        result: PipelineResult,
        frame_index: int,
    ) -> None:
        """Fold one frame's detections into the running de-duplicated set.

        Two classes of sighting are dropped here rather than persisted:

        * **Textless boxes.** A detector hit that OCR read nothing from tells a
          video reviewer nothing they can act on, and because a moving vehicle
          crosses the frame, keying such boxes by position manufactured a fresh
          "unreadable" history row every few dozen pixels of travel.
        * **Unclassified fragments** shorter than
          :data:`_MIN_UNCLASSIFIED_TEXT_LEN` -- partial reads off blurred
          frames (``S``, ``BEK``, ``187``). Strings the classifier *did* place
          in a family are kept whatever their length or validity: a military
          plate is a finding, not noise.

        Args:
            best_by_key: Accumulator mapping a plate string to the best
                sighting so far: ``(entry, frame_index, times_seen)``. Mutated.
            result: The current frame's pipeline output.
            frame_index: Index of the current frame, kept so the persisted row
                can carry a timestamp.
        """
        for entry in result.results:
            if not entry.has_text or entry.recognition is None:
                continue
            recognition = entry.recognition
            is_unclassified = recognition.kind in ("", PlateKind.UNKNOWN.value)
            if (
                is_unclassified
                and not recognition.is_valid_format
                and len(recognition.text) < _MIN_UNCLASSIFIED_TEXT_LEN
            ):
                continue

            key = recognition.text
            score = recognition.confidence

            existing = best_by_key.get(key)
            if existing is None:
                best_by_key[key] = (entry, frame_index, 1)
                continue

            previous, previous_frame, seen = existing
            previous_score = (
                previous.recognition.confidence
                if previous.recognition is not None
                else previous.detection.confidence
            )
            if score > previous_score:
                best_by_key[key] = (entry, frame_index, seen + 1)
            else:
                best_by_key[key] = (previous, previous_frame, seen + 1)

    @staticmethod
    def _collapse_variants(
        best_by_key: dict[str, tuple[DetectionResult, int, int]],
        max_frame_gap: int,
    ) -> list[tuple[DetectionResult, int]]:
        """Merge single-character OCR variants of one physical plate.

        The per-string accumulator cannot see that ``51P51578`` and
        ``51P54578`` were the same motorcycle read twice, so it hands over one
        row per spelling. This pass absorbs a reading into another when the
        two strings differ by **at most one edit** and were seen **within**
        ``max_frame_gap`` frames of each other -- both conditions together,
        because either alone also matches two genuinely different plates.

        Which spelling survives is decided by evidence, not arrival order:
        readings are ranked valid-format first, then by how many frames voted
        for them, then by OCR confidence. Confidence alone is a poor judge at
        one-character granularity -- in the demo video the *wrong* spelling
        held the higher score (0.919 against 0.913) while the correct one had
        the majority of frames.

        Args:
            best_by_key: The accumulator built by :meth:`_merge_frame_results`.
            max_frame_gap: Largest frame-index distance at which two readings
                may still be considered simultaneous. Non-positive disables
                merging (an unknown frame rate must not cause false merges).

        Returns:
            The surviving sightings as ``(entry, frame_index)`` pairs, in
            ranking order.
        """

        def rank(item: tuple[DetectionResult, int, int]) -> tuple[int, int, float]:
            entry, _, seen = item
            recognition = entry.recognition
            valid = 1 if recognition is not None and recognition.is_valid_format else 0
            confidence = recognition.confidence if recognition is not None else 0.0
            return (valid, seen, confidence)

        ranked = sorted(best_by_key.values(), key=rank, reverse=True)
        winners: list[tuple[DetectionResult, int]] = []
        winner_texts: list[tuple[str, int]] = []

        for entry, frame_index, _seen in ranked:
            text = entry.recognition.text if entry.recognition is not None else ""
            absorbed = max_frame_gap > 0 and any(
                abs(frame_index - winner_frame) <= max_frame_gap
                and _is_fuzzy_duplicate_plate(text, winner_text)
                for winner_text, winner_frame in winner_texts
            )
            if absorbed:
                continue
            winners.append((entry, frame_index))
            winner_texts.append((text, frame_index))
        return winners

    @staticmethod
    def _progress(frame_index: int, total_frames: int) -> float:
        """Compute a job's completion fraction.

        Args:
            frame_index: Index of the frame just read.
            total_frames: Total frames reported by the container, or ``0`` when
                unknown -- some containers do not carry a reliable count.

        Returns:
            A fraction in ``[0.0, 1.0]``. When the total is unknown the value
            stays just below completion, because reporting 1.0 before the job
            has finished would make the client stop polling and miss the
            result.
        """
        if total_frames <= 0:
            return 0.99
        return min(0.99, frame_index / total_frames)

    @staticmethod
    def _is_cancelled(db: Session, job: DetectionJob) -> bool:
        """Return whether the job was cancelled while it was running.

        Re-read rather than trusted from the in-memory object: a cancellation
        arrives on a different session and this one would otherwise never
        observe it.

        Args:
            db: The background task's session.
            job: The job being processed.

        Returns:
            ``True`` if the stored status is ``cancelled``.
        """
        db.refresh(job, attribute_names=["status"])
        return job.status == JobStatus.CANCELLED.value

    # -- Jobs -------------------------------------------------------------

    def get_job(self, db: Session, job_id: str) -> DetectionJobResponse:
        """Return the current state of a job.

        Args:
            db: Session for this request.
            job_id: Identifier handed to the client when the job was created.

        Returns:
            The job's response model, including progress and detection count.

        Raises:
            NotFoundError: If no such job exists.
        """
        job = db.get(DetectionJob, job_id)
        if job is None:
            raise NotFoundError.for_resource("job", job_id)
        return to_job_response(job, self._storage)

    def _create_job(
        self,
        db: Session,
        *,
        input_type: InputType,
        source_path: str | None,
        status: JobStatus = JobStatus.PROCESSING,
    ) -> DetectionJob:
        """Insert a job row and flush so its generated id is available.

        Args:
            db: Session for this unit of work.
            input_type: Which input produced the job.
            source_path: Stored path of the source file, relative to the
                storage root, or ``None`` for a webcam session.
            status: Initial lifecycle state.

        Returns:
            The persisted and committed job.
        """
        job = DetectionJob(
            input_type=input_type.value,
            status=status.value,
            progress=0.0,
            source_path=source_path,
        )
        db.add(job)
        # Commit, not flush. This used to flush and keep the transaction open,
        # reasoning that "a later failure should roll the whole detection back
        # rather than leave a job with no results". That reasoning produced the
        # opposite of what it wanted: :meth:`_fail_job` rolls back *before*
        # writing the failure record, so the uncommitted job row went with it,
        # ``db.get`` returned ``None``, and a failed image upload left **zero
        # rows** -- the failure became invisible to the usage figures instead
        # of being recorded.
        #
        # A failed job row is not "a job with no results"; it *is* the record of
        # the failure, and it is what the run deserves to leave behind. The
        # detection rows are still written afterwards and are still rolled back
        # on failure, so the guarantee that actually mattered is untouched.
        #
        # ``create_video_job`` has always committed here, which is why the video
        # path recorded its failures correctly while the image and webcam paths
        # did not. This makes all three consistent.
        db.commit()
        return job

    def _resume_or_create_webcam_job(self, db: Session, job_id: str | None) -> DetectionJob:
        """Find the webcam session a frame belongs to, or start a new one.

        An unknown or finished identifier starts a fresh session rather than
        raising: a browser that reloads mid-session, or one resuming after the
        server restarted, should keep working instead of showing an error for
        something the user did not do.

        Args:
            db: Session for this request.
            job_id: Identifier supplied by the client, if any.

        Returns:
            The job the frame's detections belong to.
        """
        if job_id:
            existing = db.get(DetectionJob, job_id)
            if (
                existing is not None
                and existing.input_type == InputType.WEBCAM.value
                and not existing.is_finished
            ):
                return existing
            logger.debug(
                "webcam session not reusable, starting a new one",
                extra={"requested_job_id": job_id},
            )
        return self._create_job(db, input_type=InputType.WEBCAM, source_path=None)

    @staticmethod
    def _finish_job(job: DetectionJob, *, status: JobStatus) -> None:
        """Move a job into a terminal state.

        Args:
            job: The job to finish.
            status: The terminal state to record.
        """
        job.status = status.value
        job.progress = 1.0
        job.completed_at = utcnow()

    def _fail_job(self, db: Session, job: DetectionJob, error: Exception) -> None:
        """Record a failure on a job without hiding the original exception.

        The session is rolled back first: whatever partial writes the failed
        attempt made must not survive, and the failure record itself has to be
        written in a clean transaction or it would be rolled back along with
        them.

        Args:
            db: Session for this unit of work.
            job: The job that failed.
            error: The exception that caused it. Its text goes into
                ``error_message``, which is never returned to a user.
        """
        job_id = job.id
        db.rollback()
        try:
            fresh = db.get(DetectionJob, job_id)
            if fresh is not None:
                fresh.status = JobStatus.FAILED.value
                fresh.error_message = f"{type(error).__name__}: {error}"
                fresh.completed_at = utcnow()
                db.commit()
        except Exception:  # noqa: BLE001 -- never mask the original failure
            logger.exception("could not record job failure", extra={"job_id": job_id})
            db.rollback()

    def _mark_job_failed(self, db: Session, job_id: str, error: Exception) -> None:
        """Record a background job's failure from a clean session state.

        Args:
            db: Session owned by the background task.
            job_id: Identifier of the failed job.
            error: The exception that ended it.
        """
        try:
            job = db.get(DetectionJob, job_id)
            if job is not None:
                job.status = JobStatus.FAILED.value
                job.error_message = f"{type(error).__name__}: {error}"
                job.completed_at = utcnow()
                db.commit()
        except Exception:  # noqa: BLE001
            logger.exception("could not record job failure", extra={"job_id": job_id})
            db.rollback()

    # -- Pipeline and persistence -----------------------------------------

    def _run_pipeline(
        self, image: ImageArray, *, job_id: str, read_text: bool = True
    ) -> PipelineResult:
        """Invoke the pipeline and translate its exceptions to API errors.

        This is the NFR-M1 translation point. ``ALPRError`` carries an English
        developer message and knows nothing about HTTP; letting it propagate
        would either leak that text or produce an unhandled 500 with a
        traceback. It is converted here into a
        :class:`~backend.core.exceptions.ProcessingError`, which carries a
        Vietnamese user message and keeps the technical text for the log.

        Args:
            image: The decoded source image or frame.
            job_id: Recorded in the error context so a failure can be traced.

        Returns:
            The pipeline's result.

        Raises:
            ProcessingError: If the pipeline raised, for any reason.
        """
        try:
            return self._pipeline.process(image, read_text=read_text)
        except ALPRError as error:
            raise ProcessingError.from_pipeline_error(
                error,
                stage="recognition",
                context={"job_id": job_id, "engine": self._pipeline.name},
            ) from error
        except Exception as error:
            # A pipeline that raises something outside its own hierarchy is a
            # bug, but it must still not reach the user as a traceback.
            raise ProcessingError.from_pipeline_error(
                error,
                stage="recognition",
                context={"job_id": job_id, "engine": self._pipeline.name, "unexpected": True},
            ) from error

    @staticmethod
    def _decode_image(data: bytes) -> ImageArray:
        """Decode uploaded bytes into a BGR image array.

        Args:
            data: The raw file contents.

        Returns:
            The decoded image as a BGR ``uint8`` array.

        Raises:
            ValidationError: If the bytes cannot be decoded. This is separate
                from the magic-byte check: a file can carry a valid JPEG header
                and still be truncated or corrupt beyond it.
        """
        buffer = np.frombuffer(data, dtype=np.uint8)
        image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
        if image is None or image.size == 0:
            raise ValidationError(
                "cv2.imdecode returned no image for the uploaded bytes",
                user_message=(
                    "Không thể đọc được nội dung ảnh. "
                    "Tệp có thể bị hỏng hoặc không phải là ảnh hợp lệ."
                ),
                context={"size_bytes": len(data)},
            )
        return image

    def _persist_results(
        self,
        db: Session,
        *,
        job: DetectionJob,
        result: PipelineResult,
        input_type: InputType,
        image_path: str | None,
        video_times: list[float | None] | None = None,
    ) -> list[DetectionHistory]:
        """Write one history row per detected plate.

        Every detection is stored, including those OCR could not read. A plate
        that was located but not recognised is a real, reportable outcome;
        dropping such rows would remove exactly the failures the evaluation
        chapter counts and make recognition accuracy look perfect by
        construction.

        Args:
            db: Session for this unit of work. Flushed, not committed -- the
                caller owns the transaction boundary.
            job: The job these detections belong to.
            result: The pipeline's output.
            input_type: Denormalised onto each row so history filtering needs
                no join.
            image_path: Stored path of the source image, or ``None`` for webcam
                frames, which are not kept.

        Returns:
            The persisted rows, in pipeline order.
        """
        detected_at = utcnow()
        rows: list[DetectionHistory] = []

        for index, entry in enumerate(result.results):
            bbox = entry.detection.bbox
            recognition = entry.recognition

            crop_path: str | None = None
            if entry.plate_image is not None and entry.plate_image.size:
                crop_path = self._storage.save_plate_crop(
                    entry.plate_image, job_id=job.id, index=index
                ).relative_path

            row = DetectionHistory(
                # Empty text is stored as NULL, not as "", so that "no reading"
                # is one value everywhere instead of two that queries must both
                # remember to handle.
                plate_number=(recognition.text or None) if recognition else None,
                raw_ocr_text=(recognition.raw_text or None) if recognition else None,
                confidence=entry.detection.confidence,
                ocr_confidence=recognition.confidence if recognition else None,
                input_type=input_type.value,
                image_path=image_path,
                plate_image_path=crop_path,
                bbox_x=bbox.x,
                bbox_y=bbox.y,
                bbox_w=bbox.width,
                bbox_h=bbox.height,
                is_valid_format=bool(recognition.is_valid_format) if recognition else False,
                plate_line_count=recognition.line_count if recognition else None,
                # Only a 3- or 4-character upper line is a legal Vietnamese
                # reading, and the column's CHECK says so. Anything else came
                # from a mis-segmented crop rather than from the plate, so it is
                # stored as "not recorded" instead of being pushed at the
                # constraint -- an unusable observation must not be able to fail
                # the write for a plate that was otherwise read fine.
                upper_char_count=(
                    recognition.upper_char_count
                    if recognition and recognition.upper_char_count in (3, 4)
                    else None
                ),
                # Vehicle-class attributes. Stored as NULL rather than "" when
                # absent, matching how the text columns above treat "nothing
                # read": one value for "not recorded", not two.
                plate_kind=(recognition.kind or None) if recognition else None,
                plate_color=entry.plate_color or None,
                plate_color_confidence=entry.plate_color_confidence or None,
                # Positional, matching this entry's index in ``result.results``.
                # Absent for images and realtime frames, which have no timeline.
                video_time_seconds=(
                    video_times[index]
                    if video_times is not None and index < len(video_times)
                    else None
                ),
                processing_time=entry.processing_time,
                detected_time=detected_at,
                source_job_id=job.id,
            )
            db.add(row)
            rows.append(row)

        db.flush()
        return rows

    # -- Maintenance ------------------------------------------------------

    def warmup(self) -> None:
        """Prime the pipeline if it supports it.

        Called once at start-up so the first user request does not pay the
        one-off cost of paging in weights and compiling kernels (NFR-P1).
        Optional on the protocol, so a pipeline without a warm-up cost need not
        implement it.
        """
        warmup = getattr(self._pipeline, "warmup", None)
        if callable(warmup):
            warmup()
