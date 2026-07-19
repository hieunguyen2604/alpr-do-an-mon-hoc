"""End-to-end ALPR pipeline: detect, crop, recognise, normalise.

This module wires the three stages together and does nothing else. It owns no
model, imports no ML runtime at module level, and knows only the abstractions
declared in :mod:`ai.inference.interfaces`.

Dependency injection (NFR-M5)
-----------------------------
:class:`ALPRPipeline` receives its detector, recogniser and normalizer as
constructor arguments and never builds one itself. That is what makes the OCR
engine replaceable without touching this file, the service layer or the
routers: swapping PaddleOCR for EasyOCR means passing a different
:class:`~ai.inference.interfaces.BaseRecognizer` at start-up.

:func:`build_default_pipeline` exists for the callers that just want the
project's standard combination. It is a *convenience wrapper around* the class,
not a part of it -- the class has no knowledge of the factory, which is why a
test can construct the pipeline from three fakes with no ML runtime installed.

Latency accounting (NFR-P1)
---------------------------
Every stage is timed separately and the breakdown is stored on the returned
:class:`~ai.inference.types.PipelineResult`. Phase 7 needs to attribute the
end-to-end latency budget to a specific stage; a single total would only say
that the pipeline is slow, not which part to optimise.

Failure policy
--------------
An image containing no plate returns an empty
:class:`~ai.inference.types.PipelineResult` -- it is a normal outcome, never an
exception. A recognition failure on *one* plate is contained: that plate comes
back with ``recognition=None`` and the remaining plates in the same image are
still processed, because losing a whole frame to one unreadable crop would
throw away good data.

Architectural constraint (NFR-M1): this module imports NumPy, the standard
library and its own package only -- never the web framework (FastAPI) or its
schema library (Pydantic).
"""

from __future__ import annotations

import logging
import time
from typing import Final

import numpy as np

from ai.inference.config import InferenceConfig
from ai.inference.exceptions import ALPRError, InvalidImageError
from ai.inference.interfaces import BaseDetector, BaseNormalizer, BaseRecognizer
from ai.inference.types import (
    BoundingBox,
    DetectionResult,
    ImageArray,
    PipelineResult,
    PlateDetection,
    PlateRecognition,
)

__all__ = ["STAGE_NAMES", "ALPRPipeline", "build_default_pipeline"]

_LOGGER = logging.getLogger(__name__)

STAGE_NAMES: Final[tuple[str, ...]] = ("detect", "crop", "ocr", "normalize", "total")
"""Keys always present in :attr:`~ai.inference.types.PipelineResult.stage_times`.

Fixed and exhaustive so that a benchmark can build a table without having to
discover the keys at runtime, and so that a stage which never ran reports
``0.0`` rather than being absent.
"""


