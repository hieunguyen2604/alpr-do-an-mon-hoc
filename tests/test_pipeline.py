"""Unit tests for :mod:`ai.inference.pipeline`.

The pipeline is tested with fake stages rather than real engines. That is not a
shortcut: the pipeline's whole job is ordering, cropping, timing and failure
containment, and none of that involves a model. Driving it with fakes is what
lets these tests run in milliseconds, without Ultralytics or PaddleOCR
installed, and lets them assert on behaviour -- such as "a crashing recogniser
must not lose the other plates" -- that is impractical to provoke with a real
engine.
"""

from __future__ import annotations

import numpy as np
import pytest

from ai.inference.config import InferenceConfig
from ai.inference.exceptions import InvalidImageError, RecognitionError
from ai.inference.interfaces import BaseDetector, BaseNormalizer, BaseRecognizer
from ai.inference.pipeline import STAGE_NAMES, ALPRPipeline
from ai.inference.types import BoundingBox, ImageArray, PlateDetection, PlateRecognition


# --------------------------------------------------------------------- #
# Test doubles
# --------------------------------------------------------------------- #
class FakeDetector(BaseDetector):
    """A detector that returns a fixed list of boxes and counts its calls."""

    def __init__(self, detections: list[PlateDetection] | None = None) -> None:
        self._detections = detections or []
        self.calls = 0
        self.warmup_calls = 0
        self.last_image: ImageArray | None = None

    @property
    def name(self) -> str:
        return "fake-detector"

    def detect(self, image: ImageArray) -> list[PlateDetection]:
        self.calls += 1
        self.last_image = image
        return list(self._detections)

    def warmup(self) -> None:
        self.warmup_calls += 1


class FakeRecognizer(BaseRecognizer):
    """A recogniser returning canned text, optionally raising on the Nth call."""

    def __init__(
        self,
        text: str = "51F73420",
        raise_on_call: int | None = None,
        error: Exception | None = None,
    ) -> None:
        self._text = text
        self._raise_on_call = raise_on_call
        self._error = error or RecognitionError("fake OCR failure")
        self.calls = 0
        self.warmup_calls = 0
        self.received_shapes: list[tuple[int, ...]] = []

    @property
    def name(self) -> str:
        return "fake-recognizer"

    def recognize(self, plate_image: ImageArray) -> PlateRecognition:
        self.calls += 1
        self.received_shapes.append(tuple(plate_image.shape))
        if self._raise_on_call is not None and self.calls == self._raise_on_call:
            raise self._error
        return PlateRecognition(
            text=self._text,
            raw_text=f"{self._text}-raw",
            confidence=0.9,
            line_count=1,
            is_valid_format=False,
        )

    def warmup(self) -> None:
        self.warmup_calls += 1


class FakeNormalizer(BaseNormalizer):
    """A minimal normalizer implementing only the interface method."""

    def __init__(self, valid: bool = True) -> None:
        self._valid = valid
        self.calls = 0
        self.received: list[str] = []

    def normalize(self, raw_text: str) -> tuple[str, bool]:
        self.calls += 1
        self.received.append(raw_text)
        return raw_text.replace("-", ""), self._valid


def make_detection(x: int, y: int, w: int, h: int, conf: float = 0.9) -> PlateDetection:
    """Build a detection at the given rectangle."""
    return PlateDetection(bbox=BoundingBox(x=x, y=y, width=w, height=h), confidence=conf)


def make_image(width: int = 200, height: int = 100) -> ImageArray:
    """Build a deterministic non-uniform BGR test image."""
    rng = np.random.default_rng(seed=1234)
    return rng.integers(0, 256, size=(height, width, 3), dtype=np.uint8)


def build(
    detector: BaseDetector | None = None,
    recognizer: BaseRecognizer | None = None,
    normalizer: BaseNormalizer | None = None,
) -> ALPRPipeline:
    """Assemble a pipeline from fakes, filling in defaults."""
    return ALPRPipeline(
        detector=detector or FakeDetector(),
        recognizer=recognizer or FakeRecognizer(),
        normalizer=normalizer or FakeNormalizer(),
        config=InferenceConfig(model_path="models/best.pt"),
    )


