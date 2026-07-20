"""Geometry helpers that turn a two-line plate crop into a one-line strip.

This module is the concrete answer to project risk **R-04** -- two-line plates.
It is deliberately *engine-agnostic*: it contains pure image geometry and
contrast work, imports no OCR runtime, and can therefore be reused unchanged if
the recogniser behind :class:`~ai.inference.interfaces.BaseRecognizer` is
swapped for a different engine.

Why the problem exists
----------------------
Modern text recognisers are CRNN/CTC models. Their core assumption is a
*monotonic alignment* between image columns and output characters, which only
holds when the text sits on a single line. On top of that, the recognition
module of PP-OCR resizes every crop to a **fixed height of 48 px**. A
motorcycle plate has an aspect ratio near 1.36, so after that resize each of
its two text lines is squeezed into roughly 24 px of height -- below the point
where the glyphs are still separable. The published consequence is stark: on
the Brazilian RodoSol-ALPR dataset, OpenALPR reports 94.3% on single-line car
plates but only 45.7% on two-line motorcycle plates (Laroca et al., VISAPP
2022). Those numbers describe Brazilian data, not Vietnamese, and are quoted
here only as a quantitative analogue for the difficulty of the two-line layout.

The strategy implemented here
-----------------------------
**Split-then-hstack.** Cut the crop into an upper and a lower half *with
deliberate vertical overlap*, resize both halves to a common height, then
:func:`numpy.hstack` them into one wide single-line strip. The recogniser then
sees exactly the kind of input its architecture was designed for, and the full
48 px budget is spent on one line of glyphs instead of two.

Typical use::

    if estimate_line_count(crop) == 2:
        upper, lower = split_two_line(crop)
        crop = merge_two_line(upper, lower)
    crop = preprocess_plate(crop)

Every step is individually switchable through keyword arguments so that Phase 7
can ablate them one at a time and measure what each contributes.
"""

from __future__ import annotations

import logging
from typing import Final

import cv2
import numpy as np

from ai.inference.exceptions import InvalidImageError
from ai.inference.types import BoundingBox, ImageArray

__all__ = [
    "DEFAULT_TWO_LINE_AR_THRESHOLD",
    "UPPER_HALF_END_RATIO",
    "LOWER_HALF_START_RATIO",
    "MIN_MERGE_HEIGHT",
    "estimate_line_count",
    "split_two_line",
    "merge_two_line",
    "preprocess_plate",
]

_LOGGER = logging.getLogger(__name__)

DEFAULT_TWO_LINE_AR_THRESHOLD: Final[float] = 2.5
"""Aspect-ratio cut-off below which a crop is treated as a two-line plate.

See :func:`estimate_line_count` for the reasoning. Mirrors the default of
:attr:`~ai.inference.config.InferenceConfig.two_line_aspect_ratio_threshold`;
callers should pass the configured value rather than rely on this constant.
"""

UPPER_HALF_END_RATIO: Final[float] = 5.0 / 12.0
"""Fraction of the crop height at which the upper half stops (0.4167)."""

LOWER_HALF_START_RATIO: Final[float] = 1.0 / 3.0
"""Fraction of the crop height at which the lower half starts (0.3333).

Smaller than :data:`UPPER_HALF_END_RATIO` on purpose -- the two halves overlap
by 1/12 of the plate height. See :func:`split_two_line`.
"""

MIN_MERGE_HEIGHT: Final[int] = 48
"""Floor for the common height used when merging the two halves, in pixels.

Matches the fixed input height of the PP-OCR recognition module: producing a
strip shorter than this would force the engine to upscale a degraded image,
which loses detail that was still present in the source crop.
"""

_CLAHE_DEFAULT_CLIP_LIMIT: Final[float] = 2.0
_CLAHE_DEFAULT_TILE_GRID: Final[tuple[int, int]] = (8, 8)
_DENOISE_DEFAULT_DIAMETER: Final[int] = 5
_DENOISE_DEFAULT_SIGMA_COLOR: Final[float] = 50.0
_DENOISE_DEFAULT_SIGMA_SPACE: Final[float] = 50.0


