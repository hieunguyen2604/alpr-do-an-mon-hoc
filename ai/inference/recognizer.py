"""PaddleOCR-backed implementation of BaseRecognizer for text recognition on license plates."""

from __future__ import annotations

import logging
import os
import time

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from typing import Any, Final, Sequence

import numpy as np

from ai.inference.config import InferenceConfig
from ai.inference.exceptions import (
    InvalidImageError,
    ModelLoadError,
    RecognitionError,
)
from ai.inference.interfaces import BaseRecognizer
from ai.inference.two_line import (
    estimate_line_count,
    merge_two_line,
    preprocess_plate,
    split_two_line,
)
from ai.inference.types import ImageArray, PlateRecognition

__all__ = [
    "OCR_VERSION",
    "DEFAULT_ENABLE_MKLDNN",
    "OCR_INPUT_HEIGHT",
    "PaddleOcrRecognizer",
]

_LOGGER = logging.getLogger(__name__)

OCR_VERSION: Final[str] = "PP-OCRv5"
"""PP-OCR generation this recogniser pins."""

TEXT_DETECTION_MODEL: Final[str] = "PP-OCRv5_mobile_det"
"""Text-detection sub-model pinned for CPU inference."""

RECOGNITION_MODEL_BY_LANG: Final[dict[str, str]] = {
    "en": "en_PP-OCRv5_mobile_rec",
    "ch": "PP-OCRv5_mobile_rec",
}
"""Recognition sub-model per language code, all mobile variants."""

DEFAULT_ENABLE_MKLDNN: Final[bool] = False
"""Whether the oneDNN (MKL-DNN) CPU acceleration path is enabled by default."""

_WARMUP_HEIGHT: Final[int] = 64
_WARMUP_WIDTH: Final[int] = 224
_MIN_OCR_HEIGHT: Final[int] = 64
"""Crops shorter than this are enlarged before OCR."""

_MAX_OCR_HEIGHT: Final[int] = 64
"""Crops taller than this are shrunk before OCR."""

OCR_INPUT_HEIGHT: Final[int] = _MIN_OCR_HEIGHT
"""Public alias for the height every crop is normalised to before OCR."""

MIN_FRAGMENT_HEIGHT_RATIO: Final[float] = 0.50
"""Minimum height of a text fragment, relative to the tallest one, to be kept."""


