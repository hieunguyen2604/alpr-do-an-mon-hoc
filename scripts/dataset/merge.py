"""Merge several raw datasets into one uniform YOLO corpus under ``datasets/processed``.

Usage examples::

    python scripts/dataset/merge.py
    python scripts/dataset/merge.py --input-dir datasets/raw --datasets vnlp roboflow_vn_plates
    python scripts/dataset/merge.py --link --include-unlabeled

What merging actually has to solve
----------------------------------
**Name collisions.** Nearly every plate dataset numbers its files ``0001.jpg``,
``img_1.jpg`` or a UUID. Copying two of them into one directory silently
overwrites files, and the loss is invisible because the count still looks
plausible. Every file is therefore renamed ``<dataset>_<index>`` with a
zero-padded index, which is unique by construction and, crucially, keeps the
source dataset readable in the filename -- ``deduplicate.py --dataset-from
filename-prefix`` and the per-source statistics both depend on that.

**Class id space.** Different sources index their classes differently: one
dataset's class ``0`` is ``plate``, another's is ``car`` with ``plate`` at ``2``.
This project is a single-class detection problem, so by default every box is
remapped to class ``0`` (``license_plate``). ``--keep-class-ids`` disables the
remap for the rare case where a source really is single-class and already
correct, but the default is the safe one.

**Traceability.** Every output file is recorded in ``merge_manifest.csv`` next
to the dataset it came from and its original path. Without that, a suspicious
image found during training is untraceable, and licence attribution -- which the
thesis needs -- becomes guesswork.

Ordering is deterministic: sources are processed in sorted order and files
within a source in sorted order, so re-running produces byte-identical names.
"""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Iterable, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    IMAGE_EXTENSIONS,
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
    BoxRecord,
    ImageRecord,
    LabelParseError,
    image_path_to_label_path,
    parse_yolo_label_file,
    write_yolo_label_file,
)

LOGGER = logging.getLogger("dataset.merge")

INDEX_WIDTH: Final[int] = 6
"""Zero-padding width for the file index. Six digits covers a million images."""


