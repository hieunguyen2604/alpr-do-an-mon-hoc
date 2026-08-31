"""End-to-end ALPR pipeline: detect, crop, recognise, normalise (NFR-M5, NFR-P1, NFR-M1)."""

from __future__ import annotations

import logging
import time
from typing import Final

import numpy as np

from ai.inference.config import InferenceConfig
from ai.inference.exceptions import ALPRError, InvalidImageError
from ai.inference.interfaces import BaseDetector, BaseNormalizer, BaseRecognizer
from ai.inference.plate_color import classify_plate_color
from ai.inference.superres import SR_SCALES, superres_upscale
from ai.inference.two_line import (
    UPPER_HALF_END_RATIO,
    rectify_plate,
    split_two_line,
    stretch_vertical,
)
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
    "should_retry_skewed",
    "retry_skewed_variants",
    "refine_kind_with_color",
    "RESCUE_UPPER_END_RATIOS",
    "RESCUE_MIN_UPPER_CONFIDENCE",
    "RETRY_STRETCH_MAX_RATIO",
    "RETRY_STRETCH_FACTOR",
    "RETRY_SR_MAX_SIDE",
]

_LOGGER = logging.getLogger(__name__)

STAGE_NAMES: Final[tuple[str, ...]] = ("detect", "crop", "ocr", "normalize", "total")
"""Keys always present in :attr:`~ai.inference.types.PipelineResult.stage_times`."""


class ALPRPipeline:
    """Run detection, recognition and normalisation over one image."""

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

    # Identity
    @property
    def name(self) -> str:
        """Return a combined engine identifier, e.g. ``"yolo:best.pt+paddleocr-..."``."""
        return f"{self._safe_name(self._detector)}+{self._safe_name(self._recognizer)}"

    @property
    def is_ready(self) -> bool:
        """Return whether this pipeline can produce genuine results."""
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

    # Lifecycle
    def warmup(self) -> None:
        """Prime both models so the first real request is not the slow one."""
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

    # Main entry point
    def process(self, image: ImageArray, *, read_text: bool = True) -> PipelineResult:
        """Find and read every license plate in one image or video frame."""
        self._validate_image(image)
        height, width = int(image.shape[0]), int(image.shape[1])

        total_started = time.perf_counter()
        stage_times: dict[str, float] = {name: 0.0 for name in STAGE_NAMES}

        detect_started = time.perf_counter()
        detections = self._detector.detect(image)
        stage_times["detect"] = time.perf_counter() - detect_started

        results: list[DetectionResult] = []
        for index, detection in enumerate(detections):
            result, elapsed = self._process_one_plate(image, detection, index, read_text=read_text)
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

    # Internals
    def _process_one_plate(
        self,
        image: ImageArray,
        detection: PlateDetection,
        index: int,
        *,
        read_text: bool = True,
    ) -> tuple[DetectionResult, dict[str, float]]:
        """Crop, recognise and normalise a single detected plate."""
        elapsed = {"crop": 0.0, "ocr": 0.0, "normalize": 0.0}

        crop_started = time.perf_counter()
        plate_image = self._crop(image, detection.bbox)
        elapsed["crop"] = time.perf_counter() - crop_started

        # Plate colour classified from crop before normalisation to break vehicle family ties
        color = classify_plate_color(plate_image) if plate_image is not None else None
        color_name = color.color.value if color is not None else ""

        recognition: PlateRecognition | None = None
        if plate_image is not None and read_text:
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

                if self._config.rectify_enabled and should_retry_skewed(recognition):
                    retry_started = time.perf_counter()
                    recognition = retry_skewed_variants(
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
        """Cut the plate region out of the source image."""
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
        """Read one crop, containing any failure to this plate alone."""
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
        except Exception as error:
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
        """Correct and validate the raw string read from one plate."""
        raw_source = recognition.text or recognition.raw_text
        kind = ""
        display_text = ""

        try:
            detailed = getattr(self._normalizer, "normalize_detailed", None)
            if callable(detailed):
                outcome = detailed(raw_source, line_count=recognition.line_count)
                text, is_valid = outcome.text, outcome.is_valid_format
                kind = refine_kind_with_color(outcome, plate_color, recognition.line_count)
                display_text = _format_for_display(
                    self._normalizer,
                    text,
                    recognition.line_count,
                    kind=kind,
                    upper_char_count=recognition.upper_char_count,
                )
            else:
                text, is_valid = self._normalizer.normalize(raw_source)
        except Exception as error:
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
            upper_char_count=recognition.upper_char_count,
        )

    @staticmethod
    def _safe_name(component: object) -> str:
        """Return a component's ``name``, falling back to its class name."""
        try:
            name = getattr(component, "name", None)
        except Exception:
            return type(component).__name__
        return str(name) if name else type(component).__name__

    @staticmethod
    def _validate_image(image: ImageArray) -> None:
        """Reject anything that is not a usable image before any stage runs."""
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
    """Assemble the project's standard pipeline."""
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