class PaddleOcrRecognizer(BaseRecognizer):
    """Read plate characters with PaddleOCR, handling one- and two-line plates."""

    def __init__(
        self,
        config: InferenceConfig | None = None,
        *,
        preprocess: bool = True,
        enable_mkldnn: bool = DEFAULT_ENABLE_MKLDNN,
        engine: Any | None = None,
    ) -> None:
        """Prepare the recogniser without loading any model yet."""
        self._config = config if config is not None else InferenceConfig()
        self._preprocess = preprocess
        self._enable_mkldnn = enable_mkldnn
        self._engine = engine

    @property
    def name(self) -> str:
        """Return the engine identifier used in logs and benchmark reports."""
        recognition = RECOGNITION_MODEL_BY_LANG.get(self._config.ocr_lang)
        if recognition is None:
            return f"paddleocr-{OCR_VERSION}-auto({self._config.ocr_lang})"
        return f"paddleocr-{OCR_VERSION}-mobile(det={TEXT_DETECTION_MODEL})"

    @property
    def config(self) -> InferenceConfig:
        """Return the configuration this recogniser was built with."""
        return self._config

    def recognize(self, plate_image: ImageArray) -> PlateRecognition:
        """Read the plate text from a cropped plate image."""
        self._validate_crop(plate_image)

        started = time.perf_counter()
        line_count = estimate_line_count(plate_image, self._config.two_line_aspect_ratio_threshold)

        ocr_input = plate_image
        if line_count == 2:
            upper, lower = split_two_line(ocr_input)
            ocr_input = merge_two_line(upper, lower)

        if self._preprocess:
            ocr_input = preprocess_plate(
                ocr_input,
                upscale_to_height=_MIN_OCR_HEIGHT,
                downscale_to_height=_MAX_OCR_HEIGHT,
            )
        else:
            # Scale cap is preserved during ablation to avoid detector firing failures
            ocr_input = preprocess_plate(
                ocr_input,
                to_grayscale=False,
                apply_clahe=False,
                denoise=False,
                upscale_to_height=_MIN_OCR_HEIGHT,
                downscale_to_height=_MAX_OCR_HEIGHT,
            )

        texts, scores = self._run_ocr(ocr_input)
        raw_text = " ".join(texts).strip()
        text = "".join(raw_text.split()).upper()
        confidence = _aggregate_confidence(texts, scores)

        # Upper-line length tracks serial boundary for two-line plates (0 if unread)
        upper_char_count = 0
        if line_count == 2 and len(texts) >= 2:
            upper_char_count = sum(1 for ch in texts[0] if ch.isalnum())

        _LOGGER.info(
            "Plate recognition finished",
            extra={
                "engine": self.name,
                "line_count": line_count,
                "raw_text": raw_text,
                "text": text,
                "confidence": round(confidence, 4),
                "segments": len(texts),
                "upper_char_count": upper_char_count,
                "elapsed_ms": round((time.perf_counter() - started) * 1000.0, 2),
            },
        )

        return PlateRecognition(
            text=text,
            raw_text=raw_text,
            confidence=confidence,
            line_count=line_count,
            is_valid_format=False,
            upper_char_count=upper_char_count,
        )

    def warmup(self) -> None:
        """Load the models and run one throwaway pass to prime the engine."""
        try:
            blank = np.full((_WARMUP_HEIGHT, _WARMUP_WIDTH, 3), 255, dtype=np.uint8)
            started = time.perf_counter()
            self.recognize(blank)
            _LOGGER.info(
                "OCR engine warmed up",
                extra={
                    "engine": self.name,
                    "elapsed_ms": round((time.perf_counter() - started) * 1000.0, 2),
                },
            )
        except Exception as error:  # noqa: BLE001 - warm-up must never block start-up
            _LOGGER.warning(
                "OCR warm-up failed, continuing without it",
                extra={"engine": self.name, "error": str(error)},
            )

    def _run_ocr(self, image: ImageArray) -> tuple[list[str], list[float]]:
        """Run the engine and return the fragments in left-to-right order."""
        engine = self._ensure_engine()
        try:
            raw_results = engine.predict(image)
        except Exception as error:
            raise RecognitionError(
                f"PaddleOCR inference failed on a {image.shape} crop: {error}"
            ) from error

        return _parse_ocr_output(raw_results)

    def _ensure_engine(self) -> Any:
        """Return the OCR engine, constructing it on first use."""
        if self._engine is not None:
            return self._engine

        try:
            from paddleocr import PaddleOCR, TextRecognition
        except ImportError as error:
            raise ModelLoadError(
                "PaddleOCR is not installed in the active environment; "
                "install the OCR requirements before running recognition"
            ) from error

        device = "gpu" if self._config.ocr_use_gpu else "cpu"

        if self._config.ocr_skip_detection:
            return self._build_recognition_only_engine(TextRecognition, device)

        # Pinned sub-model names ensure consistent architecture selection
        recognition_model = RECOGNITION_MODEL_BY_LANG.get(self._config.ocr_lang)
        if recognition_model is not None:
            model_kwargs: dict[str, Any] = {
                "text_detection_model_name": TEXT_DETECTION_MODEL,
                "text_recognition_model_name": recognition_model,
            }
            selection = f"det={TEXT_DETECTION_MODEL}, rec={recognition_model}"
            rec_dir = self._config.ocr_rec_model_dir
            if (
                rec_dir is not None
                and rec_dir.is_dir()
                and (rec_dir / "inference.pdiparams").exists()
            ):
                # Fine-tuned recognition model directory override
                model_kwargs["text_recognition_model_dir"] = str(rec_dir)
                selection += f", rec_dir={rec_dir}"



        else:
            LOGGER_MSG = (
                "No pinned mobile model pair for lang=%r; falling back to "
                "PaddleOCR's own resolution, which may select a server-sized "
                "detection model and cost roughly 2,7x more per crop."
            )
            _LOGGER.warning(LOGGER_MSG, self._config.ocr_lang)
            model_kwargs = {
                "lang": self._config.ocr_lang,
                "ocr_version": OCR_VERSION,
            }
            selection = f"lang={self._config.ocr_lang}, {OCR_VERSION}"

        if device == "cpu":
            model_kwargs["cpu_threads"] = int(os.environ.get("OMP_NUM_THREADS", "1"))

        started = time.perf_counter()
        try:
            self._engine = PaddleOCR(
                device=device,
                enable_mkldnn=self._enable_mkldnn,
                # One text region per crop: document-level pre-processing skipped
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                **model_kwargs,
            )
        except Exception as error:
            raise ModelLoadError(
                f"Failed to load PaddleOCR ({selection}, device={device!r}): {error}"
            ) from error

        _LOGGER.info(
            "OCR engine loaded",
            extra={
                "engine": self.name,
                "lang": self._config.ocr_lang,
                "device": device,
                "enable_mkldnn": self._enable_mkldnn,
                "elapsed_ms": round((time.perf_counter() - started) * 1000.0, 2),
            },
        )
        return self._engine

    def _build_recognition_only_engine(self, factory: Any, device: str) -> Any:
        """Build a recognition-only engine that reads the whole crop at once."""
        recognition_model = RECOGNITION_MODEL_BY_LANG.get(self._config.ocr_lang)
        kwargs: dict[str, Any] = {"device": device}
        if device == "cpu":
            kwargs["cpu_threads"] = int(os.environ.get("OMP_NUM_THREADS", "1"))
        if recognition_model is not None:
            kwargs["model_name"] = recognition_model

        rec_dir = self._config.ocr_rec_model_dir
        if rec_dir is not None and rec_dir.is_dir() and (rec_dir / "inference.pdiparams").exists():
            kwargs["model_dir"] = str(rec_dir)

        started = time.perf_counter()
        try:
            self._engine = factory(**kwargs)
        except Exception as error:
            raise ModelLoadError(
                f"Failed to load the recognition-only engine ({kwargs}): {error}"
            ) from error

        _LOGGER.info(
            "OCR engine loaded (recognition only, detection stage skipped)",
            extra={
                "engine": self.name,
                "model_name": recognition_model,
                "model_dir": str(rec_dir) if "model_dir" in kwargs else None,
                "device": device,
                "elapsed_ms": round((time.perf_counter() - started) * 1000.0, 2),
            },
        )
        return self._engine

    @staticmethod
    def _validate_crop(plate_image: ImageArray) -> None:
        """Reject crops that cannot be processed."""
        if plate_image is None or not isinstance(plate_image, np.ndarray):
            raise InvalidImageError(
                "plate_image must be a NumPy array, got " f"{type(plate_image).__name__}"
            )
        if plate_image.ndim not in (2, 3):
            raise InvalidImageError(
                "plate_image must be a 2-D or 3-D array, got " f"{plate_image.ndim} dimensions"
            )
        if plate_image.size == 0 or 0 in plate_image.shape[:2]:
            raise InvalidImageError(
                "plate_image must have a positive width and height, got shape "
                f"{plate_image.shape}"
            )


