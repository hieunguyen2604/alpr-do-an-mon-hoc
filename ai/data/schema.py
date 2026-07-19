"""In-memory representation of a labelled training image, plus YOLO label I/O.

Why a dedicated schema
----------------------
Every script under ``scripts/dataset/`` reads and writes the same thing: an
image file next to a ``.txt`` label file in YOLO format. Re-parsing that format
in six different places is how silent inconsistencies get introduced, so all of
it lives here.

The YOLO label format
---------------------
One box per line, whitespace separated, coordinates **normalised to ``[0, 1]``
against the image dimensions**::

    <class_id> <x_center> <y_center> <width> <height>

This project extends that with two optional trailing fields so that datasets
carrying transcriptions (notably VNLP) survive a round-trip::

    <class_id> <x_center> <y_center> <width> <height> <plate_text> <line_count>

The extension is backwards compatible: a plain five-field line parses fine, and
:meth:`BoxRecord.to_yolo_line` only emits the extra fields when they carry
information. Ultralytics ignores trailing fields it does not understand, but
:func:`write_yolo_label_file` still defaults to strict five-field output so the
files handed to the trainer are unambiguous.

Aspect ratio, carefully
-----------------------
The stored ``width``/``height`` are *fractions of the image*, not pixels. The
ratio ``width / height`` is therefore **not** the plate's real aspect ratio
unless the image happens to be square. Getting this wrong silently corrupts the
one-line/two-line estimate, so :class:`BoxRecord` has no bare ``aspect_ratio``
property -- the only way to obtain one is
:meth:`BoxRecord.aspect_ratio_for` / :meth:`ImageRecord.box_aspect_ratios`,
both of which require the image dimensions.

Line-count thresholds (Phase 1, QCVN 08:2024/BCA)
-------------------------------------------------
========================  ==============  ============  =========
Plate type                Size (mm)       Aspect ratio  Lines
========================  ==============  ============  =========
Car, long plate           520 x 110       4.727         1
Car, short plate          330 x 165       2.000         2
Motorcycle                190 x 140       1.357         2
========================  ==============  ============  =========

The decision threshold sits in the empty band between 2.000 and 4.727; this
module uses 2.5. See :func:`estimate_line_count` for the (important) caveats.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
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

# --------------------------------------------------------------------------
# Class space
# --------------------------------------------------------------------------

PLATE_CLASS_ID: Final[int] = 0
"""The only class in the merged dataset. Detection is a single-class problem."""

PLATE_CLASS_NAME: Final[str] = "license_plate"
"""Human-readable name written into the Ultralytics ``data.yaml``."""

# --------------------------------------------------------------------------
# Aspect-ratio constants (Phase 1 / QCVN 08:2024/BCA)
# --------------------------------------------------------------------------

AR_CAR_LONG: Final[float] = 520.0 / 110.0
"""~4.727 -- car long plate, single line."""

AR_CAR_SHORT: Final[float] = 330.0 / 165.0
"""2.000 -- car short plate, two lines."""

AR_MOTORCYCLE: Final[float] = 190.0 / 140.0
"""~1.357 -- motorcycle plate, two lines."""

AR_ONE_LINE_MIN: Final[float] = 2.5
"""Boxes at or above this ratio are *guessed* to be single-line.

Chosen as a mid-point of the empty band between the widest two-line plate
(2.000) and the narrowest one-line plate (4.727). It is a heuristic, not a
measurement -- see :func:`estimate_line_count`.
"""

LineCount = Literal[1, 2]
"""Number of text rows on a plate. Vietnamese plates have exactly one or two."""

# --------------------------------------------------------------------------
# Character sets
# --------------------------------------------------------------------------

FULL_LETTERS: Final[str] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
"""All 26 Latin letters."""

EXCLUDED_LETTERS: Final[frozenset[str]] = frozenset("IJOQW")
"""The five letters that never appear on a Vietnamese plate.

