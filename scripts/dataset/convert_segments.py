"""Convert YOLO segmentation polygon labels into detection bounding boxes.

Some Vietnamese license plate datasets ship *segmentation* labels: each line is
``class x1 y1 x2 y2 ... xn yn`` with an arbitrary number of polygon vertices.
The rest of this pipeline -- and YOLO11 detection training -- expects
``class x_center y_center width height``.

The two formats are not merely different, they are silently incompatible: a
polygon line has at least 7 fields, so the detection parser happily reads
``x1 y1 x2 y2`` as ``x y w h`` and produces a box that is geometrically
meaningless but structurally valid. Nothing crashes, verification mostly
passes, and the model trains on nonsense. Converting explicitly -- and keeping
the originals -- is the only safe option.

Beyond geometry, this script preserves a second piece of information that would
otherwise be thrown away. Datasets that separate long plates from square plates
(``BSD`` / ``BSV``) are encoding the **line count** of the plate, which is the
single hardest axis of this problem: OpenALPR scores 94.3% on one-line car
plates but 45.7% on two-line motorcycle plates. Downstream, ``split.py
--stratify`` and ``statistics.py`` otherwise have to guess the line count from
the box aspect ratio, a heuristic that perspective and loose boxes routinely
defeat. Mapping the source class to a true ``line_count`` in the label extras
replaces that guess with ground truth.

Example:
    python scripts/dataset/convert_segments.py \\
        --input-dir datasets/raw/hf_vn_plates_segment \\
        --line-count-map 0=1,1=2
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

from _common import (
    add_common_arguments,
    bootstrap_project_path,
    configure_logging,
    write_json,
)

bootstrap_project_path()

from ai.data.schema import BoxRecord, write_yolo_label_file  # noqa: E402

LOGGER = logging.getLogger(__name__)

#: Directory name the untouched polygon labels are moved to. Its presence is
#: also how a re-run knows it must read the originals rather than re-convert
#: already-converted boxes.
BACKUP_DIR_NAME = "labels_polygon"

#: A detection line has exactly this many fields before the optional extras.
DETECTION_FIELD_COUNT = 5


@dataclass(frozen=True)
class ConversionStats:
    """Tally of one conversion run.

    Attributes:
        files_read: Label files opened.
        files_written: Label files written.
        polygons_converted: Polygon lines turned into boxes.
        passthrough_boxes: Lines already in detection format, copied as-is.
        lines_skipped: Lines that could not be parsed at all.
        clipped: Boxes whose extent left ``[0, 1]`` and was clipped.
    """

    files_read: int = 0
    files_written: int = 0
    polygons_converted: int = 0
    passthrough_boxes: int = 0
    lines_skipped: int = 0
    clipped: int = 0


def parse_line_count_map(raw: str) -> dict[int, int]:
    """Parse a ``0=1,1=2`` class-id-to-line-count mapping.

    Args:
        raw: Comma-separated ``class_id=line_count`` pairs. Empty means no
            mapping, in which case line counts are left unknown and downstream
            code falls back to the aspect-ratio heuristic.

    Returns:
        Mapping from source class id to line count.

    Raises:
        argparse.ArgumentTypeError: If a pair is malformed or the line count is
            neither 1 nor 2. Vietnamese plates have no third form, so any other
            value is a typo rather than an exotic case worth supporting.
    """
    mapping: dict[int, int] = {}
    if not raw.strip():
        return mapping

    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" not in chunk:
            raise argparse.ArgumentTypeError(f"expected 'class_id=line_count', got {chunk!r}")
        left, _, right = chunk.partition("=")
        try:
            class_id = int(left)
            line_count = int(right)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"both sides of {chunk!r} must be integers") from exc
        if line_count not in (1, 2):
            raise argparse.ArgumentTypeError(
                f"line count must be 1 or 2, got {line_count} in {chunk!r}"
            )
        mapping[class_id] = line_count
    return mapping


def polygon_to_box(
    coords: list[float],
    *,
    class_id: int,
    line_count: int | None,
) -> tuple[BoxRecord, bool]:
    """Compute the axis-aligned bounding box of a normalised polygon.

    Args:
        coords: Flat ``[x1, y1, x2, y2, ...]`` list of normalised vertices.
        class_id: Source class id, carried through unchanged.
        line_count: True line count when the source class encodes it.

    Returns:
        ``(box, was_clipped)``. ``was_clipped`` is ``True`` when any vertex lay
        outside ``[0, 1]`` and had to be pulled back in.

    Raises:
        ValueError: If the coordinate list is empty or has an odd length.
    """
    if not coords or len(coords) % 2 != 0:
        raise ValueError(
            f"polygon needs an even, non-zero number of coordinates, got {len(coords)}"
        )

    xs = coords[0::2]
    ys = coords[1::2]

    raw_min_x, raw_max_x = min(xs), max(xs)
    raw_min_y, raw_max_y = min(ys), max(ys)

    min_x, max_x = max(0.0, raw_min_x), min(1.0, raw_max_x)
    min_y, max_y = max(0.0, raw_min_y), min(1.0, raw_max_y)

    was_clipped = raw_min_x < 0.0 or raw_min_y < 0.0 or raw_max_x > 1.0 or raw_max_y > 1.0

    return (
        BoxRecord(
            x_center=(min_x + max_x) / 2.0,
            y_center=(min_y + max_y) / 2.0,
            width=max(0.0, max_x - min_x),
            height=max(0.0, max_y - min_y),
            class_id=class_id,
            plate_text=None,
            line_count=line_count,  # type: ignore[arg-type]
        ),
        was_clipped,
    )


def convert_label_file(
    source: Path,
    destination: Path,
    *,
    line_count_map: dict[int, int],
) -> ConversionStats:
    """Convert one label file from polygons to boxes.

    Lines already in detection format are passed through untouched, so running
    this on a mixed or partially converted directory is safe.

    Args:
        source: Label file to read.
        destination: Where the converted labels are written. Parents are made.
        line_count_map: Source class id to true line count.

    Returns:
        Stats for this single file.
    """
    polygons = 0
    passthrough = 0
    skipped = 0
    clipped = 0
    boxes: list[BoxRecord] = []

    try:
        text = source.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        LOGGER.warning("Cannot read %s: %s", source, exc)
        return ConversionStats(files_read=0, lines_skipped=1)

    for line_number, line in enumerate(text.splitlines(), start=1):
        parts = line.split()
        if not parts:
            continue

        try:
            class_id = int(float(parts[0]))
        except ValueError:
            LOGGER.warning(
                "%s:%d: class id %r is not numeric, line skipped",
                source,
                line_number,
                parts[0],
            )
            skipped += 1
            continue

        line_count = line_count_map.get(class_id)

        if len(parts) == DETECTION_FIELD_COUNT or (
            len(parts) > DETECTION_FIELD_COUNT and len(parts) % 2 == 0
        ):
            # Even total field count means class + 4 geometry + extras, i.e.
            # already a detection line. A polygon always yields an odd total
            # (1 class + an even number of coordinates).
            try:
                box = BoxRecord.from_yolo_line(line)
            except Exception as exc:  # noqa: BLE001 - report, never abort
                LOGGER.warning("%s:%d: %s, line skipped", source, line_number, exc)
                skipped += 1
                continue
            if line_count is not None and box.line_count is None:
                from dataclasses import replace

                box = replace(box, line_count=line_count)  # type: ignore[arg-type]
            boxes.append(box)
            passthrough += 1
            continue

        try:
            coords = [float(value) for value in parts[1:]]
        except ValueError:
            LOGGER.warning(
                "%s:%d: non-numeric polygon coordinate, line skipped",
                source,
                line_number,
            )
            skipped += 1
            continue

        try:
            box, was_clipped = polygon_to_box(coords, class_id=class_id, line_count=line_count)
        except ValueError as exc:
            LOGGER.warning("%s:%d: %s, line skipped", source, line_number, exc)
            skipped += 1
            continue

        boxes.append(box)
        polygons += 1
        clipped += int(was_clipped)

    destination.parent.mkdir(parents=True, exist_ok=True)
    # include_extras is always on: the line count is the whole reason this
    # script bothers to look at the source class id.
    write_yolo_label_file(destination, boxes, include_extras=True)

    return ConversionStats(
        files_read=1,
        files_written=1,
        polygons_converted=polygons,
        passthrough_boxes=passthrough,
        lines_skipped=skipped,
        clipped=clipped,
    )


def resolve_source_labels(input_dir: Path, *, in_place: bool) -> tuple[Path, Path]:
    """Decide which directory to read labels from and which to write to.

    When converting in place the original ``labels/`` is moved aside to
    :data:`BACKUP_DIR_NAME` on the first run. Later runs detect the backup and
    read from it, which makes the operation idempotent -- the polygons are never
    lost and never double-converted.

    Args:
        input_dir: Dataset root containing ``labels/``.
        in_place: Overwrite ``labels/`` rather than writing somewhere else.

    Returns:
        ``(source_labels_dir, destination_labels_dir)``.

    Raises:
        FileNotFoundError: If no label directory can be found.
    """
    labels = input_dir / "labels"
    backup = input_dir / BACKUP_DIR_NAME

    if backup.is_dir():
        LOGGER.info("Found existing polygon backup at %s, reading from it", backup)
        return backup, labels

    if not labels.is_dir():
        raise FileNotFoundError(
            f"No labels directory under {input_dir}. Expected {labels} "
            f"or a previous backup at {backup}."
        )

    if in_place:
        LOGGER.info("Moving original polygon labels %s -> %s", labels, backup)
        labels.rename(backup)
        return backup, labels

    return labels, labels


def convert_dataset(
    input_dir: Path,
    *,
    output_dir: Path | None,
    line_count_map: dict[int, int],
) -> ConversionStats:
    """Convert every label file in a dataset.

    Args:
        input_dir: Dataset root containing ``labels/``.
        output_dir: Write converted labels here instead of in place.
        line_count_map: Source class id to true line count.

    Returns:
        Aggregated stats across every file.

    Raises:
        FileNotFoundError: If no label directory exists.
    """
    in_place = output_dir is None
    source_dir, destination_dir = resolve_source_labels(input_dir, in_place=in_place)
    if output_dir is not None:
        destination_dir = output_dir

    label_files = sorted(source_dir.rglob("*.txt"))
    if not label_files:
        LOGGER.warning("No .txt label files found under %s", source_dir)

    total = ConversionStats()
    for label_file in label_files:
        relative = label_file.relative_to(source_dir)
        stats = convert_label_file(
            label_file,
            destination_dir / relative,
            line_count_map=line_count_map,
        )
        total = ConversionStats(
            files_read=total.files_read + stats.files_read,
            files_written=total.files_written + stats.files_written,
            polygons_converted=total.polygons_converted + stats.polygons_converted,
            passthrough_boxes=total.passthrough_boxes + stats.passthrough_boxes,
            lines_skipped=total.lines_skipped + stats.lines_skipped,
            clipped=total.clipped + stats.clipped,
        )

    return total


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser.

    Returns:
        The configured parser.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Convert YOLO segmentation polygon labels into detection bounding "
            "boxes, preserving the plate line count encoded in the source class."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Originals are moved to 'labels_polygon/' and never deleted, so the "
            "conversion can always be redone or audited."
        ),
    )
    add_common_arguments(parser)
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Dataset root containing a labels/ directory.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Write converted labels here. Omit to convert in place, moving the "
            "originals to labels_polygon/."
        ),
    )
    parser.add_argument(
        "--line-count-map",
        type=parse_line_count_map,
        default="",
        help=(
            "Map source class ids to true plate line counts, e.g. '0=1,1=2' for "
            "a dataset whose class 0 is a long one-line plate (BSD) and class 1 "
            "a square two-line plate (BSV). Without this the line count stays "
            "unknown and downstream code falls back to the aspect-ratio guess."
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Write a JSON summary of the conversion here.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point.

    Args:
        argv: Argument vector; defaults to ``sys.argv[1:]``.

    Returns:
        Process exit code: 0 on success, 1 if the dataset could not be read.
    """
    args = build_parser().parse_args(argv)
    configure_logging(args.log_level)

    input_dir: Path = args.input_dir.expanduser().resolve()
    line_count_map: dict[int, int] = args.line_count_map

    LOGGER.info("Converting polygon labels under %s", input_dir)
    if line_count_map:
        LOGGER.info("Line count map: %s", line_count_map)
    else:
        LOGGER.warning(
            "No --line-count-map given; line counts stay unknown and downstream "
            "stratification falls back to the aspect-ratio heuristic."
        )

    try:
        stats = convert_dataset(
            input_dir,
            output_dir=args.output_dir,
            line_count_map=line_count_map,
        )
    except FileNotFoundError as exc:
        LOGGER.error("%s", exc)
        return 1

    LOGGER.info("Label files written : %d", stats.files_written)
    LOGGER.info("Polygons converted  : %d", stats.polygons_converted)
    LOGGER.info("Already boxes       : %d", stats.passthrough_boxes)
    LOGGER.info("Lines skipped       : %d", stats.lines_skipped)
    LOGGER.info("Boxes clipped to 0-1: %d", stats.clipped)

    if args.report is not None:
        payload = {
            "input_dir": str(input_dir),
            "line_count_map": {str(k): v for k, v in line_count_map.items()},
            "files_written": stats.files_written,
            "polygons_converted": stats.polygons_converted,
            "passthrough_boxes": stats.passthrough_boxes,
            "lines_skipped": stats.lines_skipped,
            "clipped": stats.clipped,
        }
        write_json(args.report, payload)
        LOGGER.info("Report written to %s", args.report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