@dataclass(slots=True)
class MergeStats:
    """Counters for one merge run.

    Attributes:
        copied: Images written to the output directory.
        skipped_unlabeled: Images passed over for having no label file.
        skipped_unreadable: Images whose dimensions could not be read.
        skipped_bad_label: Images whose label file failed to parse.
        skipped_excluded: Images skipped because they were on the exclusion list.
        boxes: Total boxes written.
        boxes_dropped: Boxes discarded by class filtering.
        per_dataset: Images written, per source dataset.
    """

    copied: int = 0
    skipped_unlabeled: int = 0
    skipped_unreadable: int = 0
    skipped_bad_label: int = 0
    skipped_excluded: int = 0
    boxes: int = 0
    boxes_dropped: int = 0
    per_dataset: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable view."""
        return {
            "images_written": self.copied,
            "boxes_written": self.boxes,
            "boxes_dropped_by_class_filter": self.boxes_dropped,
            "skipped_unlabeled": self.skipped_unlabeled,
            "skipped_unreadable": self.skipped_unreadable,
            "skipped_bad_label": self.skipped_bad_label,
            "skipped_excluded": self.skipped_excluded,
            "images_per_dataset": dict(sorted(self.per_dataset.items())),
        }


def discover_datasets(input_dir: Path, names: Sequence[str] | None = None) -> dict[str, Path]:
    """Find the source datasets to merge.

    Args:
        input_dir: Either a directory whose immediate subdirectories are
            datasets (the ``datasets/raw`` layout), or a single dataset
            directory containing images directly.
        names: Restrict to these dataset directory names.

    Returns:
        A mapping from dataset slug to its directory, in sorted order.

    Raises:
        FileNotFoundError: If ``input_dir`` does not exist.
        ValueError: If a requested name has no matching directory.
    """
    if not input_dir.is_dir():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    subdirectories = sorted(
        path for path in input_dir.iterdir() if path.is_dir() and not path.name.startswith(".")
    )
    candidates = {path.name: path for path in subdirectories}

    # A directory holding images but no dataset subdirectories is itself one
    # dataset; treating it as an empty parent would silently merge nothing.
    if not candidates and any(iter_image_files(input_dir, recursive=False)):
        candidates = {input_dir.name: input_dir}

    if names:
        missing = [name for name in names if name not in candidates]
        if missing:
            raise ValueError(
                f"No directory for dataset(s) {', '.join(missing)} under {input_dir}. "
                f"Available: {', '.join(sorted(candidates)) or '(none)'}"
            )
        candidates = {name: candidates[name] for name in names}

    return dict(sorted(candidates.items()))


def find_label_for(image_path: Path, dataset_root: Path) -> Path | None:
    """Locate the YOLO label file belonging to an image.

    Datasets are inconsistent about layout, so three conventions are tried in
    order: the Ultralytics ``images``/``labels`` mirror, a sibling ``.txt``, and
    a flat ``labels/`` directory at the dataset root. Returning ``None`` rather
    than guessing keeps an unlabelled image reportable.

    Args:
        image_path: The image.
        dataset_root: Root of the dataset being merged.

    Returns:
        The label path, or ``None`` if no candidate exists.
    """
    mirrored = image_path_to_label_path(image_path)
    if mirrored.is_file():
        return mirrored

    sibling = image_path.with_suffix(".txt")
    if sibling.is_file():
        return sibling

    flat = dataset_root / "labels" / f"{image_path.stem}.txt"
    if flat.is_file():
        return flat

    return None


def remap_boxes(
    boxes: Iterable[BoxRecord],
    *,
    keep_class_ids: bool,
    accept_classes: frozenset[int] | None,
) -> tuple[list[BoxRecord], int]:
    """Filter and remap boxes into the merged class space.

    Args:
        boxes: Boxes parsed from a source label file.
        keep_class_ids: Preserve the original class ids instead of collapsing
            everything to :data:`~ai.data.schema.PLATE_CLASS_ID`.
        accept_classes: When given, only boxes with these source class ids are
            kept. Use it for multi-class sources where only one class is the
            plate.

    Returns:
        ``(kept_boxes, dropped_count)``.
    """
    from dataclasses import replace

    kept: list[BoxRecord] = []
    dropped = 0
    for box in boxes:
        if accept_classes is not None and box.class_id not in accept_classes:
            dropped += 1
            continue
        kept.append(box if keep_class_ids else replace(box, class_id=PLATE_CLASS_ID))
    return kept, dropped


def parse_per_dataset_classes(values: Sequence[str] | None) -> dict[str, frozenset[int]]:
    """Parse ``--accept-classes-for NAME=ID[,ID...]`` arguments.

    A single global ``--accept-classes`` cannot express the real situation:
    ``roboflow_eric_nguyen`` needs class ``1`` (``vehicle``) dropped, while
    ``hf_vn_plates_segment`` needs class ``1`` (``BSV``, the two-line plate)
    kept. Applying one filter to both would silently delete every two-line
    motorcycle plate -- exactly the hardest and most valuable subset.

    Args:
        values: Raw ``NAME=ID,ID`` strings, or ``None``.

    Returns:
        Mapping from dataset name to the accepted original class ids.

    Raises:
        ValueError: If an entry is malformed or an id is not an integer.
    """
    parsed: dict[str, frozenset[int]] = {}
    for raw in values or ():
        if "=" not in raw:
            raise ValueError(f"expected NAME=ID[,ID...], got {raw!r}")
        name, _, ids = raw.partition("=")
        name = name.strip()
        if not name:
            raise ValueError(f"empty dataset name in {raw!r}")
        try:
            wanted = frozenset(int(part) for part in ids.split(",") if part.strip())
        except ValueError as exc:
            raise ValueError(f"non-integer class id in {raw!r}") from exc
        if not wanted:
            raise ValueError(f"no class ids given in {raw!r}")
        parsed[name] = wanted
    return parsed


def load_exclusions(path: Path | None) -> frozenset[str]:
    """Read a list of source image paths to skip.

    Used to drop images that ``verify_annotations.py`` flagged as broken, so
    the merged corpus never carries a known-bad label into training.

    Args:
        path: Text file with one path per line; ``#`` starts a comment. Blank
            lines are ignored. ``None`` means no exclusions.

    Returns:
        Set of lower-cased basenames to skip. Basenames are used because the
        verification report and the merge walk can resolve the same file
        through different absolute prefixes.

    Raises:
        OSError: If the file exists but cannot be read.
    """
    if path is None:
        return frozenset()
    names: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        entry = line.split("#", 1)[0].strip()
        if entry:
            names.add(Path(entry).name.lower())
    LOGGER.info("Loaded %d exclusion entr(ies) from %s", len(names), path)
    return frozenset(names)


def place_file(source: Path, destination: Path, *, link: bool) -> None:
    """Put a source file at a destination, by hard link or by copy.

    Args:
        source: File to place.
        destination: Where it should end up. Parent directories are created.
        link: Try a hard link first. The merged corpus duplicates every image,
            which for a 37k-image dataset is gigabytes; a hard link costs
            nothing. It only works within one filesystem, so a failure falls
            back to copying rather than aborting.

    Raises:
        OSError: If the copy fails.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()

    if link:
        try:
            os.link(source, destination)
            return
        except OSError as exc:
            LOGGER.debug("Hard link failed for %s (%s); copying instead", source, exc)

    shutil.copy2(source, destination)