``I`` and ``O`` are omitted because they are indistinguishable from ``1`` and
``0``; ``J``, ``Q`` and ``W`` are simply not allocated.
"""

SERIAL_FIRST_LETTERS: Final[str] = "ABCDEFGHKLMNPSTUVXYZ"
"""The 20 letters permitted as the *first* character of a serial group."""

SERIAL_SECOND_LETTERS_MOTORCYCLE: Final[str] = "ABCDEFHKLMNPRSTUVXYZ"
"""Second serial letter on motorcycle plates: ``R`` is allowed, ``G`` is not."""

OCR_SAFE_CHARSET: Final[str] = "0123456789" + "".join(
    sorted(set(SERIAL_FIRST_LETTERS) | {"R"})
)
"""Digits plus the 21 letters that can actually occur (20 serial letters + ``R``).

Use this for **post-processing constraints only**.
"""

OCR_TRAINING_CHARSET: Final[str] = "0123456789" + FULL_LETTERS
"""Digits plus all 26 letters -- what an OCR model should be *trained* on.

Deliberately wider than :data:`OCR_SAFE_CHARSET`. Narrowing the charset at the
model level is a trap: if ``R`` (or any letter) is absent from the vocabulary
the model physically cannot emit it, and the information is lost before
post-processing ever runs. Restrict at the post-processing stage, where a wrong
guess is still recoverable and measurable.
"""


class LabelParseError(ValueError):
    """Raised when a YOLO label line or file cannot be interpreted.

    Carries enough context (file, line number) for a verification report to
    point a human at the exact offending row.
    """


# --------------------------------------------------------------------------
# Line-count heuristic
# --------------------------------------------------------------------------


def estimate_line_count(aspect_ratio: float) -> LineCount:
    """Guess how many text rows a plate has from its aspect ratio.

    This is a **heuristic**, and every caller must treat it as one. It is
    derived from the nominal plate dimensions in QCVN 08:2024/BCA, which
    describe a plate viewed head-on. Three things break it in practice:

    * **Perspective.** A plate photographed at an angle projects narrower, so a
      one-line plate can fall below the threshold.
    * **Loose boxes.** An annotation with generous padding inflates the height
      more than the width for wide plates, pulling the ratio down.
    * **Deformed plates.** Bent motorcycle plates are common in Vietnamese
      traffic footage.

    Its intended use is producing an approximate distribution for stratified
    splitting and for statistics -- never for asserting ground truth. Where a
    dataset ships a real line-count label, prefer that label.

    Args:
        aspect_ratio: Plate width divided by plate height, **in pixels**.

    Returns:
        ``1`` if the box is at least as wide as :data:`AR_ONE_LINE_MIN`,
        otherwise ``2``.

    Raises:
        ValueError: If ``aspect_ratio`` is not a positive finite number.
    """
    if not math.isfinite(aspect_ratio) or aspect_ratio <= 0.0:
        raise ValueError(f"Aspect ratio must be positive and finite, got {aspect_ratio!r}")
    return 1 if aspect_ratio >= AR_ONE_LINE_MIN else 2


# --------------------------------------------------------------------------
# Box
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BoxRecord:
    """One annotated license plate inside an image, in normalised YOLO coords.

    The four geometry fields are fractions of the image dimensions, so a record
    survives resizing the image unchanged. They are **not** validated on
    construction: the whole point of ``verify_annotations.py`` is to *find*
    malformed labels, which is impossible if merely loading them raises. Call
    :meth:`validate` to collect problems as messages.

    Attributes:
        x_center: Box centre on the x-axis, fraction of image width.
        y_center: Box centre on the y-axis, fraction of image height.
        width: Box width, fraction of image width.
        height: Box height, fraction of image height.
        class_id: Class index. Always :data:`PLATE_CLASS_ID` after merging.
        plate_text: Ground-truth transcription (e.g. ``"51F-12345"``) when the
            source dataset provides one, otherwise ``None``. Detection-only
            datasets such as CCPD-for-pretraining leave this empty.
        line_count: True number of text rows when known. ``None`` means unknown
            -- use :meth:`estimated_line_count` to fall back to the heuristic.
    """

    x_center: float
    y_center: float
    width: float
    height: float
    class_id: int = PLATE_CLASS_ID
    plate_text: str | None = None
    line_count: LineCount | None = None

    # -- derived geometry ---------------------------------------------------

    @property
    def area(self) -> float:
        """Return the box area as a fraction of the total image area."""
        return self.width * self.height

    @property
    def xyxy_normalised(self) -> tuple[float, float, float, float]:
        """Return ``(x1, y1, x2, y2)`` corners, still normalised to ``[0, 1]``."""
        half_w = self.width / 2.0
        half_h = self.height / 2.0
        return (
            self.x_center - half_w,
            self.y_center - half_h,
            self.x_center + half_w,
            self.y_center + half_h,
        )

    def to_pixels(self, image_width: int, image_height: int) -> tuple[int, int, int, int]:
        """Return ``(x1, y1, x2, y2)`` in whole pixels for a given image size.

        Args:
            image_width: Image width in pixels. Must be positive.
            image_height: Image height in pixels. Must be positive.

        Returns:
            Corner coordinates rounded to integers. The result is *not* clamped
            to the image -- a label that runs off the edge produces coordinates
            outside it, which is exactly what a verifier needs to see.

        Raises:
            ValueError: If either dimension is not positive.
        """
        _require_positive_dimensions(image_width, image_height)
        x1, y1, x2, y2 = self.xyxy_normalised
        return (
            round(x1 * image_width),
            round(y1 * image_height),
            round(x2 * image_width),
            round(y2 * image_height),
        )

    def aspect_ratio_for(self, image_width: int, image_height: int) -> float:
        """Return the box's true pixel aspect ratio (width / height).

        The normalised ``width`` and ``height`` are relative to *different*
        denominators, so their ratio is meaningless on its own; the image
        dimensions are what convert it back into a real shape.

        Args:
            image_width: Image width in pixels. Must be positive.
            image_height: Image height in pixels. Must be positive.

        Returns:
            Plate width divided by plate height, in pixels.

        Raises:
            ValueError: If either image dimension is not positive, or if the
                box has zero height (its ratio is undefined).
        """
        _require_positive_dimensions(image_width, image_height)
        pixel_height = self.height * image_height
        if pixel_height <= 0.0:
            raise ValueError("Cannot compute aspect ratio for a box of zero height")
        return (self.width * image_width) / pixel_height

    def estimated_line_count(self, image_width: int, image_height: int) -> LineCount:
        """Return :attr:`line_count` if known, else the aspect-ratio guess.

        Args:
            image_width: Image width in pixels.
            image_height: Image height in pixels.

        Returns:
            ``1`` or ``2``. A value derived from :func:`estimate_line_count` is
            a heuristic; see that function for when it misfires.

        Raises:
            ValueError: If the image dimensions or box height are unusable.
        """
        if self.line_count is not None:
            return self.line_count
        return estimate_line_count(self.aspect_ratio_for(image_width, image_height))

    # -- validation ---------------------------------------------------------

    def validate(self, *, min_area: float = 0.0) -> list[str]:
        """Check the box for the defects a YOLO trainer cannot tolerate.

        Nothing is raised and nothing is mutated: problems come back as
        human-readable strings so a caller can aggregate them into a report.

        Args:
            min_area: Optional lower bound on :attr:`area`, as a fraction of
                image area. A box smaller than this yields a ``warning:``
                message rather than an error -- tiny plates are legal but hard
                to learn. ``0.0`` disables the check.

        Returns:
            A list of messages, empty when the box is well formed. Messages
            beginning with ``warning:`` are advisory; all others are errors.
        """
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
            # Range checks below would be meaningless against NaN/inf.
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
        # A tolerance of 1e-6 absorbs the rounding of exporters that write six
        # decimals; anything larger is a genuinely out-of-frame box.
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

    def clipped(self) -> BoxRecord:
        """Return a copy with corners clamped into ``[0, 1]``.

        Clamping is applied to the *corners*, then the centre and size are
        recomputed, so a box hanging over the edge is trimmed rather than
        shifted. A box lying entirely outside the frame degenerates to zero
        size, which :meth:`validate` then reports -- it is not silently dropped.

        Returns:
            A new :class:`BoxRecord`; the original is untouched.
        """
        x1, y1, x2, y2 = self.xyxy_normalised
        x1, y1 = max(0.0, x1), max(0.0, y1)
        x2, y2 = min(1.0, x2), min(1.0, y2)
        new_width = max(0.0, x2 - x1)
        new_height = max(0.0, y2 - y1)
        return replace(
            self,
            x_center=x1 + new_width / 2.0,
            y_center=y1 + new_height / 2.0,
            width=new_width,
            height=new_height,
        )

    # -- serialisation ------------------------------------------------------

    def to_yolo_line(self, *, precision: int = 6, include_extras: bool = False) -> str:
        """Render the box as a single YOLO label line.

        Args:
            precision: Number of decimal places for the four coordinates.
            include_extras: When ``True``, append ``plate_text`` and
                ``line_count`` as trailing fields (the project extension).
                Whitespace inside ``plate_text`` is replaced with ``_`` so the
                line stays parseable. Fields are only appended when they hold a
                value; ``plate_text`` is written as ``-`` if it is missing but
                ``line_count`` is present, to keep the columns aligned.

        Returns:
            The line, without a trailing newline.
        """
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
        """Parse one YOLO label line into a :class:`BoxRecord`.

        Accepts the standard five-field form, the project's extended form
        (``... <plate_text> [<line_count>]``), and the six-field form emitted by
        prediction runs where the sixth field is a confidence score -- a numeric
        sixth field is treated as confidence and discarded, not as text.

        No range checking happens here. A structurally valid line describing an
        impossible box parses successfully and is caught by :meth:`validate`;
        that separation is what lets the verifier report bad labels instead of
        dying on them.

        Args:
            line: A single line, with or without surrounding whitespace.

        Returns:
            The parsed box.

        Raises:
            LabelParseError: If the line has too few fields, or if the class id
                or any coordinate is not numeric.
        """
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
            raise LabelParseError(
                f"coordinates {parts[1:5]!r} are not all numeric"
            ) from exc

        plate_text: str | None = None
        line_count: LineCount | None = None

        extras = parts[5:]
        if extras and not _looks_numeric(extras[0]):
            raw_text = extras[0]
            plate_text = None if raw_text == "-" else raw_text.replace("_", " ").strip() or None
            extras = extras[1:]
            if extras and extras[0] in {"1", "2"}:
                line_count = 1 if extras[0] == "1" else 2
        # Any other trailing field (e.g. a confidence score) is ignored on
        # purpose: it is not part of this schema and must not become text.

        return cls(
            x_center=x_center,
            y_center=y_center,
            width=width,
            height=height,
            class_id=class_id,
            plate_text=plate_text,
            line_count=line_count,
        )


# --------------------------------------------------------------------------
# Image
# --------------------------------------------------------------------------


@dataclass(slots=True)
class ImageRecord:
    """One image together with every plate annotated in it.

    Mutable by design: the merge and augmentation stages rewrite :attr:`path`
    and :attr:`split` as records move through the pipeline.

    An image with an empty :attr:`boxes` list is legitimate -- YOLO uses such
    background images to learn what is *not* a plate -- so emptiness is never
    treated as an error, only counted.

    Attributes:
        path: Location of the image file. Absolute after loading.
        width: Image width in pixels.
        height: Image height in pixels.
        source_dataset: Slug of the dataset this image came from, e.g.
            ``"vnlp"``. Preserved through merging so that per-source statistics
            and licence attribution stay possible.
        split: ``"train"``, ``"val"``, ``"test"`` or ``"unassigned"``.
        boxes: The plates annotated in this image.
    """

    path: Path
    width: int
    height: int
    source_dataset: str
    split: str = "unassigned"
    boxes: list[BoxRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Coerce :attr:`path` to a :class:`~pathlib.Path`.

        Callers frequently hold plain strings (CSV manifests, JSON reports);
        normalising once here means no downstream code has to guess the type.
        """
        if not isinstance(self.path, Path):
            self.path = Path(self.path)

    # -- derived ------------------------------------------------------------

    @property
    def box_count(self) -> int:
        """Return the number of annotated plates."""
        return len(self.boxes)

    @property
    def is_background(self) -> bool:
        """Return ``True`` if the image has no plates (a negative sample)."""
        return not self.boxes

    @property
    def image_aspect_ratio(self) -> float:
        """Return the image's own width/height ratio.

        Raises:
            ValueError: If the stored dimensions are not positive.
        """
        _require_positive_dimensions(self.width, self.height)
        return self.width / self.height

    @property
    def label_path(self) -> Path:
        """Return the conventional label path for this image.

        Follows the Ultralytics convention: the same stem with a ``.txt``
        suffix, in a sibling directory where the last path component named
        ``images`` becomes ``labels``. When no such component exists the label
        is assumed to sit beside the image.

        Returns:
            The expected label file path. Existence is *not* checked.
        """
        return image_path_to_label_path(self.path)

    def box_aspect_ratios(self) -> list[float]:
        """Return the true pixel aspect ratio of every box.

        Boxes with zero height are skipped rather than raising, so this can be
        called on unverified data to build a distribution.

        Returns:
            One ratio per usable box, in box order.
        """
        ratios: list[float] = []
        for box in self.boxes:
            try:
                ratios.append(box.aspect_ratio_for(self.width, self.height))
            except ValueError:
                continue
        return ratios

    def estimated_line_counts(self) -> list[LineCount]:
        """Return the per-box line count, true label where known else heuristic.

        Returns:
            One entry per box whose line count could be determined. Boxes with
            zero height are skipped.
        """
        counts: list[LineCount] = []
        for box in self.boxes:
            try:
                counts.append(box.estimated_line_count(self.width, self.height))
            except ValueError:
                continue
        return counts

    def dominant_line_count(self) -> LineCount | None:
        """Return the most common line count among this image's boxes.

        Used as the stratification key when splitting: an image is filed under
        the plate type it mostly contains.

        Returns:
            ``1``, ``2``, or ``None`` when the image has no usable box. Ties are
            broken towards ``2``, the harder and rarer class -- keeping the
            minority class evenly spread matters more than being exactly right
            about a mixed image.
        """
        counts = self.estimated_line_counts()
        if not counts:
            return None
        ones = counts.count(1)
        twos = len(counts) - ones
        return 1 if ones > twos else 2

    # -- validation ---------------------------------------------------------

    def validate(self, *, min_box_area: float = 0.0) -> list[str]:
        """Check the image record and all of its boxes.

        Args:
            min_box_area: Forwarded to :meth:`BoxRecord.validate` as the small
                box warning threshold.

        Returns:
            A list of messages, empty when everything is well formed. Box
            messages are prefixed with ``box <index>:``. Messages containing
            ``warning:`` are advisory.
        """
        issues: list[str] = []
        if self.width <= 0 or self.height <= 0:
            issues.append(
                f"image dimensions must be positive, got {self.width}x{self.height}"
            )
        for index, box in enumerate(self.boxes):
            for message in box.validate(min_area=min_box_area):
                issues.append(f"box {index}: {message}")
        return issues

    # -- serialisation ------------------------------------------------------

    def to_yolo_lines(self, *, include_extras: bool = False) -> list[str]:
        """Render every box as a YOLO label line.

        Args:
            include_extras: Forwarded to :meth:`BoxRecord.to_yolo_line`.

        Returns:
            One string per box, in box order.
        """
        return [box.to_yolo_line(include_extras=include_extras) for box in self.boxes]

    def write_label(self, label_path: Path | None = None, *, include_extras: bool = False) -> Path:
        """Write this record's boxes to a YOLO label file.

        A background image produces an empty file rather than no file at all:
        Ultralytics treats a missing label as *unlabelled* and an empty label as
        *deliberately empty*, and conflating the two poisons training.

        Args:
            label_path: Destination. Defaults to :attr:`label_path`.
            include_extras: Forwarded to :meth:`to_yolo_lines`.

        Returns:
            The path written to.

        Raises:
            OSError: If the file cannot be created.
        """
        destination = label_path if label_path is not None else self.label_path
        write_yolo_label_file(destination, self.boxes, include_extras=include_extras)
        return destination

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
        """Build a record by reading the label file belonging to an image.

        A missing label file yields a record with no boxes; distinguishing
        "missing" from "empty" is the verifier's job, not the loader's, and it
        needs a record in hand either way to report against.

        Args:
            image_path: Path to the image. Not opened -- pass the dimensions in.
            width: Image width in pixels.
            height: Image height in pixels.
            source_dataset: Slug of the originating dataset.
            label_path: Explicit label location. Defaults to the Ultralytics
                convention derived from ``image_path``.
            split: Initial split assignment.

        Returns:
            The populated record.

        Raises:
            LabelParseError: If the label file exists but contains a malformed
                line. The message names the file and the line number.
        """
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