def _validate_image(image: ImageArray, argument_name: str) -> None:
    """Reject arrays that cannot be treated as an image.

    Args:
        image: Candidate array.
        argument_name: Name of the caller's parameter, used in the message.

    Raises:
        InvalidImageError: If the array is ``None``, not a NumPy array, has
            fewer than two dimensions, or has a zero-sized side.
    """
    if image is None or not isinstance(image, np.ndarray):
        raise InvalidImageError(
            f"{argument_name} must be a NumPy array, got {type(image).__name__}"
        )
    if image.ndim not in (2, 3):
        raise InvalidImageError(
            f"{argument_name} must be a 2-D or 3-D array, got {image.ndim} dimensions"
        )
    if image.size == 0 or image.shape[0] == 0 or image.shape[1] == 0:
        raise InvalidImageError(
            f"{argument_name} must have a positive width and height, " f"got shape {image.shape}"
        )


def estimate_line_count(
    source: ImageArray | BoundingBox,
    threshold: float = DEFAULT_TWO_LINE_AR_THRESHOLD,
) -> int:
    """Guess whether a plate carries its characters on one line or two.

    .. warning::
       **This is a heuristic proposed by this project, not a legal rule.**
       No Vietnamese regulation states how to classify a plate from its aspect
       ratio. What the regulation does provide (QCVN 08:2024/BCA, in force from
       2025-01-01) are the physical plate sizes, and those leave a wide empty
       band:

       =========================== ============= ============== =========
       Plate type                  Size (mm)     Aspect ratio   Lines
       =========================== ============= ============== =========
       Car, long plate             110 x 520     4.727          1
       Car, short plate            165 x 330     2.000          2
       Motorcycle                  140 x 190     1.357          2
       =========================== ============= ============== =========

       No plate type falls between 2.000 and 4.727, so any cut-off inside that
       2.727-wide gap separates the classes. This function defaults to 2.5,
       biased towards the two-line side because the two-line path degrades
       gracefully on a one-line input while the reverse does not.

    .. note::
       Ratios between roughly 2.5 and 3.0 are a genuine grey zone: a one-line
       plate photographed at a sharp angle has a *bounding-box* ratio that
       drops into it. Measuring on a rectified crop, or on the ratio of
       ``cv2.minAreaRect``, is markedly more reliable than measuring on an
       axis-aligned YOLO box. Phase 7 should quantify how often this matters.

    Args:
        source: Either a plate crop as a NumPy array -- the ratio is taken from
            ``shape[1] / shape[0]`` -- or a
            :class:`~ai.inference.types.BoundingBox`, whose
            :attr:`~ai.inference.types.BoundingBox.aspect_ratio` is used.
        threshold: Aspect ratio below which the plate is reported as two-line.
            Must be positive.

    Returns:
        ``2`` when the plate is estimated to carry two lines, ``1`` otherwise.

    Raises:
        InvalidImageError: If ``source`` is an array that is not a usable image.
        ValueError: If ``threshold`` is not positive.
    """
    if threshold <= 0.0:
        raise ValueError(f"threshold must be positive, got {threshold}")

    if isinstance(source, BoundingBox):
        aspect_ratio = source.aspect_ratio
    else:
        _validate_image(source, "source")
        height, width = source.shape[0], source.shape[1]
        aspect_ratio = width / height

    line_count = 2 if aspect_ratio < threshold else 1
    _LOGGER.debug(
        "Estimated plate line count",
        extra={
            "aspect_ratio": round(aspect_ratio, 4),
            "threshold": threshold,
            "line_count": line_count,
        },
    )
    return line_count


