"""Immutable data structures exchanged across the ALPR pipeline.

These are plain :mod:`dataclasses`. They deliberately do **not** use Pydantic:
the ``ai`` package must stay framework-free (NFR-M1). The API layer defines its
own Pydantic schemas and maps them from these objects, which keeps the wire
format free to evolve independently of the pipeline's internal model.

Object graph produced by one pipeline run::

    PipelineResult
    └── results: list[DetectionResult]
        ├── detection:   PlateDetection      (always present)
        │   └── bbox:    BoundingBox
        ├── recognition: PlateRecognition | None   (None if OCR read nothing)
        └── plate_image: ndarray | None            (the cropped plate)

Field names line up with the approved ``detection_history`` table so the
persistence layer is a direct mapping rather than a translation.
"""

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
    """An axis-aligned rectangle in pixel coordinates.

    The origin is the top-left corner of the image, the x-axis grows to the
    right and the y-axis downwards -- the OpenCV/NumPy convention.

    This class stores the ``xywh`` form because that is what the
    ``detection_history`` table persists (``bbox_x``, ``bbox_y``, ``bbox_w``,
    ``bbox_h``). Use :meth:`from_xyxy` to build one from a corner-pair, which
    is what YOLO returns.

    Coordinates are validated on construction: a detector that produces boxes
    running past the image border must clamp them before building a
    ``BoundingBox``.

    Attributes:
        x: Left edge, in pixels. Must be >= 0.
        y: Top edge, in pixels. Must be >= 0.
        width: Box width, in pixels. Must be > 0.
        height: Box height, in pixels. Must be > 0.

    Raises:
        ValueError: If any coordinate is negative or either side is not
            strictly positive.
    """

    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        """Validate the rectangle right after construction.

        Raises:
            ValueError: If the rectangle is degenerate or has negative origin.
        """
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
        """Return width divided by height.

        The pipeline uses this to guess whether a plate is one line or two:
        Vietnamese single-line plates are wide (ratio well above 2), while
        square-ish two-line plates sit near 1. The decision threshold lives in
        :class:`~ai.inference.config.InferenceConfig`, not here.
        """
        return self.width / self.height

    def to_xyxy(self) -> tuple[int, int, int, int]:
        """Return the box as ``(x1, y1, x2, y2)`` corner coordinates.

        Returns:
            The top-left and bottom-right corners. The bottom-right corner is
            exclusive, so the tuple can be used directly for NumPy slicing:
            ``image[y1:y2, x1:x2]``.
        """
        return self.x, self.y, self.x2, self.y2

    def area(self) -> int:
        """Return the area of the box in square pixels."""
        return self.width * self.height

    @classmethod
    def from_xyxy(cls, x1: float, y1: float, x2: float, y2: float) -> BoundingBox:
        """Build a box from corner coordinates, rounding to whole pixels.

        Detectors such as YOLO emit float corner coordinates; this is the
        conversion point into the pipeline's integer pixel model.

        Args:
            x1: Left edge.
            y1: Top edge.
            x2: Right edge, exclusive.
            y2: Bottom edge, exclusive.

        Returns:
            The equivalent ``xywh`` bounding box.

        Raises:
            ValueError: If the resulting rectangle is degenerate or has a
                negative origin -- i.e. if the corners were swapped or the box
                collapsed to nothing when rounded.
        """
        left, top = round(x1), round(y1)
        return cls(x=left, y=top, width=round(x2) - left, height=round(y2) - top)


@dataclass(frozen=True, slots=True)
class PlateDetection:
    """One license plate located in an image by the detector.

    This is the output of the *detection* stage only -- no text has been read
    yet. It is deliberately separate from :class:`PlateRecognition` because the
    two stages have independent confidence scores that the approved schema
    stores in separate columns (``confidence`` vs ``ocr_confidence``); merging
    them would make it impossible to tell which stage was uncertain.

    Attributes:
        bbox: Where the plate sits in the source image.
        confidence: Detector confidence in ``[0.0, 1.0]``. Persisted as
            ``detection_history.confidence``.
    """

    bbox: BoundingBox
    confidence: float


@dataclass(frozen=True, slots=True)
class PlateRecognition:
    """The text read from a cropped plate, before and after normalisation.

    Both the corrected and the raw string are kept. ``raw_text`` is what the
    OCR engine actually returned; ``text`` is the result of normalisation and
    regex correction. Storing both is a hard requirement of the approved schema
    because comparing them is the only way to measure what the post-processing
    step contributes to overall accuracy.

    Attributes:
        text: Normalised plate string, e.g. ``"51F-12345"``. Persisted as
            ``detection_history.plate_number``.
        raw_text: The unmodified OCR output. Persisted as
            ``detection_history.raw_ocr_text``.
        confidence: OCR confidence in ``[0.0, 1.0]``. Persisted as
            ``detection_history.ocr_confidence`` -- kept apart from the
            detector's own confidence.
        line_count: Number of text lines on the plate, ``1`` or ``2``.
        is_valid_format: Whether :attr:`text` matches a known Vietnamese plate
            format. ``False`` does not mean the record is discarded -- it is
            stored and flagged, so that failures remain measurable.
    """

    text: str
    raw_text: str
    confidence: float
    line_count: int
    is_valid_format: bool


@dataclass(slots=True)
class DetectionResult:
    """Everything the pipeline learned about a single plate.

    One source image yields one of these per plate found, so an image showing
    three vehicles produces three ``DetectionResult`` objects -- all belonging
    to the *same* upload. That grouping is what ``source_job_id`` records in the
    database, and it is why dashboard statistics must count jobs rather than
    rows.

    This dataclass is mutable and non-frozen: :attr:`plate_image` is a heavy
    NumPy array that later stages may release once it has been written to disk.

    Attributes:
        detection: Where the plate is and how sure the detector was.
        recognition: What was read from it, or ``None`` when OCR produced
            nothing usable. A detection with no recognition is still a valid,
            reportable result.
        plate_image: The cropped plate as a BGR array, or ``None`` if the crop
            was not kept. Excluded from comparison and from ``repr`` -- NumPy
            arrays have no scalar truth value, so comparing them inside a
            dataclass would raise.
        processing_time: Seconds spent on this plate, detection plus OCR.
    """

    detection: PlateDetection
    recognition: PlateRecognition | None = None
    plate_image: ImageArray | None = field(default=None, repr=False, compare=False)
    processing_time: float = 0.0

    @property
    def has_text(self) -> bool:
        """Return ``True`` if OCR produced a non-empty plate string."""
        return self.recognition is not None and bool(self.recognition.text)


@dataclass(slots=True)
class PipelineResult:
    """The complete outcome of running the pipeline over one image or frame.

    Carrying the source dimensions alongside the results lets consumers scale
    bounding boxes to a different display size without needing the original
    image -- the frontend draws overlays on a resized preview.

    Attributes:
        results: One entry per plate found, in detector order. Empty when the
            image contains no plate, which is a normal outcome rather than an
            error.
        total_time: Wall-clock seconds for the whole run. This is not the sum
            of the per-plate times: it also covers decoding, pre-processing and
            any work shared between plates.
        image_width: Width in pixels of the image that was processed.
        image_height: Height in pixels of the image that was processed.
        stage_times: Seconds spent in each pipeline stage, keyed by stage name
            (``detect``, ``crop``, ``ocr``, ``normalize``, ``total``). Empty
            when the producer did not measure them -- the placeholder pipeline
            in the API layer does not. The breakdown exists because attributing
            the end-to-end latency budget to a single stage is what makes it
            actionable; a total alone only says the pipeline is slow.
    """

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