RESCUE_UPPER_END_RATIOS: Final[tuple[float, ...]] = (UPPER_HALF_END_RATIO, 0.55)
RESCUE_MIN_UPPER_CONFIDENCE: Final[float] = 0.8


def should_rescue_two_line(recognition: PlateRecognition) -> bool:
    """Decide whether a two-line read is worth a second, narrower attempt."""
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
    """Re-read the upper half alone and prepend it to a failed two-line read."""
    extra: dict[str, object] = dict(context or {})

    for ratio in RESCUE_UPPER_END_RATIOS:
        kind = ""
        display_text = ""

        try:
            upper, _lower = split_two_line(plate_image, upper_end_ratio=ratio)
            upper_read = recognizer.recognize(upper)

            if not upper_read.text:
                continue

            if upper_read.confidence < RESCUE_MIN_UPPER_CONFIDENCE:
                _LOGGER.info(
                    "Upper fragment below confidence floor, not prepending",
                    extra={
                        **extra,
                        "upper_fragment": upper_read.text,
                        "upper_confidence": round(upper_read.confidence, 3),
                        "upper_end_ratio": ratio,
                    },
                )
                continue

            combined = f"{upper_read.text}{recognition.raw_text}"

            # Upper-line length read outright (strongest evidence for upper_char_count);
            # counted over alphanumerics because the fragment may carry a separator.
            upper_chars = sum(1 for ch in upper_read.text if ch.isalnum())

            detailed = getattr(normalizer, "normalize_detailed", None)
            if callable(detailed):
                outcome = detailed(combined, line_count=2)
                text, is_valid = outcome.text, outcome.is_valid_format
                # A rescued string is a different plate: family and rendering recomputed.
                kind = refine_kind_with_color(outcome, color, 2)
                # Same evidence as above, read off the hybrid combination.
                display_text = _format_for_display(
                    normalizer, text, 2, kind=kind, upper_char_count=upper_chars
                )
            else:
                text, is_valid = normalizer.normalize(combined)
        except Exception as error:  # noqa: BLE001 - a rescue must not become a failure
            # One degenerate cut does not end the rescue; a later ratio may still work.
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
            upper_char_count=upper_chars,
        )

    return recognition


RETRY_STRETCH_MAX_RATIO: Final[float] = 4.2
"""Widest crop the vertical-stretch retry still treats as a possible two-line."""

RETRY_STRETCH_FACTOR: Final[float] = 2.0
"""Vertical multiplier for the foreshortening retry."""

RETRY_SR_MAX_SIDE: Final[int] = 200
"""Largest crop side, in pixels, still eligible for the super-resolution retry."""


_UNCLASSIFIED_KINDS: Final[tuple[str, ...]] = ("", "unknown")
"""Kind values that mean the classifier found nothing at all."""


def should_retry_skewed(recognition: PlateRecognition | None) -> bool:
    """Return whether the skew-retry ladder should spend calls on this read."""
    return (
        recognition is not None
        and not recognition.is_valid_format
        and recognition.kind in _UNCLASSIFIED_KINDS
    )