def _aggregate_confidence(texts: Sequence[str], scores: Sequence[float]) -> float:
    """Combine per-fragment OCR scores into one confidence for the plate."""
    weights = [len(text) for text in texts]
    total_weight = sum(weights)
    if total_weight == 0:
        return 0.0
    weighted = sum(score * weight for score, weight in zip(scores, weights))
    return float(min(1.0, max(0.0, weighted / total_weight)))


def _parse_ocr_output(raw_results: Any) -> tuple[list[str], list[float]]:
    """Extract texts, scores and reading order from a PaddleOCR result."""
    if not raw_results:
        return [], []

    # (left edge, height, text, score) -- height only used for artefact filtering.
    fragments: list[tuple[float, float, str, float]] = []
    for result in raw_results:
        texts = _lookup(result, "rec_texts") or []
        scores = _lookup(result, "rec_scores") or []

        if not texts:
            # Recognition-only mode: wrap singular text/score into list without polygons
            single = _lookup(result, "rec_text")
            if single:
                texts = [single]
                score = _lookup(result, "rec_score")
                scores = [score] if score is not None else []

        polys = _lookup(result, "rec_polys")
        if polys is None:
            polys = _lookup(result, "dt_polys")

        for index, text in enumerate(texts):
            if not text:
                continue
            score = float(scores[index]) if index < len(scores) else 0.0
            left, height = _fragment_geometry(polys, index)
            fragments.append((left, height, str(text), score))

    fragments = _drop_short_fragments(fragments)
    fragments.sort(key=lambda fragment: fragment[0])
    return (
        [text for _, _, text, _ in fragments],
        [score for _, _, _, score in fragments],
    )


def _drop_short_fragments(
    fragments: list[tuple[float, float, str, float]],
) -> list[tuple[float, float, str, float]]:
    """Discard fragments far shorter than the tallest one."""
    tallest = max((height for _, height, _, _ in fragments), default=0.0)
    if tallest <= 0.0:
        return fragments

    minimum = tallest * MIN_FRAGMENT_HEIGHT_RATIO
    kept = [fragment for fragment in fragments if fragment[1] >= minimum]
    dropped = len(fragments) - len(kept)
    if dropped:
        _LOGGER.debug(
            "Discarded short OCR fragments as detector artefacts",
            extra={
                "dropped": dropped,
                "tallest_fragment_height": round(tallest, 1),
                "min_height": round(minimum, 1),
                "dropped_texts": [text for _, height, text, _ in fragments if height < minimum],
            },
        )
    return kept


def _lookup(result: Any, key: str) -> Any:
    """Read ``key`` from a mapping-like or attribute-like OCR result."""
    try:
        return result[key]
    except (TypeError, KeyError, IndexError):
        return getattr(result, key, None)


def _fragment_geometry(polys: Any, index: int) -> tuple[float, float]:
    """Return the left edge and the height of one detected text polygon."""
    if polys is None or index >= len(polys):
        return float(index), 0.0
    try:
        polygon = np.asarray(polys[index], dtype=float)
        ys = polygon[:, 1]
        return float(polygon[:, 0].min()), float(ys.max() - ys.min())
    except (ValueError, IndexError, TypeError):
        return float(index), 0.0
