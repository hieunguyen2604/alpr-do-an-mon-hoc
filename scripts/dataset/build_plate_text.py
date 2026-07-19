#!/usr/bin/env python
"""Rebuild license-plate text strings from character-level YOLO annotations.

Two of the surveyed Roboflow datasets annotate **every character** on the plate
with its own bounding box instead of annotating the plate as a whole. That makes
them the only source in this project that carries the information needed to
measure OCR accuracy (NFR-A4..A7): the ground-truth *string* of each plate.

This script turns those per-character boxes back into a string:

1. Decode each box's class id into a character (see :data:`DATASET_SPECS`).
2. Cluster the boxes into text lines by their vertical centre.
3. Sort lines top-to-bottom, and the boxes inside each line left-to-right.
4. Concatenate. The number of clusters is the plate's **real** ``line_count`` --
   a measured label, not the aspect-ratio heuristic used elsewhere in the
   pipeline (``scripts/dataset/README.md`` section 5).
5. Check the result against the Vietnamese plate grammar via
   :mod:`ai.inference.normalizer`, which is the Phase 4 port of
   ``docs/reports/01-vn-plate-standards.md`` section 8.

Output is ``datasets/annotations/plate_text_labels.csv``. With
``--verify-samples N`` the script also renders N random images with their boxes
and reconstructed string drawn on top, so that the reconstruction can be checked
by eye before the labels are trusted.

Class-id decoding
    ``roboflow_ocr_conversion`` names its classes with the characters
    themselves, so decoding is the identity.

    ``roboflow_ocr_plate`` does **not**: its ``data.yaml`` names are the opaque
    strings ``'0'``..``'29'``. The mapping from those ids to characters was
    recovered from a stray image inside the dataset itself
    (``0_jpg.rf.7b00e9b620a815161f9df08554976e69.jpg``), which is not a plate at
    all but a rendered font chart listing glyphs against their Unicode
    codepoints, fully annotated with all 30 classes. Reading the chart yields
    :data:`_OCR_PLATE_CHARSET`. See ``docs/reports/04-ocr-report.md`` for the
    derivation and its corroboration against class frequencies.

Example
    python scripts/dataset/build_plate_text.py --verify-samples 20
"""

from __future__ import annotations

import argparse
import collections
import logging
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Iterable, Sequence

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    add_common_arguments,
    bootstrap_project_path,
    configure_logging,
    resolve_dataset_paths,
    write_csv,
    write_json,
)

LOGGER: Final = logging.getLogger(__name__)

IMAGE_EXTENSIONS: Final[tuple[str, ...]] = (".jpg", ".jpeg", ".png", ".bmp", ".webp")

#: Filename markers of image families that turned out **not** to be Vietnamese
#: plates at all. ``roboflow_ocr_plate`` is contaminated with European plates:
#: the ``iwt*`` family is Czech (visible ``CZ`` EU band, format ``1B9 4686``) and
#: the ``*PlateBaza*`` family comes from a Croatian/Polish plate database
#: (``ZG 567-EF``). Both decode correctly but can never match a Vietnamese
#: pattern, so they are flagged rather than counted as reconstruction failures.
FOREIGN_SOURCE_MARKERS: Final[tuple[str, ...]] = ("iwt", "platebaza")

#: Character set of ``roboflow_ocr_plate``, indexed by the integer value of the
#: class *name* in ``data.yaml`` (not by the class index). Recovered from the
#: annotated font chart shipped inside the dataset; see the module docstring.
#: Equal to ``OCR_SAFE_CHARSET`` minus the letter ``R``.
_OCR_PLATE_CHARSET: Final[str] = "123456789ABCDEFGHKLMNPSTUVXYZ0"