def split_two_line(
    image: ImageArray,
    upper_end_ratio: float = UPPER_HALF_END_RATIO,
    lower_start_ratio: float = LOWER_HALF_START_RATIO,
) -> tuple[ImageArray, ImageArray]:
    """Cut a two-line plate crop into an upper and a lower half, with overlap.

    The two halves **overlap on purpose**. A naive cut at exactly half the
    height slices through glyphs whenever the crop is not perfectly framed --
    the plate border adds padding that is rarely symmetric, and a slight tilt
    shifts the true separator by several pixels across the width. Amputating
    the feet of the upper row or the caps of the lower row is far more damaging
    to a recogniser than showing it a few stray pixels of the neighbouring row,
    which it simply ignores as background.

    With the default ratios the upper half spans ``[0, 5h/12)`` and the lower
    half ``[h/3, h)``, so they share the band ``[h/3, 5h/12)`` -- one twelfth of
    the plate height. These ratios are taken from published work on Vietnamese
    two-line plates rather than tuned here, so that the baseline measurement in
    Phase 4 starts from a known-good configuration.

    Args:
        image: The plate crop, grayscale or BGR. Not modified.
        upper_end_ratio: Where the upper half ends, as a fraction of height.
        lower_start_ratio: Where the lower half starts, as a fraction of
            height. Must be smaller than ``upper_end_ratio`` for the halves to
            overlap.

    Returns:
        An ``(upper, lower)`` pair of views cut from ``image``. Both are
        guaranteed to have at least one row.

    Raises:
        InvalidImageError: If ``image`` is not a usable image.
        ValueError: If the ratios are outside ``(0, 1)`` or would produce an
            empty half.
    """
    _validate_image(image, "image")

    if not 0.0 < upper_end_ratio <= 1.0:
        raise ValueError(f"upper_end_ratio must be within (0.0, 1.0], got {upper_end_ratio}")
    if not 0.0 <= lower_start_ratio < 1.0:
        raise ValueError(f"lower_start_ratio must be within [0.0, 1.0), got {lower_start_ratio}")

    height = image.shape[0]
    upper_end = int(upper_end_ratio * height)
    lower_start = int(lower_start_ratio * height)

    # Guarantee non-empty halves even for crops only a few pixels tall, where
    # int() truncation could otherwise collapse a slice to zero rows.
    upper_end = max(upper_end, 1)
    lower_start = min(lower_start, height - 1)

    if lower_start >= upper_end:
        _LOGGER.warning(
            "Two-line split produced no overlap between halves",
            extra={
                "height": height,
                "upper_end": upper_end,
                "lower_start": lower_start,
            },
        )

    upper: ImageArray = image[0:upper_end]
    lower: ImageArray = image[lower_start:]
    return upper, lower


def merge_two_line(
    upper: ImageArray,
    lower: ImageArray,
    target_height: int | None = None,
) -> ImageArray:
    """Join the two halves of a plate side by side into one single-line strip.

    This is the step that actually defuses risk R-04. A CRNN/CTC recogniser
    assumes a monotonic left-to-right alignment between image columns and
    emitted characters, and PP-OCR's recognition module resizes every input to
    a **fixed height of 48 px**. Feed it a motorcycle plate (aspect ratio about
    1.36) unchanged and each of the two text rows is compressed to roughly
    24 px -- at that scale the strokes merge and the engine reads nothing
    usable. Concatenating the halves horizontally instead gives a strip whose
    aspect ratio is several times wider, so the single row of glyphs receives
    the full 48 px height budget.

    Reading order is preserved: the upper half is placed on the left, which is
    exactly the order in which a Vietnamese two-line plate is read (province
    code and series on top, running number below).

    Args:
        upper: Upper half of the plate, as returned by :func:`split_two_line`.
        lower: Lower half of the plate.
        target_height: Common height both halves are resized to, in pixels.
            When ``None`` (the default) it is the larger of the two input
            heights, floored at :data:`MIN_MERGE_HEIGHT` so the strip is never
            shorter than the recogniser's own input height. Aspect ratio of
            each half is preserved, so the halves keep their relative width.

    Returns:
        A single image of height ``target_height`` whose width is the sum of
        the two resized half-widths. The channel layout matches the inputs;
        if one input is grayscale and the other is BGR, both are promoted to
        BGR so they can be stacked.

    Raises:
        InvalidImageError: If either half is not a usable image.
        ValueError: If ``target_height`` is not positive.
    """
    _validate_image(upper, "upper")
    _validate_image(lower, "lower")

    if target_height is None:
        target_height = max(upper.shape[0], lower.shape[0], MIN_MERGE_HEIGHT)
    elif target_height <= 0:
        raise ValueError(f"target_height must be positive, got {target_height}")

    upper_bgr, lower_bgr = _match_channels(upper, lower)
    resized_upper = _resize_to_height(upper_bgr, target_height)
    resized_lower = _resize_to_height(lower_bgr, target_height)

    merged: ImageArray = np.hstack((resized_upper, resized_lower))
    _LOGGER.debug(
        "Merged two-line plate halves into a single-line strip",
        extra={
            "upper_shape": tuple(upper.shape),
            "lower_shape": tuple(lower.shape),
            "merged_shape": tuple(merged.shape),
        },
    )
    return merged


