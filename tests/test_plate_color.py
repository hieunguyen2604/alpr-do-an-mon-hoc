"""Tests for background-colour classification of plate crops."""

from __future__ import annotations

import numpy as np
import pytest

from ai.inference.plate_color import (
    MIN_DOMINANT_FRACTION,
    ColorEstimate,
    PlateColor,
    classify_plate_color,
)

# BGR, matching what OpenCV hands the classifier.
_WHITE = (245, 245, 245)
_YELLOW = (30, 200, 235)
_BLUE = (150, 70, 30)
_RED = (40, 40, 200)
_BLACK = (20, 20, 20)


def make_plate(
    background: tuple[int, int, int],
    characters: tuple[int, int, int] = _BLACK,
    width: int = 200,
    height: int = 60,
) -> np.ndarray:
    """Build a plate-like image: a coloured field with darker character bars."""
    image = np.full((height, width, 3), background, dtype=np.uint8)
    for index in range(5):
        left = int(width * (0.12 + index * 0.16))
        image[int(height * 0.25) : int(height * 0.75), left : left + int(width * 0.05)] = characters
    return image


class TestDominantColours:
    @pytest.mark.parametrize(
        ("background", "expected"),
        [
            (_WHITE, PlateColor.WHITE),
            (_YELLOW, PlateColor.YELLOW),
            (_BLUE, PlateColor.BLUE),
            (_RED, PlateColor.RED),
        ],
    )
    def test_names_each_plate_background(
        self, background: tuple[int, int, int], expected: PlateColor
    ) -> None:
        estimate = classify_plate_color(make_plate(background))
        assert estimate.color is expected
        assert estimate.confidence >= MIN_DOMINANT_FRACTION

    def test_light_characters_on_a_dark_field_do_not_flip_the_verdict(self) -> None:
        """Army and state plates carry white characters on a coloured field."""
        estimate = classify_plate_color(make_plate(_RED, characters=_WHITE))
        assert estimate.color is PlateColor.RED

    def test_a_diplomatic_plate_reads_as_white(self) -> None:
        """Red serial letters on white must not outvote the white background."""
        estimate = classify_plate_color(make_plate(_WHITE, characters=_RED))
        assert estimate.color is PlateColor.WHITE

    def test_reports_the_evidence_behind_the_verdict(self) -> None:
        estimate = classify_plate_color(make_plate(_YELLOW))
        assert estimate.fractions[PlateColor.YELLOW] > estimate.fractions[PlateColor.WHITE]
        assert estimate.label == "Nền vàng"


class TestBorderContamination:
    def test_surrounding_bodywork_does_not_decide_the_colour(self) -> None:
        """A loose crop puts car paint in the outer band; the centre must win."""
        plate = make_plate(_WHITE, width=240, height=80)
        plate[:12, :] = _RED
        plate[-12:, :] = _RED
        plate[:, :30] = _RED
        plate[:, -30:] = _RED

        assert classify_plate_color(plate).color is PlateColor.WHITE


class TestUnreadableInput:
    @pytest.mark.parametrize(
        "image",
        [
            np.zeros((0, 0, 3), dtype=np.uint8),
            np.zeros((10, 10), dtype=np.uint8),
            np.zeros((10, 10, 4), dtype=np.uint8),
        ],
        ids=["empty", "grayscale", "four-channel"],
    )
    def test_unusable_arrays_return_unknown_without_raising(self, image: np.ndarray) -> None:
        """An unreadable colour is a normal outcome, exactly like an unreadable plate."""
        estimate = classify_plate_color(image)
        assert estimate.color is PlateColor.UNKNOWN
        assert estimate.confidence == 0.0

    def test_none_returns_unknown(self) -> None:
        assert classify_plate_color(None).color is PlateColor.UNKNOWN  # type: ignore[arg-type]

    def test_a_dark_frame_is_unknown_rather_than_guessed(self) -> None:
        """Under-exposure must not be reported as a colour the system cannot see."""
        estimate = classify_plate_color(np.full((60, 200, 3), (10, 10, 10), dtype=np.uint8))
        assert estimate.color is PlateColor.UNKNOWN

    def test_a_crop_too_small_to_inset_is_still_classified(self) -> None:
        """Trimming must not produce an empty slice on a tiny crop."""
        estimate = classify_plate_color(np.full((3, 3, 3), _YELLOW, dtype=np.uint8))
        assert isinstance(estimate, ColorEstimate)
