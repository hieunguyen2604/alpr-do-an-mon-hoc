"""Geometry helpers that turn two-line plate crops into single-line strips (Risk R-04)."""

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
    "MIN_RECTIFY_ANGLE_DEGREES",
    "MAX_RECTIFY_ANGLE_DEGREES",
    "MIN_RECTIFY_AREA_FRACTION",
    "estimate_line_count",
    "rectify_plate",
    "stretch_vertical",
    "split_two_line",
    "merge_two_line",
    "preprocess_plate",
]

_LOGGER = logging.getLogger(__name__)

DEFAULT_TWO_LINE_AR_THRESHOLD: Final[float] = 2.5
"""Aspect-ratio cut-off below which a crop is treated as a two-line plate."""

UPPER_HALF_END_RATIO: Final[float] = 5.0 / 12.0
"""Fraction of the crop height at which the upper half stops (0.4167)."""

LOWER_HALF_START_RATIO: Final[float] = 1.0 / 3.0
"""Fraction of the crop height at which the lower half starts (0.3333)."""

MIN_MERGE_HEIGHT: Final[int] = 48
"""Floor for the common height used when merging the two halves, in pixels."""

MIN_RECTIFY_ANGLE_DEGREES: Final[float] = 1.5
"""Estimated skew below which :func:`rectify_plate` leaves the crop untouched."""

MAX_RECTIFY_ANGLE_DEGREES: Final[float] = 35.0
"""Estimated skew above which the estimate itself is distrusted."""

MIN_RECTIFY_AREA_FRACTION: Final[float] = 0.25
"""Smallest fraction of the crop the candidate plate blob must cover."""

_CLAHE_DEFAULT_CLIP_LIMIT: Final[float] = 2.0
_CLAHE_DEFAULT_TILE_GRID: Final[tuple[int, int]] = (8, 8)
_DENOISE_DEFAULT_DIAMETER: Final[int] = 5
_DENOISE_DEFAULT_SIGMA_COLOR: Final[float] = 50.0
_DENOISE_DEFAULT_SIGMA_SPACE: Final[float] = 50.0


def _validate_image(image: ImageArray, argument_name: str) -> None:
    """Reject arrays that cannot be treated as an image."""
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
    """Guess whether a plate carries its characters on one line or two."""
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


