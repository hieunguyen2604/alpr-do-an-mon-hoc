"""Classify the background colour of a cropped Vietnamese licence plate.

Why colour is worth reading at all
----------------------------------
:mod:`ai.inference.plate_rules` classifies a plate by the *shape of its
character string*, which is powerful but blind to a distinction the law draws in
colour alone. Circular 79/2024/TT-BCA gives a business vehicle a **yellow**
plate carrying exactly the same layout as a private vehicle's **white** one:
``29E-015.66`` is the same string either way. No amount of regular-expression
work can tell those apart, because the difference is not in the string.

Colour and string classification are therefore complementary, and deliberately
kept separate:

===============  ==========================  ============================
Plate            Background colour           Kind from the string
===============  ==========================  ============================
Private car      white                       ``CAR``
Business car     **yellow**                  ``CAR``  (identical!)
State agency     blue                        ``BLUE_CAR``
Army             red                         ``MILITARY``
Diplomatic       white, red serial letters   ``DIPLOMATIC``
===============  ==========================  ============================

Only the pair identifies the vehicle class. The last row shows why colour alone
is not enough either: a diplomatic plate has a white background like a private
one, and only its string reveals what it is.

How the classification works
----------------------------
The crop is converted to HSV and reduced to the fraction of pixels falling in
each colour band. The largest fraction wins, provided it clears
:data:`MIN_DOMINANT_FRACTION`; otherwise the answer is
:attr:`PlateColor.UNKNOWN` rather than a guess.

Two details matter more than the thresholds:

* **Only the centre of the crop is sampled** (:data:`CENTRE_INSET`). A detector
  box is rarely tight, so the outer band often holds bumper, windscreen or road
  -- and a red car behind a white plate would otherwise win the vote outright.
* **Character pixels are not excluded.** They do not need to be: characters
  occupy a minority of the plate, and each band's threshold is a fraction of the
  sampled area, not a majority of it. Trying to mask them out would mean
  segmenting glyphs, which is a far more fragile step than the one it protects.

Thresholds were calibrated against real crops produced by this project's own
detector -- not against a colour chart -- because what matters is how a plate
looks after JPEG compression, motion blur and an evening exposure, not what its
paint measures under studio light.
"""

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
    """Background colours a Vietnamese plate can carry.

    Members:
        WHITE: Private vehicles, businesses and domestic organisations. Also the
            background of diplomatic plates, whose red serial letters do not
            cover enough area to change the dominant colour.
        YELLOW: Commercial transport -- taxi, lorry, coach, ride-hailing.
        BLUE: Party, State, political-social organisations, public service units.
        RED: Army vehicles.
        UNKNOWN: No band was dominant enough to name. A crop that is too dark,
            too blown out or mostly not-a-plate lands here, and reporting that
            honestly is more useful than defaulting to white.
    """

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
    """The classification of one crop, with the evidence behind it.

    The per-band fractions are carried alongside the verdict on purpose: a
    borderline call is far easier to review when the numbers that produced it
    are visible, and the evaluation harness can report a distribution instead of
    a bare label.

    Attributes:
        color: The winning colour, or :attr:`PlateColor.UNKNOWN`.
        confidence: Fraction of sampled pixels in the winning band, ``0.0`` to
            ``1.0``. Not a probability -- it is the margin the decision rests on.
        fractions: Fraction of sampled pixels in each band, including the ones
            that lost.
    """

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
    """Trim :data:`CENTRE_INSET` from every edge.

    Args:
        image: The plate crop, BGR ``uint8``.

    Returns:
        The central region, or the original array when trimming would leave
        fewer than two pixels on an axis -- a crop that small carries no usable
        histogram either way, and returning an empty slice would raise.
    """
    height, width = image.shape[:2]
    inset_y = int(height * CENTRE_INSET)
    inset_x = int(width * CENTRE_INSET)
    if height - 2 * inset_y < 2 or width - 2 * inset_x < 2:
        return image
    return image[inset_y : height - inset_y, inset_x : width - inset_x]


def classify_plate_color(plate_image: ImageArray) -> ColorEstimate:
    """Name the background colour of a cropped plate.

    Args:
        plate_image: The crop as a BGR ``uint8`` array, as produced by the
            detector stage. Grayscale input is rejected rather than guessed at:
            a colour verdict from an image with no colour would be fiction.

    Returns:
        A :class:`ColorEstimate`. An empty, single-channel or otherwise
        unusable array yields :attr:`PlateColor.UNKNOWN` with zero confidence
        instead of raising -- a plate whose colour cannot be read is a normal
        outcome that must still be recorded, exactly as an unreadable plate is.
    """
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