# --------------------------------------------------------------------------
# File-level helpers
# --------------------------------------------------------------------------


def image_path_to_label_path(image_path: Path) -> Path:
    """Map an image path to its Ultralytics label path.

    The convention is to mirror the directory tree, replacing the *last* path
    component named ``images`` with ``labels`` and the suffix with ``.txt``::

        datasets/processed/images/train/a.jpg -> datasets/processed/labels/train/a.txt

    Replacing the last rather than the first occurrence matters: a dataset
    rooted at ``.../images/`` that also contains ``.../images/train/images/``
    must resolve against the innermost one.

    Args:
        image_path: Path to an image file.

    Returns:
        The expected label path. When no ``images`` component exists, the label
        is placed beside the image with a ``.txt`` suffix.
    """
    parts = list(image_path.parts)
    for index in range(len(parts) - 1, -1, -1):
        if parts[index] == "images":
            parts[index] = "labels"
            return Path(*parts).with_suffix(".txt")
    return image_path.with_suffix(".txt")


def parse_yolo_label_file(label_path: Path) -> list[BoxRecord]:
    """Read a YOLO label file into a list of boxes.

    Blank lines and ``#`` comment lines are skipped, which keeps hand-annotated
    files usable.

    Args:
        label_path: Path to the ``.txt`` label file.

    Returns:
        The boxes, in file order. An empty file yields an empty list.

    Raises:
        LabelParseError: If any line is malformed. The message includes the file
            name and the 1-based line number.
        OSError: If the file cannot be read.
    """
    boxes: list[BoxRecord] = []
    # errors="replace" keeps a stray non-UTF-8 byte from aborting the whole
    # run; a corrupted line then surfaces as a parse error naming its number.
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
    """Write boxes to a YOLO label file, creating parent directories.

    Args:
        label_path: Destination ``.txt`` path.
        boxes: Boxes to write. May be empty, producing an empty file.
        include_extras: Emit the ``plate_text``/``line_count`` extension.
            Leave ``False`` for files fed to Ultralytics.
        precision: Decimal places for coordinates.

    Raises:
        OSError: If the file cannot be created.
    """
    label_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        box.to_yolo_line(precision=precision, include_extras=include_extras) for box in boxes
    ]
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
    """Yield an :class:`ImageRecord` for every image found under a directory.

    Kept free of OpenCV so that :mod:`ai.data` has no heavy image dependency;
    the caller supplies dimensions it has already measured.

    Args:
        images_dir: Directory to walk recursively.
        source_dataset: Slug recorded on each record.
        dimensions: Map from image path to ``(width, height)``. Images absent
            from the map are skipped -- they are the ones the caller failed to
            open, and inventing a size for them would hide the failure.
        split: Split assigned to every record.
        extensions: Lowercase file suffixes treated as images.

    Yields:
        One record per readable image, in sorted path order.

    Raises:
        LabelParseError: If a label file is malformed.
    """
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


# --------------------------------------------------------------------------
# Internal
# --------------------------------------------------------------------------


def _require_positive_dimensions(width: int, height: int) -> None:
    """Raise if an image size is unusable as a denominator.

    Args:
        width: Image width in pixels.
        height: Image height in pixels.

    Raises:
        ValueError: If either value is not strictly positive.
    """
    if width <= 0 or height <= 0:
        raise ValueError(f"Image dimensions must be positive, got {width}x{height}")


def _looks_numeric(token: str) -> bool:
    """Return ``True`` if a token parses as a float.

    Used to tell a confidence score in field six apart from a plate
    transcription. Vietnamese plates always contain a letter, so a purely
    numeric sixth field is never a plate string.

    Args:
        token: The raw field.

    Returns:
        Whether :func:`float` accepts it.
    """
    try:
        float(token)
    except ValueError:
        return False
    return True
