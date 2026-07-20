"""Unit tests for the two-line plate handling helpers.

These cover the geometry of :mod:`ai.inference.two_line` -- the module that
carries risk R-04. They use synthetic arrays only, so they run fast and need no
OCR engine, no model weights and no network.
"""

from __future__ import annotations

import numpy as np
import pytest

from ai.inference.exceptions import InvalidImageError
from ai.inference.two_line import (
    LOWER_HALF_START_RATIO,
    MIN_MERGE_HEIGHT,
    UPPER_HALF_END_RATIO,
    estimate_line_count,
    merge_two_line,
    preprocess_plate,
    split_two_line,
)
from ai.inference.types import BoundingBox


def _image(height: int, width: int, channels: int = 3) -> np.ndarray:
    """Build a mid-grey test image of a given size.

    Args:
        height: Image height in pixels.
        width: Image width in pixels.
        channels: Number of channels; ``0`` yields a 2-D grayscale array.

    Returns:
        A ``uint8`` array filled with 128.
    """
    shape = (height, width) if channels == 0 else (height, width, channels)
    return np.full(shape, 128, dtype=np.uint8)


class TestEstimateLineCount:
    """Aspect-ratio based classification of one-line versus two-line plates."""

    @pytest.mark.parametrize(
        ("width", "height", "aspect_ratio", "expected_lines", "plate_type"),
        [
            (190, 140, 1.357, 2, "motorcycle 190x140mm"),
            (330, 165, 2.000, 2, "car short plate 330x165mm"),
            (520, 110, 4.727, 1, "car long plate 520x110mm"),
        ],
    )
    def test_matches_qcvn_plate_dimensions(
        self,
        width: int,
        height: int,
        aspect_ratio: float,
        expected_lines: int,
        plate_type: str,
    ) -> None:
        """The three plate sizes of QCVN 08:2024/BCA classify correctly."""
        assert width / height == pytest.approx(aspect_ratio, abs=0.01), plate_type
        assert estimate_line_count(_image(height, width)) == expected_lines

    def test_accepts_a_bounding_box(self) -> None:
        """A BoundingBox is classified from its own aspect ratio."""
        assert estimate_line_count(BoundingBox(x=0, y=0, width=190, height=140)) == 2
        assert estimate_line_count(BoundingBox(x=5, y=7, width=520, height=110)) == 1

    def test_threshold_is_exclusive_on_the_two_line_side(self) -> None:
        """A ratio exactly at the threshold counts as one line."""
        assert estimate_line_count(_image(100, 250), threshold=2.5) == 1
        assert estimate_line_count(_image(100, 249), threshold=2.5) == 2

    def test_custom_threshold_shifts_the_decision(self) -> None:
        """The cut-off is a parameter, not a hard-coded constant."""
        square_ish = _image(100, 300)
        assert estimate_line_count(square_ish, threshold=2.5) == 1
        assert estimate_line_count(square_ish, threshold=3.5) == 2

    def test_rejects_a_non_positive_threshold(self) -> None:
        """A meaningless threshold fails loudly."""
        with pytest.raises(ValueError, match="threshold must be positive"):
            estimate_line_count(_image(100, 300), threshold=0.0)

    def test_rejects_an_empty_image(self) -> None:
        """An empty array is an invalid image, not a zero-line plate."""
        with pytest.raises(InvalidImageError):
            estimate_line_count(np.zeros((0, 10, 3), dtype=np.uint8))


class TestSplitTwoLine:
    """Cutting a two-line crop into overlapping halves."""

    def test_halves_use_the_documented_ratios(self) -> None:
        """Upper half ends at 5h/12 and lower half starts at h/3."""
        image = _image(120, 200)
        upper, lower = split_two_line(image)

        assert upper.shape[0] == int(UPPER_HALF_END_RATIO * 120)  # 50
        assert lower.shape[0] == 120 - int(LOWER_HALF_START_RATIO * 120)  # 80
        assert upper.shape[1] == lower.shape[1] == 200

    def test_halves_overlap(self) -> None:
        """The two halves share a band, so no glyph is cut in half.

        Combined height greater than the source height is the observable
        signature of the overlap.
        """
        height = 140
        upper, lower = split_two_line(_image(height, 190))

        overlap = upper.shape[0] + lower.shape[0] - height
        assert overlap > 0
        expected_overlap = int(UPPER_HALF_END_RATIO * height) - int(LOWER_HALF_START_RATIO * height)
        assert overlap == expected_overlap

    def test_overlapping_band_holds_identical_pixels(self) -> None:
        """The shared band is the same content in both halves."""
        image = np.random.default_rng(0).integers(0, 256, size=(120, 200, 3), dtype=np.uint8)
        upper, lower = split_two_line(image)

        band_start = int(LOWER_HALF_START_RATIO * 120)
        band_end = int(UPPER_HALF_END_RATIO * 120)
        np.testing.assert_array_equal(upper[band_start:band_end], lower[: band_end - band_start])

    def test_halves_are_never_empty_for_tiny_crops(self) -> None:
        """Integer truncation cannot collapse a half to zero rows."""
        upper, lower = split_two_line(_image(2, 10))
        assert upper.shape[0] >= 1
        assert lower.shape[0] >= 1

    def test_works_on_grayscale(self) -> None:
        """A 2-D crop splits just like a 3-D one."""
        upper, lower = split_two_line(_image(120, 200, channels=0))
        assert upper.ndim == lower.ndim == 2

    def test_rejects_an_invalid_image(self) -> None:
        """Splitting nothing is an error."""
        with pytest.raises(InvalidImageError):
            split_two_line(np.zeros((0, 0, 3), dtype=np.uint8))