def merge_datasets(
    sources: dict[str, Path],
    output_dir: Path,
    *,
    keep_class_ids: bool = False,
    accept_classes: frozenset[int] | None = None,
    accept_classes_per_dataset: dict[str, frozenset[int]] | None = None,
    exclude_names: frozenset[str] = frozenset(),
    include_unlabeled: bool = False,
    link: bool = False,
    include_extras: bool = False,
) -> tuple[MergeStats, list[dict[str, Any]]]:
    """Copy every source dataset into one uniform YOLO directory.

    Args:
        sources: Mapping from dataset slug to source directory.
        output_dir: Destination root; ``images/`` and ``labels/`` are created
            inside it.
        keep_class_ids: Preserve original class ids rather than remapping.
        accept_classes: Only keep boxes with these source class ids.
        accept_classes_per_dataset: Per-dataset override of ``accept_classes``,
            for corpora where the same class id means different things in
            different sources.
        exclude_names: Lower-cased image basenames to skip entirely, typically
            images that failed annotation verification.
        include_unlabeled: Write images that have no label file, with an empty
            label. Off by default -- see the warning logged when it is on.
        link: Hard link instead of copying.
        include_extras: Write ``plate_text``/``line_count`` into the label
            files. Leave off for files fed straight to Ultralytics.

    Returns:
        ``(stats, manifest_rows)``.

    Raises:
        OSError: If the output directory cannot be written.
    """
    images_dir = output_dir / "images"
    labels_dir = output_dir / "labels"
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    stats = MergeStats()
    manifest: list[dict[str, Any]] = []

    per_dataset_filters = accept_classes_per_dataset or {}

    for dataset, dataset_root in sources.items():
        image_paths = list(iter_image_files(dataset_root))
        dataset_accept = per_dataset_filters.get(dataset, accept_classes)
        if dataset in per_dataset_filters:
            LOGGER.info(
                "[%s] class filter: keeping original class id(s) %s",
                dataset,
                sorted(per_dataset_filters[dataset]),
            )
        LOGGER.info("[%s] %d candidate images in %s", dataset, len(image_paths), dataset_root)
        written = 0

        for image_path in image_paths:
            if image_path.name.lower() in exclude_names:
                stats.skipped_excluded += 1
                LOGGER.info("[%s] excluded by verification: %s", dataset, image_path.name)
                continue

            label_path = find_label_for(image_path, dataset_root)
            if label_path is None and not include_unlabeled:
                stats.skipped_unlabeled += 1
                LOGGER.debug("[%s] no label for %s; skipping", dataset, image_path.name)
                continue

            size = read_image_size(image_path)
            if size is None:
                stats.skipped_unreadable += 1
                LOGGER.warning("[%s] cannot read %s; skipping", dataset, image_path)
                continue

            boxes: list[BoxRecord] = []
            if label_path is not None:
                try:
                    boxes = parse_yolo_label_file(label_path)
                except (LabelParseError, OSError) as exc:
                    stats.skipped_bad_label += 1
                    LOGGER.warning("[%s] bad label, skipping image: %s", dataset, exc)
                    continue

            boxes, dropped = remap_boxes(
                boxes, keep_class_ids=keep_class_ids, accept_classes=dataset_accept
            )
            stats.boxes_dropped += dropped

            new_stem = f"{dataset}_{written:0{INDEX_WIDTH}d}"
            suffix = image_path.suffix.lower()
            if suffix not in IMAGE_EXTENSIONS:
                suffix = ".jpg"
            new_image = images_dir / f"{new_stem}{suffix}"
            new_label = labels_dir / f"{new_stem}.txt"

            try:
                place_file(image_path, new_image, link=link)
            except OSError as exc:
                stats.skipped_unreadable += 1
                LOGGER.error("[%s] could not place %s: %s", dataset, image_path, exc)
                continue

            write_yolo_label_file(new_label, boxes, include_extras=include_extras)

            record = ImageRecord(
                path=new_image,
                width=size[0],
                height=size[1],
                source_dataset=dataset,
                boxes=boxes,
            )
            manifest.append(
                {
                    "new_image": new_image.name,
                    "new_label": new_label.name,
                    "source_dataset": dataset,
                    "source_image": image_path,
                    "source_label": label_path,
                    "width": size[0],
                    "height": size[1],
                    "box_count": len(boxes),
                    "dominant_line_count": record.dominant_line_count() or "",
                }
            )

            written += 1
            stats.copied += 1
            stats.boxes += len(boxes)

        stats.per_dataset[dataset] = written
        LOGGER.info("[%s] merged %d images", dataset, written)

    return stats, manifest


