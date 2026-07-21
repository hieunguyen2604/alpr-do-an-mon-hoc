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
from ai.inference.plate_color import classify_plate_color
from ai.inference.two_line import UPPER_HALF_END_RATIO, split_two_line
from ai.inference.types import (
    BoundingBox,
    DetectionResult,
    ImageArray,
    PipelineResult,
    PlateDetection,
    PlateRecognition,
)

__all__ = [
    "STAGE_NAMES",
    "ALPRPipeline",
    "build_default_pipeline",
    "should_rescue_two_line",
    "rescue_two_line_upper",
    "refine_kind_with_color",
    "RESCUE_UPPER_END_RATIOS",
]

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
        return f"{self._safe_name(self._detector)}+{self._safe_name(self._recognizer)}"

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

        # Colour is read from the crop, not the string, and answers a question no
        # rule over the characters can: a business vehicle's yellow plate and a
        # State vehicle's blue one carry the *same* layout as a private
        # vehicle's white one. Computed before normalisation because the family
        # classifier below uses it to break exactly that tie. Cheap (a histogram
        # over the centre of one small crop) and it never raises -- an unreadable
        # colour comes back as "unknown".
        color = classify_plate_color(plate_image) if plate_image is not None else None
        color_name = color.color.value if color is not None else ""

        recognition: PlateRecognition | None = None
        if plate_image is not None:
            ocr_started = time.perf_counter()
            recognition = self._recognize(plate_image, detection, index)
            elapsed["ocr"] = time.perf_counter() - ocr_started

            if recognition is not None:
                normalize_started = time.perf_counter()
                recognition = self._normalize(recognition, detection, index, color_name)
                elapsed["normalize"] = time.perf_counter() - normalize_started

                if should_rescue_two_line(recognition):
                    retry_started = time.perf_counter()
                    recognition = rescue_two_line_upper(
                        self._recognizer,
                        self._normalizer,
                        plate_image,
                        recognition,
                        context={
                            "plate_index": index,
                            "bbox": detection.bbox.to_xyxy(),
                        },
                        color=color_name,
                    )
                    elapsed["ocr"] += time.perf_counter() - retry_started

        return (
            DetectionResult(
                detection=detection,
                recognition=recognition,
                plate_image=plate_image,
                processing_time=sum(elapsed.values()),
                plate_color=color.color.value if color is not None else "",
                plate_color_confidence=round(color.confidence, 4) if color is not None else 0.0,
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
                "Unexpected OCR error for one plate, keeping the detection without text",
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
        plate_color: str = "",
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
        kind = ""
        display_text = ""

        try:
            detailed = getattr(self._normalizer, "normalize_detailed", None)
            if callable(detailed):
                outcome = detailed(raw_source, line_count=recognition.line_count)
                text, is_valid = outcome.text, outcome.is_valid_format
                # The family and the human-readable rendering are both already
                # computed inside the normalizer. Dropping them here -- as this
                # method used to -- is what made an army plate reach the user
                # labelled "wrong format" with nothing to explain why.
                kind = refine_kind_with_color(outcome, plate_color, recognition.line_count)
                display_text = _format_for_display(self._normalizer, text, recognition.line_count)
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
            kind=kind,
            display_text=display_text,
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
            raise InvalidImageError(f"Input image has a zero-sized axis (shape={image.shape}).")


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


# --------------------------------------------------------------------------- #
# Two-line rescue -- shared by the pipeline and the evaluation harness
# --------------------------------------------------------------------------- #
RESCUE_UPPER_END_RATIOS: Final[tuple[float, ...]] = (UPPER_HALF_END_RATIO, 0.55)
"""Upper-half cut ratios the rescue tries, in order, until one validates.

The first entry is the ratio the main strip is built with, so the cheap case --
the upper line sits where the geometry assumes -- is tried first and behaves
exactly as before.

The second exists because that assumption fails on tightly framed crops. The
cut at 5/12 lands *inside* the glyphs of the upper row when the plate fills its
bounding box, and an amputated row is not merely degraded: PP-OCR's text
detector fires on it not at all. Measured on ``demo/images/nhieu-bien-3.png``,
a 67x41 crop reading ``77-H5`` over ``4374``::

    cut at 0.4167 -> ''        (nothing detected)
    cut at 0.4500 -> ''
    cut at 0.5000 -> ''
    cut at 0.5500 -> '77-H5'   at 0.975 confidence

The transition is a cliff, not a slope, which is why one extra ratio well clear
of it recovers the case and a small nudge would not. 0.55 keeps a margin above
the 0.50 that still failed, and stays below the point where the lower row would
start intruding on a normally framed plate.

Every ratio here costs one OCR call, and only on crops that already failed
validation. Adding entries is therefore cheap in the common case and must still
be justified by measurement -- see ``docs/reports/15-two-line-rescue-ladder.json``.
"""


def should_rescue_two_line(recognition: PlateRecognition) -> bool:
    """Decide whether a two-line read is worth a second, narrower attempt.

    Args:
        recognition: The already-normalised result of the first attempt.

    Returns:
        ``True`` only for a two-line plate whose normalised text failed format
        validation while still carrying some text. A result that already
        validated is never retried, which is what makes the rescue structurally
        unable to regress a plate that was read correctly the first time.
    """
    return (
        recognition.line_count == 2
        and not recognition.is_valid_format
        and bool(recognition.raw_text)
    )


def rescue_two_line_upper(
    recognizer: BaseRecognizer,
    normalizer: BaseNormalizer,
    plate_image: ImageArray,
    recognition: PlateRecognition,
    context: dict[str, object] | None = None,
    color: str = "",
) -> PlateRecognition:
    """Re-read the upper half alone and prepend it to a failed two-line read.

    Why this exists
    ---------------
    A two-line crop is read by cutting it into overlapping halves, stacking them
    side by side and running OCR **once** on the resulting strip. That design is
    not incidental. Reading each half separately and joining the two strings
    scores 3.5% against the strip's 64.5% on a 200-plate sample, because the
    halves overlap on purpose and the overlap band then gets read twice,
    duplicating characters -- ``84G122593`` comes back as ``84-G124E009.01225.93``.
    Merging first is precisely what lets the text detector discard that band.

    The strip has one failure mode of its own. When the upper line sits low in a
    loosely-cropped plate, the detector finds a single text region -- the lower
    line -- and the province code and serial letter are lost outright.
    ``29E-015.66`` comes back as ``015.66``: five bare digits matching no
    Vietnamese layout, so validation correctly rejects it. This matches the
    measured error profile, where deletions outnumber substitutions on two-line
    plates: a whole missing line is what a deletion-dominated profile looks like.

    The upper half **on its own** reads fine in those cases -- ``29E`` at 0.98
    confidence for that plate. So this function spends one extra OCR call on it
    and re-normalises ``upper + strip``, keeping the attempt only if the combined
    string validates.

    Why more than one cut is tried
    ------------------------------
    Re-cutting at the *same* ratio the strip used cannot help when the ratio is
    itself what broke the read. On a tightly framed crop the 5/12 cut lands
    inside the upper row of glyphs, and PP-OCR's detector then reports no text
    region at all rather than a degraded one -- so the rescue received an empty
    string and had nothing to prepend. :data:`RESCUE_UPPER_END_RATIOS` therefore
    holds a short ladder of cuts, tried in order until one produces a string that
    validates. The first entry reproduces the previous behaviour exactly, so a
    plate the old rescue recovered is recovered by the same call as before.

    Measured on 900 two-line plates over two independent samples: +1.86 points on
    700 (60.14% to 62.00%, 13 rescued) and +0.5 on 200, with **zero** regressions
    in either. The extra call fires on about a fifth of two-line crops -- only
    those that had already failed -- for roughly 22 ms of mean latency. See
    ``docs/reports/15-two-line-fallback-700.json``.

    Kept as a free function rather than a private pipeline method on purpose:
    ``ai/evaluation/ocr_accuracy.py`` drives the recogniser and the normalizer
    directly, without constructing a pipeline. Were the rescue a method, the
    published NFR-A5/A6/A7 figures would measure a code path that production does
    not use -- the evaluation would silently understate the shipped system.

    Args:
        recognizer: The OCR engine to spend the extra call on.
        normalizer: The stage that decides whether the combined string is a
            valid Vietnamese plate. Its verdict is the only accept criterion.
        plate_image: The original crop, before any splitting.
        recognition: The failed, already-normalised first attempt.
        context: Optional fields merged into the log records, so a caller that
            has a plate index or bounding box can make the entry traceable.
        color: Background colour of the crop, forwarded so the rescued string
            is classified with the same evidence as a first-attempt one.

    Returns:
        A recognition carrying the recovered plate number, or the unchanged
        argument when the retry produces nothing that validates. Any failure
        inside the retry returns the original result: a rescue attempt must never
        cost more than it can win.
    """
    extra: dict[str, object] = dict(context or {})

    for ratio in RESCUE_UPPER_END_RATIOS:
        kind = ""
        display_text = ""

        try:
            upper, _lower = split_two_line(plate_image, upper_end_ratio=ratio)
            upper_read = recognizer.recognize(upper)

            # Nothing read means this cut has nothing to contribute: the combined
            # string would be the first attempt's text unchanged, which has
            # already been rejected. Skipping saves the normalisation and, more
            # importantly, keeps the log honest about which cut did the work.
            if not upper_read.text:
                continue

            combined = f"{upper_read.text}{recognition.raw_text}"

            detailed = getattr(normalizer, "normalize_detailed", None)
            if callable(detailed):
                outcome = detailed(combined, line_count=2)
                text, is_valid = outcome.text, outcome.is_valid_format
                # The rescued string is a different plate number from the one the
                # first attempt produced, so its family and rendering have to be
                # recomputed here. Carrying the first attempt's values over would
                # describe a string that no longer exists.
                kind = refine_kind_with_color(outcome, color, 2)
                display_text = _format_for_display(normalizer, text, 2)
            else:
                text, is_valid = normalizer.normalize(combined)
        except Exception as error:  # noqa: BLE001 - a rescue must not become a failure
            # Try the next ratio rather than abandoning the rescue: a crop only
            # a few pixels tall can make one cut degenerate while a later, more
            # generous one is still a usable image.
            _LOGGER.warning(
                "Upper-line rescue attempt failed, trying the next cut",
                extra={
                    **extra,
                    "upper_end_ratio": ratio,
                    "error": f"{type(error).__name__}: {error}",
                },
            )
            continue

        if not is_valid:
            continue

        _LOGGER.info(
            "Upper-line rescue recovered a two-line plate",
            extra={
                **extra,
                "first_attempt": recognition.text,
                "recovered": text,
                "upper_fragment": upper_read.text,
                "upper_end_ratio": ratio,
            },
        )
        return PlateRecognition(
            text=text,
            raw_text=recognition.raw_text,
            confidence=recognition.confidence,
            line_count=2,
            is_valid_format=True,
            kind=kind,
            display_text=display_text,
        )

    return recognition


def _format_for_display(normalizer: BaseNormalizer, text: str, line_count: int) -> str:
    """Render a plate string with the separators the physical plate carries.

    Args:
        normalizer: The injected normalizer. ``format_for_display`` is an
            optional capability beyond :class:`BaseNormalizer`, so it is probed.
        text: The bare normalised string, e.g. ``"29E01566"``.
        line_count: Lines on the plate, forwarded to disambiguate layouts that
            share a character pattern.

    Returns:
        The formatted string, e.g. ``"29E-015.66"``. Falls back to ``text``
        unchanged when the normalizer cannot format or raises -- a cosmetic
        step must never cost a plate that was read correctly.
    """
    formatter = getattr(normalizer, "format_for_display", None)
    if not callable(formatter):
        return text
    try:
        return formatter(text, line_count=line_count) or text
    except Exception:  # noqa: BLE001 - presentation must not break recognition
        _LOGGER.debug("format_for_display failed for %r, showing the bare string", text)
        return text


# Which string-level candidate a colour should promote. A blue background is
# the *only* evidence that separates a state-agency plate from a private one:
# `80A-123.45` is a legal string for both, so the character classifier reports
# them as equally plausible candidates and picks the commoner one.
_COLOR_PREFERRED_KINDS: Final[dict[str, tuple[str, ...]]] = {
    "blue": ("blue_car", "blue_motorcycle"),
}

_BLUE_EQUIVALENT: Final[dict[str, str]] = {
    "car": "blue_car",
    "motorcycle_new": "blue_motorcycle",
    "motorcycle_old": "blue_motorcycle",
}
"""The State-agency counterpart of each civil family.

Keyed on the family the *character string* established, because that is the only
evidence for car-versus-motorcycle: the serial pattern differs (`65A` versus
`65K1`) while the colour is identical either way.
"""


def refine_kind_with_color(outcome: object, color: str, line_count: int) -> str:
    """Resolve a string-level plate-family ambiguity using the plate's colour.

    The ambiguity being resolved
    ----------------------------
    Vietnamese plate layouts are not unique to a plate family. Asked to classify
    ``80A12345``, the character rules return four candidates -- ``car``,
    ``motorcycle_old``, ``blue_car``, ``blue_motorcycle`` -- and flag the result
    ambiguous, because every one of them is a legal reading of that string. The
    normalizer then has to pick one, and picks the commonest: ``car``.

    That answer is right most of the time and silently wrong for every State
    vehicle, whose plate carries the same characters on a **blue** field. No
    amount of work on the regular expressions can fix it: the distinction is not
    in the string. It is in the pixels, which this stage has.

    So the colour is allowed to promote a candidate the string already
    considered plausible -- and nothing more. It cannot invent a family the
    character rules rejected, which keeps a misread colour from fabricating a
    classification: the worst a wrong colour can do is choose the wrong member of
    a set the string itself called equally likely.

    Args:
        outcome: The normalizer's detailed result, carrying ``decision.kind`` and
            ``decision.candidates``.
        color: Background colour from :func:`~ai.inference.plate_color.classify_plate_color`.
        line_count: Lines on the plate, used to choose between the car and the
            motorcycle member of a promoted pair.

    Returns:
        The refined plate-kind string, or the original verdict when the colour
        offers no evidence -- unknown colour, a colour with no preferred family,
        or a string the rules classified unambiguously.
    """
    decision = getattr(outcome, "decision", None)
    original = getattr(getattr(decision, "kind", None), "value", "")
    if decision is None or not original:
        return original

    preferred = _COLOR_PREFERRED_KINDS.get(color)
    if preferred is None:
        return original

    candidates = {
        getattr(candidate, "value", "") for candidate in getattr(decision, "candidates", ())
    }
    if original not in candidates:
        # The string was classified unambiguously -- military, diplomatic,
        # special. Colour must not overrule a definite reading.
        return original

    # Promote within the vehicle class the *string* already established, never
    # across it. The serial pattern is what separates a car from a motorcycle --
    # `65A` is a car serial, `65K1` a motorcycle one -- and the colour has
    # nothing to say about that distinction.
    #
    # An earlier version chose between `blue_car` and `blue_motorcycle` by line
    # count, on the assumption that two lines meant a motorcycle. Real data
    # disproved it: `65A-004.50` is a two-line State **car** plate, and
    # QCVN 08:2024/BCA defines the 330x165 two-line format for cars precisely so
    # that it can exist. The assumption cost the promotion on exactly the plates
    # it was meant to catch.
    target = _BLUE_EQUIVALENT.get(original)
    if target is not None and target in candidates:
        return target
    return original
