"""Classify the background colour of a cropped Vietnamese license plate (TT 79/2024)."""

from __future__ import annotations

from enum import StrEnum
from typing import Final

import cv2
import numpy as np

from ai.inference.types import ImageArray

__all__ = [
    "CENTRE_INSET",
    "MIN_DOMINANT_FRACTION",
    "PlateColor",
    "ColorEstimate",
    "classify_plate_color",
]


class PlateColor(StrEnum):
    """Background colours a Vietnamese plate can carry."""

    WHITE = "white"
    YELLOW = "yellow"
    BLUE = "blue"
    RED = "red"
    UNKNOWN = "unknown"


VIETNAMESE_LABELS: Final[dict[PlateColor, str]] = {
    PlateColor.WHITE: "Nền trắng",
    PlateColor.YELLOW: "Nền vàng",
    PlateColor.BLUE: "Nền xanh",
    PlateColor.RED: "Nền đỏ",
    PlateColor.UNKNOWN: "Không xác định",
}
"""User-facing Vietnamese labels, kept next to the enum so the two cannot drift."""


CENTRE_INSET: Final[float] = 0.18
"""Fraction trimmed from each edge before sampling.

A detector box includes surrounding bodywork often enough that the outer band is
not reliably plate. Trimming 18% per side keeps roughly the middle two-thirds in
each axis -- enough pixels for a stable histogram, tight enough that a coloured
car body behind a white plate cannot dominate the vote.
"""

MIN_DOMINANT_FRACTION: Final[float] = 0.30
"""Share of sampled pixels the winning band must reach to be named.

Set from the failure direction that matters: naming a colour wrongly is worse
than admitting ignorance, because a wrong colour asserts a vehicle class the
system cannot back up.
"""

# HSV bands in OpenCV's ranges: H 0-179, S 0-255, V 0-255.
_YELLOW_HUE: Final[tuple[int, int]] = (15, 42)
_BLUE_HUE: Final[tuple[int, int]] = (90, 138)
_RED_HUE_LOW: Final[tuple[int, int]] = (0, 10)
_RED_HUE_HIGH: Final[tuple[int, int]] = (165, 179)

_CHROMATIC_MIN_SATURATION: Final[int] = 70
"""Below this, a pixel is grey rather than coloured, whatever its hue says.

Hue is meaningless at low saturation -- a near-grey pixel still reports some
hue, and without this gate the noise in a white plate would be distributed
across the coloured bands.
"""

_CHROMATIC_MIN_VALUE: Final[int] = 45
"""Below this a pixel is shadow; its hue is unreliable and it is ignored."""

_WHITE_MAX_SATURATION: Final[int] = 65
_WHITE_MIN_VALUE: Final[int] = 105


class ColorEstimate:
    """The classification of one crop, with the evidence behind it."""

    __slots__ = ("color", "confidence", "fractions")

    def __init__(
        self,
        color: PlateColor,
        confidence: float,
        fractions: dict[PlateColor, float],
    ) -> None:
        self.color = color
        self.confidence = confidence
        self.fractions = fractions

    @property
    def label(self) -> str:
        """Return the Vietnamese label for :attr:`color`."""
        return VIETNAMESE_LABELS[self.color]

    def __repr__(self) -> str:
        return f"ColorEstimate(color={self.color.value!r}, confidence={self.confidence:.3f})"


def _centre_region(image: ImageArray) -> ImageArray:
    """Trim :data:`CENTRE_INSET` from every edge."""
    height, width = image.shape[:2]
    inset_y = int(height * CENTRE_INSET)
    inset_x = int(width * CENTRE_INSET)
    if height - 2 * inset_y < 2 or width - 2 * inset_x < 2:
        return image
    return image[inset_y : height - inset_y, inset_x : width - inset_x]


def classify_plate_color(plate_image: ImageArray) -> ColorEstimate:
    """Name the background colour of a cropped plate."""
    empty = dict.fromkeys(PlateColor, 0.0)

    if plate_image is None or plate_image.size == 0:
        return ColorEstimate(PlateColor.UNKNOWN, 0.0, empty)
    if plate_image.ndim != 3 or plate_image.shape[2] != 3:
        return ColorEstimate(PlateColor.UNKNOWN, 0.0, empty)

    region = _centre_region(plate_image)
    hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
    hue, saturation, value = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    total = float(hue.size)
    if total == 0:
        return ColorEstimate(PlateColor.UNKNOWN, 0.0, empty)

    chromatic = (saturation >= _CHROMATIC_MIN_SATURATION) & (value >= _CHROMATIC_MIN_VALUE)

    def _band(low: int, high: int) -> np.ndarray:
        return chromatic & (hue >= low) & (hue <= high)

    yellow = _band(*_YELLOW_HUE)
    blue = _band(*_BLUE_HUE)
    red = _band(*_RED_HUE_LOW) | _band(*_RED_HUE_HIGH)
    white = (saturation <= _WHITE_MAX_SATURATION) & (value >= _WHITE_MIN_VALUE)

    fractions = {
        PlateColor.WHITE: float(np.count_nonzero(white)) / total,
        PlateColor.YELLOW: float(np.count_nonzero(yellow)) / total,
        PlateColor.BLUE: float(np.count_nonzero(blue)) / total,
        PlateColor.RED: float(np.count_nonzero(red)) / total,
        PlateColor.UNKNOWN: 0.0,
    }

    winner = max(fractions, key=lambda key: fractions[key])
    share = fractions[winner]
    if share < MIN_DOMINANT_FRACTION:
        return ColorEstimate(PlateColor.UNKNOWN, share, fractions)
    return ColorEstimate(winner, share, fractions)