def preprocess_plate(
    image: ImageArray,
    to_grayscale: bool = True,
    apply_clahe: bool = True,
    denoise: bool = True,
    clahe_clip_limit: float = _CLAHE_DEFAULT_CLIP_LIMIT,
    clahe_tile_grid_size: tuple[int, int] = _CLAHE_DEFAULT_TILE_GRID,
    upscale_to_height: int | None = None,
    downscale_to_height: int | None = None,
) -> ImageArray:
    """Clean up a plate crop before handing it to the OCR engine.

    Three light-touch steps, each independently switchable so that Phase 7 can
    ablate them and attribute the accuracy change to a specific one:

    1. **Grayscale.** Vietnamese plate characters carry no colour information;
       dropping the two chroma channels removes a nuisance variable introduced
       by coloured street lighting.
    2. **CLAHE.** Plates are retro-reflective metal with embossed characters
       (1.7 mm relief per QCVN 08:2024/BCA), so a headlight or the sun produces
       a bright patch over part of the plate while the rest stays dark. A
       *global* histogram stretch cannot fix that; contrast-limited adaptive
       equalisation works tile by tile and does. The clip limit keeps it from
       amplifying sensor noise in the flat background areas.
    3. **Denoise.** A bilateral filter -- edge-preserving on purpose, because a
       Gaussian blur strong enough to remove sensor noise also rounds off the
       stroke ends that distinguish ``8`` from ``B``.

    The result is always a 3-channel BGR array even when ``to_grayscale`` is
    enabled (the single channel is replicated), so that the output can be fed
    to any engine without callers having to branch on channel count.

    Args:
        image: The plate crop, grayscale or BGR. Not modified.
        to_grayscale: Whether to discard colour information.
        apply_clahe: Whether to run contrast-limited adaptive histogram
            equalisation. Requires a single-channel image, so it is skipped
            with a warning when ``to_grayscale`` is disabled.
        denoise: Whether to run the edge-preserving bilateral filter.
        clahe_clip_limit: Contrast ceiling for CLAHE. Higher values give more
            local contrast and more amplified noise.
        clahe_tile_grid_size: CLAHE tile grid as ``(rows, columns)``.
        upscale_to_height: When set, the crop is enlarged to this height
            (aspect ratio preserved) before the other steps run. Small crops
            benefit, since interpolating first gives CLAHE more pixels to work
            with. Never downscales. ``None`` disables the step.
        downscale_to_height: When set, a crop *taller* than this is shrunk to
            it (aspect ratio preserved). ``None`` disables the step.

            .. warning::
               This is not a performance knob -- it is a **correctness fix**,
               and leaving it unset costs everything. PP-OCR's text detector is
               a DB segmentation network trained on document and scene text at
               ordinary sizes; give it glyphs several hundred pixels tall and
               its shrink map fires nowhere, so the pipeline returns *no text
               at all*. Measured on the Phase 2b label corpus, whose crops are
               exported at 640x640: with no cap, whole-plate accuracy is
               **0 out of 100** sampled crops, one-line and two-line alike;
               capping the strip at 64 px it is 48/50 and 31/50. The engine was
               never the problem, the input scale was.

               The failure is invisible in ordinary operation because a plate
               cropped out of a 640-wide scene is only 20-40 px tall, well
               under any cap. It appears the moment a user uploads a close-up
               photograph -- exactly the input a web UI invites.

    Returns:
        The processed crop as a BGR ``uint8`` array.

    Raises:
        InvalidImageError: If ``image`` is not a usable image.
        ValueError: If ``clahe_clip_limit`` is not positive, the tile grid is
            not a pair of positive integers, either height bound is not
            positive, or ``downscale_to_height`` is below
            ``upscale_to_height`` (which would make the two steps fight).
    """
    _validate_image(image, "image")

    if clahe_clip_limit <= 0.0:
        raise ValueError(f"clahe_clip_limit must be positive, got {clahe_clip_limit}")
    if len(clahe_tile_grid_size) != 2 or any(v <= 0 for v in clahe_tile_grid_size):
        raise ValueError(
            "clahe_tile_grid_size must be a pair of positive integers, "
            f"got {clahe_tile_grid_size}"
        )
    if upscale_to_height is not None and upscale_to_height <= 0:
        raise ValueError(f"upscale_to_height must be positive, got {upscale_to_height}")
    if downscale_to_height is not None and downscale_to_height <= 0:
        raise ValueError(f"downscale_to_height must be positive, got {downscale_to_height}")
    if (
        upscale_to_height is not None
        and downscale_to_height is not None
        and downscale_to_height < upscale_to_height
    ):
        raise ValueError(
            "downscale_to_height must not be smaller than upscale_to_height, got "
            f"{downscale_to_height} < {upscale_to_height}"
        )

    working = image.copy()

    if upscale_to_height is not None and working.shape[0] < upscale_to_height:
        working = _resize_to_height(working, upscale_to_height)

    if downscale_to_height is not None and working.shape[0] > downscale_to_height:
        working = _resize_to_height(working, downscale_to_height)

    if to_grayscale and working.ndim == 3:
        working = cv2.cvtColor(working, cv2.COLOR_BGR2GRAY)

    if apply_clahe:
        if working.ndim == 2:
            clahe = cv2.createCLAHE(
                clipLimit=clahe_clip_limit,
                tileGridSize=clahe_tile_grid_size,
            )
            working = clahe.apply(working)
        else:
            _LOGGER.warning(
                "Skipping CLAHE: it needs a single-channel image, enable to_grayscale to use it",
                extra={"channels": working.shape[2]},
            )

    if denoise:
        working = cv2.bilateralFilter(
            working,
            d=_DENOISE_DEFAULT_DIAMETER,
            sigmaColor=_DENOISE_DEFAULT_SIGMA_COLOR,
            sigmaSpace=_DENOISE_DEFAULT_SIGMA_SPACE,
        )

    if working.ndim == 2:
        working = cv2.cvtColor(working, cv2.COLOR_GRAY2BGR)

    return working


