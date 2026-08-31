"""Unit tests for the two-line plate handling helpers."""

from __future__ import annotations

import cv2
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
    rectify_plate,
    split_two_line,
    stretch_vertical,
)
from ai.inference.types import BoundingBox


def _image(height: int, width: int, channels: int = 3) -> np.ndarray:
    """Build a mid-grey test image of a given size."""
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
        """The two halves share a band, so no glyph is cut in half."""
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
        """A motorcycle plate turns from near-square into a wide strip."""
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


def _synthetic_plate(width: int, height: int) -> np.ndarray:
    """Draw a bright plate with two dark text rows on a plain background."""
    plate = np.full((height, width, 3), 235, dtype=np.uint8)
    cv2.rectangle(plate, (0, 0), (width - 1, height - 1), (40, 40, 40), 3)
    cv2.putText(
        plate, "59-X1", (18, int(height * 0.42)),
        cv2.FONT_HERSHEY_SIMPLEX, height / 130.0, (20, 20, 20), 4,
    )
    cv2.putText(
        plate, "39458", (14, int(height * 0.86)),
        cv2.FONT_HERSHEY_SIMPLEX, height / 130.0, (20, 20, 20), 4,
    )
    return plate


def _skewed_crop(plate: np.ndarray, angle_degrees: float) -> np.ndarray:
    """Rotate a plate and cut its axis-aligned bounding box, like YOLO does."""
    height, width = plate.shape[:2]
    diagonal = int(np.hypot(height, width)) + 20
    background = np.full((diagonal, diagonal, 3), 90, dtype=np.uint8)
    y0, x0 = (diagonal - height) // 2, (diagonal - width) // 2
    background[y0 : y0 + height, x0 : x0 + width] = plate
    matrix = cv2.getRotationMatrix2D((diagonal / 2, diagonal / 2), angle_degrees, 1.0)
    rotated = cv2.warpAffine(background, matrix, (diagonal, diagonal), borderValue=(90, 90, 90))
    gray = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)
    ys, xs = np.where(gray > 150)
    return rotated[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]


class TestRectifyPlate:
    """Deskewing, the step the two-line design always began with (6.4.9)."""

    @pytest.mark.parametrize("angle", [-25.0, -12.0, 12.0, 25.0])
    def test_recovers_the_true_aspect_ratio_of_a_skewed_motorcycle_plate(
        self, angle: float
    ) -> None:
        """Both skew directions come back near the 190x140 physical ratio."""
        crop = _skewed_crop(_synthetic_plate(190, 140), angle)
        rectified = rectify_plate(crop)
        ratio = rectified.shape[1] / rectified.shape[0]
        assert 1.15 <= ratio <= 1.55

    @pytest.mark.parametrize("angle", [-20.0, 20.0])
    def test_fixes_the_line_count_of_a_skewed_one_line_plate(self, angle: float) -> None:
        """The measured 6.3.9 failure inverted: a skewed 110x520 car plate's"""
        crop = _skewed_crop(_synthetic_plate(520, 110), angle)
        assert estimate_line_count(crop) == 2  # the pre-rectify misclassification
        rectified = rectify_plate(crop)
        assert estimate_line_count(rectified) == 1

    def test_frontal_crop_is_returned_unchanged(self) -> None:
        """Below the minimum angle the crop must stay bit-identical -- this is"""
        plate = _synthetic_plate(190, 140)
        assert rectify_plate(plate) is plate

    def test_featureless_crop_is_returned_unchanged(self) -> None:
        """No dominant blob means no trustworthy estimate, so no correction."""
        noise = np.random.default_rng(7).integers(0, 256, size=(80, 110, 3), dtype=np.uint8)
        result = rectify_plate(noise)
        assert result.shape == noise.shape

    def test_grayscale_input_is_accepted(self) -> None:
        """The helper mirrors the module's grayscale-or-BGR contract."""
        crop = cv2.cvtColor(_skewed_crop(_synthetic_plate(190, 140), 15.0), cv2.COLOR_BGR2GRAY)
        rectified = rectify_plate(crop)
        assert rectified.ndim == 2
        assert 1.15 <= rectified.shape[1] / rectified.shape[0] <= 1.55

    def test_rejects_invalid_bounds(self) -> None:
        """Misordered or non-positive angle bounds fail loudly."""
        plate = _synthetic_plate(190, 140)
        with pytest.raises(ValueError, match="positive"):
            rectify_plate(plate, min_angle_degrees=0.0)
        with pytest.raises(ValueError, match="below"):
            rectify_plate(plate, min_angle_degrees=40.0, max_angle_degrees=10.0)

    def test_rejects_an_invalid_image(self) -> None:
        """An unusable crop is reported, not processed."""
        with pytest.raises(InvalidImageError):
            rectify_plate(np.zeros((0, 10, 3), dtype=np.uint8))


class TestStretchVertical:
    """The foreshortening counter-move used by the skew retry ladder."""

    def test_doubles_the_height_and_keeps_the_width(self) -> None:
        stretched = stretch_vertical(_image(40, 140), factor=2.0)
        assert stretched.shape[0] == 80
        assert stretched.shape[1] == 140

    def test_moves_an_ambiguous_ratio_into_two_line_territory(self) -> None:
        """The whole point: ratio 3.5 is 'one line', stretched it splits."""
        crop = _image(40, 140)
        assert estimate_line_count(crop) == 1
        assert estimate_line_count(stretch_vertical(crop)) == 2

    def test_rejects_a_non_stretching_factor(self) -> None:
        with pytest.raises(ValueError, match="greater than 1"):
            stretch_vertical(_image(40, 140), factor=1.0)

    def test_rejects_an_invalid_image(self) -> None:
        with pytest.raises(InvalidImageError):
            stretch_vertical(np.zeros((0, 10, 3), dtype=np.uint8))