def rectify_plate(
    image: ImageArray,
    min_angle_degrees: float = MIN_RECTIFY_ANGLE_DEGREES,
    max_angle_degrees: float = MAX_RECTIFY_ANGLE_DEGREES,
) -> ImageArray:
    """Deskew a plate crop by rotating its dominant blob level and re-cropping."""
    _validate_image(image, "image")
    if min_angle_degrees <= 0.0 or max_angle_degrees <= 0.0:
        raise ValueError(
            "angle bounds must be positive, got "
            f"min={min_angle_degrees}, max={max_angle_degrees}"
        )
    if min_angle_degrees >= max_angle_degrees:
        raise ValueError(
            "min_angle_degrees must be below max_angle_degrees, got "
            f"min={min_angle_degrees}, max={max_angle_degrees}"
        )

    height, width = image.shape[0], image.shape[1]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Test both polarities to handle bright (white) and dark (blue) plates
    best_rect: tuple[tuple[float, float], tuple[float, float], float] | None = None
    best_area = 0.0
    for candidate in (binary, cv2.bitwise_not(binary)):
        contours, _ = cv2.findContours(candidate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            continue
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        if area > best_area:
            best_area = area
            best_rect = cv2.minAreaRect(largest)

    if best_rect is None or best_area < MIN_RECTIFY_AREA_FRACTION * height * width:
        _LOGGER.debug(
            "Rectify skipped: no dominant plate blob",
            extra={"blob_area": best_area, "crop_area": height * width},
        )
        return image

    (center_x, center_y), (rect_side_a, rect_side_b), _raw_angle = best_rect
    rect_width = max(rect_side_a, rect_side_b)
    rect_height = min(rect_side_a, rect_side_b)
    # Version-independent tilt angle calculation from the longest bounding box edge
    box = cv2.boxPoints(best_rect)
    edges = box - np.roll(box, 1, axis=0)
    longest_edge = edges[int(np.argmax(np.hypot(edges[:, 0], edges[:, 1])))]
    angle = float(np.degrees(np.arctan2(longest_edge[1], longest_edge[0])))
    if angle > 90.0:
        angle -= 180.0
    elif angle <= -90.0:
        angle += 180.0

    if abs(angle) < min_angle_degrees or abs(angle) > max_angle_degrees:
        _LOGGER.debug(
            "Rectify skipped: angle outside actionable range",
            extra={"angle": round(angle, 2)},
        )
        return image

    # Rotate on expanded canvas with border replication to prevent phantom edges
    matrix = cv2.getRotationMatrix2D((center_x, center_y), angle, 1.0)
    cos = abs(matrix[0, 0])
    sin = abs(matrix[0, 1])
    canvas_width = int(height * sin + width * cos) + 2
    canvas_height = int(height * cos + width * sin) + 2
    matrix[0, 2] += canvas_width / 2.0 - center_x
    matrix[1, 2] += canvas_height / 2.0 - center_y
    rotated = cv2.warpAffine(
        image,
        matrix,
        (canvas_width, canvas_height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )

    # Margin around fitted rectangle to avoid clipping boundary characters
    cut_width = min(canvas_width, int(rect_width * 1.04) + 2)
    cut_height = min(canvas_height, int(rect_height * 1.08) + 2)
    rectified: ImageArray = cv2.getRectSubPix(
        rotated,
        (cut_width, cut_height),
        (canvas_width / 2.0, canvas_height / 2.0),
    )

    _LOGGER.debug(
        "Rectified skewed plate crop",
        extra={
            "angle": round(angle, 2),
            "input_shape": (height, width),
            "output_shape": tuple(rectified.shape[:2]),
        },
    )
    return rectified


def stretch_vertical(image: ImageArray, factor: float = 2.0) -> ImageArray:
    """Stretch a crop vertically, undoing pitch foreshortening."""
    _validate_image(image, "image")
    if factor <= 1.0:
        raise ValueError(f"factor must be greater than 1, got {factor}")
    height, width = image.shape[0], image.shape[1]
    stretched: ImageArray = cv2.resize(
        image, (width, int(height * factor)), interpolation=cv2.INTER_CUBIC
    )
    return stretched


def split_two_line(
    image: ImageArray,
    upper_end_ratio: float = UPPER_HALF_END_RATIO,
    lower_start_ratio: float = LOWER_HALF_START_RATIO,
) -> tuple[ImageArray, ImageArray]:
    """Cut a two-line plate crop into an upper and a lower half, with overlap."""
    _validate_image(image, "image")

    if not 0.0 < upper_end_ratio <= 1.0:
        raise ValueError(f"upper_end_ratio must be within (0.0, 1.0], got {upper_end_ratio}")
    if not 0.0 <= lower_start_ratio < 1.0:
        raise ValueError(f"lower_start_ratio must be within [0.0, 1.0), got {lower_start_ratio}")

    height = image.shape[0]
    upper_end = int(upper_end_ratio * height)
    lower_start = int(lower_start_ratio * height)

    # Guarantee non-empty split halves even for tiny crops
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
    """Join the two halves of a plate side by side into one single-line strip."""
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
    """Clean up a plate crop before handing it to the OCR engine."""
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
    """Resize an image to a given height, preserving its aspect ratio."""
    source_height, source_width = image.shape[0], image.shape[1]
    if source_height == height:
        return image
    width = max(1, round(source_width * height / source_height))
    interpolation = cv2.INTER_CUBIC if height > source_height else cv2.INTER_AREA
    return cv2.resize(image, (width, height), interpolation=interpolation)


def _match_channels(first: ImageArray, second: ImageArray) -> tuple[ImageArray, ImageArray]:
    """Promote both images to BGR when their channel counts differ."""
    if first.ndim == second.ndim:
        return first, second
    if first.ndim == 2:
        return cv2.cvtColor(first, cv2.COLOR_GRAY2BGR), second
    return first, cv2.cvtColor(second, cv2.COLOR_GRAY2BGR)
