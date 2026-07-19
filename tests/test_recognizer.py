"""Unit tests for the OCR recogniser's flow and output parsing.

These use a fake engine, so they need no model weights, no network and no
PaddlePaddle runtime. They cover the parts this project owns -- validation,
the two-line branch, fragment ordering, artefact filtering and confidence
aggregation -- rather than PaddleOCR's own accuracy, which is what the Phase 4
benchmark measures.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from ai.inference.config import InferenceConfig
from ai.inference.exceptions import InvalidImageError, RecognitionError
from ai.inference.interfaces import BaseRecognizer
from ai.inference.recognizer import (
    MIN_FRAGMENT_HEIGHT_RATIO,
    OCR_INPUT_HEIGHT,
    PaddleOcrRecognizer,
    _aggregate_confidence,
    _parse_ocr_output,
)


def _poly(x0: float, y0: float, x1: float, y1: float) -> list[list[float]]:
    """Build a rectangular detection polygon in PaddleOCR's corner order."""
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def _result(
    texts: list[str], scores: list[float], polys: list[Any] | None
) -> dict[str, Any]:
    """Build one PaddleOCR-3.x-shaped result mapping."""
    payload: dict[str, Any] = {"rec_texts": texts, "rec_scores": scores}
    if polys is not None:
        payload["rec_polys"] = polys
    return payload


class FakeEngine:
    """Stand-in for the PaddleOCR pipeline, recording the images it saw."""

    def __init__(self, results: list[Any] | Exception) -> None:
        self.results = results
        self.seen: list[np.ndarray] = []

    def predict(self, image: np.ndarray) -> list[Any]:
        """Return the canned payload, or raise the canned error."""
        self.seen.append(image)
        if isinstance(self.results, Exception):
            raise self.results
        return self.results


def _recognizer(results: list[Any] | Exception, **kwargs: Any) -> PaddleOcrRecognizer:
    """Build a recogniser wired to a fake engine."""
    return PaddleOcrRecognizer(
        InferenceConfig(), engine=FakeEngine(results), **kwargs
    )


class TestContract:
    """The recogniser honours the abstraction the pipeline depends on."""

    def test_implements_the_base_interface(self) -> None:
        """It really is a BaseRecognizer, so it is substitutable (NFR-M5)."""
        assert isinstance(_recognizer([]), BaseRecognizer)

    def test_exposes_a_name(self) -> None:
        """The engine identifies itself for logs and benchmark reports."""
        assert "paddleocr" in _recognizer([]).name

    def test_warmup_swallows_engine_failures(self) -> None:
        """A failed warm-up must never stop the service from starting."""
        _recognizer(RuntimeError("engine exploded")).warmup()


class TestValidation:
    """Unusable crops are rejected before any inference is attempted."""

    @pytest.mark.parametrize(
        "bad",
        [
            None,
            "not an array",
            np.zeros((0, 10, 3), dtype=np.uint8),
            np.zeros((10, 0, 3), dtype=np.uint8),
            np.zeros((2, 2, 2, 2), dtype=np.uint8),
        ],
    )
    def test_rejects_invalid_crops(self, bad: Any) -> None:
        """Anything that is not a usable image raises InvalidImageError."""
        with pytest.raises(InvalidImageError):
            _recognizer([]).recognize(bad)  # type: ignore[arg-type]

    def test_engine_failure_becomes_a_recognition_error(self) -> None:
        """An engine crash surfaces as the package's own exception type."""
        recognizer = _recognizer(RuntimeError("boom"))
        with pytest.raises(RecognitionError, match="PaddleOCR inference failed"):
            recognizer.recognize(np.full((110, 520, 3), 255, dtype=np.uint8))