class ALPRPipeline:
    """Run detection, recognition and normalisation over one image.

    The pipeline is a *composition* object: it holds no model and performs no
    inference of its own. Its entire responsibility is ordering the stages,
    cropping between them, timing each one and containing per-plate failures.

    Thread-safety follows the injected components. The pipeline itself keeps no
    mutable state between calls, but the reference recogniser is not
    thread-safe, so give each worker thread its own pipeline or serialise
    access.

    Example:
        Wire the standard combination explicitly::

            config = InferenceConfig.from_env()
            pipeline = ALPRPipeline(
                detector=YoloPlateDetector(config),
                recognizer=PaddleOcrRecognizer(config),
                normalizer=VietnamesePlateNormalizer(),
                config=config,
            )
            pipeline.warmup()
            result = pipeline.process(cv2.imread("car.jpg"))

    Args:
        detector: Locates the plates. Required.
        recognizer: Reads the characters off each crop. Required.
        normalizer: Corrects and validates the raw OCR string. Required.
        config: Runtime settings. Only
            :attr:`~ai.inference.config.InferenceConfig.two_line_aspect_ratio_threshold`
            is read here, to report a line count for plates the recogniser did
            not report one for. A default instance is built when omitted.

    Raises:
        TypeError: If any of the three stages is ``None``. Failing at
            construction is deliberate: a pipeline missing a stage cannot
            produce a meaningful result, and discovering that on the first
            request would be far harder to diagnose.
    """

    def __init__(
        self,
        detector: BaseDetector,
        recognizer: BaseRecognizer,
        normalizer: BaseNormalizer,
        config: InferenceConfig | None = None,
    ) -> None:
        """Store the injected stages after checking that all three are present."""
        if detector is None:
            raise TypeError("ALPRPipeline requires a detector; got None")
        if recognizer is None:
            raise TypeError("ALPRPipeline requires a recognizer; got None")
        if normalizer is None:
            raise TypeError("ALPRPipeline requires a normalizer; got None")

        self._detector = detector
        self._recognizer = recognizer
        self._normalizer = normalizer
        self._config = config if config is not None else InferenceConfig()

        _LOGGER.info(
            "ALPR pipeline assembled",
            extra={
                "detector": self._safe_name(detector),
                "recognizer": self._safe_name(recognizer),
                "normalizer": type(normalizer).__name__,
            },
        )

    # ----------------------------------------------------------------- #
    # Identity
    # ----------------------------------------------------------------- #
    @property
    def name(self) -> str:
        """Return a combined engine identifier, e.g. ``"yolo:best.pt+paddleocr-..."``.

        Both halves are included because a benchmark number is only
        reproducible if it names the detector *and* the recogniser that
        produced it.
        """
        return (
            f"{self._safe_name(self._detector)}+{self._safe_name(self._recognizer)}"
        )

    @property
    def is_ready(self) -> bool:
        """Return whether this pipeline can produce genuine results.

        Always ``True`` for this class: dependency injection means the detector
        and the recogniser were constructed -- and their weights therefore
        loaded or verified -- before the pipeline existed. A missing weights
        file fails inside the detector's constructor, so an ``ALPRPipeline``
        instance cannot exist in a not-ready state.

        The property exists so that the real pipeline and the API layer's
        placeholder are interchangeable, and so ``/health`` can distinguish
        them.
        """
        return True

    @property
    def detector(self) -> BaseDetector:
        """Return the injected detector."""
        return self._detector

    @property
    def recognizer(self) -> BaseRecognizer:
        """Return the injected recogniser."""
        return self._recognizer

    @property
    def normalizer(self) -> BaseNormalizer:
        """Return the injected normalizer."""
        return self._normalizer

    @property
    def config(self) -> InferenceConfig:
        """Return the configuration this pipeline was built with."""
        return self._config

    # ----------------------------------------------------------------- #
    # Lifecycle
    # ----------------------------------------------------------------- #
    def warmup(self) -> None:
        """Prime both models so the first real request is not the slow one.

        Delegates to the detector's and the recogniser's own ``warmup``. A
        failure in either is logged and swallowed: a warm-up is an
        optimisation, and refusing to start the service because a synthetic
        blank image produced no text would be the wrong trade-off. A genuine
        model problem surfaces on the first real call, where it belongs.
        """
        started = time.perf_counter()
        for label, component in (
            ("detector", self._detector),
            ("recognizer", self._recognizer),
        ):
            try:
                component.warmup()
            except Exception as error:  # noqa: BLE001 - warm-up must not block start-up
                _LOGGER.warning(
                    "Pipeline warm-up stage failed, continuing without it",
                    extra={
                        "stage": label,
                        "engine": self._safe_name(component),
                        "error": f"{type(error).__name__}: {error}",
                    },
                )

        _LOGGER.info(
            "ALPR pipeline warmed up",
            extra={
                "pipeline": self.name,
                "elapsed_ms": round((time.perf_counter() - started) * 1000.0, 2),
            },
        )

    # ----------------------------------------------------------------- #
    # Main entry point
    # ----------------------------------------------------------------- #
    def process(self, image: ImageArray) -> PipelineResult:
        """Find and read every license plate in one image or video frame.

        Stages, in order: detect the plates, crop each one, read it, then
        correct and validate the string. Each stage is timed separately and the
        totals are reported in
        :attr:`~ai.inference.types.PipelineResult.stage_times`.

        Args:
            image: Source image as a BGR ``uint8`` array of shape
                ``(height, width, 3)`` -- what ``cv2.imread`` returns.

        Returns:
            A :class:`~ai.inference.types.PipelineResult` with one
            :class:`~ai.inference.types.DetectionResult` per plate found, in
            detector order (descending confidence). An image containing no
            plate yields an empty result -- a normal outcome, never an error.

            A plate whose recognition failed is still present, with
            ``recognition=None``: the detection is real information and
            dropping it would hide the failure from the statistics.

        Raises:
            InvalidImageError: If the input is not a usable image.
            DetectionError: If the detection stage itself fails. Detection is
                not contained the way recognition is -- if the detector is
                broken there is nothing to report about this image.
        """
        self._validate_image(image)
        height, width = int(image.shape[0]), int(image.shape[1])

        total_started = time.perf_counter()
        stage_times: dict[str, float] = {name: 0.0 for name in STAGE_NAMES}

        detect_started = time.perf_counter()
        detections = self._detector.detect(image)
        stage_times["detect"] = time.perf_counter() - detect_started

        results: list[DetectionResult] = []
        for index, detection in enumerate(detections):
            result, elapsed = self._process_one_plate(image, detection, index)
            for stage, seconds in elapsed.items():
                stage_times[stage] += seconds
            results.append(result)

        stage_times["total"] = time.perf_counter() - total_started

        pipeline_result = PipelineResult(
            results=results,
            total_time=stage_times["total"],
            image_width=width,
            image_height=height,
            stage_times=stage_times,
        )

        _LOGGER.info(
            "Pipeline run finished",
            extra={
                "pipeline": self.name,
                "image_size": f"{width}x{height}",
                "plates_detected": pipeline_result.plate_count,
                "plates_recognized": pipeline_result.recognized_count,
                "detect_ms": round(stage_times["detect"] * 1000.0, 2),
                "crop_ms": round(stage_times["crop"] * 1000.0, 2),
                "ocr_ms": round(stage_times["ocr"] * 1000.0, 2),
                "normalize_ms": round(stage_times["normalize"] * 1000.0, 2),
                "total_ms": round(stage_times["total"] * 1000.0, 2),
            },
        )
        return pipeline_result

    # ----------------------------------------------------------------- #
    # Internals
    # ----------------------------------------------------------------- #
    def _process_one_plate(
        self, image: ImageArray, detection: PlateDetection, index: int
    ) -> tuple[DetectionResult, dict[str, float]]:
        """Crop, recognise and normalise a single detected plate.

        Args:
            image: The full source image.
            detection: One box produced by the detector.
            index: Position of this plate in the detector's output, used only
                in log records so a failure can be tied to a specific box.

        Returns:
            A ``(result, elapsed)`` pair. ``elapsed`` maps the ``crop``, ``ocr``
            and ``normalize`` stage names to the seconds this plate spent in
            each, for accumulation by :meth:`process`.
        """
        elapsed = {"crop": 0.0, "ocr": 0.0, "normalize": 0.0}

        crop_started = time.perf_counter()
        plate_image = self._crop(image, detection.bbox)
        elapsed["crop"] = time.perf_counter() - crop_started

        recognition: PlateRecognition | None = None
        if plate_image is not None:
            ocr_started = time.perf_counter()
            recognition = self._recognize(plate_image, detection, index)
            elapsed["ocr"] = time.perf_counter() - ocr_started

            if recognition is not None:
                normalize_started = time.perf_counter()
                recognition = self._normalize(recognition, detection, index)
                elapsed["normalize"] = time.perf_counter() - normalize_started

        return (
            DetectionResult(
                detection=detection,
                recognition=recognition,
                plate_image=plate_image,
                processing_time=sum(elapsed.values()),
            ),
            elapsed,
        )

    @staticmethod
    def _crop(image: ImageArray, bbox: BoundingBox) -> ImageArray | None:
        """Cut the plate region out of the source image.

        The detector contract already promises clamped boxes, but the box is
        re-clamped here anyway: a crop is the one place where an off-by-one
        produces a silently empty array instead of an error, and a third-party
        detector plugged in through :class:`~ai.inference.interfaces.BaseDetector`
        may not honour the contract as carefully.

        Args:
            image: The full source image.
            bbox: Where the plate sits.

        Returns:
            A copy of the plate region, or ``None`` if the box lies outside the
            image and the crop would be empty. A copy rather than a view,
            because the crop outlives the caller's frame in video mode and a
            view would pin the whole frame in memory.
        """
        height, width = image.shape[0], image.shape[1]
        x1 = max(0, min(bbox.x, width))
        y1 = max(0, min(bbox.y, height))
        x2 = max(x1, min(bbox.x2, width))
        y2 = max(y1, min(bbox.y2, height))

        if x2 <= x1 or y2 <= y1:
            _LOGGER.warning(
                "Skipping a plate whose box produced an empty crop",
                extra={
                    "bbox": bbox.to_xyxy(),
                    "image_size": f"{width}x{height}",
                },
            )
            return None

        crop: ImageArray = image[y1:y2, x1:x2].copy()
        return crop

    def _recognize(
        self, plate_image: ImageArray, detection: PlateDetection, index: int
    ) -> PlateRecognition | None:
        """Read one crop, containing any failure to this plate alone.

        Args:
            plate_image: The cropped plate.
            detection: The detection this crop came from, for the log record.
            index: Position of the plate in the detector's output.

        Returns:
            The recognition, or ``None`` when the OCR stage failed. Returning
            ``None`` rather than propagating keeps one unreadable crop from
            costing the whole frame; the detection itself is still reported.
        """
        try:
            return self._recognizer.recognize(plate_image)
        except ALPRError as error:
            _LOGGER.warning(
                "OCR failed for one plate, keeping the detection without text",
                extra={
                    "plate_index": index,
                    "bbox": detection.bbox.to_xyxy(),
                    "engine": self._safe_name(self._recognizer),
                    "error": f"{type(error).__name__}: {error}",
                },
            )
            return None
        except Exception as error:  # noqa: BLE001 - a third-party engine may raise anything
            _LOGGER.exception(
                "Unexpected OCR error for one plate, keeping the detection "
                "without text",
                extra={
                    "plate_index": index,
                    "bbox": detection.bbox.to_xyxy(),
                    "engine": self._safe_name(self._recognizer),
                    "error": f"{type(error).__name__}: {error}",
                },
            )
            return None

    def _normalize(
        self,
        recognition: PlateRecognition,
        detection: PlateDetection,
        index: int,
    ) -> PlateRecognition:
        """Correct and validate the raw string read from one plate.

        The recogniser deliberately returns ``is_valid_format=False`` for every
        crop -- judging the format is not its job. This step is what fills that
        field in, and what turns an approximate character string into a plate
        number.

        ``line_count`` is forwarded when the normalizer accepts it. That is an
        optional capability, not part of
        :class:`~ai.inference.interfaces.BaseNormalizer`, so it is probed
        rather than assumed: an engine implementing only the interface method
        still works, just without the ambiguity resolution.

        Args:
            recognition: What the recogniser returned.
            detection: The detection it came from, for the log record.
            index: Position of the plate in the detector's output.

        Returns:
            A new :class:`~ai.inference.types.PlateRecognition` carrying the
            normalised text and the validity flag. ``raw_text`` is preserved
            unchanged -- comparing it against ``text`` is the only way to
            measure what this stage contributes.
        """
        raw_source = recognition.text or recognition.raw_text

        try:
            detailed = getattr(self._normalizer, "normalize_detailed", None)
            if callable(detailed):
                outcome = detailed(raw_source, line_count=recognition.line_count)
                text, is_valid = outcome.text, outcome.is_valid_format
            else:
                text, is_valid = self._normalizer.normalize(raw_source)
        except Exception as error:  # noqa: BLE001 - never lose a plate to a rule bug
            _LOGGER.exception(
                "Normalisation failed, keeping the raw OCR string",
                extra={
                    "plate_index": index,
                    "bbox": detection.bbox.to_xyxy(),
                    "raw_text": recognition.raw_text,
                    "error": f"{type(error).__name__}: {error}",
                },
            )
            return recognition

        return PlateRecognition(
            text=text,
            raw_text=recognition.raw_text,
            confidence=recognition.confidence,
            line_count=recognition.line_count,
            is_valid_format=is_valid,
        )

    @staticmethod
    def _safe_name(component: object) -> str:
        """Return a component's ``name``, falling back to its class name.

        Args:
            component: Any injected stage.

        Returns:
            The engine identifier. A component whose ``name`` property raises
            must not be able to break a log record, so the class name is used
            instead.
        """
        try:
            name = getattr(component, "name", None)
        except Exception:  # noqa: BLE001 - logging must never raise
            return type(component).__name__
        return str(name) if name else type(component).__name__

    @staticmethod
    def _validate_image(image: ImageArray) -> None:
        """Reject anything that is not a usable image before any stage runs.

        Args:
            image: The candidate input.

        Raises:
            InvalidImageError: If the input is ``None``, not a NumPy array, has
                the wrong rank, or has a zero-sized side.
        """
        if image is None:
            raise InvalidImageError("Input image is None; nothing to process.")
        if not isinstance(image, np.ndarray):
            raise InvalidImageError(
                "Input image must be a numpy.ndarray in OpenCV BGR format, got "
                f"{type(image).__name__}."
            )
        if image.size == 0:
            raise InvalidImageError(
                f"Input image is empty (shape={image.shape}); it was most likely "
                "produced by a failed decode."
            )
        if image.ndim not in (2, 3):
            raise InvalidImageError(
                "Input image must have 2 dimensions (grayscale) or 3 "
                f"(height, width, channels), got {image.ndim} (shape={image.shape})."
            )
        if image.shape[0] <= 0 or image.shape[1] <= 0:
            raise InvalidImageError(
                f"Input image has a zero-sized axis (shape={image.shape})."
            )