@dataclass(frozen=True)
class DatasetSpec:
    """How to decode one dataset's class ids into characters.

    :param directory: Directory name under ``datasets/raw``.
    :param decoding: ``"literal"`` when ``data.yaml`` names *are* the characters,
        ``"charset"`` when the names are integer indices into :attr:`charset`.
    :param charset: Ordered characters, used only when ``decoding == "charset"``.
    :param splits: Sub-directories to scan.
    """

    directory: str
    decoding: str
    charset: str | None = None
    splits: tuple[str, ...] = ("train", "valid", "test")


DATASET_SPECS: Final[tuple[DatasetSpec, ...]] = (
    DatasetSpec(directory="roboflow_ocr_plate", decoding="charset", charset=_OCR_PLATE_CHARSET),
    DatasetSpec(directory="roboflow_ocr_conversion", decoding="literal"),
)


#: Vietnamese electric two-wheeler series. The plate carries ``MĐ``; the letter
#: ``Đ`` is outside the annotation charset and was written as ``D``. These are
#: real Vietnamese plates but the Phase 1 grammar has no pattern for them.
_ELECTRIC_SERIES_RE: Final = re.compile(r"^\d{2}M[DB]")


class PlateTextError(RuntimeError):
    """Raised when a dataset cannot be decoded at all."""


@dataclass(frozen=True)
class CharBox:
    """One decoded character box in normalised YOLO coordinates."""

    char: str
    x_center: float
    y_center: float
    width: float
    height: float


@dataclass
class Reconstruction:
    """Result of rebuilding one plate string."""

    plate_text: str
    line_count: int
    char_count: int
    lines: list[list[CharBox]]
    notes: list[str]


# ---------------------------------------------------------------------------
# Class-id decoding
# ---------------------------------------------------------------------------


def build_class_map(spec: DatasetSpec, names: Sequence[str]) -> dict[int, str]:
    """Map YOLO class index to character for one dataset.

    :param spec: Decoding rule for the dataset.
    :param names: ``names`` list from ``data.yaml``, ordered by class index.
    :returns: Mapping of class index to a single character.
    :raises PlateTextError: If the names cannot be decoded under ``spec``.
    """
    mapping: dict[int, str] = {}
    if spec.decoding == "literal":
        for index, name in enumerate(names):
            text = str(name).strip().upper()
            if len(text) != 1:
                raise PlateTextError(
                    f"{spec.directory}: class name {name!r} is not a single character"
                )
            mapping[index] = text
        return mapping

    if spec.decoding == "charset":
        if not spec.charset:
            raise PlateTextError(f"{spec.directory}: charset decoding requires a charset")
        for index, name in enumerate(names):
            try:
                position = int(str(name).strip())
            except ValueError as exc:
                raise PlateTextError(
                    f"{spec.directory}: class name {name!r} is not an integer index"
                ) from exc
            if not 0 <= position < len(spec.charset):
                raise PlateTextError(
                    f"{spec.directory}: class name {name!r} outside charset of "
                    f"length {len(spec.charset)}"
                )
            mapping[index] = spec.charset[position]
        return mapping

    raise PlateTextError(f"{spec.directory}: unknown decoding {spec.decoding!r}")


def read_label_file(path: Path, class_map: dict[int, str]) -> list[CharBox]:
    """Parse one YOLO label file into decoded character boxes.

    Malformed rows are skipped with a warning rather than aborting the run.

    :param path: Label file in YOLO ``cls cx cy w h`` format.
    :param class_map: Mapping from class index to character.
    :returns: Decoded boxes, in file order.
    """
    boxes: list[CharBox] = []
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        LOGGER.warning("Cannot read label file %s", path)
        return boxes

    for line_number, line in enumerate(raw.splitlines(), start=1):
        parts = line.split()
        if not parts:
            continue
        if len(parts) < 5:
            LOGGER.warning("%s:%d has %d fields, expected 5", path, line_number, len(parts))
            continue
        try:
            class_index = int(float(parts[0]))
            cx, cy, width, height = (float(value) for value in parts[1:5])
        except ValueError:
            LOGGER.warning("%s:%d is not numeric", path, line_number)
            continue
        char = class_map.get(class_index)
        if char is None:
            LOGGER.warning("%s:%d unknown class index %d", path, line_number, class_index)
            continue
        boxes.append(CharBox(char=char, x_center=cx, y_center=cy, width=width, height=height))
    return boxes


