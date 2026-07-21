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
from ai.inference.pipeline import (
    STAGE_NAMES,
    ALPRPipeline,
    refine_kind_with_color,
    retry_skewed_variants,
    should_retry_skewed,
)
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
    config: InferenceConfig | None = None,
) -> ALPRPipeline:
    """Assemble a pipeline from fakes, filling in defaults."""
    return ALPRPipeline(
        detector=detector or FakeDetector(),
        recognizer=recognizer or FakeRecognizer(),
        normalizer=normalizer or FakeNormalizer(),
        config=config or InferenceConfig(model_path="models/best.pt"),
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
        detector = FakeDetector([make_detection(10, 10, 60, 20), make_detection(90, 40, 50, 20)])
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
        result = build(detector=detector, normalizer=ExplodingNormalizer()).process(make_image())
        recognition = result.results[0].recognition
        assert recognition is not None, "the plate must survive a normalizer crash"
        assert recognition.text == "51F73420"

    def test_a_box_outside_the_image_is_skipped_not_fatal(self) -> None:
        detector = FakeDetector([make_detection(500, 500, 40, 20)])
        recognizer = FakeRecognizer()
        result = build(detector=detector, recognizer=recognizer).process(make_image(200, 100))
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


# --------------------------------------------------------------------- #
# Two-line rescue: re-reading the upper half after a failed strip read
# --------------------------------------------------------------------- #
class TwoLineRecognizer(BaseRecognizer):
    """Reproduces the strip failure mode: the upper line is lost, alone it reads.

    Call 1 is the merged strip, which the real engine sometimes reads as the
    lower line only. Every later call is the upper half on its own, which reads
    correctly -- exactly the asymmetry the rescue path exists to exploit.
    """

    def __init__(self, strip_text: str = "01566", upper_text: str = "29E") -> None:
        self._strip_text = strip_text
        self._upper_text = upper_text
        self.calls = 0
        self.warmup_calls = 0

    @property
    def name(self) -> str:
        return "two-line-recognizer"

    def recognize(self, plate_image: ImageArray) -> PlateRecognition:
        self.calls += 1
        text = self._strip_text if self.calls == 1 else self._upper_text
        return PlateRecognition(
            text=text,
            raw_text=text,
            confidence=0.9,
            line_count=2 if self.calls == 1 else 1,
            is_valid_format=False,
        )

    def warmup(self) -> None:
        self.warmup_calls += 1


class LengthNormalizer(BaseNormalizer):
    """Accepts a string only once it is long enough to be a plate.

    Stands in for the real format rules: `01566` alone is rejected, and the
    same string with its province code and serial letter restored is accepted.
    """

    def __init__(self, minimum_length: int = 8) -> None:
        self.minimum_length = minimum_length
        self.received: list[str] = []

    def normalize(self, raw_text: str) -> tuple[str, bool]:
        self.received.append(raw_text)
        cleaned = raw_text.replace("-", "").replace(".", "")
        return cleaned, len(cleaned) >= self.minimum_length


class TestTwoLineRescue:
    def test_recovers_a_plate_whose_upper_line_was_lost(self) -> None:
        recognizer = TwoLineRecognizer()
        detector = FakeDetector([make_detection(10, 10, 60, 40)])

        result = build(
            detector=detector, recognizer=recognizer, normalizer=LengthNormalizer()
        ).process(make_image())

        recognition = result.results[0].recognition
        assert recognition is not None
        assert recognition.text == "29E01566", "the upper fragment must be prepended"
        assert recognition.is_valid_format is True
        assert recognizer.calls == 2, "exactly one extra OCR call, not a full re-run"

    def test_a_valid_first_read_is_never_retried(self) -> None:
        recognizer = TwoLineRecognizer(strip_text="29E01566")
        detector = FakeDetector([make_detection(10, 10, 60, 40)])

        result = build(
            detector=detector, recognizer=recognizer, normalizer=LengthNormalizer()
        ).process(make_image())

        assert recognizer.calls == 1, "a plate that already validated must not be re-read"
        assert result.results[0].recognition is not None
        assert result.results[0].recognition.text == "29E01566"

    def test_keeps_the_first_result_when_the_retry_still_fails(self) -> None:
        recognizer = TwoLineRecognizer(strip_text="01566", upper_text="")
        detector = FakeDetector([make_detection(10, 10, 60, 40)])

        result = build(
            detector=detector, recognizer=recognizer, normalizer=LengthNormalizer()
        ).process(make_image())

        recognition = result.results[0].recognition
        assert recognition is not None
        assert recognition.text == "01566", "a failed rescue must not overwrite the original"
        assert recognition.is_valid_format is False

    def test_a_raising_retry_does_not_lose_the_plate(self) -> None:
        class ExplodingOnRetry(TwoLineRecognizer):
            def recognize(self, plate_image: ImageArray) -> PlateRecognition:
                if self.calls >= 1:
                    self.calls += 1
                    raise RecognitionError("retry exploded")
                return super().recognize(plate_image)

        result = build(
            detector=FakeDetector([make_detection(10, 10, 60, 40)]),
            recognizer=ExplodingOnRetry(),
            normalizer=LengthNormalizer(),
        ).process(make_image())

        recognition = result.results[0].recognition
        assert recognition is not None, "a failed rescue must never drop the detection"
        assert recognition.text == "01566"

    def test_a_hesitant_upper_fragment_is_not_prepended(self) -> None:
        """The 21/07/2026 '81B-9458' case: a low-confidence fragment must not
        be bent into a legal plate by position repair. Correct fragments
        measure >= 0.95; the floor is 0.9."""

        class HesitantUpper(TwoLineRecognizer):
            def recognize(self, plate_image: ImageArray) -> PlateRecognition:
                result = super().recognize(plate_image)
                if self.calls > 1:  # the upper-half retry reads
                    return PlateRecognition(
                        text=result.text, raw_text=result.raw_text,
                        confidence=0.7, line_count=result.line_count,
                        is_valid_format=False,
                    )
                return result

        result = build(
            detector=FakeDetector([make_detection(10, 10, 60, 40)]),
            recognizer=HesitantUpper(),
            normalizer=LengthNormalizer(),
        ).process(make_image())

        recognition = result.results[0].recognition
        assert recognition is not None
        assert recognition.text == "01566", "a 0.7-confidence fragment must be discarded"
        assert recognition.is_valid_format is False

    def test_single_line_plates_are_never_retried(self) -> None:
        recognizer = FakeRecognizer(text="51F1")
        result = build(
            detector=FakeDetector([make_detection(10, 10, 60, 40)]),
            recognizer=recognizer,
            normalizer=LengthNormalizer(),
        ).process(make_image())

        assert recognizer.calls == 1, "the rescue is scoped to two-line plates only"
        assert result.results[0].recognition is not None

    def test_the_rescue_still_reports_family_and_display_text(self) -> None:
        """A rescued plate is a different string, so both must be recomputed.

        Carrying the failed attempt's classification forward would describe a
        plate number that no longer exists — and leaving them empty, as the
        first version of the rescue did, silently stripped the very fields the
        interface uses to avoid mislabelling a plate.
        """

        class KindAwareNormalizer(LengthNormalizer):
            def normalize_detailed(self, raw_text: str, line_count: int | None = None) -> object:
                cleaned, valid = self.normalize(raw_text)

                class _Kind:
                    value = "car"

                class _Decision:
                    kind = _Kind()

                class _Outcome:
                    text = cleaned
                    is_valid_format = valid
                    decision = _Decision()

                return _Outcome()

            def format_for_display(self, text: str, line_count: int | None = None) -> str:
                return f"{text[:3]}-{text[3:6]}.{text[6:]}"

        result = build(
            detector=FakeDetector([make_detection(10, 10, 60, 40)]),
            recognizer=TwoLineRecognizer(),
            normalizer=KindAwareNormalizer(),
        ).process(make_image())

        recognition = result.results[0].recognition
        assert recognition is not None
        assert recognition.text == "29E01566"
        assert recognition.kind == "car", "the rescued string must be reclassified"
        assert recognition.display_text == "29E-015.66"


# --------------------------------------------------------------------- #
# Skew retry ladder: re-reading a failed crop through corrected variants
# --------------------------------------------------------------------- #
def make_flat_image(width: int = 400, height: int = 200) -> ImageArray:
    """A uniform image, so ``rectify_plate`` is a guaranteed no-op.

    The retry tests must control exactly which variant fires. On a uniform
    crop the dominant blob is the whole crop at angle zero, so the deskew
    variant is skipped and only geometry chosen by the test (the crop's
    aspect ratio) decides whether the stretch variant runs.
    """
    return np.full((height, width, 3), 128, dtype=np.uint8)


class ForeshortenedRecognizer(BaseRecognizer):
    """Reproduces the measured 6.3.9 case (frame 168 of the demo video).

    The raw crop (call 1, ratio over the two-line threshold) reads empty. The
    vertically stretched variant (call 2) reads the lower line only. The
    rescue's upper-half calls (3+) read the upper line. Only the full chain
    retry -> variant read -> upper rescue assembles the whole plate.
    """

    def __init__(self, lower_text: str = "4374", upper_text: str = "77H5") -> None:
        self._lower_text = lower_text
        self._upper_text = upper_text
        self.calls = 0
        self.warmup_calls = 0

    @property
    def name(self) -> str:
        return "foreshortened-recognizer"

    def recognize(self, plate_image: ImageArray) -> PlateRecognition:
        self.calls += 1
        if self.calls == 1:
            return PlateRecognition(
                text="", raw_text="", confidence=0.0, line_count=1, is_valid_format=False
            )
        if self.calls == 2:
            return PlateRecognition(
                text=self._lower_text,
                raw_text=self._lower_text,
                confidence=0.9,
                line_count=2,
                is_valid_format=False,
            )
        return PlateRecognition(
            text=self._upper_text,
            raw_text=self._upper_text,
            confidence=0.95,
            line_count=1,
            is_valid_format=False,
        )

    def warmup(self) -> None:
        self.warmup_calls += 1


class TestShouldRetrySkewed:
    def test_a_missing_recognition_is_not_retried(self) -> None:
        assert should_retry_skewed(None) is False

    def test_a_valid_read_is_not_retried(self) -> None:
        valid = PlateRecognition(
            text="51G31691", raw_text="51G-316.91", confidence=0.9,
            line_count=1, is_valid_format=True,
        )
        assert should_retry_skewed(valid) is False

    def test_an_empty_read_is_retried(self) -> None:
        empty = PlateRecognition(
            text="", raw_text="", confidence=0.0, line_count=1, is_valid_format=False
        )
        assert should_retry_skewed(empty) is True

    def test_a_recognised_military_plate_is_never_retried(self) -> None:
        """The 21/07/2026 field regression, pinned.

        A military plate is read correctly and deliberately reported invalid
        (recognise-to-exclude). The first ladder treated that as a failed read,
        re-read the crop through a stretched variant, and OCR smeared
        ``KV-69-38`` into ``14D7-069.38`` -- a valid-looking civilian
        motorcycle. Any read the classifier placed in a family is a finding,
        not a failure.
        """
        military = PlateRecognition(
            text="KV6938", raw_text="KV-69-38", confidence=0.89,
            line_count=1, is_valid_format=False, kind="military",
        )
        assert should_retry_skewed(military) is False


class TestSkewRetryLadder:
    def test_recovers_a_foreshortened_two_line_plate(self) -> None:
        """The full 6.3.9 chain: empty read, stretch, lower line, upper rescue."""
        recognizer = ForeshortenedRecognizer()
        # 140x40 crop: ratio 3.5, inside the stretch band [2.5, 4.2].
        detector = FakeDetector([make_detection(10, 10, 140, 40)])

        result = build(
            detector=detector, recognizer=recognizer, normalizer=LengthNormalizer()
        ).process(make_flat_image())

        recognition = result.results[0].recognition
        assert recognition is not None
        assert recognition.text == "77H54374"
        assert recognition.is_valid_format is True
        assert recognizer.calls == 3, "raw read + stretched read + one rescue call"

    def test_the_ladder_is_off_when_rectify_is_disabled(self) -> None:
        recognizer = ForeshortenedRecognizer()
        detector = FakeDetector([make_detection(10, 10, 140, 40)])

        result = build(
            detector=detector,
            recognizer=recognizer,
            normalizer=LengthNormalizer(),
            config=InferenceConfig(model_path="models/best.pt", rectify_enabled=False),
        ).process(make_flat_image())

        recognition = result.results[0].recognition
        assert recognition is not None
        assert recognition.text == ""
        assert recognizer.calls == 1, "the ablation switch must silence every retry"

    def test_a_wide_one_line_crop_is_not_stretched(self) -> None:
        """Ratio 5.0 is beyond RETRY_STRETCH_MAX_RATIO: a real one-line plate
        whose read failed for other reasons must not cost stretch calls."""
        recognizer = ForeshortenedRecognizer()
        detector = FakeDetector([make_detection(10, 10, 200, 40)])

        result = build(
            detector=detector, recognizer=recognizer, normalizer=LengthNormalizer()
        ).process(make_flat_image())

        assert recognizer.calls == 1
        recognition = result.results[0].recognition
        assert recognition is not None
        assert recognition.text == ""

    def test_a_retry_that_still_fails_keeps_the_first_result(self) -> None:
        """The accept criterion is validation; junk from a variant is discarded."""
        recognizer = ForeshortenedRecognizer(lower_text="999", upper_text="")
        detector = FakeDetector([make_detection(10, 10, 140, 40)])

        result = build(
            detector=detector, recognizer=recognizer, normalizer=LengthNormalizer()
        ).process(make_flat_image())

        recognition = result.results[0].recognition
        assert recognition is not None
        assert recognition.text == "", "an invalid variant read must never replace the original"
        assert recognition.is_valid_format is False

    def test_a_red_plate_is_never_retried(self) -> None:
        """Defence in depth for the military flip: red backgrounds exist only
        on army plates, so even an unclassified failed read off a red crop
        must not be re-read into a 'valid' civil string."""
        recognizer = ForeshortenedRecognizer()
        failed = PlateRecognition(
            text="", raw_text="", confidence=0.0, line_count=1, is_valid_format=False
        )

        outcome = retry_skewed_variants(
            recognizer,
            LengthNormalizer(),
            make_flat_image(140, 40),
            failed,
            color="red",
        )

        assert outcome is failed, "the original read must come back untouched"
        assert recognizer.calls == 0, "not a single OCR call may be spent on a red crop"

    def test_a_military_first_read_stops_the_ladder_in_the_pipeline(self) -> None:
        """End-to-end pin of the KV-69-38 regression through process()."""

        class MilitaryNormalizer(LengthNormalizer):
            def normalize_detailed(self, raw_text: str, line_count: int | None = None) -> object:
                class _Kind:
                    value = "military"

                class _Decision:
                    kind = _Kind()

                class _Outcome:
                    text = "KV6938"
                    is_valid_format = False
                    decision = _Decision()

                return _Outcome()

        recognizer = ForeshortenedRecognizer()
        # Ratio 3.5: squarely inside the stretch band, so only the kind gate
        # can be what stops the retry.
        detector = FakeDetector([make_detection(10, 10, 140, 40)])

        result = build(
            detector=detector, recognizer=recognizer, normalizer=MilitaryNormalizer()
        ).process(make_flat_image())

        recognition = result.results[0].recognition
        assert recognition is not None
        assert recognition.text == "KV6938"
        assert recognition.kind == "military"
        assert recognition.is_valid_format is False
        assert recognizer.calls == 1, "a recognised military read must never be re-read"


# --------------------------------------------------------------------- #
# Resolving a string-level ambiguity with the plate's colour
# --------------------------------------------------------------------- #
class _Kind:
    """Minimal stand-in for ``PlateKind``: anything with a ``.value``."""

    def __init__(self, value: str) -> None:
        self.value = value


class _Decision:
    def __init__(self, kind: str, candidates: tuple[str, ...]) -> None:
        self.kind = _Kind(kind)
        self.candidates = tuple(_Kind(name) for name in candidates)


class _Outcome:
    def __init__(self, kind: str, candidates: tuple[str, ...]) -> None:
        self.decision = _Decision(kind, candidates)


_AMBIGUOUS = ("car", "motorcycle_old", "blue_car", "blue_motorcycle")


class TestColorResolvesKindAmbiguity:
    def test_blue_promotes_a_car_to_a_state_plate(self) -> None:
        """`80A-123.45` is a legal string for both a private and a State car."""
        outcome = _Outcome("car", _AMBIGUOUS)
        assert refine_kind_with_color(outcome, "blue", 1) == "blue_car"

    def test_blue_promotes_a_motorcycle_by_line_count(self) -> None:
        outcome = _Outcome("motorcycle_old", _AMBIGUOUS)
        assert refine_kind_with_color(outcome, "blue", 2) == "blue_motorcycle"

    @pytest.mark.parametrize("color", ["white", "yellow", "unknown", ""])
    def test_other_colours_leave_the_string_verdict_alone(self, color: str) -> None:
        """Only blue carries family evidence; yellow is handled at the label layer."""
        outcome = _Outcome("car", _AMBIGUOUS)
        assert refine_kind_with_color(outcome, color, 1) == "car"

    @pytest.mark.parametrize("kind", ["military", "diplomatic", "special"])
    def test_colour_cannot_overrule_an_unambiguous_string(self, kind: str) -> None:
        """A misread colour must not be able to reclassify a definite reading.

        An army plate whose crop is misjudged as blue stays an army plate: the
        colour may only promote a family the character rules already listed as
        plausible.
        """
        outcome = _Outcome(kind, (kind,))
        assert refine_kind_with_color(outcome, "blue", 1) == kind

    def test_a_two_line_plate_can_still_be_a_state_car(self) -> None:
        """Two lines does not imply a motorcycle, and assuming so lost real plates.

        `65A-004.50` is a two-line State **car** plate; QCVN 08:2024/BCA defines
        the 330x165 two-line car format precisely so that it can exist. An
        earlier version of the refinement chose between `blue_car` and
        `blue_motorcycle` by line count, and therefore refused to promote exactly
        the plates it was written for -- found by running the real image, not by
        review.
        """
        outcome = _Outcome("car", ("car", "blue_car"))
        assert refine_kind_with_color(outcome, "blue", 2) == "blue_car"

    def test_promotion_never_crosses_the_vehicle_class(self) -> None:
        """Colour says nothing about car versus motorcycle; the serial pattern does."""
        outcome = _Outcome("motorcycle_old", _AMBIGUOUS)
        assert refine_kind_with_color(outcome, "blue", 1) == "blue_motorcycle"

    def test_an_outcome_without_a_classification_is_handled(self) -> None:
        """`BaseNormalizer` promises only `normalize`; absence must not raise."""
        assert refine_kind_with_color(object(), "blue", 1) == ""