def retry_skewed_variants(
    recognizer: BaseRecognizer,
    normalizer: BaseNormalizer,
    plate_image: ImageArray,
    recognition: PlateRecognition,
    context: dict[str, object] | None = None,
    color: str = "",
) -> PlateRecognition:
    """Re-read a failed crop through geometry-corrected variants."""
    extra: dict[str, object] = dict(context or {})

    # Red background exists ONLY on army plates: no read off a red crop may be
    # upgraded to a valid civil string, whatever the characters say.
    if color == "red":
        _LOGGER.info(
            "Skew retry refused: red plate background",
            extra={**extra, "first_attempt": recognition.text},
        )
        return recognition

    variants: list[tuple[str, ImageArray]] = []
    try:
        rectified = rectify_plate(plate_image)
        if rectified is not plate_image:
            variants.append(("rectify", rectified))
    except ALPRError as error:
        _LOGGER.warning(
            "Skew retry could not rectify the crop",
            extra={**extra, "error": f"{type(error).__name__}: {error}"},
        )

    height, width = plate_image.shape[0], plate_image.shape[1]
    aspect_ratio = width / height if height else 0.0
    config = getattr(recognizer, "config", None)
    two_line_threshold = getattr(config, "two_line_aspect_ratio_threshold", 2.5)
    if two_line_threshold <= aspect_ratio <= RETRY_STRETCH_MAX_RATIO:
        try:
            variants.append(
                ("stretch", stretch_vertical(plate_image, RETRY_STRETCH_FACTOR))
            )
        except ALPRError as error:
            _LOGGER.warning(
                "Skew retry could not stretch the crop",
                extra={**extra, "error": f"{type(error).__name__}: {error}"},
            )

    # SR variants only for small crops (measured recoveries at 32x23 and 171x120 px);
    # tried after geometry because they are the more expensive hypothesis.
    if (
        getattr(config, "sr_retry_enabled", True)
        and max(height, width) <= RETRY_SR_MAX_SIDE
    ):
        for scale in SR_SCALES:
            upscaled = superres_upscale(plate_image, scale)
            if upscaled is not None:
                variants.append((f"sr_x{scale}", upscaled))

    for variant_name, variant_image in variants:
        variant_extra = {**extra, "variant": variant_name}
        try:
            attempt = recognizer.recognize(variant_image)
            if not attempt.text:
                candidate = attempt
            else:
                detailed = getattr(normalizer, "normalize_detailed", None)
                if callable(detailed):
                    outcome = detailed(attempt.raw_text, line_count=attempt.line_count)
                    variant_kind = refine_kind_with_color(outcome, color, attempt.line_count)
                    candidate = PlateRecognition(
                        text=outcome.text,
                        raw_text=attempt.raw_text,
                        confidence=attempt.confidence,
                        line_count=attempt.line_count,
                        is_valid_format=outcome.is_valid_format,
                        kind=variant_kind,
                        display_text=_format_for_display(
                            normalizer,
                            outcome.text,
                            attempt.line_count,
                            kind=variant_kind,
                            upper_char_count=attempt.upper_char_count,
                        ),
                        upper_char_count=attempt.upper_char_count,
                    )
                else:
                    text, is_valid = normalizer.normalize(attempt.raw_text)
                    candidate = PlateRecognition(
                        text=text,
                        raw_text=attempt.raw_text,
                        confidence=attempt.confidence,
                        line_count=attempt.line_count,
                        is_valid_format=is_valid,
                        upper_char_count=attempt.upper_char_count,
                    )

            # The rescue must run on the VARIANT image: its geometry owns the cut ratios.
            if not candidate.is_valid_format and should_rescue_two_line(candidate):
                candidate = rescue_two_line_upper(
                    recognizer,
                    normalizer,
                    variant_image,
                    candidate,
                    context=variant_extra,
                    color=color,
                )

            # Hybrid rescue: upper line off the variant, lower line off the original read
            # (measured on a 32x23 px crop where each half alone failed validation).
            if not candidate.is_valid_format and recognition.raw_text:
                hybrid_base = PlateRecognition(
                    text=recognition.text,
                    raw_text=recognition.raw_text,
                    confidence=recognition.confidence,
                    line_count=recognition.line_count,
                    is_valid_format=False,
                    upper_char_count=recognition.upper_char_count,
                )
                if should_rescue_two_line(hybrid_base):
                    rescued = rescue_two_line_upper(
                        recognizer,
                        normalizer,
                        variant_image,
                        hybrid_base,
                        context={**variant_extra, "hybrid_lower": "original"},
                        color=color,
                    )
                    if rescued.is_valid_format:
                        candidate = rescued
        except Exception as error:  # noqa: BLE001 - a retry must not become a failure
            _LOGGER.warning(
                "Skew retry variant failed, trying the next",
                extra={**variant_extra, "error": f"{type(error).__name__}: {error}"},
            )
            continue

        if candidate.is_valid_format:
            _LOGGER.info(
                "Skew retry recovered a plate",
                extra={
                    **variant_extra,
                    "first_attempt": recognition.text,
                    "recovered": candidate.text,
                },
            )
            return candidate

    return recognition


def _format_for_display(
    normalizer: BaseNormalizer,
    text: str,
    line_count: int,
    kind: str = "",
    upper_char_count: int = 0,
) -> str:
    """Render a plate string with the separators the physical plate carries."""
    formatter = getattr(normalizer, "format_for_display", None)
    if not callable(formatter):
        return text
    try:
        try:
            return (
                formatter(
                    text,
                    line_count=line_count,
                    kind=kind or None,
                    upper_char_count=upper_char_count,
                )
                or text
            )
        except TypeError:
            # Older normalizer signature: probe capabilities, degrade one step at a time.
            try:
                return formatter(text, line_count=line_count, kind=kind or None) or text
            except TypeError:
                return formatter(text, line_count=line_count) or text
    except Exception:  # noqa: BLE001 - presentation must not break recognition
        _LOGGER.debug("format_for_display failed for %r, showing the bare string", text)
        return text


# Blue background is the only evidence separating a state-agency plate from a
# private one: 80A-123.45 is a legal string for both.
_COLOR_PREFERRED_KINDS: Final[dict[str, tuple[str, ...]]] = {
    "blue": ("blue_car", "blue_motorcycle"),
}

_BLUE_EQUIVALENT: Final[dict[str, str]] = {
    "car": "blue_car",
    "motorcycle_new": "blue_motorcycle",
    "motorcycle_old": "blue_motorcycle",
}
"""The State-agency counterpart of each civil family."""


def refine_kind_with_color(outcome: object, color: str, line_count: int) -> str:
    """Resolve a string-level plate-family ambiguity using the plate's colour."""
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

    # Promote within the vehicle class the string established, never across it:
    # colour says nothing about car vs motorcycle, and line count was tried and
    # disproved (65A-004.50 is a two-line State car, QCVN 08:2024 330x165).
    target = _BLUE_EQUIVALENT.get(original)
    if target is not None and target in candidates:
        return target
    return original