# --------------------------------------------------------------------- #
# Construction and dependency injection (NFR-M5)
# --------------------------------------------------------------------- #
class TestConstruction:
    def test_stores_injected_stages(self) -> None:
        detector, recognizer, normalizer = (
            FakeDetector(),
            FakeRecognizer(),
            FakeNormalizer(),
        )
        pipeline = ALPRPipeline(detector, recognizer, normalizer)
        assert pipeline.detector is detector
        assert pipeline.recognizer is recognizer
        assert pipeline.normalizer is normalizer

    @pytest.mark.parametrize("missing", ["detector", "recognizer", "normalizer"])
    def test_rejects_a_missing_stage(self, missing: str) -> None:
        stages = {
            "detector": FakeDetector(),
            "recognizer": FakeRecognizer(),
            "normalizer": FakeNormalizer(),
        }
        stages[missing] = None  # type: ignore[assignment]
        with pytest.raises(TypeError, match=missing):
            ALPRPipeline(**stages)  # type: ignore[arg-type]

    def test_builds_a_default_config_when_omitted(self) -> None:
        assert isinstance(build().config, InferenceConfig)

    def test_name_combines_both_engines(self) -> None:
        assert build().name == "fake-detector+fake-recognizer"

    def test_is_ready(self) -> None:
        assert build().is_ready is True


# --------------------------------------------------------------------- #
# Input validation
# --------------------------------------------------------------------- #
class TestInputValidation:
    @pytest.mark.parametrize(
        "bad",
        [
            None,
            "not an image",
            np.zeros((0, 10, 3), dtype=np.uint8),
            np.zeros((5, 5, 3, 2), dtype=np.uint8),
        ],
    )
    def test_rejects_unusable_input(self, bad: object) -> None:
        with pytest.raises(InvalidImageError):
            build().process(bad)  # type: ignore[arg-type]

    def test_does_not_call_the_detector_on_bad_input(self) -> None:
        detector = FakeDetector()
        with pytest.raises(InvalidImageError):
            build(detector=detector).process(None)  # type: ignore[arg-type]
        assert detector.calls == 0


# --------------------------------------------------------------------- #
# The empty case -- must never raise
# --------------------------------------------------------------------- #
class TestNoPlateFound:
    def test_returns_an_empty_result(self) -> None:
        result = build(detector=FakeDetector([])).process(make_image())
        assert result.plate_count == 0
        assert result.recognized_count == 0
        assert result.results == []
        assert len(result) == 0

    def test_records_the_image_dimensions(self) -> None:
        result = build(detector=FakeDetector([])).process(make_image(320, 240))
        assert (result.image_width, result.image_height) == (320, 240)

    def test_never_calls_the_recognizer(self) -> None:
        recognizer = FakeRecognizer()
        build(detector=FakeDetector([]), recognizer=recognizer).process(make_image())
        assert recognizer.calls == 0


# --------------------------------------------------------------------- #
# The happy path
# --------------------------------------------------------------------- #
class TestSuccessfulRun:
    def test_produces_one_result_per_detection(self) -> None:
        detector = FakeDetector(
            [make_detection(10, 10, 60, 20), make_detection(90, 40, 50, 20)]
        )
        result = build(detector=detector).process(make_image())
        assert result.plate_count == 2
        assert result.recognized_count == 2

    def test_crops_the_region_named_by_the_box(self) -> None:
        recognizer = FakeRecognizer()
        detector = FakeDetector([make_detection(10, 20, 60, 30)])
        build(detector=detector, recognizer=recognizer).process(make_image())
        assert recognizer.received_shapes == [(30, 60, 3)]

    def test_crop_is_a_copy_not_a_view(self) -> None:
        image = make_image()
        detector = FakeDetector([make_detection(10, 10, 40, 20)])
        result = build(detector=detector).process(image)
        crop = result.results[0].plate_image
        assert crop is not None
        crop[:] = 0
        assert image[10:30, 10:50].any(), "mutating the crop must not touch the source"

    def test_normalizer_receives_the_recognizer_output(self) -> None:
        normalizer = FakeNormalizer()
        detector = FakeDetector([make_detection(0, 0, 40, 20)])
        build(
            detector=detector,
            recognizer=FakeRecognizer(text="51F-734.20"),
            normalizer=normalizer,
        ).process(make_image())
        assert normalizer.received == ["51F-734.20"]

    def test_normalization_fills_in_the_validity_flag(self) -> None:
        detector = FakeDetector([make_detection(0, 0, 40, 20)])
        result = build(detector=detector, normalizer=FakeNormalizer(valid=True)).process(
            make_image()
        )
        recognition = result.results[0].recognition
        assert recognition is not None
        assert recognition.is_valid_format is True

    def test_raw_text_survives_normalization(self) -> None:
        """The raw string is the only way to measure what normalisation adds."""
        detector = FakeDetector([make_detection(0, 0, 40, 20)])
        result = build(detector=detector, recognizer=FakeRecognizer(text="51F-1")).process(
            make_image()
        )
        recognition = result.results[0].recognition
        assert recognition is not None
        assert recognition.raw_text == "51F-1-raw"
        assert recognition.text == "51F1"


