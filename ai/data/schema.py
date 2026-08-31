"""In-memory representation of labelled training images and YOLO label file I/O (QCVN 08:2024)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Iterable, Iterator, Literal, Sequence

__all__ = [
    "AR_ONE_LINE_MIN",
    "AR_CAR_LONG",
    "AR_CAR_SHORT",
    "AR_MOTORCYCLE",
    "EXCLUDED_LETTERS",
    "FULL_LETTERS",
    "OCR_SAFE_CHARSET",
    "OCR_TRAINING_CHARSET",
    "PLATE_CLASS_ID",
    "PLATE_CLASS_NAME",
    "SERIAL_FIRST_LETTERS",
    "SERIAL_SECOND_LETTERS_MOTORCYCLE",
    "LineCount",
    "BoxRecord",
    "ImageRecord",
    "LabelParseError",
    "estimate_line_count",
    "image_path_to_label_path",
    "iter_records_from_directory",
    "parse_yolo_label_file",
    "write_yolo_label_file",
]

PLATE_CLASS_ID: Final[int] = 0
"""Single class index for license plate detection."""

PLATE_CLASS_NAME: Final[str] = "license_plate"
"""Human-readable class name for data.yaml."""

AR_CAR_LONG: Final[float] = 520.0 / 110.0
"""Aspect ratio for single-line car plate (~4.727)."""

AR_CAR_SHORT: Final[float] = 330.0 / 165.0
"""Aspect ratio for two-line car plate (2.000)."""

AR_MOTORCYCLE: Final[float] = 190.0 / 140.0
"""Aspect ratio for two-line motorcycle plate (~1.357)."""

AR_ONE_LINE_MIN: Final[float] = 2.5
"""Aspect ratio threshold to classify single-line vs two-line plates."""

LineCount = Literal[1, 2]
"""Number of text rows on a plate."""

FULL_LETTERS: Final[str] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
"""All 26 Latin uppercase letters."""

EXCLUDED_LETTERS: Final[frozenset[str]] = frozenset("IJOQW")
"""Letters not used on Vietnamese plates."""

SERIAL_FIRST_LETTERS: Final[str] = "ABCDEFGHKLMNPSTUVXYZ"
"""Valid initial serial letters under TT 79/2024."""

SERIAL_SECOND_LETTERS_MOTORCYCLE: Final[str] = "ABCDEFHKLMNPRSTUVXYZ"
"""Valid second serial letters for motorcycles."""

OCR_SAFE_CHARSET: Final[str] = "0123456789" + "".join(sorted(set(SERIAL_FIRST_LETTERS) | {"R"}))
"""Allowed characters for post-processing validation."""

OCR_TRAINING_CHARSET: Final[str] = "0123456789" + FULL_LETTERS
"""Full character set for OCR model training."""


class LabelParseError(ValueError):
    """Raised when a YOLO label file cannot be parsed."""


def estimate_line_count(aspect_ratio: float) -> LineCount:
    """Estimate whether a plate is single-line (1) or two-line (2) based on aspect ratio."""
    if not math.isfinite(aspect_ratio) or aspect_ratio <= 0.0:
        raise ValueError(f"Aspect ratio must be positive and finite, got {aspect_ratio!r}")
    return 1 if aspect_ratio >= AR_ONE_LINE_MIN else 2


@dataclass(frozen=True, slots=True)
class BoxRecord:
    """Normalized bounding box annotation and optional transcription."""

    x_center: float
    y_center: float
    width: float
    height: float
    class_id: int = PLATE_CLASS_ID
    plate_text: str | None = None
    line_count: LineCount | None = None

    @property
    def area(self) -> float:
        """Return relative box area."""
        return self.width * self.height

    @property
    def xyxy_normalised(self) -> tuple[float, float, float, float]:
        """Return normalized (x1, y1, x2, y2) coordinates."""
        half_w = self.width / 2.0
        half_h = self.height / 2.0
        return (
            self.x_center - half_w,
            self.y_center - half_h,
            self.x_center + half_w,
            self.y_center + half_h,
        )

    def aspect_ratio_for(self, image_width: int, image_height: int) -> float:
        """Compute pixel aspect ratio given image dimensions."""
        _require_positive_dimensions(image_width, image_height)
        pixel_height = self.height * image_height
        if pixel_height <= 0.0:
            raise ValueError("Cannot compute aspect ratio for a box of zero height")
        return (self.width * image_width) / pixel_height

    def estimated_line_count(self, image_width: int, image_height: int) -> LineCount:
        """Return known line count or compute heuristic estimate."""
        if self.line_count is not None:
            return self.line_count
        return estimate_line_count(self.aspect_ratio_for(image_width, image_height))

    def validate(self, *, min_area: float = 0.0) -> list[str]:
        """Validate box coordinates and boundary constraints."""
        issues: list[str] = []

        for name, value in (
            ("x_center", self.x_center),
            ("y_center", self.y_center),
            ("width", self.width),
            ("height", self.height),
        ):
            if not math.isfinite(value):
                issues.append(f"{name} is not a finite number ({value!r})")

        if issues:
            return issues

        if self.class_id < 0:
            issues.append(f"class_id must be non-negative, got {self.class_id}")

        for name, value in (
            ("x_center", self.x_center),
            ("y_center", self.y_center),
            ("width", self.width),
            ("height", self.height),
        ):
            if not 0.0 <= value <= 1.0:
                issues.append(f"{name}={value:.6f} is outside the YOLO range [0, 1]")

        if self.width <= 0.0 or self.height <= 0.0:
            issues.append(
                f"box has non-positive size (width={self.width:.6f}, "
                f"height={self.height:.6f}) so its area is zero or negative"
            )

        x1, y1, x2, y2 = self.xyxy_normalised
        tolerance = 1e-6
        if x1 < -tolerance or y1 < -tolerance or x2 > 1.0 + tolerance or y2 > 1.0 + tolerance:
            issues.append(
                f"box extends past the image border: corners "
                f"({x1:.6f}, {y1:.6f}) -> ({x2:.6f}, {y2:.6f})"
            )

        if min_area > 0.0 and 0.0 < self.area < min_area:
            issues.append(
                f"warning: box area {self.area * 100:.4f}% of the image is below the "
                f"{min_area * 100:.2f}% threshold; plates this small are hard to learn"
            )

        return issues

    def to_yolo_line(self, *, precision: int = 6, include_extras: bool = False) -> str:
        """Serialize box to a standard or extended YOLO label line."""
        coords = " ".join(
            f"{value:.{precision}f}"
            for value in (self.x_center, self.y_center, self.width, self.height)
        )
        line = f"{self.class_id} {coords}"

        if not include_extras:
            return line
        if self.plate_text is None and self.line_count is None:
            return line

        text = "-" if self.plate_text is None else "_".join(self.plate_text.split())
        line = f"{line} {text}"
        if self.line_count is not None:
            line = f"{line} {self.line_count}"
        return line

    @classmethod
    def from_yolo_line(cls, line: str) -> BoxRecord:
        """Parse a YOLO annotation line into a BoxRecord."""
        parts = line.split()
        if len(parts) < 5:
            raise LabelParseError(
                f"expected at least 5 fields (class x y w h), got {len(parts)}: {line.strip()!r}"
            )

        try:
            class_id = int(float(parts[0]))
        except ValueError as exc:
            raise LabelParseError(f"class id {parts[0]!r} is not a number") from exc

        try:
            x_center, y_center, width, height = (float(value) for value in parts[1:5])
        except ValueError as exc:
            raise LabelParseError(f"coordinates {parts[1:5]!r} are not all numeric") from exc

        plate_text: str | None = None
        line_count: LineCount | None = None

        extras = parts[5:]
        if extras and not _looks_numeric(extras[0]):
            raw_text = extras[0]
            plate_text = None if raw_text == "-" else raw_text.replace("_", " ").strip() or None
            extras = extras[1:]
            if extras and extras[0] in {"1", "2"}:
                line_count = 1 if extras[0] == "1" else 2

        return cls(
            x_center=x_center,
            y_center=y_center,
            width=width,
            height=height,
            class_id=class_id,
            plate_text=plate_text,
            line_count=line_count,
        )


@dataclass(slots=True)
class ImageRecord:
    """Image metadata and associated bounding box annotations."""

    path: Path
    width: int
    height: int
    source_dataset: str
    split: str = "unassigned"
    boxes: list[BoxRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path):
            self.path = Path(self.path)

    @property
    def label_path(self) -> Path:
        """Return expected YOLO label file path."""
        return image_path_to_label_path(self.path)

    def estimated_line_counts(self) -> list[LineCount]:
        """Return list of line counts for all annotated boxes."""
        counts: list[LineCount] = []
        for box in self.boxes:
            try:
                counts.append(box.estimated_line_count(self.width, self.height))
            except ValueError:
                continue
        return counts

    def validate(self, *, min_box_area: float = 0.0) -> list[str]:
        """Validate image dimensions and all box annotations."""
        issues: list[str] = []
        if self.width <= 0 or self.height <= 0:
            issues.append(f"image dimensions must be positive, got {self.width}x{self.height}")
        for index, box in enumerate(self.boxes):
            for message in box.validate(min_area=min_box_area):
                issues.append(f"box {index}: {message}")
        return issues

    @classmethod
    def from_label_file(
        cls,
        image_path: Path,
        width: int,
        height: int,
        source_dataset: str,
        *,
        label_path: Path | None = None,
        split: str = "unassigned",
    ) -> ImageRecord:
        """Construct ImageRecord by reading corresponding YOLO label file."""
        resolved_label = (
            label_path if label_path is not None else image_path_to_label_path(image_path)
        )
        boxes = parse_yolo_label_file(resolved_label) if resolved_label.is_file() else []
        return cls(
            path=image_path,
            width=width,
            height=height,
            source_dataset=source_dataset,
            split=split,
            boxes=boxes,
        )


def image_path_to_label_path(image_path: Path) -> Path:
    """Map image file path to corresponding YOLO label path."""
    parts = list(image_path.parts)
    for index in range(len(parts) - 1, -1, -1):
        if parts[index] == "images":
            parts[index] = "labels"
            return Path(*parts).with_suffix(".txt")
    return image_path.with_suffix(".txt")


def parse_yolo_label_file(label_path: Path) -> list[BoxRecord]:
    """Parse YOLO label file into a list of BoxRecords."""
    boxes: list[BoxRecord] = []
    text = label_path.read_text(encoding="utf-8", errors="replace")
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            boxes.append(BoxRecord.from_yolo_line(stripped))
        except LabelParseError as exc:
            raise LabelParseError(f"{label_path}:{line_number}: {exc}") from exc
    return boxes


def write_yolo_label_file(
    label_path: Path,
    boxes: Iterable[BoxRecord],
    *,
    include_extras: bool = False,
    precision: int = 6,
) -> None:
    """Write BoxRecords to YOLO label file."""
    label_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [box.to_yolo_line(precision=precision, include_extras=include_extras) for box in boxes]
    content = "\n".join(lines)
    if content:
        content += "\n"
    label_path.write_text(content, encoding="utf-8")


def iter_records_from_directory(
    images_dir: Path,
    source_dataset: str,
    dimensions: dict[Path, tuple[int, int]],
    *,
    split: str = "unassigned",
    extensions: Sequence[str] = (".jpg", ".jpeg", ".png", ".bmp", ".webp"),
) -> Iterator[ImageRecord]:
    """Iterate and yield ImageRecords from a directory."""
    allowed = {suffix.lower() for suffix in extensions}
    for image_path in sorted(images_dir.rglob("*")):
        if not image_path.is_file() or image_path.suffix.lower() not in allowed:
            continue
        size = dimensions.get(image_path)
        if size is None:
            continue
        yield ImageRecord.from_label_file(
            image_path,
            width=size[0],
            height=size[1],
            source_dataset=source_dataset,
            split=split,
        )


def _require_positive_dimensions(width: int, height: int) -> None:
    """Validate that image dimensions are positive integers."""
    if width <= 0 or height <= 0:
        raise ValueError(f"Image dimensions must be positive, got {width}x{height}")


def _looks_numeric(token: str) -> bool:
    """Return True if token is parseable as float."""
    try:
        float(token)
    except ValueError:
        return False
    return True