def _resize_to_height(image: ImageArray, height: int) -> ImageArray:
    """Resize an image to a given height, preserving its aspect ratio.

    Args:
        image: Source image.
        height: Target height in pixels. Must be positive.

    Returns:
        The resized image, at least one pixel wide. Enlarging uses cubic
        interpolation (smoother strokes for the recogniser) and shrinking uses
        area interpolation (no aliasing).
    """
    source_height, source_width = image.shape[0], image.shape[1]
    if source_height == height:
        return image
    width = max(1, round(source_width * height / source_height))
    interpolation = cv2.INTER_CUBIC if height > source_height else cv2.INTER_AREA
    return cv2.resize(image, (width, height), interpolation=interpolation)


def _match_channels(first: ImageArray, second: ImageArray) -> tuple[ImageArray, ImageArray]:
    """Promote both images to BGR when their channel counts differ.

    ``np.hstack`` refuses arrays whose trailing dimensions disagree, so a
    grayscale half cannot be stacked next to a colour one.

    Args:
        first: First image.
        second: Second image.

    Returns:
        The two images with a matching number of channels.
    """
    if first.ndim == second.ndim:
        return first, second
    if first.ndim == 2:
        return cv2.cvtColor(first, cv2.COLOR_GRAY2BGR), second
    return first, cv2.cvtColor(second, cv2.COLOR_GRAY2BGR)
