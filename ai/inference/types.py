"""Immutable dataclasses exchanged across the ALPR pipeline (NFR-M1)."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import numpy.typing as npt

__all__ = [
    "ImageArray",
    "BoundingBox",
    "PlateDetection",
    "PlateRecognition",
    "DetectionResult",
    "PipelineResult",
]

ImageArray = npt.NDArray[np.uint8]
"""An image in OpenCV's native format: ``(height, width, 3)`` BGR, ``uint8``."""


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """An axis-aligned rectangle in pixel coordinates."""

    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        """Validate the rectangle right after construction."""
        if self.x < 0 or self.y < 0:
            raise ValueError(
                f"Bounding box origin must be non-negative, got x={self.x}, y={self.y}"
            )
        if self.width <= 0 or self.height <= 0:
            raise ValueError(
                "Bounding box must have positive size, got "
                f"width={self.width}, height={self.height}"
            )

    @property
    def x2(self) -> int:
        """Return the x coordinate of the right edge (exclusive)."""
        return self.x + self.width

    @property
    def y2(self) -> int:
        """Return the y coordinate of the bottom edge (exclusive)."""
        return self.y + self.height

    @property
    def aspect_ratio(self) -> float:
        """Return width divided by height."""
        return self.width / self.height

    def to_xyxy(self) -> tuple[int, int, int, int]:
        """Return the box as ``(x1, y1, x2, y2)`` corner coordinates."""
        return self.x, self.y, self.x2, self.y2

    def area(self) -> int:
        """Return the area of the box in square pixels."""
        return self.width * self.height

    @classmethod
    def from_xyxy(cls, x1: float, y1: float, x2: float, y2: float) -> BoundingBox:
        """Build a box from corner coordinates, rounding to whole pixels."""
        left, top = round(x1), round(y1)
        return cls(x=left, y=top, width=round(x2) - left, height=round(y2) - top)


@dataclass(frozen=True, slots=True)
class PlateDetection:
    """One license plate located in an image by the detector."""

    bbox: BoundingBox
    confidence: float


@dataclass(frozen=True, slots=True)
class PlateRecognition:
    """The text read from a cropped plate, before and after normalisation."""

    text: str
    raw_text: str
    confidence: float
    line_count: int
    is_valid_format: bool
    kind: str = ""
    display_text: str = ""
    upper_char_count: int = 0


@dataclass(slots=True)
class DetectionResult:
    """Everything the pipeline learned about a single plate."""

    detection: PlateDetection
    recognition: PlateRecognition | None = None
    plate_image: ImageArray | None = field(default=None, repr=False, compare=False)
    processing_time: float = 0.0
    plate_color: str = ""
    plate_color_confidence: float = 0.0

    @property
    def has_text(self) -> bool:
        """Return ``True`` if OCR produced a non-empty plate string."""
        return self.recognition is not None and bool(self.recognition.text)


@dataclass(slots=True)
class PipelineResult:
    """The complete outcome of running the pipeline over one image or frame."""

    results: list[DetectionResult] = field(default_factory=list)
    total_time: float = 0.0
    image_width: int = 0
    image_height: int = 0
    stage_times: dict[str, float] = field(default_factory=dict)

    @property
    def plate_count(self) -> int:
        """Return the number of plates detected in the image."""
        return len(self.results)

    @property
    def recognized_count(self) -> int:
        """Return how many detected plates also yielded readable text."""
        return sum(1 for result in self.results if result.has_text)

    def __len__(self) -> int:
        """Return the number of plates detected, so ``len(result)`` works."""
        return len(self.results)