# --------------------------------------------------------------------- #
# Failure containment
# --------------------------------------------------------------------- #
class TestFailureContainment:
    def test_one_failing_crop_does_not_lose_the_others(self) -> None:
        detector = FakeDetector(
            [
                make_detection(0, 0, 40, 20),
                make_detection(50, 0, 40, 20),
                make_detection(100, 0, 40, 20),
            ]
        )
        recognizer = FakeRecognizer(raise_on_call=2)
        result = build(detector=detector, recognizer=recognizer).process(make_image())

        assert result.plate_count == 3, "the failed plate must still be reported"
        assert result.recognized_count == 2
        assert result.results[1].recognition is None
        assert result.results[1].has_text is False

    def test_contains_an_unexpected_engine_error_too(self) -> None:
        """A third-party engine may raise anything; one plate must not cost the frame."""
        detector = FakeDetector([make_detection(0, 0, 40, 20)])
        recognizer = FakeRecognizer(raise_on_call=1, error=RuntimeError("boom"))
        result = build(detector=detector, recognizer=recognizer).process(make_image())
        assert result.plate_count == 1
        assert result.results[0].recognition is None

    def test_a_normalizer_bug_keeps_the_raw_recognition(self) -> None:
        class ExplodingNormalizer(BaseNormalizer):
            def normalize(self, raw_text: str) -> tuple[str, bool]:
                raise ValueError("rule bug")

        detector = FakeDetector([make_detection(0, 0, 40, 20)])
        result = build(detector=detector, normalizer=ExplodingNormalizer()).process(
            make_image()
        )
        recognition = result.results[0].recognition
        assert recognition is not None, "the plate must survive a normalizer crash"
        assert recognition.text == "51F73420"

    def test_a_box_outside_the_image_is_skipped_not_fatal(self) -> None:
        detector = FakeDetector([make_detection(500, 500, 40, 20)])
        recognizer = FakeRecognizer()
        result = build(detector=detector, recognizer=recognizer).process(
            make_image(200, 100)
        )
        assert result.plate_count == 1
        assert result.results[0].plate_image is None
        assert result.results[0].recognition is None
        assert recognizer.calls == 0


# --------------------------------------------------------------------- #
# Latency accounting (NFR-P1)
# --------------------------------------------------------------------- #
class TestTiming:
    def test_reports_every_stage(self) -> None:
        detector = FakeDetector([make_detection(0, 0, 40, 20)])
        result = build(detector=detector).process(make_image())
        assert set(result.stage_times) == set(STAGE_NAMES)
        assert all(value >= 0.0 for value in result.stage_times.values())

    def test_empty_stages_report_zero_rather_than_being_absent(self) -> None:
        result = build(detector=FakeDetector([])).process(make_image())
        assert result.stage_times["ocr"] == 0.0
        assert result.stage_times["crop"] == 0.0
        assert result.stage_times["detect"] > 0.0

    def test_total_covers_the_individual_stages(self) -> None:
        detector = FakeDetector([make_detection(0, 0, 40, 20)])
        result = build(detector=detector).process(make_image())
        stages = result.stage_times
        parts = stages["detect"] + stages["crop"] + stages["ocr"] + stages["normalize"]
        assert stages["total"] >= parts
        assert result.total_time == stages["total"]

    def test_per_plate_time_is_recorded(self) -> None:
        detector = FakeDetector([make_detection(0, 0, 40, 20)])
        result = build(detector=detector).process(make_image())
        assert result.results[0].processing_time > 0.0


# --------------------------------------------------------------------- #
# Warm-up
# --------------------------------------------------------------------- #
class TestWarmup:
    def test_warms_up_both_models(self) -> None:
        detector, recognizer = FakeDetector(), FakeRecognizer()
        build(detector=detector, recognizer=recognizer).warmup()
        assert detector.warmup_calls == 1
        assert recognizer.warmup_calls == 1

    def test_a_failing_warmup_does_not_block_start_up(self) -> None:
        class ExplodingDetector(FakeDetector):
            def warmup(self) -> None:
                raise RuntimeError("cannot warm up")

        recognizer = FakeRecognizer()
        build(detector=ExplodingDetector(), recognizer=recognizer).warmup()
        assert recognizer.warmup_calls == 1, "the second stage must still be warmed"
