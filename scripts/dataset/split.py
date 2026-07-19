"""Split the merged corpus into train/val/test without leaking duplicates.

Usage examples::

    python scripts/dataset/split.py
    python scripts/dataset/split.py --ratios 0.8 0.1 0.1 --stratify
    python scripts/dataset/split.py --seed 1337 --link

The leakage problem this script exists to solve
------------------------------------------------
Splitting image-by-image is wrong for this dataset. The public Vietnamese plate
collections overlap heavily: the same photograph appears in several of them, and
a single collection often contains several frames of one vehicle. Assign those
copies independently and one lands in ``train`` while its twin lands in
``test``. The model then scores well on ``test`` by recognising a picture it has
already memorised, and the reported accuracy is fiction.

The unit of splitting here is therefore a **group**, not an image:

1. ``deduplicate.py`` writes ``duplicate_groups.json`` -- every set of images it
   judged near-identical.
2. Every image in such a group forms one indivisible unit. Images in no group
   are singleton units.
3. Units, not images, are dealt into the three splits.

A group is kept whole even when its members were never deleted, so running
``deduplicate.py`` in report-only mode is enough to make the split safe.

Because units vary in size, a plain proportional cut would overshoot. Units are
assigned greedily to whichever split is furthest below its target share, which
keeps the realised ratios close to the requested ones without ever breaking a
unit apart.

Stratification
--------------
``--stratify`` balances the estimated one-line / two-line plate mix across the
splits. Two-line motorcycle plates are the project's known weak point (OpenALPR:
94.3% on one-line car plates versus 45.7% on two-line motorcycle plates), and a
test set that happens to be short of them would hide exactly the failure the
evaluation needs to measure. The line count comes from the aspect-ratio
heuristic, so the balance is approximate -- but approximately balanced is far
better than accidentally skewed.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import random
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Iterable, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    add_common_arguments,
    bootstrap_project_path,
    configure_logging,
    iter_image_files,
    read_image_size,
    resolve_dataset_paths,
    write_csv,
    write_json,
)

bootstrap_project_path()

from ai.data.schema import (  # noqa: E402
    PLATE_CLASS_ID,
    PLATE_CLASS_NAME,
    ImageRecord,
    LabelParseError,
    image_path_to_label_path,
    parse_yolo_label_file,
)

LOGGER = logging.getLogger("dataset.split")

SPLIT_NAMES: Final[tuple[str, str, str]] = ("train", "val", "test")
DEFAULT_RATIOS: Final[tuple[float, float, float]] = (0.70, 0.20, 0.10)


@dataclass(slots=True)
class SplitUnit:
    """A set of images that must all land in the same split.

    Attributes:
        unit_id: Stable identifier, ``"group:<n>"`` or ``"single:<name>"``.
        images: The image paths belonging to this unit.
        stratum: Stratification key -- ``1``, ``2`` or ``"unknown"``.
        datasets: Source dataset slugs represented in this unit.
    """

    unit_id: str
    images: list[Path] = field(default_factory=list)
    stratum: str = "unknown"
    datasets: set[str] = field(default_factory=set)

    @property
    def size(self) -> int:
        """Return the number of images in the unit."""
        return len(self.images)


def parse_ratios(values: Sequence[float]) -> tuple[float, float, float]:
    """Validate and normalise the three split ratios.

    Args:
        values: Exactly three non-negative numbers.

    Returns:
        The ratios normalised to sum to 1.

    Raises:
        ValueError: If there are not three values, if any is negative, or if
            they sum to zero.
    """
    if len(values) != 3:
        raise ValueError(f"Expected 3 ratios (train val test), got {len(values)}")
    if any(value < 0 for value in values):
        raise ValueError(f"Ratios must be non-negative, got {values}")

    total = sum(values)
    if total <= 0:
        raise ValueError("Ratios must sum to more than zero")
    if abs(total - 1.0) > 1e-6:
        LOGGER.warning("Ratios sum to %.4f; normalising to 1.0", total)
    return (values[0] / total, values[1] / total, values[2] / total)


def load_duplicate_groups(
    groups_path: Path, manifest_path: Path | None
) -> dict[str, int]:
    """Load the duplicate group index and translate it onto merged file names.

    ``deduplicate.py`` is normally run over ``datasets/raw``, whose paths no
    longer exist once ``merge.py`` has renamed everything. The merge manifest
    records ``source_image -> new_image``, so it can carry the grouping across
    the rename. Three lookups are attempted per entry, most specific first:
    the manifest translation, an exact path match, then a bare file name match.

    Args:
        groups_path: ``duplicate_groups.json`` from ``deduplicate.py``.
        manifest_path: ``merge_manifest.csv`` from ``merge.py``, or ``None``.

    Returns:
        A mapping from merged image *file name* to group id. Empty when no
        grouping information exists -- the caller then treats every image as a
        singleton and warns.
    """
    if not groups_path.is_file():
        return {}

    try:
        payload = json.loads(groups_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        LOGGER.error(
            "Cannot read duplicate groups from %s (%s). Continuing WITHOUT "
            "leakage protection -- near-duplicate images may be split apart.",
            groups_path,
            exc,
        )
        return {}

    raw_groups = payload.get("groups", {})
    if not isinstance(raw_groups, dict):
        LOGGER.error("%s has no usable 'groups' mapping", groups_path)
        return {}

    source_to_new: dict[str, str] = {}
    if manifest_path is not None and manifest_path.is_file():
        try:
            with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    source = row.get("source_image")
                    new_image = row.get("new_image")
                    if source and new_image:
                        source_to_new[source] = new_image
                        source_to_new[Path(source).name] = new_image
        except OSError as exc:
            LOGGER.warning("Cannot read merge manifest %s: %s", manifest_path, exc)

    translated: dict[str, int] = {}
    for original_path, group_id in raw_groups.items():
        mapped = source_to_new.get(original_path) or source_to_new.get(
            Path(original_path).name
        )
        key = mapped or Path(original_path).name
        translated[key] = int(group_id)

    LOGGER.info(
        "Loaded %d grouped images from %s (%d translated via the merge manifest)",
        len(translated),
        groups_path,
        sum(1 for path in raw_groups if source_to_new.get(Path(path).name)),
    )
    return translated


def build_units(
    image_paths: Sequence[Path],
    group_index: dict[str, int],
    *,
    stratify: bool,
) -> list[SplitUnit]:
    """Turn images into indivisible split units.

    Args:
        image_paths: Every image in the merged corpus.
        group_index: File name to duplicate-group id, from
            :func:`load_duplicate_groups`.
        stratify: Compute the one-line/two-line stratum for each unit. This
            costs one image-header read and one label parse per image, so it is
            skipped when not needed.

    Returns:
        The units, sorted by id for reproducibility.
    """
    grouped: dict[str, SplitUnit] = {}

    for image_path in image_paths:
        group_id = group_index.get(image_path.name)
        unit_id = f"group:{group_id}" if group_id is not None else f"single:{image_path.name}"
        unit = grouped.get(unit_id)
        if unit is None:
            unit = SplitUnit(unit_id=unit_id)
            grouped[unit_id] = unit
        unit.images.append(image_path)
        unit.datasets.add(image_path.stem.rsplit("_", 1)[0])

    units = [grouped[key] for key in sorted(grouped)]

    if stratify:
        for unit in units:
            unit.stratum = _unit_stratum(unit)

    group_units = sum(1 for unit in units if unit.size > 1)
    LOGGER.info(
        "Built %d split units from %d images (%d multi-image duplicate groups)",
        len(units),
        len(image_paths),
        group_units,
    )
    return units


def _unit_stratum(unit: SplitUnit) -> str:
    """Determine a unit's stratification key.

    Args:
        unit: The unit to classify.

    Returns:
        ``"1"``, ``"2"``, or ``"unknown"`` when no image in the unit yields a
        usable box. Ties across a multi-image unit are broken towards ``"2"``,
        matching :meth:`ImageRecord.dominant_line_count`: keeping the scarcer
        two-line class evenly spread matters more than classifying a mixed unit
        precisely.
    """
    counts: Counter[int] = Counter()
    for image_path in unit.images:
        size = read_image_size(image_path)
        if size is None:
            continue
        label_path = image_path_to_label_path(image_path)
        if not label_path.is_file():
            continue
        try:
            boxes = parse_yolo_label_file(label_path)
        except (LabelParseError, OSError):
            continue
        record = ImageRecord(
            path=image_path,
            width=size[0],
            height=size[1],
            source_dataset="",
            boxes=boxes,
        )
        counts.update(record.estimated_line_counts())

    if not counts:
        return "unknown"
    return "1" if counts.get(1, 0) > counts.get(2, 0) else "2"


def assign_units(
    units: Sequence[SplitUnit],
    ratios: tuple[float, float, float],
    *,
    seed: int,
    stratify: bool,
) -> dict[str, str]:
    """Deal units into the three splits, honouring the target ratios.

    Units have different sizes, so a positional cut of a shuffled list would
    miss the targets whenever a large duplicate group lands near a boundary.
    Instead each unit goes to whichever split is currently furthest below its
    target *image* count, measured as a fraction of that split's target so the
    small val/test splits are not starved by the large train split.

    Args:
        units: The units to assign.
        ratios: Normalised ``(train, val, test)`` shares.
        seed: Seed for the shuffle, so a run is reproducible.
        stratify: Assign within each stratum separately, which keeps the
            one-line/two-line mix balanced across splits.

    Returns:
        A mapping from ``unit_id`` to split name.
    """
    strata: dict[str, list[SplitUnit]] = defaultdict(list)
    for unit in units:
        strata[unit.stratum if stratify else "all"].append(unit)

    assignment: dict[str, str] = {}

    for stratum in sorted(strata):
        members = strata[stratum]
        rng = random.Random(f"{seed}:{stratum}")
        # Largest units first: placing the big, awkward groups while every split
        # still has room keeps the realised ratios much closer to target than
        # discovering a 40-image group at the very end.
        shuffled = sorted(members, key=lambda unit: (-unit.size, unit.unit_id))
        rng.shuffle(shuffled)
        shuffled.sort(key=lambda unit: -unit.size)

        total_images = sum(unit.size for unit in shuffled)
        targets = {name: ratio * total_images for name, ratio in zip(SPLIT_NAMES, ratios)}
        current = {name: 0 for name in SPLIT_NAMES}

        for unit in shuffled:
            best = max(
                (name for name in SPLIT_NAMES if targets[name] > 0),
                key=lambda name: (targets[name] - current[name]) / targets[name],
                default=SPLIT_NAMES[0],
            )
            assignment[unit.unit_id] = best
            current[best] += unit.size

        LOGGER.debug(
            "Stratum %-8s %5d images -> train %d, val %d, test %d",
            stratum,
            total_images,
            current["train"],
            current["val"],
            current["test"],
        )

    return assignment


def verify_no_leakage(
    units: Sequence[SplitUnit], assignment: dict[str, str]
) -> list[str]:
    """Confirm that no duplicate group was split across two splits.

    This re-derives the guarantee from the final assignment rather than trusting
    that :func:`assign_units` did its job. It is cheap, and a silent leak is the
    one failure that would invalidate every number in the thesis.

    Args:
        units: The units that were assigned.
        assignment: The unit-to-split mapping.

    Returns:
        A list of violation messages, empty when the split is sound.
    """
    image_to_split: dict[str, str] = {}
    violations: list[str] = []

    for unit in units:
        split = assignment.get(unit.unit_id)
        if split is None:
            violations.append(f"unit {unit.unit_id} was never assigned to a split")
            continue
        for image_path in unit.images:
            previous = image_to_split.get(image_path.name)
            if previous is not None and previous != split:
                violations.append(
                    f"{image_path.name} appears in both {previous} and {split}"
                )
            image_to_split[image_path.name] = split

    return violations


def materialise(
    units: Sequence[SplitUnit],
    assignment: dict[str, str],
    output_dir: Path,
    *,
    link: bool,
    keep_extras: bool = False,
) -> tuple[dict[str, int], list[dict[str, Any]]]:
    """Write the split out in the Ultralytics directory layout.

    Produces ``images/<split>/`` and ``labels/<split>/``, which is the layout
    :func:`ai.data.schema.image_path_to_label_path` understands.

    Args:
        units: The assigned units.
        assignment: Unit-to-split mapping.
        output_dir: Destination root.
        link: Hard link instead of copying where the filesystem allows.
        keep_extras: Copy the ``plate_text``/``line_count`` extension through
            verbatim. Off by default because Ultralytics **cannot read it**: its
            loader parses every field after the class id as a float, hits the
            ``-`` placeholder, and discards the image as corrupt. A whole corpus
            can vanish this way while the run still looks healthy, so the
            training-facing copy is written as plain 5-field YOLO unless the
            caller explicitly asks otherwise for offline analysis.

    Returns:
        ``(counts_per_split, manifest_rows)``.

    Raises:
        OSError: If the destination cannot be written.
    """
    counts: dict[str, int] = {name: 0 for name in SPLIT_NAMES}
    rows: list[dict[str, Any]] = []

    for name in SPLIT_NAMES:
        (output_dir / "images" / name).mkdir(parents=True, exist_ok=True)
        (output_dir / "labels" / name).mkdir(parents=True, exist_ok=True)

    for unit in units:
        split = assignment[unit.unit_id]
        for image_path in unit.images:
            destination_image = output_dir / "images" / split / image_path.name
            destination_label = output_dir / "labels" / split / f"{image_path.stem}.txt"

            _place(image_path, destination_image, link=link)

            source_label = image_path_to_label_path(image_path)
            if source_label.is_file():
                if keep_extras:
                    _place(source_label, destination_label, link=link)
                else:
                    _write_plain_label(source_label, destination_label)
            else:
                # An empty label is not the same as a missing one: it declares
                # "no plates here" instead of "not annotated".
                destination_label.write_text("", encoding="utf-8")

            counts[split] += 1
            rows.append(
                {
                    "image": image_path.name,
                    "split": split,
                    "unit_id": unit.unit_id,
                    "unit_size": unit.size,
                    "stratum": unit.stratum,
                    "source_dataset": "|".join(sorted(unit.datasets)),
                }
            )

    return counts, rows


def _write_plain_label(source: Path, destination: Path) -> None:
    """Copy a label file, dropping any extras so Ultralytics can read it.

    The merged corpus may carry ``plate_text``/``line_count`` after the four
    geometry fields. That extension is ours; the Ultralytics loader treats every
    trailing field as a polygon coordinate and rejects the whole image when it
    meets the non-numeric ``-`` placeholder. Rewriting to plain 5-field YOLO is
    what makes the split directly trainable.

    A label that cannot be parsed is copied through unchanged rather than
    silently emptied, so the damage stays visible to ``verify_annotations.py``
    instead of turning into a mysteriously empty annotation.

    Args:
        source: Label file in the merged corpus.
        destination: Where the plain label is written.
    """
    try:
        boxes = parse_yolo_label_file(source)
    except Exception as exc:  # noqa: BLE001 - report, never abort a whole split
        LOGGER.warning(
            "Cannot parse %s (%s); copying it through unchanged.", source, exc
        )
        destination.write_bytes(source.read_bytes())
        return

    lines = [box.to_yolo_line(include_extras=False) for box in boxes]
    destination.write_text(
        "\n".join(lines) + ("\n" if lines else ""), encoding="utf-8"
    )


def _place(source: Path, destination: Path, *, link: bool) -> None:
    """Hard link or copy one file into place.

    Args:
        source: File to place.
        destination: Target path.
        link: Attempt a hard link first, falling back to a copy.

    Raises:
        OSError: If the copy fails.
    """
    if destination.exists():
        destination.unlink()
    if link:
        try:
            os.link(source, destination)
            return
        except OSError:
            pass
    shutil.copy2(source, destination)


def write_dataset_yaml(output_dir: Path, *, class_names: dict[int, str] | None = None) -> Path:
    """Write the Ultralytics ``data.yaml`` describing the split.

    The ``path`` key is absolute. Ultralytics resolves relative dataset paths
    against its own settings directory rather than the current working
    directory, which is a reliable source of "dataset not found" confusion.

    Args:
        output_dir: The split root; the file is written inside it.
        class_names: Class id to name. Defaults to the single plate class.

    Returns:
        The path written to.

    Raises:
        OSError: If the file cannot be written.
    """
    names = class_names or {PLATE_CLASS_ID: PLATE_CLASS_NAME}
    lines = [
        "# Ultralytics dataset descriptor - generated by scripts/dataset/split.py",
        "# Do not edit by hand; re-run split.py instead.",
        f"path: {output_dir.as_posix()}",
        "train: images/train",
        "val: images/val",
        "test: images/test",
        "",
        f"nc: {len(names)}",
        "names:",
    ]
    lines.extend(f"  {class_id}: {name}" for class_id, name in sorted(names.items()))

    destination = output_dir / "data.yaml"
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    LOGGER.info("Wrote dataset descriptor: %s", destination)
    return destination


def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line parser.

    Returns:
        The configured parser.
    """
    parser = argparse.ArgumentParser(
        prog="split.py",
        description=(
            "Split the merged corpus into train/val/test, keeping every "
            "near-duplicate group inside a single split to prevent leakage."
        ),
        epilog=(
            "Examples:\n"
            "  python split.py\n"
            "  python split.py --ratios 0.8 0.1 0.1 --stratify\n"
            "  python split.py --seed 1337 --link\n\n"
            "Run deduplicate.py first: without duplicate_groups.json this script\n"
            "cannot protect against leakage and will say so loudly."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="Merged corpus produced by merge.py (default: <datasets>/processed/merged).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="Where to write the split dataset (default: <datasets>/processed/yolo).",
    )
    parser.add_argument(
        "--ratios",
        nargs=3,
        type=float,
        default=list(DEFAULT_RATIOS),
        metavar=("TRAIN", "VAL", "TEST"),
        help="Train/val/test shares; normalised if they do not sum to 1 (default: 0.7 0.2 0.1).",
    )
    parser.add_argument(
        "--duplicate-groups",
        type=Path,
        default=None,
        metavar="FILE",
        help=(
            "duplicate_groups.json from deduplicate.py "
            "(default: <datasets>/reports/duplicate_groups.json)."
        ),
    )
    parser.add_argument(
        "--stratify",
        action="store_true",
        help=(
            "Balance the estimated one-line/two-line plate mix across splits. "
            "Recommended: two-line motorcycle plates are the weakest case and a "
            "test set short of them hides the problem."
        ),
    )
    parser.add_argument(
        "--keep-extras",
        action="store_true",
        help=(
            "Keep the plate_text/line_count extension in the split labels. OFF "
            "by default: Ultralytics cannot parse those extra fields and drops "
            "every such image as corrupt. Only enable for offline analysis of "
            "the split, never for a directory you intend to train on."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        metavar="N",
        help="Random seed, so the split is reproducible (default: %(default)s).",
    )
    parser.add_argument(
        "--link",
        action="store_true",
        help="Hard link instead of copying, saving disk space.",
    )
    parser.add_argument(
        "--allow-no-groups",
        action="store_true",
        help=(
            "Proceed even when no duplicate group file exists. The split is then "
            "NOT protected against leakage."
        ),
    )
    return add_common_arguments(parser)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point.

    Args:
        argv: Argument list, defaulting to ``sys.argv[1:]``.

    Returns:
        ``0`` on success; ``1`` if the input is missing, the ratios are
        invalid, leakage protection is unavailable without ``--allow-no-groups``,
        or the post-split leakage check fails.
    """
    args = build_parser().parse_args(argv)
    configure_logging(args.log_level)

    paths = resolve_dataset_paths(args.datasets_dir)
    input_dir = (args.input_dir or (paths.processed / "merged")).expanduser().resolve()
    output_dir = (args.output_dir or (paths.processed / "yolo")).expanduser().resolve()
    groups_path = (
        args.duplicate_groups or (paths.reports / "duplicate_groups.json")
    ).expanduser().resolve()

    try:
        ratios = parse_ratios(args.ratios)
    except ValueError as exc:
        LOGGER.error("%s", exc)
        return 1

    images_dir = input_dir / "images"
    scan_dir = images_dir if images_dir.is_dir() else input_dir
    image_paths = list(iter_image_files(scan_dir))
    if not image_paths:
        LOGGER.error("No images found under %s. Run merge.py first.", scan_dir)
        return 1

    group_index = load_duplicate_groups(groups_path, input_dir / "merge_manifest.csv")
    if not group_index:
        message = (
            f"No duplicate group information at {groups_path}. Every image will be "
            "treated as independent, so near-duplicates CAN be split across "
            "train and test and the reported accuracy may be inflated."
        )
        if not args.allow_no_groups:
            LOGGER.error("%s", message)
            LOGGER.error(
                "Run deduplicate.py first (report-only is enough), or pass "
                "--allow-no-groups to accept the risk."
            )
            return 1
        LOGGER.warning("%s", message)

    units = build_units(image_paths, group_index, stratify=args.stratify)
    assignment = assign_units(units, ratios, seed=args.seed, stratify=args.stratify)

    violations = verify_no_leakage(units, assignment)
    if violations:
        LOGGER.error("Leakage check FAILED with %d violation(s):", len(violations))
        for violation in violations[:20]:
            LOGGER.error("    %s", violation)
        return 1
    LOGGER.info("Leakage check passed: no duplicate group spans two splits.")

    try:
        counts, rows = materialise(
            units,
            assignment,
            output_dir,
            link=args.link,
            keep_extras=args.keep_extras,
        )
        yaml_path = write_dataset_yaml(output_dir)
    except OSError as exc:
        LOGGER.error("Could not write the split: %s", exc)
        return 1

    write_csv(
        output_dir / "split_manifest.csv",
        rows,
        fieldnames=["image", "split", "unit_id", "unit_size", "stratum", "source_dataset"],
    )

    total = sum(counts.values())
    stratum_breakdown: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        stratum_breakdown[str(row["split"])][str(row["stratum"])] += 1

    summary = {
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "data_yaml": str(yaml_path),
        "seed": args.seed,
        "stratified": bool(args.stratify),
        "requested_ratios": dict(zip(SPLIT_NAMES, ratios)),
        "images_total": total,
        "images_per_split": counts,
        "realised_ratios": {
            name: round(counts[name] / total, 4) if total else 0.0 for name in SPLIT_NAMES
        },
        "units_total": len(units),
        "multi_image_units": sum(1 for unit in units if unit.size > 1),
        "largest_unit": max((unit.size for unit in units), default=0),
        "stratum_per_split": {
            split: dict(sorted(counter.items()))
            for split, counter in sorted(stratum_breakdown.items())
        },
        "leakage_protection": bool(group_index),
    }
    write_json(paths.reports / "split_report.json", summary)

    LOGGER.info("=" * 70)
    for name in SPLIT_NAMES:
        share = counts[name] / total if total else 0.0
        LOGGER.info(
            "%-6s %6d images (%.1f%%, requested %.1f%%)",
            name,
            counts[name],
            100 * share,
            100 * ratios[SPLIT_NAMES.index(name)],
        )
    if args.stratify:
        for split, counter in sorted(stratum_breakdown.items()):
            LOGGER.info(
                "    %-6s strata: %s",
                split,
                ", ".join(f"{key}-line={value}" for key, value in sorted(counter.items())),
            )
    LOGGER.info("Dataset descriptor: %s", yaml_path)
    LOGGER.info("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