class TestRecognizeFlow:
    """End-to-end behaviour of :meth:`PaddleOcrRecognizer.recognize`."""

    def test_one_line_plate_is_not_split(self) -> None:
        """A wide crop keeps its aspect ratio through to the engine."""
        recognizer = _recognizer(
            [_result(["51A-12345"], [0.98], [_poly(10, 20, 500, 90)])]
        )
        crop = np.full((110, 520, 3), 255, dtype=np.uint8)
        recognition = recognizer.recognize(crop)

        assert recognition.line_count == 1
        assert recognition.text == "51A-12345"
        assert recognition.raw_text == "51A-12345"
        assert recognition.confidence == pytest.approx(0.98)

    def test_two_line_plate_is_merged_into_a_wide_strip(self) -> None:
        """A near-square crop reaches the engine as a single-line strip."""
        engine = FakeEngine([_result(["29-B1", "234.56"], [0.9, 0.9], None)])
        recognizer = PaddleOcrRecognizer(InferenceConfig(), engine=engine)
        crop = np.full((280, 380, 3), 255, dtype=np.uint8)

        recognition = recognizer.recognize(crop)

        assert recognition.line_count == 2
        seen = engine.seen[0]
        assert crop.shape[1] / crop.shape[0] < 2.0
        assert seen.shape[1] / seen.shape[0] > 4.0

    def test_text_is_not_normalised(self) -> None:
        """Separators survive; correction is the normalizer's job."""
        recognizer = _recognizer([_result(["29-b1", "234.56"], [1.0, 1.0], None)])
        recognition = recognizer.recognize(np.full((280, 380, 3), 255, dtype=np.uint8))

        assert recognition.raw_text == "29-b1 234.56"
        assert recognition.text == "29-B1234.56"
        assert "-" in recognition.text and "." in recognition.text
        assert recognition.is_valid_format is False

    def test_unreadable_crop_returns_empty_instead_of_raising(self) -> None:
        """A blurred plate is a normal outcome that must still be recorded."""
        recognition = _recognizer([]).recognize(
            np.full((110, 520, 3), 255, dtype=np.uint8)
        )

        assert recognition.text == ""
        assert recognition.raw_text == ""
        assert recognition.confidence == 0.0
        assert recognition.line_count == 1

    def test_preprocessing_can_be_disabled(self) -> None:
        """The ablation switch drops the enhancement chain but keeps the scale cap.

        ``preprocess=False`` exists to measure what CLAHE and denoising
        contribute. It must **not** also disable the height normalisation:
        PP-OCR's text detector returns nothing at all on glyphs hundreds of
        pixels tall, so an ablation that removed the cap would measure the
        detector failing to fire rather than the enhancement chain.

        A crop already at the target height is therefore passed through
        untouched, while an oversized one is still shrunk.
        """
        crop = np.full((OCR_INPUT_HEIGHT, 520, 3), 255, dtype=np.uint8)
        engine = FakeEngine([])
        PaddleOcrRecognizer(
            InferenceConfig(), preprocess=False, engine=engine
        ).recognize(crop)

        np.testing.assert_array_equal(engine.seen[0], crop)

    def test_oversized_crop_is_shrunk_to_the_ocr_input_height(self) -> None:
        """A close-up crop is capped before it reaches the engine.

        Regression guard for the Phase 4 finding: without this cap the engine
        read nothing on any crop of the 640x640 label corpus.
        """
        crop = np.full((640, 640, 3), 255, dtype=np.uint8)
        engine = FakeEngine([])
        PaddleOcrRecognizer(InferenceConfig(), engine=engine).recognize(crop)

        assert engine.seen[0].shape[0] == OCR_INPUT_HEIGHT


class TestParseOcrOutput:
    """Fragment ordering, artefact filtering and defensive parsing."""

    def test_orders_fragments_left_to_right(self) -> None:
        """Reading order follows horizontal position, not engine order.

        After the two-line merge the upper row sits on the left, so sorting by
        x recovers the correct plate reading order.
        """
        texts, _ = _parse_ocr_output(
            [
                _result(
                    ["234.56", "29-B1"],
                    [1.0, 1.0],
                    [_poly(652, 68, 951, 154), _poly(99, 59, 494, 184)],
                )
            ]
        )
        assert texts == ["29-B1", "234.56"]

    def test_drops_short_artefact_fragments(self) -> None:
        """A sliver detection is discarded even at plausible confidence.

        Reproduces the CLAHE artefact seen during bring-up: a 10 px-tall
        fragment alongside genuine rows of 125 px and 87 px.
        """
        texts, scores = _parse_ocr_output(
            [
                _result(
                    ["cYanmaGaYGntaYellowb", "29-B1", "234.56"],
                    [0.84, 0.9999, 0.9999],
                    [
                        _poly(686, 5, 779, 15),
                        _poly(100, 59, 496, 184),
                        _poly(653, 69, 653 + 299, 69 + 87),
                    ],
                )
            ]
        )
        assert texts == ["29-B1", "234.56"]
        assert len(scores) == 2

    def test_keeps_fragments_just_above_the_height_ratio(self) -> None:
        """The filter does not eat legitimately shorter rows."""
        tall, short = 100.0, 100.0 * MIN_FRAGMENT_HEIGHT_RATIO + 1.0
        texts, _ = _parse_ocr_output(
            [
                _result(
                    ["AA", "BB"],
                    [0.9, 0.9],
                    [_poly(0, 0, 50, tall), _poly(60, 0, 110, short)],
                )
            ]
        )
        assert texts == ["AA", "BB"]

    def test_without_geometry_the_engine_order_is_preserved(self) -> None:
        """Missing polygons disable both sorting and filtering, not parsing."""
        texts, _ = _parse_ocr_output([_result(["FIRST", "SECOND"], [0.9, 0.8], None)])
        assert texts == ["FIRST", "SECOND"]

    def test_skips_empty_strings(self) -> None:
        """Empty fragments never reach the output."""
        texts, _ = _parse_ocr_output([_result(["", "51A"], [0.1, 0.9], None)])
        assert texts == ["51A"]

    def test_handles_an_empty_payload(self) -> None:
        """No detection at all parses to empty lists, not an error."""
        assert _parse_ocr_output([]) == ([], [])
        assert _parse_ocr_output(None) == ([], [])


class TestAggregateConfidence:
    """Confidence is a length-weighted mean, not a plain average."""

    def test_long_fragments_dominate(self) -> None:
        """A confident single character cannot mask an unsure long one."""
        weighted = _aggregate_confidence(["A", "1234567"], [0.99, 0.40])
        assert weighted < 0.5
        assert weighted == pytest.approx((0.99 + 0.40 * 7) / 8)

    def test_empty_input_is_zero(self) -> None:
        """Nothing read means zero confidence, not a division by zero."""
        assert _aggregate_confidence([], []) == 0.0
        assert _aggregate_confidence([""], [0.9]) == 0.0

    def test_result_is_clamped(self) -> None:
        """A misbehaving engine cannot push confidence outside [0, 1]."""
        assert _aggregate_confidence(["AB"], [1.5]) == 1.0
        assert _aggregate_confidence(["AB"], [-0.5]) == 0.0
