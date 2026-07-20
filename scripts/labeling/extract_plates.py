"""Cut every ground-truth plate region out of the test split, ready for labelling.

Why this script exists
----------------------
The merged dataset carries bounding boxes only: it says *where* each plate is,
never *what it reads*. That is enough to train and evaluate the detector, and
useless for evaluating OCR. Without a string ground truth the accuracy targets
NFR-A4..A7 cannot be measured at all -- not measured badly, simply not measured.

The agreed remedy is to hand-label a few hundred test images. This script
prepares that work: it crops each annotated plate, enlarges it until a human can
actually read it, and writes a manifest so every crop can be traced back to the
image and box it came from.

Cropping uses the *ground-truth* boxes, never the detector. That separation is
deliberate: labels produced from detector output would inherit the detector's
misses and drift, and the resulting figure would silently measure the two stages
together instead of OCR alone.

Two details worth knowing
-------------------------
**Padding is cosmetic.** A crop taken exactly on the box edge often clips the
first and last glyph, so a small margin is added for the human's benefit. The
aspect ratio in the manifest is always computed from the *unpadded* box, so the
line-count estimate describes the plate rather than the margin.

**The line-count column is a guess.** It applies the aspect-ratio heuristic
described in ``docs/reports/01-vn-plate-standards.md``; the labelling tool
pre-fills the radio button with it and the human corrects it when it is wrong.

Usage::

    python scripts/labeling/extract_plates.py
    python scripts/labeling/extract_plates.py --split test --target-height 220
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Iterator, Sequence

import cv2
import numpy as np

__all__ = [
    "PROJECT_ROOT",
    "TWO_LINE_ASPECT_RATIO_THRESHOLD",
    "CropRecord",
    "estimate_line_count",
    "extract_split",
    "main",
    "read_yolo_boxes",
]

LOGGER = logging.getLogger("labeling.extract_plates")

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
"""Repository root, derived from ``<root>/scripts/labeling/extract_plates.py``."""

IMAGE_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
)
"""Lowercase suffixes treated as images, matching the dataset scripts."""

TWO_LINE_ASPECT_RATIO_THRESHOLD: Final[float] = 2.5
"""Width/height ratio below which a plate is guessed to carry two text lines.

This is a **heuristic, not a legal rule**. QCVN 08:2024/BCA fixes the physical
plate sizes, and those sizes happen to separate cleanly:

======================== ============ ============= =======
Plate                    Size (mm)    Aspect ratio  Lines
======================== ============ ============= =======
Car, long plate          520 x 110    4.727         1
Car, short plate         330 x 165    2.000         2
Motorcycle               190 x 140    1.357         2
======================== ============ ============= =======

The gap between 2.000 and 4.727 is wide, so a threshold of 2.5 sits comfortably
inside it. What the standard does *not* guarantee is that a detected box has the
plate's true proportions: perspective, a tight or loose box and motion blur all
distort the ratio. Treat the output as a default to be corrected, which is
exactly how the labelling tool uses it.