class TestMergeTwoLine:
    """Stacking the halves horizontally into a single-line strip."""

    def test_width_is_the_sum_and_height_is_uniform(self) -> None:
        """Merged width equals the sum of the resized halves' widths."""
        upper = _image(50, 200)
        lower = _image(80, 200)
        merged = merge_two_line(upper, lower)

        target_height = max(50, 80, MIN_MERGE_HEIGHT)
        expected_width = round(200 * target_height / 50) + round(200 * target_height / 80)

        assert merged.shape[0] == target_height
        assert merged.shape[1] == expected_width

    def test_respects_an_explicit_target_height(self) -> None:
        """A caller-supplied height wins over the default."""
        merged = merge_two_line(_image(50, 200), _image(80, 200), target_height=96)
        assert merged.shape[0] == 96

    def test_never_falls_below_the_recogniser_input_height(self) -> None:
        """Tiny halves are enlarged rather than fed to OCR undersized."""
        merged = merge_two_line(_image(10, 40), _image(12, 40))
        assert merged.shape[0] == MIN_MERGE_HEIGHT

    def test_result_is_wide_enough_to_read_as_one_line(self) -> None:
        """A motorcycle plate turns from near-square into a wide strip.

        This is the whole point of the transform: PP-OCR resizes to a fixed
        48 px height, which destroys a two-row plate but suits a wide strip.
        """
        plate = _image(140, 190)
        upper, lower = split_two_line(plate)
        merged = merge_two_line(upper, lower)

        assert plate.shape[1] / plate.shape[0] < 2.0
        assert merged.shape[1] / merged.shape[0] > 4.0

    def test_mixed_channel_halves_are_promoted_to_colour(self) -> None:
        """A grayscale half and a colour half can still be stacked."""
        merged = merge_two_line(_image(50, 200, channels=0), _image(50, 200))
        assert merged.ndim == 3
        assert merged.shape[2] == 3

    def test_rejects_a_non_positive_target_height(self) -> None:
        """An impossible target height fails loudly."""
        with pytest.raises(ValueError, match="target_height must be positive"):
            merge_two_line(_image(50, 200), _image(50, 200), target_height=0)

    def test_rejects_an_invalid_half(self) -> None:
        """Merging with an empty half is an error."""
        with pytest.raises(InvalidImageError):
            merge_two_line(_image(50, 200), np.zeros((0, 10, 3), dtype=np.uint8))


class TestPreprocessPlate:
    """Contrast and noise clean-up, with every step switchable."""

    def test_returns_bgr_even_when_converting_to_grayscale(self) -> None:
        """Downstream engines always receive three channels."""
        result = preprocess_plate(_image(60, 200))
        assert result.ndim == 3
        assert result.shape[2] == 3
        assert result.dtype == np.uint8

    def test_does_not_modify_the_input(self) -> None:
        """Pre-processing works on a copy."""
        image = np.random.default_rng(1).integers(0, 256, size=(60, 200, 3), dtype=np.uint8)
        original = image.copy()
        preprocess_plate(image)
        np.testing.assert_array_equal(image, original)

    def test_every_step_can_be_disabled(self) -> None:
        """With all steps off the crop passes through unchanged."""
        image = np.random.default_rng(2).integers(0, 256, size=(60, 200, 3), dtype=np.uint8)
        result = preprocess_plate(image, to_grayscale=False, apply_clahe=False, denoise=False)
        np.testing.assert_array_equal(result, image)

    def test_clahe_changes_a_low_contrast_crop(self) -> None:
        """CLAHE is actually applied, not silently skipped."""
        rng = np.random.default_rng(3)
        low_contrast = rng.integers(100, 140, size=(60, 200, 3), dtype=np.uint8)

        without = preprocess_plate(low_contrast, apply_clahe=False, denoise=False)
        with_clahe = preprocess_plate(low_contrast, apply_clahe=True, denoise=False)

        assert with_clahe.std() > without.std()

    def test_upscale_enlarges_small_crops_only(self) -> None:
        """Small crops grow to the requested height; large ones are untouched."""
        small = preprocess_plate(_image(20, 100), upscale_to_height=64)
        assert small.shape[0] == 64
        assert small.shape[1] == round(100 * 64 / 20)

        large = preprocess_plate(_image(120, 400), upscale_to_height=64)
        assert large.shape[0] == 120

    def test_rejects_invalid_parameters(self) -> None:
        """Bad tuning values fail loudly instead of silently misbehaving."""
        image = _image(60, 200)
        with pytest.raises(ValueError, match="clahe_clip_limit must be positive"):
            preprocess_plate(image, clahe_clip_limit=0.0)
        with pytest.raises(ValueError, match="clahe_tile_grid_size"):
            preprocess_plate(image, clahe_tile_grid_size=(0, 8))
        with pytest.raises(ValueError, match="upscale_to_height must be positive"):
            preprocess_plate(image, upscale_to_height=-1)

    def test_rejects_an_invalid_image(self) -> None:
        """An unusable crop is reported, not processed."""
        with pytest.raises(InvalidImageError):
            preprocess_plate(np.zeros((0, 10, 3), dtype=np.uint8))