# ---------------------------------------------------------------------------
# Line clustering and string reconstruction
# ---------------------------------------------------------------------------


def cluster_lines(boxes: Sequence[CharBox], *, gap_ratio: float = 0.6) -> list[list[CharBox]]:
    """Group character boxes into text lines by vertical position.

    Boxes are sorted by vertical centre and split wherever the gap to the next
    box exceeds ``gap_ratio`` times the median character height. A ratio below 1
    is what separates *stacked lines* (gap of roughly one character height) from
    *jitter inside one line* (gap of a few percent), and unlike a fixed
    ``k`` it does not force a two-line answer onto a one-line plate.

    :param boxes: Decoded character boxes.
    :param gap_ratio: Fraction of median character height treated as a line break.
    :returns: Lines ordered top to bottom; each line keeps input order.
    """
    if not boxes:
        return []

    ordered = sorted(boxes, key=lambda box: box.y_center)
    heights = sorted(box.height for box in ordered)
    median_height = heights[len(heights) // 2]
    if median_height <= 0:
        return [list(ordered)]

    threshold = gap_ratio * median_height
    lines: list[list[CharBox]] = [[ordered[0]]]
    for previous, current in zip(ordered, ordered[1:]):
        if current.y_center - previous.y_center > threshold:
            lines.append([current])
        else:
            lines[-1].append(current)
    return lines


def reconstruct(boxes: Sequence[CharBox], *, gap_ratio: float = 0.6) -> Reconstruction:
    """Rebuild the plate string from character boxes.

    :param boxes: Decoded character boxes for one image.
    :param gap_ratio: Passed through to :func:`cluster_lines`.
    :returns: The reconstruction, including per-line boxes for rendering.
    """
    notes: list[str] = []
    lines = cluster_lines(boxes, gap_ratio=gap_ratio)
    sorted_lines = [sorted(line, key=lambda box: box.x_center) for line in lines]
    text = "".join(box.char for line in sorted_lines for box in line)

    if len(sorted_lines) > 2:
        notes.append(f"clustered_into_{len(sorted_lines)}_lines_not_a_plate")
    if len(boxes) < 6:
        notes.append(f"only_{len(boxes)}_characters")
    if len(boxes) > 10:
        notes.append(f"{len(boxes)}_characters_above_plate_maximum")

    overlaps = _count_horizontal_overlaps(sorted_lines)
    if overlaps:
        notes.append(f"{overlaps}_overlapping_boxes_in_line")

    return Reconstruction(
        plate_text=text,
        line_count=len(sorted_lines),
        char_count=len(boxes),
        lines=sorted_lines,
        notes=notes,
    )


def is_foreign_source(image_path: Path) -> bool:
    """Report whether an image belongs to a known non-Vietnamese family.

    :param image_path: Image path whose filename is inspected.
    :returns: ``True`` when the filename carries a :data:`FOREIGN_SOURCE_MARKERS` marker.
    """
    stem = image_path.stem.lower()
    return any(marker in stem for marker in FOREIGN_SOURCE_MARKERS)


def _count_horizontal_overlaps(lines: Sequence[Sequence[CharBox]]) -> int:
    """Count neighbouring boxes inside a line that overlap heavily.

    Heavy horizontal overlap means two boxes annotate the same glyph, which
    silently duplicates a character in the reconstructed string.

    :param lines: Lines of boxes already sorted left to right.
    :returns: Number of overlapping neighbour pairs.
    """
    overlaps = 0
    for line in lines:
        for left, right in zip(line, line[1:]):
            centre_gap = abs(right.x_center - left.x_center)
            if centre_gap < 0.35 * min(left.width, right.width):
                overlaps += 1
    return overlaps


# ---------------------------------------------------------------------------
# Rendering for manual verification
# ---------------------------------------------------------------------------


def render_verification_sample(
    image_path: Path,
    reconstruction: Reconstruction,
    destination: Path,
) -> bool:
    """Draw character boxes and the reconstructed string onto a copy of an image.

    :param image_path: Source image.
    :param reconstruction: Reconstruction to visualise.
    :param destination: Output PNG path.
    :returns: ``True`` when the file was written.
    """
    try:
        import cv2  # noqa: PLC0415
    except ImportError:
        LOGGER.error("opencv-python is required for --verify-samples")
        return False

    image = cv2.imread(str(image_path))
    if image is None:
        LOGGER.warning("Cannot decode image %s", image_path)
        return False

    height, width = image.shape[:2]
    palette = [(60, 200, 60), (60, 160, 255)]
    for line_index, line in enumerate(reconstruction.lines):
        colour = palette[line_index % len(palette)]
        for order, box in enumerate(line):
            x1 = int((box.x_center - box.width / 2) * width)
            y1 = int((box.y_center - box.height / 2) * height)
            x2 = int((box.x_center + box.width / 2) * width)
            y2 = int((box.y_center + box.height / 2) * height)
            cv2.rectangle(image, (x1, y1), (x2, y2), colour, 1)
            cv2.putText(
                image,
                f"{order}:{box.char}",
                (x1, max(10, y1 - 3)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                colour,
                1,
                cv2.LINE_AA,
            )

    banner = f"{reconstruction.plate_text}  lines={reconstruction.line_count}"
    cv2.rectangle(image, (0, 0), (width, 26), (0, 0, 0), -1)
    cv2.putText(
        image, banner, (5, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA
    )

    destination.parent.mkdir(parents=True, exist_ok=True)
    return bool(cv2.imwrite(str(destination), image))


# ---------------------------------------------------------------------------
# Dataset traversal
# ---------------------------------------------------------------------------


def _find_image(images_dir: Path, stem: str) -> Path | None:
    """Locate the image matching a label stem, trying the usual extensions."""
    for extension in IMAGE_EXTENSIONS:
        candidate = images_dir / f"{stem}{extension}"
        if candidate.exists():
            return candidate
    return None


def iter_dataset_labels(
    dataset_dir: Path, spec: DatasetSpec
) -> Iterable[tuple[str, Path, list[CharBox]]]:
    """Yield ``(split, image_path, boxes)`` for every labelled image in a dataset.

    :param dataset_dir: Dataset root containing ``data.yaml`` and split folders.
    :param spec: Decoding rule for the dataset.
    :raises PlateTextError: If ``data.yaml`` is missing or undecodable.
    """
    config_path = dataset_dir / "data.yaml"
    if not config_path.exists():
        raise PlateTextError(f"{dataset_dir}: data.yaml not found")

    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    names = config.get("names")
    if not names:
        raise PlateTextError(f"{config_path}: no names")
    class_map = build_class_map(spec, list(names))
    LOGGER.info(
        "%s: %d classes decoded to charset %r",
        spec.directory,
        len(class_map),
        "".join(sorted(set(class_map.values()))),
    )

    for split in spec.splits:
        labels_dir = dataset_dir / split / "labels"
        images_dir = dataset_dir / split / "images"
        if not labels_dir.is_dir():
            continue
        for label_path in sorted(labels_dir.glob("*.txt")):
            image_path = _find_image(images_dir, label_path.stem)
            if image_path is None:
                LOGGER.warning("No image for label %s", label_path)
                continue
            yield split, image_path, read_label_file(label_path, class_map)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def build_rows(
    raw_dir: Path,
    specs: Sequence[DatasetSpec],
    *,
    gap_ratio: float,
) -> tuple[list[dict[str, Any]], list[tuple[Path, Reconstruction, bool]]]:
    """Reconstruct plate strings for every dataset in ``specs``.

    :param raw_dir: ``datasets/raw`` directory.
    :param specs: Datasets to process.
    :param gap_ratio: Line-clustering threshold.
    :returns: ``(csv_rows, renderables)`` where renderables pair image paths with
        their reconstruction for optional visual verification.
    """
    bootstrap_project_path()
    from ai.inference.normalizer import VietnamesePlateNormalizer  # noqa: PLC0415

    normalizer = VietnamesePlateNormalizer()
    rows: list[dict[str, Any]] = []
    renderables: list[tuple[Path, Reconstruction, bool]] = []

    for spec in specs:
        dataset_dir = raw_dir / spec.directory
        if not dataset_dir.is_dir():
            LOGGER.warning("Dataset directory missing, skipping: %s", dataset_dir)
            continue

        for split, image_path, boxes in iter_dataset_labels(dataset_dir, spec):
            if not boxes:
                rows.append(
                    {
                        "image_path": image_path.as_posix(),
                        "plate_text": "",
                        "line_count": 0,
                        "char_count": 0,
                        "is_valid_format": False,
                        "source_dataset": spec.directory,
                        "confidence_note": "no_boxes",
                    }
                )
                continue

            result = reconstruct(boxes, gap_ratio=gap_ratio)
            outcome = normalizer.normalize_detailed(
                result.plate_text, line_count=result.line_count
            )
            is_valid = bool(outcome.is_valid_format and outcome.text == result.plate_text)

            notes = list(result.notes)
            if is_foreign_source(image_path):
                notes.append("non_vietnamese_source_image")
            if _ELECTRIC_SERIES_RE.match(result.plate_text):
                notes.append("electric_series_MD_not_in_phase1_grammar")
            if outcome.is_valid_format and outcome.text != result.plate_text:
                notes.append("valid_only_after_normalizer_correction")
            if not outcome.is_valid_format:
                notes.append("no_matching_plate_pattern")

            rows.append(
                {
                    "image_path": image_path.as_posix(),
                    "plate_text": result.plate_text,
                    "line_count": result.line_count,
                    "char_count": result.char_count,
                    "is_valid_format": is_valid,
                    "source_dataset": spec.directory,
                    "confidence_note": ";".join(notes) if notes else f"ok;split={split}",
                }
            )
            renderables.append((image_path, result, is_valid))

    return rows, renderables


def summarise(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate reconstruction statistics for the run report."""
    per_dataset: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    line_counts: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    reasons: collections.Counter = collections.Counter()

    for row in rows:
        dataset = row["source_dataset"]
        per_dataset[dataset]["images"] += 1
        if row["plate_text"]:
            per_dataset[dataset]["reconstructed"] += 1
        if row["is_valid_format"]:
            per_dataset[dataset]["valid_format"] += 1
        else:
            for note in str(row["confidence_note"]).split(";"):
                if note and not note.startswith("ok"):
                    reasons[note] += 1
        line_counts[dataset][row["line_count"]] += 1

    foreign = [row for row in rows if "non_vietnamese_source_image" in str(row["confidence_note"])]
    domestic = [row for row in rows if row not in foreign]
    domestic_valid = sum(1 for row in domestic if row["is_valid_format"])

    return {
        "charsets": {
            spec.directory: spec.charset for spec in DATASET_SPECS if spec.charset
        },
        "vietnamese_only": {
            "foreign_source_images": len(foreign),
            "vietnamese_candidate_images": len(domestic),
            "valid_format": domestic_valid,
            "valid_format_rate": round(domestic_valid / max(1, len(domestic)), 4),
        },
        "per_dataset": {
            name: {
                **dict(counter),
                "valid_format_rate": round(
                    counter["valid_format"] / max(1, counter["images"]), 4
                ),
                "line_count_distribution": dict(sorted(line_counts[name].items())),
            }
            for name, counter in per_dataset.items()
        },
        "totals": {
            "images": len(rows),
            "reconstructed": sum(1 for row in rows if row["plate_text"]),
            "valid_format": sum(1 for row in rows if row["is_valid_format"]),
        },
        "failure_reasons": dict(reasons.most_common()),
    }


def _stratified_sample(
    renderables: Sequence[tuple[Path, Reconstruction, bool]],
    count: int,
    *,
    seed: int,
) -> list[tuple[Path, Reconstruction, bool]]:
    """Pick verification samples spanning both line counts and both verdicts.

    A uniform random sample would be dominated by two-line plates that already
    validate, which is exactly the case least in need of human eyes. This draws
    from four strata -- one-line valid, two-line valid, one-line rejected,
    two-line rejected -- so the reviewer sees the failure modes too.

    :param renderables: Candidates as ``(image_path, reconstruction, is_valid)``.
    :param count: Total number of samples wanted.
    :param seed: Random seed.
    :returns: Selected candidates.
    """
    rng = random.Random(seed)
    strata: dict[tuple[bool, int], list[tuple[Path, Reconstruction, bool]]] = (
        collections.defaultdict(list)
    )
    for item in renderables:
        strata[(item[2], min(item[1].line_count, 2))].append(item)

    chosen: list[tuple[Path, Reconstruction, bool]] = []
    order = sorted(strata)
    per_stratum = max(1, count // max(1, len(order)))
    for key in order:
        pool = strata[key]
        chosen.extend(rng.sample(pool, min(per_stratum, len(pool))))

    remaining = [item for item in renderables if item not in chosen]
    if len(chosen) < count and remaining:
        chosen.extend(rng.sample(remaining, min(count - len(chosen), len(remaining))))
    return chosen[:count]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Rebuild plate strings from character-level YOLO annotations."
    )
    add_common_arguments(parser)
    parser.add_argument(
        "--gap-ratio",
        type=float,
        default=0.6,
        help="Line break threshold as a fraction of median character height.",
    )
    parser.add_argument(
        "--verify-samples",
        type=int,
        default=0,
        help="Render this many random annotated images for manual verification.",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for verification sampling."
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point."""
    args = parse_args(argv)
    configure_logging(getattr(args, "log_level", "INFO"))
    paths = resolve_dataset_paths(getattr(args, "datasets_dir", None))

    try:
        rows, renderables = build_rows(paths.raw, DATASET_SPECS, gap_ratio=args.gap_ratio)
    except PlateTextError:
        LOGGER.exception("Cannot decode dataset")
        return 1

    if not rows:
        LOGGER.error("No character-level datasets found under %s", paths.raw)
        return 1

    csv_path = paths.annotations / "plate_text_labels.csv"
    write_csv(
        csv_path,
        rows,
        fieldnames=[
            "image_path",
            "plate_text",
            "line_count",
            "char_count",
            "is_valid_format",
            "source_dataset",
            "confidence_note",
        ],
    )
    LOGGER.info("Wrote %d rows to %s", len(rows), csv_path)

    report = summarise(rows)
    report_path = paths.reports / "plate_text_report.json"
    write_json(report_path, report)
    LOGGER.info("Wrote report to %s", report_path)

    if args.verify_samples > 0 and renderables:
        sample_dir = paths.annotations / "verify_samples"
        sample_dir.mkdir(parents=True, exist_ok=True)
        chosen = _stratified_sample(renderables, args.verify_samples, seed=args.seed)
        written = 0
        for image_path, result, is_valid in chosen:
            tag = "OK" if is_valid else "CHECK"
            name = f"{tag}__{result.plate_text or 'EMPTY'}__{image_path.stem[:32]}.png"
            if render_verification_sample(image_path, result, sample_dir / name):
                written += 1
        LOGGER.info("Wrote %d verification images to %s", written, sample_dir)

    totals = report["totals"]
    LOGGER.info(
        "Images=%d reconstructed=%d valid_format=%d (%.1f%%)",
        totals["images"],
        totals["reconstructed"],
        totals["valid_format"],
        100 * totals["valid_format"] / max(1, totals["images"]),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
