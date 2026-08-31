"""Orchestration of the recognition pipeline, storage and persistence."""

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
"""Stateless formatter for display rendering of stored plates."""

_PROGRESS_COMMIT_EVERY: Final[int] = 10
"""Processed frame interval between progress commits."""

_MIN_UNCLASSIFIED_TEXT_LEN: Final[int] = 7
"""Minimum text length threshold for unclassified video plate persistence."""

_VARIANT_MERGE_WINDOW_SECONDS: Final[float] = 3.5
"""Maximum time gap in seconds to merge plate reading variants."""


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
    """Return whether two plate strings describe the same physical vehicle."""
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


# The pipeline contract


@runtime_checkable
class PlatePipeline(Protocol):
    """What this service requires of a recognition pipeline."""

    @property
    def name(self) -> str:
        """Return a short engine identifier, e.g. ``"yolo11n+paddleocr"``."""
        ...

    @property
    def is_ready(self) -> bool:
        """Return whether the pipeline can produce genuine results."""
        ...

    def process(self, image: ImageArray, *, read_text: bool = True) -> PipelineResult:
        """Find and read every license plate in one image or video frame."""
        ...


class StubPipeline:
    """A placeholder pipeline that fabricates structurally valid results."""

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
        """Fabricate one detection positioned inside the given image."""
        started = time.perf_counter()
        height, width = int(image.shape[0]), int(image.shape[1])

        # Realistic single-line plate box clamped to positive dimensions
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
        # Perturb raw text to exercise OCR correction downstream
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
    """The pipeline that is installed when the real one could not be built."""

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
        """Refuse the request."""
        raise ALPRError(f"Recognition pipeline is not available: {self._reason}")

    def warmup(self) -> None:
        """Do nothing; there is no model to prime."""
        return None


# Mapping helpers


def to_job_response(job: DetectionJob, storage: StorageService) -> DetectionJobResponse:
    """Map a job row to its API representation."""
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
    """Render a stored plate number with the separators the real plate carries."""
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
    """Map a persisted detection row to the per-plate response model."""
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
    """Map a pipeline result to the response model **without** storing it."""
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


# Service


class DetectionService:
    """Runs detections and records them."""

    def __init__(
        self,
        *,
        pipeline: PlatePipeline,
        storage: StorageService,
        settings: Settings,
    ) -> None:
        """Create the service."""
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
        """Detect and recognise every plate in an uploaded image."""
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
        """Detect plates in a single webcam frame."""
        # Validated as an image subject to magic-byte and size rules (NFR-S1, NFR-S3)
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

            # Advance processed frames counter
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

    def create_video_job(
        self,
        db: Session,
        *,
        data: bytes,
        original_filename: str | None = None,
    ) -> DetectionJob:
        """Accept a video upload and queue it, without processing it."""
        stored = self._storage.save_upload(
            data, kind=MediaKind.VIDEO, original_filename=original_filename
        )
        # _create_job commits so job is visible to background worker and pollers
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
        """Process a queued video to completion."""
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
        """Run the sampling loop over one video."""
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

        # Capture dimensions must be queried before capture.release()
        frame_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        frame_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        # Capture FPS for frame-to-timestamp calculation
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

        # Unknown frame rate disables variant merge window
        max_frame_gap = int(_VARIANT_MERGE_WINDOW_SECONDS * fps) if fps > 0 else 0
        sightings = self._collapse_variants(best_by_key, max_frame_gap=max_frame_gap)
        merged = [entry for entry, _ in sightings]
        # Plate timestamp in seconds (None if frame rate is unknown)
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
        # Video re-encoding with annotated boxes is intentionally kept out of
        # scope on CPU to preserve real-time throughput. The dashboard exposes
        # the per-plate crops that the pipeline persisted for inspection.
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
        """Fold one frame's detections into the running de-duplicated set."""
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
        """Merge single-character OCR variants of one physical plate."""

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
        """Compute a job's completion fraction."""
        if total_frames <= 0:
            return 0.99
        return min(0.99, frame_index / total_frames)

    @staticmethod
    def _is_cancelled(db: Session, job: DetectionJob) -> bool:
        """Return whether the job was cancelled while it was running."""
        db.refresh(job, attribute_names=["status"])
        return job.status == JobStatus.CANCELLED.value

    # -- Jobs -------------------------------------------------------------

    def get_job(self, db: Session, job_id: str) -> DetectionJobResponse:
        """Return the current state of a job."""
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
        """Insert a job row and flush so its generated id is available."""
        job = DetectionJob(
            input_type=input_type.value,
            status=status.value,
            progress=0.0,
            source_path=source_path,
        )
        db.add(job)
        # Commit, not flush: _fail_job rolls back BEFORE writing the failure record,
        # so an uncommitted job row would vanish with it and a failed upload would
        # leave zero rows. A failed job row IS the record of the failure.
        db.commit()
        return job

    def _resume_or_create_webcam_job(self, db: Session, job_id: str | None) -> DetectionJob:
        """Find the webcam session a frame belongs to, or start a new one."""
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
        """Move a job into a terminal state."""
        job.status = status.value
        job.progress = 1.0
        job.completed_at = utcnow()

    def _fail_job(self, db: Session, job: DetectionJob, error: Exception) -> None:
        """Record a failure on a job without hiding the original exception."""
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
        """Record a background job's failure from a clean session state."""
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
        """Invoke the pipeline and translate its exceptions to API errors."""
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
        """Decode uploaded bytes into a BGR image array."""
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
        """Write one history row per detected plate."""
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
                # Empty text stored as NULL to unify "no reading" representation
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
                # Store upper char count only for 3 or 4 valid chars per CHECK constraint
                upper_char_count=(
                    recognition.upper_char_count
                    if recognition and recognition.upper_char_count in (3, 4)
                    else None
                ),
                # Vehicle-class attributes (NULL when absent)
                plate_kind=(recognition.kind or None) if recognition else None,
                plate_color=entry.plate_color or None,
                plate_color_confidence=entry.plate_color_confidence or None,
                # Positional timestamp matching entry index in results
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
        """Prime the pipeline if it supports it."""
        warmup = getattr(self._pipeline, "warmup", None)
        if callable(warmup):
            warmup()