The value matches ``InferenceConfig.two_line_aspect_ratio_threshold`` so the
labelling defaults and the pipeline agree.
"""

DEFAULT_TARGET_HEIGHT: Final[int] = 200
"""Height in pixels every crop is scaled to, so faint plates stay readable."""

DEFAULT_MAX_WIDTH: Final[int] = 1400
"""Upper bound on crop width, so a very wide plate still fits on screen."""

DEFAULT_PADDING_RATIO: Final[float] = 0.04
"""Fraction of the box size added on each side, purely to avoid clipping glyphs."""

MANIFEST_FIELDNAMES: Final[tuple[str, ...]] = (
    "crop_file",
    "source_image",
    "box_index",
    "bbox_x",
    "bbox_y",
    "bbox_w",
    "bbox_h",
    "aspect_ratio",
    "estimated_lines",
    "crop_width",
    "crop_height",
)
"""Column order of the generated manifest."""


@dataclass(frozen=True, slots=True)
class CropRecord:
    """One extracted plate crop and the provenance needed to trace it back.

    Attributes:
        crop_file: File name of the crop inside the output directory, in the
            form ``<source stem>__box<N>.jpg``. Unique within a split, and the
            join key used by the labelling tool.
        source_image: File name of the image the crop came from.
        box_index: Zero-based position of the box within its label file, so the
            crop can be matched to the exact annotation line.
        bbox_x: Left edge of the unpadded box in source-image pixels.
        bbox_y: Top edge of the unpadded box in source-image pixels.
        bbox_w: Width of the unpadded box in pixels.
        bbox_h: Height of the unpadded box in pixels.
        aspect_ratio: ``bbox_w / bbox_h``, computed before padding.
        estimated_lines: Line count guessed from :attr:`aspect_ratio`.
        crop_width: Width of the written image, after padding and scaling.
        crop_height: Height of the written image.
    """

    crop_file: str
    source_image: str
    box_index: int
    bbox_x: int
    bbox_y: int
    bbox_w: int
    bbox_h: int
    aspect_ratio: float
    estimated_lines: int
    crop_width: int
    crop_height: int

    def as_row(self) -> dict[str, object]:
        """Return the record as a manifest row.

        Returns:
            A mapping keyed by :data:`MANIFEST_FIELDNAMES`, with the aspect
            ratio rounded to three decimals for readability.
        """
        return {
            "crop_file": self.crop_file,
            "source_image": self.source_image,
            "box_index": self.box_index,
            "bbox_x": self.bbox_x,
            "bbox_y": self.bbox_y,
            "bbox_w": self.bbox_w,
            "bbox_h": self.bbox_h,
            "aspect_ratio": round(self.aspect_ratio, 3),
            "estimated_lines": self.estimated_lines,
            "crop_width": self.crop_width,
            "crop_height": self.crop_height,
        }


def estimate_line_count(
    aspect_ratio: float, *, threshold: float = TWO_LINE_ASPECT_RATIO_THRESHOLD
) -> int:
    """Guess how many text lines a plate carries from its shape.

    See :data:`TWO_LINE_ASPECT_RATIO_THRESHOLD` for why the threshold sits where
    it does and why this is a heuristic rather than a rule.

    Args:
        aspect_ratio: Box width divided by box height. Must be positive.
        threshold: Ratio at or above which the plate is called single-line.

    Returns:
        ``1`` for a wide plate, ``2`` for a squarish one.

    Raises:
        ValueError: If ``aspect_ratio`` is not positive.
    """
    if aspect_ratio <= 0.0:
        raise ValueError(f"Aspect ratio must be positive, got {aspect_ratio}")
    return 1 if aspect_ratio >= threshold else 2


def read_yolo_boxes(
    label_path: Path, image_width: int, image_height: int
) -> list[tuple[int, int, int, int]]:
    """Read a YOLO label file and convert it to pixel boxes.

    YOLO stores ``class cx cy w h`` with every coordinate normalised to
    ``[0, 1]`` and the centre -- not the corner -- as the anchor. Boxes are
    clamped to the image so that every returned rectangle is directly usable for
    slicing, and degenerate ones are dropped rather than crashing the run.

    Args:
        label_path: The ``.txt`` label file. A missing file yields an empty
            list, which is the correct reading of "this image has no plate".
        image_width: Width of the matching image, in pixels.
        image_height: Height of the matching image, in pixels.

    Returns:
        One ``(x, y, width, height)`` tuple per usable box, in file order.

    Raises:
        ValueError: If the image dimensions are not positive.
    """
    if image_width <= 0 or image_height <= 0:
        raise ValueError(f"Image size must be positive, got {image_width}x{image_height}")
    if not label_path.is_file():
        LOGGER.debug("No label file for %s", label_path.stem)
        return []

    boxes: list[tuple[int, int, int, int]] = []
    for line_number, line in enumerate(
        label_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        parts = line.split()
        if not parts:
            continue
        if len(parts) < 5:
            LOGGER.warning("Skipping malformed label line", extra={"file": str(label_path)})
            LOGGER.debug("Line %d of %s has %d fields", line_number, label_path, len(parts))
            continue

        try:
            centre_x, centre_y, width, height = (float(value) for value in parts[1:5])
        except ValueError:
            LOGGER.warning(
                "Skipping label line with non-numeric coordinates",
                extra={"file": str(label_path), "line": line_number},
            )
            continue

        # Segmentation-style labels carry a polygon instead of a box; the merge
        # stage already converted those, so anything longer here is unexpected.
        if len(parts) > 5:
            LOGGER.debug(
                "Label line %d of %s has %d extra fields; using the first four "
                "coordinates as a box",
                line_number,
                label_path,
                len(parts) - 5,
            )

        left = int(round((centre_x - width / 2.0) * image_width))
        top = int(round((centre_y - height / 2.0) * image_height))
        right = int(round((centre_x + width / 2.0) * image_width))
        bottom = int(round((centre_y + height / 2.0) * image_height))

        left = max(0, min(left, image_width - 1))
        top = max(0, min(top, image_height - 1))
        right = max(left + 1, min(right, image_width))
        bottom = max(top + 1, min(bottom, image_height))

        if right - left < 2 or bottom - top < 2:
            LOGGER.debug("Dropping degenerate box on line %d of %s", line_number, label_path)
            continue
        boxes.append((left, top, right - left, bottom - top))

    return boxes


def _iter_images(directory: Path) -> Iterator[Path]:
    """Yield image files under a directory in sorted order.

    Sorted order makes crop numbering reproducible across machines, which
    matters because the manifest and the label CSV are joined by file name.

    Args:
        directory: Where to look.

    Yields:
        Paths to image files. Nothing is yielded when the directory is absent;
        the caller reports that, since it has the context to explain it.
    """
    if not directory.is_dir():
        return
    for path in sorted(directory.iterdir()):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            yield path


def _scale_for_reading(crop: np.ndarray, *, target_height: int, max_width: int) -> np.ndarray:
    """Resize a crop so a human can comfortably read it.

    Small crops are enlarged with a cubic filter, which keeps glyph edges
    legible, and oversized ones are shrunk with area averaging, which avoids the
    aliasing a cubic filter would introduce. A very wide plate is capped so it
    still fits on screen without horizontal scrolling.

    Args:
        crop: The cropped plate as a BGR array.
        target_height: Height to scale to, in pixels. Must be positive.
        max_width: Ceiling on the resulting width, in pixels. Must be positive.

    Returns:
        The rescaled crop. The original array is returned unchanged when it is
        already the requested size.

    Raises:
        ValueError: If the crop is empty or a bound is not positive.
    """
    if crop.size == 0:
        raise ValueError("Cannot rescale an empty crop")
    if target_height <= 0 or max_width <= 0:
        raise ValueError(f"Bounds must be positive, got height={target_height}, width={max_width}")

    height, width = crop.shape[:2]
    scale = target_height / float(height)
    new_width = max(1, int(round(width * scale)))
    new_height = target_height

    if new_width > max_width:
        scale = max_width / float(width)
        new_width = max_width
        new_height = max(1, int(round(height * scale)))

    if (new_width, new_height) == (width, height):
        return crop

    interpolation = cv2.INTER_CUBIC if scale > 1.0 else cv2.INTER_AREA
    return cv2.resize(crop, (new_width, new_height), interpolation=interpolation)


def extract_split(
    images_dir: Path,
    labels_dir: Path,
    output_dir: Path,
    *,
    target_height: int = DEFAULT_TARGET_HEIGHT,
    max_width: int = DEFAULT_MAX_WIDTH,
    padding_ratio: float = DEFAULT_PADDING_RATIO,
    threshold: float = TWO_LINE_ASPECT_RATIO_THRESHOLD,
    overwrite: bool = False,
) -> list[CropRecord]:
    """Crop every annotated plate of one split and write the images to disk.

    Args:
        images_dir: Directory of source images for the split.
        labels_dir: Directory of matching YOLO ``.txt`` labels.
        output_dir: Where crops are written. Created if missing.
        target_height: Height each crop is scaled to.
        max_width: Ceiling on crop width.
        padding_ratio: Margin added around the box, as a fraction of its size.
            Cosmetic only -- it never affects the recorded coordinates or the
            aspect ratio.
        threshold: Aspect-ratio threshold for the line-count guess.
        overwrite: Re-encode crops that already exist. Off by default so an
            interrupted run resumes cheaply.

    Returns:
        One :class:`CropRecord` per crop written or already present, in image
        order. The list is what the manifest is built from.

    Raises:
        FileNotFoundError: If the image directory does not exist.
        ValueError: If ``padding_ratio`` is negative.
    """
    if not images_dir.is_dir():
        raise FileNotFoundError(f"Image directory not found: {images_dir}")
    if padding_ratio < 0.0:
        raise ValueError(f"Padding ratio must be non-negative, got {padding_ratio}")
    if not labels_dir.is_dir():
        LOGGER.warning("Label directory not found: %s", labels_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    records: list[CropRecord] = []
    unreadable_images = 0
    images_without_boxes = 0
    written = 0
    reused = 0

    image_paths = list(_iter_images(images_dir))
    LOGGER.info("Scanning %d images in %s", len(image_paths), images_dir)

    for image_path in image_paths:
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None:
            unreadable_images += 1
            LOGGER.warning("Cannot decode image, skipping: %s", image_path.name)
            continue

        image_height, image_width = image.shape[:2]
        boxes = read_yolo_boxes(labels_dir / f"{image_path.stem}.txt", image_width, image_height)
        if not boxes:
            images_without_boxes += 1
            continue

        for box_index, (box_x, box_y, box_w, box_h) in enumerate(boxes):
            pad_x = int(round(box_w * padding_ratio))
            pad_y = int(round(box_h * padding_ratio))
            left = max(0, box_x - pad_x)
            top = max(0, box_y - pad_y)
            right = min(image_width, box_x + box_w + pad_x)
            bottom = min(image_height, box_y + box_h + pad_y)

            crop = image[top:bottom, left:right]
            if crop.size == 0:
                LOGGER.warning("Empty crop for %s box %d, skipping", image_path.name, box_index)
                continue

            crop_file = f"{image_path.stem}__box{box_index}.jpg"
            destination = output_dir / crop_file

            if destination.is_file() and not overwrite:
                existing = cv2.imread(str(destination), cv2.IMREAD_COLOR)
                if existing is not None:
                    crop_height, crop_width = existing.shape[:2]
                    reused += 1
                else:
                    # Present but unreadable: treat it as absent and rewrite.
                    scaled = _scale_for_reading(
                        crop, target_height=target_height, max_width=max_width
                    )
                    crop_height, crop_width = scaled.shape[:2]
                    if not cv2.imwrite(str(destination), scaled):
                        LOGGER.error("Failed to write crop: %s", destination)
                        continue
                    written += 1
            else:
                scaled = _scale_for_reading(crop, target_height=target_height, max_width=max_width)
                crop_height, crop_width = scaled.shape[:2]
                if not cv2.imwrite(str(destination), scaled):
                    LOGGER.error("Failed to write crop: %s", destination)
                    continue
                written += 1

            aspect_ratio = box_w / float(box_h)
            records.append(
                CropRecord(
                    crop_file=crop_file,
                    source_image=image_path.name,
                    box_index=box_index,
                    bbox_x=box_x,
                    bbox_y=box_y,
                    bbox_w=box_w,
                    bbox_h=box_h,
                    aspect_ratio=aspect_ratio,
                    estimated_lines=estimate_line_count(aspect_ratio, threshold=threshold),
                    crop_width=crop_width,
                    crop_height=crop_height,
                )
            )

    LOGGER.info(
        "Extracted %d crops (%d newly written, %d already present)",
        len(records),
        written,
        reused,
    )
    if images_without_boxes:
        LOGGER.info("%d images carried no box", images_without_boxes)
    if unreadable_images:
        LOGGER.warning("%d images could not be decoded", unreadable_images)
    return records


def write_manifest(destination: Path, records: Sequence[CropRecord]) -> Path:
    """Write the crop manifest as a CSV file.

    ``utf-8-sig`` plus ``newline=""`` is the project convention: the BOM makes
    Excel pick the right encoding and the empty newline stops Python inserting
    blank rows on Windows.

    Args:
        destination: File to write. Parent directories are created.
        records: The crops to describe. An empty sequence still produces a
            header row, so downstream tools always see a valid file.

    Returns:
        The path written to.

    Raises:
        OSError: If the file cannot be written.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(MANIFEST_FIELDNAMES))
        writer.writeheader()
        for record in records:
            writer.writerow(record.as_row())
    LOGGER.info("Wrote manifest with %d rows: %s", len(records), destination)
    return destination


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser.

    Returns:
        A parser covering every knob the extraction step exposes.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Cut ground-truth plate regions out of a dataset split so they can "
            "be labelled by hand."
        )
    )
    parser.add_argument(
        "--datasets-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="Root of the datasets tree (default: <project root>/datasets).",
    )
    parser.add_argument(
        "--split",
        default="test",
        help="Split to extract from (default: %(default)s).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help=("Where crops are written " "(default: <datasets>/annotations/plates_to_label)."),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        metavar="FILE",
        help="Manifest CSV path (default: <output dir>/manifest.csv).",
    )
    parser.add_argument(
        "--target-height",
        type=int,
        default=DEFAULT_TARGET_HEIGHT,
        help="Scale every crop to this height in pixels (default: %(default)s).",
    )
    parser.add_argument(
        "--max-width",
        type=int,
        default=DEFAULT_MAX_WIDTH,
        help="Cap crop width at this many pixels (default: %(default)s).",
    )
    parser.add_argument(
        "--padding-ratio",
        type=float,
        default=DEFAULT_PADDING_RATIO,
        help=(
            "Cosmetic margin around each box, as a fraction of its size " "(default: %(default)s)."
        ),
    )
    parser.add_argument(
        "--aspect-ratio-threshold",
        type=float,
        default=TWO_LINE_ASPECT_RATIO_THRESHOLD,
        help="Below this width/height ratio a plate is guessed to have two lines "
        "(default: %(default)s).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-encode crops that already exist instead of reusing them.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Console verbosity (default: %(default)s).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the extraction step from the command line.

    Args:
        argv: Argument vector, defaulting to :data:`sys.argv`.

    Returns:
        ``0`` on success, ``1`` when the inputs are missing or nothing could be
        extracted. Returning a code rather than raising keeps the script usable
        from a shell pipeline.
    """
    args = _build_parser().parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        force=True,
    )

    datasets_dir = (args.datasets_dir or PROJECT_ROOT / "datasets").expanduser().resolve()
    images_dir = datasets_dir / "processed" / "yolo" / "images" / args.split
    labels_dir = datasets_dir / "processed" / "yolo" / "labels" / args.split
    output_dir = (
        (args.output_dir or datasets_dir / "annotations" / "plates_to_label").expanduser().resolve()
    )
    manifest_path = (args.manifest or output_dir / "manifest.csv").expanduser().resolve()

    try:
        records = extract_split(
            images_dir,
            labels_dir,
            output_dir,
            target_height=args.target_height,
            max_width=args.max_width,
            padding_ratio=args.padding_ratio,
            threshold=args.aspect_ratio_threshold,
            overwrite=args.overwrite,
        )
    except (FileNotFoundError, ValueError) as exc:
        LOGGER.error("Extraction failed: %s", exc)
        return 1

    if not records:
        LOGGER.error(
            "No crops were produced; check that %s and %s contain matching files",
            images_dir,
            labels_dir,
        )
        return 1

    try:
        write_manifest(manifest_path, records)
    except OSError as exc:
        LOGGER.error("Cannot write the manifest: %s", exc)
        return 1

    single_line = sum(1 for record in records if record.estimated_lines == 1)
    LOGGER.info(
        "Line-count estimate: %d single-line, %d two-line",
        single_line,
        len(records) - single_line,
    )
    LOGGER.info("Crops are in %s", output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