def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line parser.

    Returns:
        The configured parser.
    """
    parser = argparse.ArgumentParser(
        prog="merge.py",
        description=(
            "Merge the raw datasets into one uniform single-class YOLO corpus, "
            "renaming files to <dataset>_<index> and recording a manifest."
        ),
        epilog=(
            "Examples:\n"
            "  python merge.py\n"
            "  python merge.py --datasets vnlp --link\n"
            "  python merge.py --accept-classes 0 2\n\n"
            "Run deduplicate.py and verify_annotations.py before this step."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="Directory whose subdirectories are the source datasets (default: <datasets>/raw).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="Destination root (default: <datasets>/processed/merged).",
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        metavar="NAME",
        help="Only merge these source directories, by name.",
    )
    parser.add_argument(
        "--keep-class-ids",
        action="store_true",
        help=(
            "Preserve the original class ids instead of remapping every box to "
            f"{PLATE_CLASS_ID} ({PLATE_CLASS_NAME}). Only correct if every source "
            "is already single-class with the plate at id 0."
        ),
    )
    parser.add_argument(
        "--accept-classes",
        nargs="+",
        type=int,
        default=None,
        metavar="ID",
        help=(
            "Keep only boxes whose ORIGINAL class id is in this list. Use for "
            "multi-class sources where the plate is one class among several."
        ),
    )
    parser.add_argument(
        "--accept-classes-for",
        nargs="+",
        default=None,
        metavar="NAME=ID[,ID...]",
        help=(
            "Per-dataset class filter, overriding --accept-classes for that "
            "source. Needed when the same id means different things in "
            "different datasets, e.g. "
            "'roboflow_eric_nguyen=0' drops its 'vehicle' class while "
            "hf_vn_plates_segment keeps both 0 (BSD) and 1 (BSV)."
        ),
    )
    parser.add_argument(
        "--exclude-list",
        type=Path,
        default=None,
        metavar="FILE",
        help=(
            "Text file of source image paths to skip, one per line. Use it to "
            "drop images that verify_annotations.py reported as errors."
        ),
    )
    parser.add_argument(
        "--include-unlabeled",
        action="store_true",
        help=(
            "Include images that have no label file, writing an empty label. "
            "They become background images for the detector."
        ),
    )
    parser.add_argument(
        "--link",
        action="store_true",
        help=(
            "Hard link images instead of copying, saving disk space. Falls back "
            "to copying across filesystems."
        ),
    )
    parser.add_argument(
        "--include-extras",
        action="store_true",
        help=(
            "Write plate_text and line_count as extra label fields. Useful for "
            "the OCR stage; leave off for files fed to Ultralytics."
        ),
    )
    return add_common_arguments(parser)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point.

    Args:
        argv: Argument list, defaulting to ``sys.argv[1:]``.

    Returns:
        ``0`` on success, ``1`` if the inputs are missing or nothing was merged.
    """
    args = build_parser().parse_args(argv)
    configure_logging(args.log_level)

    paths = resolve_dataset_paths(args.datasets_dir)
    input_dir = (args.input_dir or paths.raw).expanduser().resolve()
    output_dir = (args.output_dir or (paths.processed / "merged")).expanduser().resolve()

    try:
        sources = discover_datasets(input_dir, args.datasets)
    except (FileNotFoundError, ValueError) as exc:
        LOGGER.error("%s", exc)
        return 1

    try:
        per_dataset_classes = parse_per_dataset_classes(args.accept_classes_for)
    except ValueError as exc:
        LOGGER.error("--accept-classes-for: %s", exc)
        return 1

    unknown = sorted(set(per_dataset_classes) - set(sources))
    if unknown:
        LOGGER.error(
            "--accept-classes-for names dataset(s) that are not being merged: %s. "
            "Known sources: %s",
            ", ".join(unknown),
            ", ".join(sorted(sources)),
        )
        return 1

    try:
        exclude_names = load_exclusions(args.exclude_list)
    except OSError as exc:
        LOGGER.error("Cannot read --exclude-list: %s", exc)
        return 1

    if not sources:
        LOGGER.error("No source datasets found under %s. Run download.py first.", input_dir)
        return 1

    LOGGER.info("Merging %d dataset(s) into %s", len(sources), output_dir)
    if args.include_unlabeled:
        LOGGER.warning(
            "--include-unlabeled is on. Images with no label become background "
            "images. That is only correct if they genuinely contain no plates; "
            "if the labels are merely missing, the model is being taught that "
            "plates are not plates."
        )

    try:
        stats, manifest = merge_datasets(
            sources,
            output_dir,
            keep_class_ids=args.keep_class_ids,
            accept_classes=frozenset(args.accept_classes) if args.accept_classes else None,
            accept_classes_per_dataset=per_dataset_classes,
            exclude_names=exclude_names,
            include_unlabeled=args.include_unlabeled,
            link=args.link,
            include_extras=args.include_extras,
        )
    except OSError as exc:
        LOGGER.error("Merge failed: %s", exc)
        return 1

    if stats.copied == 0:
        LOGGER.error(
            "Nothing was merged. Every candidate image was skipped -- check the "
            "counts above; the usual cause is labels living somewhere this script "
            "does not look, or a source that is not in YOLO format yet."
        )
        return 1

    manifest_path = output_dir / "merge_manifest.csv"
    write_csv(
        manifest_path,
        manifest,
        fieldnames=[
            "new_image",
            "new_label",
            "source_dataset",
            "source_image",
            "source_label",
            "width",
            "height",
            "box_count",
            "dominant_line_count",
        ],
    )

    summary = stats.as_dict()
    summary.update(
        {
            "input_dir": str(input_dir),
            "output_dir": str(output_dir),
            "sources": {name: str(path) for name, path in sources.items()},
            "class_space": (
                "original ids preserved"
                if args.keep_class_ids
                else f"all boxes remapped to {PLATE_CLASS_ID} ({PLATE_CLASS_NAME})"
            ),
            "manifest": str(manifest_path),
        }
    )
    write_json(paths.reports / "merge_report.json", summary)

    LOGGER.info("=" * 70)
    LOGGER.info("Images merged     : %d", stats.copied)
    LOGGER.info("Boxes written     : %d", stats.boxes)
    for dataset, count in sorted(stats.per_dataset.items()):
        LOGGER.info("    %-24s %d", dataset, count)
    if stats.skipped_unlabeled:
        LOGGER.warning("Skipped, no label : %d", stats.skipped_unlabeled)
    if stats.skipped_bad_label:
        LOGGER.warning("Skipped, bad label: %d", stats.skipped_bad_label)
    if stats.skipped_unreadable:
        LOGGER.warning("Skipped, unreadable: %d", stats.skipped_unreadable)
    LOGGER.info("Manifest          : %s", manifest_path)
    LOGGER.info("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