def build_default_pipeline(config: InferenceConfig | None = None) -> ALPRPipeline:
    """Assemble the project's standard pipeline.

    This is a convenience factory for callers that want the reference
    combination -- YOLO11 for detection, PP-OCRv5 mobile for recognition, the
    positional Vietnamese rules for normalisation -- without naming three
    classes. :class:`ALPRPipeline` does not depend on it: the class receives its
    stages injected, so a caller wanting a different recogniser constructs the
    pipeline directly and never calls this function.

    The concrete engines are imported inside the function body rather than at
    module level, so that importing :mod:`ai.inference.pipeline` -- and
    unit-testing the pipeline with fakes -- does not require Ultralytics or
    PaddleOCR to be installed.

    Args:
        config: Runtime settings shared by every stage. Built from the
            environment with
            :meth:`~ai.inference.config.InferenceConfig.from_env` when omitted.

    Returns:
        A ready-to-use pipeline. The models are loaded but not warmed up; call
        :meth:`ALPRPipeline.warmup` to move the first-inference cost off the
        first request.

    Raises:
        ModelLoadError: If the detector weights are missing or unreadable.
    """
    from ai.inference.detector import YoloPlateDetector
    from ai.inference.normalizer import VietnamesePlateNormalizer
    from ai.inference.recognizer import PaddleOcrRecognizer

    resolved = config if config is not None else InferenceConfig.from_env()
    return ALPRPipeline(
        detector=YoloPlateDetector(resolved),
        recognizer=PaddleOcrRecognizer(resolved),
        normalizer=VietnamesePlateNormalizer(),
        config=resolved,
    )
