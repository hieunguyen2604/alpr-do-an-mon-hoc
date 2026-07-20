"""Generate dataset statistics and charts into ``datasets/statistics/``.

Usage examples::

    python scripts/dataset/statistics.py
    python scripts/dataset/statistics.py --input-dir datasets/processed/yolo
    python scripts/dataset/statistics.py --no-charts

Outputs
-------
``statistics.json`` plus one PNG per chart:

===============================  ===============================================
File                             Question it answers
===============================  ===============================================
``images_per_split.png``         Did the split land on the requested ratios, and
                                 which source dataset dominates?
``boxes_per_image.png``          How many plates are in a typical frame?
``box_area.png``                 Are the plates large enough to learn? A mass
                                 below 0.5% of frame area predicts poor recall
                                 on small plates.
``aspect_ratio.png``             The one-line / two-line balance -- the chart
                                 that matters most for this project.
``image_sizes.png``              Do the source resolutions vary enough that a
                                 fixed 640px input distorts some of them?
``box_position_heatmap.png``     Where in the frame do plates sit? A tight
                                 cluster means the model can cheat on position.
``character_frequency.png``      Character balance, when transcriptions exist.
``plate_length.png``             Plate string length distribution.
===============================  ===============================================

Plate transcriptions
--------------------
Detection labels carry no text, so the two character charts stay empty for a
detection-only corpus. Pass ``--plate-text-csv`` to fold in the table written by
``build_plate_text.py`` (default ``datasets/annotations/plate_text_labels.csv``),
which reconstructs plate strings from the multi-class character datasets. Those
images live in a separate corpus from the detection split, so the numbers are
reported under their own provenance key rather than merged into the box counts.

The two-line question
---------------------
``aspect_ratio.png`` marks the 2.5 threshold and the three nominal plate ratios
from QCVN 08:2024/BCA. Read it as a distribution, not a classification: the
underlying line-count estimate is a heuristic and perspective smears the two
populations into each other. What the chart is genuinely useful for is spotting
a corpus that is nearly all one-line plates -- which would be a dataset that
cannot fix the known two-line motorcycle weakness (OpenALPR: 94.3% on one-line
car plates, 45.7% on two-line motorcycle plates).
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Final, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    add_common_arguments,
    bootstrap_project_path,
    configure_logging,
    iter_image_files,
    read_image_size,
    resolve_dataset_paths,
    summarise_distribution,
    write_json,
)

bootstrap_project_path()

from ai.data.schema import (  # noqa: E402
    AR_CAR_LONG,
    AR_CAR_SHORT,
    AR_MOTORCYCLE,
    AR_ONE_LINE_MIN,
    ImageRecord,
    LabelParseError,
    image_path_to_label_path,
    parse_yolo_label_file,
)

LOGGER = logging.getLogger("dataset.statistics")

ACCENT: Final[str] = "#2563eb"
"""Single accent colour. One hue keeps the chart set reading as one system."""

MUTED: Final[str] = "#94a3b8"
WARN: Final[str] = "#dc2626"
SPLIT_ORDER: Final[tuple[str, ...]] = ("train", "val", "test", "unassigned")
HEATMAP_BINS: Final[int] = 40


def collect_records(input_dir: Path) -> list[ImageRecord]:
    """Load every image and its labels from a dataset directory.

    Both layouts are handled: a split dataset (``images/train/...``) and a flat
    merged corpus (``images/...``). The split name is taken from the directory
    the image sits in, and the source dataset from the ``<dataset>_<index>``
    file stem that ``merge.py`` produces.

    Args:
        input_dir: Dataset root to scan.

    Returns:
        One record per readable image. Unreadable images and unparseable labels
        are logged and skipped -- statistics over a partially broken dataset are
        still useful, whereas a crash is not.
    """
    images_root = input_dir / "images"
    scan_root = images_root if images_root.is_dir() else input_dir

    records: list[ImageRecord] = []
    unreadable = 0
    bad_labels = 0

    for image_path in iter_image_files(scan_root):
        size = read_image_size(image_path)
        if size is None:
            unreadable += 1
            continue

        try:
            relative = image_path.relative_to(scan_root)
            split = relative.parts[0] if len(relative.parts) > 1 else "unassigned"
        except ValueError:
            split = "unassigned"

        label_path = image_path_to_label_path(image_path)
        boxes = []
        if label_path.is_file():
            try:
                boxes = parse_yolo_label_file(label_path)
            except (LabelParseError, OSError) as exc:
                LOGGER.debug("Bad label for %s: %s", image_path.name, exc)
                bad_labels += 1

        stem = image_path.stem
        source = stem.rsplit("_", 1)[0] if "_" in stem else "unknown"

        records.append(
            ImageRecord(
                path=image_path,
                width=size[0],
                height=size[1],
                source_dataset=source,
                split=split,
                boxes=boxes,
            )
        )

    if unreadable:
        LOGGER.warning("%d images could not be read and are excluded", unreadable)
    if bad_labels:
        LOGGER.warning("%d label files could not be parsed", bad_labels)
    return records


def _line_count_method(labelled: int, guessed: int) -> str:
    """Describe how the line-count distribution was obtained.

    Reporting a flat ``"HEURISTIC"`` would understate a dataset that actually
    labels plate type (``BSD``/``BSV``), and reporting ``"LABEL"`` for a mixed
    corpus would overstate it. Since the two-line plate rate is the headline
    number for this project, the provenance has to be exact.

    Args:
        labelled: Boxes whose line count came from a true label.
        guessed: Boxes whose line count came from the aspect-ratio threshold.

    Returns:
        ``"LABEL"``, ``"HEURISTIC"``, or ``"MIXED"``. Empty input counts as
        heuristic -- there is no evidence to claim otherwise.
    """
    if labelled and not guessed:
        return "LABEL"
    if guessed and not labelled:
        return "HEURISTIC"
    if labelled and guessed:
        return "MIXED"
    return "HEURISTIC"


def compute_statistics(records: Sequence[ImageRecord]) -> dict[str, Any]:
    """Reduce the loaded records to the summary written as ``statistics.json``.

    Args:
        records: The dataset.

    Returns:
        A JSON-serialisable summary.
    """
    per_split: Counter[str] = Counter()
    per_source: Counter[str] = Counter()
    per_split_source: dict[str, Counter[str]] = defaultdict(Counter)
    boxes_per_image: list[int] = []
    box_areas: list[float] = []
    aspect_ratios: list[float] = []
    image_widths: list[int] = []
    image_heights: list[int] = []
    centres: list[tuple[float, float]] = []
    characters: Counter[str] = Counter()
    plate_lengths: list[int] = []
    line_counts: Counter[str] = Counter()
    line_counts_per_split: dict[str, Counter[str]] = defaultdict(Counter)
    line_count_labelled = 0
    line_count_guessed = 0

    for record in records:
        per_split[record.split] += 1
        per_source[record.source_dataset] += 1
        per_split_source[record.split][record.source_dataset] += 1
        boxes_per_image.append(record.box_count)
        image_widths.append(record.width)
        image_heights.append(record.height)

        for box in record.boxes:
            if box.width <= 0 or box.height <= 0:
                continue
            box_areas.append(box.area)
            centres.append((box.x_center, box.y_center))
            try:
                ratio = box.aspect_ratio_for(record.width, record.height)
            except ValueError:
                continue
            aspect_ratios.append(ratio)
            estimate = str(box.estimated_line_count(record.width, record.height))
            line_counts[estimate] += 1
            line_counts_per_split[record.split][estimate] += 1
            # Track where each figure came from. A source that labels plate type
            # (e.g. BSD/BSV) gives a true line count; only the rest is guessed.
            if box.line_count is not None:
                line_count_labelled += 1
            else:
                line_count_guessed += 1

            if box.plate_text:
                text = box.plate_text.replace("-", "").replace(".", "").upper()
                characters.update(character for character in text if character.isalnum())
                plate_lengths.append(len(text))

    _describe = summarise_distribution

    total_boxes = sum(boxes_per_image)
    two_line = line_counts.get("2", 0)
    ratio_two_line = two_line / len(aspect_ratios) if aspect_ratios else 0.0

    return {
        "images_total": len(records),
        "boxes_total": total_boxes,
        "background_images": sum(1 for record in records if record.is_background),
        "images_per_split": {
            name: per_split.get(name, 0)
            for name in SPLIT_ORDER
            if per_split.get(name, 0) or name in per_split
        },
        "images_per_source": dict(sorted(per_source.items())),
        "images_per_split_and_source": {
            split: dict(sorted(counter.items()))
            for split, counter in sorted(per_split_source.items())
        },
        "boxes_per_image": _describe([float(n) for n in boxes_per_image], "boxes_per_image"),
        "boxes_per_image_histogram": dict(sorted(Counter(boxes_per_image).items())),
        "box_area_fraction": _describe(box_areas, "box_area_fraction"),
        "tiny_boxes_below_0_5_percent": sum(1 for area in box_areas if area < 0.005),
        "aspect_ratio": _describe(aspect_ratios, "box_aspect_ratio"),
        "image_width": _describe([float(w) for w in image_widths], "image_width"),
        "image_height": _describe([float(h) for h in image_heights], "image_height"),
        "line_count_estimate": {
            "method": _line_count_method(line_count_labelled, line_count_guessed),
            "threshold": AR_ONE_LINE_MIN,
            "labelled_boxes": line_count_labelled,
            "heuristic_boxes": line_count_guessed,
            "note": (
                "Per box, the true line_count label is used when the source "
                "provides one; only boxes without a label fall back to the "
                "aspect-ratio threshold. Perspective and loose boxes move "
                "unlabelled plates across that threshold, so the heuristic "
                "portion is approximate."
            ),
            "counts": dict(sorted(line_counts.items())),
            "two_line_fraction": round(ratio_two_line, 4),
            "per_split": {
                split: dict(sorted(counter.items()))
                for split, counter in sorted(line_counts_per_split.items())
            },
        },
        "plate_text": {
            "annotated_boxes": len(plate_lengths),
            "character_frequency": dict(
                sorted(characters.items(), key=lambda item: (-item[1], item[0]))
            ),
            "length_histogram": dict(sorted(Counter(plate_lengths).items())),
            "note": (
                "Empty unless labels carry the optional plate_text field "
                "(merge.py --include-extras). Detection-only sources have none."
            ),
        },
        "_centres": centres,  # Consumed by the heatmap, stripped before writing.
    }


def _normalise_plate_text(text: str) -> str:
    """Strip separators and case from a plate string.

    Args:
        text: Raw transcription, possibly containing ``-`` or ``.``.

    Returns:
        The upper-case alphanumeric-only form.
    """
    stripped = text.replace("-", "").replace(".", "").replace(" ", "").upper()
    return "".join(character for character in stripped if character.isalnum())


def compute_plate_text_statistics(csv_path: Path) -> dict[str, Any]:
    """Summarise the plate transcriptions produced by ``build_plate_text.py``.

    The character datasets are a corpus of their own: their images are not part
    of the detection split, so these figures describe what an OCR stage could be
    trained and measured on, not the detection set.

    Args:
        csv_path: Table with at least ``plate_text``; ``is_valid_format``,
            ``line_count`` and ``source_dataset`` are used when present.

    Returns:
        A JSON-serialisable summary. ``{}`` when the file holds no usable rows.

    Raises:
        OSError: If the file cannot be read.
    """
    characters: Counter[str] = Counter()
    characters_valid: Counter[str] = Counter()
    lengths: Counter[int] = Counter()
    lengths_valid: Counter[int] = Counter()
    line_counts: Counter[str] = Counter()
    per_dataset: dict[str, Counter[str]] = defaultdict(Counter)
    total = 0
    valid = 0

    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            text = _normalise_plate_text((row.get("plate_text") or "").strip())
            if not text:
                continue
            total += 1
            is_valid = (row.get("is_valid_format") or "").strip().lower() == "true"
            source = (row.get("source_dataset") or "unknown").strip() or "unknown"
            line_count = (row.get("line_count") or "unknown").strip() or "unknown"

            characters.update(text)
            lengths[len(text)] += 1
            line_counts[line_count] += 1
            per_dataset[source]["images"] += 1
            if is_valid:
                valid += 1
                characters_valid.update(text)
                lengths_valid[len(text)] += 1
                per_dataset[source]["valid_format"] += 1

    if not total:
        LOGGER.warning("No usable plate transcriptions in %s", csv_path)
        return {}

    def _by_count(counter: Counter[str]) -> dict[str, int]:
        return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))

    return {
        "source": "external",
        "csv": str(csv_path),
        "note": (
            "Reconstructed by build_plate_text.py from the multi-class character "
            "datasets. Those images are a separate corpus from the detection "
            "split, so these counts do not add to boxes_total."
        ),
        "reconstructed_strings": total,
        "valid_format_strings": valid,
        "valid_format_rate": round(valid / total, 4),
        "character_frequency": _by_count(characters),
        "character_frequency_valid_only": _by_count(characters_valid),
        "distinct_characters": len(characters),
        "length_histogram": dict(sorted(lengths.items())),
        "length_histogram_valid_only": dict(sorted(lengths_valid.items())),
        "line_count_distribution": dict(sorted(line_counts.items())),
        "per_dataset": {name: dict(counter) for name, counter in sorted(per_dataset.items())},
    }


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------


def _setup_matplotlib() -> Any:
    """Import matplotlib with a headless backend and a consistent style.

    Returns:
        The ``matplotlib.pyplot`` module.

    Raises:
        ImportError: If matplotlib is not installed.
    """
    try:
        import matplotlib

        # Agg before pyplot: these scripts run on servers and in CI with no
        # display, and the default backend would fail there.
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - dependency is declared
        raise ImportError(
            "Charts need matplotlib. Install it with: pip install matplotlib\n"
            "Or pass --no-charts to write statistics.json only."
        ) from exc

    plt.rcParams.update(
        {
            "figure.dpi": 110,
            "savefig.dpi": 150,
            "savefig.bbox": "tight",
            "font.size": 10,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.alpha": 0.25,
            "grid.linestyle": "-",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titleweight": "bold",
            "axes.titlesize": 11,
        }
    )
    return plt


def _save(plt: Any, figure: Any, destination: Path) -> Path:
    """Write a figure to disk and close it.

    Closing matters: a run over several datasets otherwise accumulates open
    figures until matplotlib starts warning and memory climbs.

    Args:
        plt: The pyplot module.
        figure: The figure to save.
        destination: Target PNG path.

    Returns:
        The path written to.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination)
    plt.close(figure)
    LOGGER.debug("Wrote chart: %s", destination)
    return destination


def render_charts(
    summary: dict[str, Any], records: Sequence[ImageRecord], output_dir: Path
) -> list[Path]:
    """Render every chart for a dataset.

    Args:
        summary: Output of :func:`compute_statistics`, including ``_centres``.
        records: The dataset, for the distributions that need raw values.
        output_dir: Directory to write the PNGs into.

    Returns:
        Paths of the charts that were written. Charts with no data to show are
        skipped rather than emitted empty.

    Raises:
        ImportError: If matplotlib is unavailable.
    """
    plt = _setup_matplotlib()
    written: list[Path] = []

    written += _chart_splits(plt, summary, output_dir)
    written += _chart_boxes_per_image(plt, summary, output_dir)
    written += _chart_box_area(plt, records, output_dir)
    written += _chart_aspect_ratio(plt, records, output_dir)
    written += _chart_image_sizes(plt, records, output_dir)
    written += _chart_heatmap(plt, summary, output_dir)
    written += _chart_characters(plt, summary, output_dir)
    written += _chart_plate_length(plt, summary, output_dir)

    return written


def _chart_splits(plt: Any, summary: dict[str, Any], output_dir: Path) -> list[Path]:
    """Chart image counts per split and per source dataset.

    Args:
        plt: The pyplot module.
        summary: The computed statistics.
        output_dir: Destination directory.

    Returns:
        A single-element list, or empty when there is nothing to plot.
    """
    per_split = summary["images_per_split"]
    per_source = summary["images_per_source"]
    if not per_split and not per_source:
        return []

    figure, axes = plt.subplots(1, 2, figsize=(11, 4.2))

    names = list(per_split)
    values = [per_split[name] for name in names]
    axes[0].bar(names, values, color=ACCENT)
    total = sum(values) or 1
    for index, value in enumerate(values):
        axes[0].text(index, value, f"{value}\n{100 * value / total:.1f}%", ha="center", va="bottom")
    axes[0].set_title("Images per split")
    axes[0].set_ylabel("images")
    axes[0].margins(y=0.18)

    sources = list(per_source)
    counts = [per_source[name] for name in sources]
    axes[1].barh(sources, counts, color=ACCENT)
    for index, value in enumerate(counts):
        axes[1].text(value, index, f" {value}", va="center")
    axes[1].set_title("Images per source dataset")
    axes[1].set_xlabel("images")
    axes[1].margins(x=0.15)

    figure.suptitle("Dataset composition", fontweight="bold")
    return [_save(plt, figure, output_dir / "images_per_split.png")]


def _chart_boxes_per_image(plt: Any, summary: dict[str, Any], output_dir: Path) -> list[Path]:
    """Chart the distribution of box counts per image.

    Args:
        plt: The pyplot module.
        summary: The computed statistics.
        output_dir: Destination directory.

    Returns:
        A single-element list, or empty when there is nothing to plot.
    """
    histogram = summary["boxes_per_image_histogram"]
    if not histogram:
        return []

    figure, axis = plt.subplots(figsize=(7, 4.2))
    keys = [int(key) for key in histogram]
    values = [histogram[key] for key in histogram]
    axis.bar(keys, values, color=ACCENT)
    for key, value in zip(keys, values):
        axis.text(key, value, str(value), ha="center", va="bottom", fontsize=9)
    axis.set_title("Plates per image")
    axis.set_xlabel("boxes in one image")
    axis.set_ylabel("images")
    axis.set_xticks(keys)
    axis.margins(y=0.15)
    return [_save(plt, figure, output_dir / "boxes_per_image.png")]


def _chart_box_area(plt: Any, records: Sequence[ImageRecord], output_dir: Path) -> list[Path]:
    """Chart the box area distribution, marking the small-plate threshold.

    Args:
        plt: The pyplot module.
        records: The dataset.
        output_dir: Destination directory.

    Returns:
        A single-element list, or empty when there are no boxes.
    """
    areas = [box.area * 100 for record in records for box in record.boxes if box.area > 0]
    if not areas:
        return []

    figure, axis = plt.subplots(figsize=(7.5, 4.2))
    axis.hist(areas, bins=50, color=ACCENT, edgecolor="white", linewidth=0.4)
    axis.axvline(0.5, color=WARN, linestyle="--", linewidth=1.5)
    tiny = sum(1 for area in areas if area < 0.5)
    axis.text(
        0.5,
        axis.get_ylim()[1] * 0.92,
        f"  0.5% threshold\n  {tiny} box(es) below ({100 * tiny / len(areas):.1f}%)",
        color=WARN,
        va="top",
        fontsize=9,
    )
    axis.set_title("Plate area as a share of the image")
    axis.set_xlabel("box area (% of image)")
    axis.set_ylabel("boxes")
    return [_save(plt, figure, output_dir / "box_area.png")]


def _chart_aspect_ratio(plt: Any, records: Sequence[ImageRecord], output_dir: Path) -> list[Path]:
    """Chart the box aspect-ratio distribution with the plate-standard markers.

    Args:
        plt: The pyplot module.
        records: The dataset.
        output_dir: Destination directory.

    Returns:
        A single-element list, or empty when there are no usable boxes.
    """
    ratios = [ratio for record in records for ratio in record.box_aspect_ratios()]
    if not ratios:
        return []

    figure, axis = plt.subplots(figsize=(9, 4.6))
    upper = min(max(ratios), 8.0)
    axis.hist(
        [ratio for ratio in ratios if ratio <= upper],
        bins=60,
        color=ACCENT,
        edgecolor="white",
        linewidth=0.4,
    )

    axis.axvline(AR_ONE_LINE_MIN, color=WARN, linestyle="--", linewidth=1.8)
    for value, label in (
        (AR_MOTORCYCLE, "motorcycle 190x140 (2 lines)"),
        (AR_CAR_SHORT, "car short 330x165 (2 lines)"),
        (AR_CAR_LONG, "car long 520x110 (1 line)"),
    ):
        if value <= upper:
            axis.axvline(value, color=MUTED, linestyle=":", linewidth=1.2)
            axis.text(
                value,
                axis.get_ylim()[1] * 0.98,
                f" {label}",
                rotation=90,
                va="top",
                fontsize=8,
                color="#475569",
            )

    one_line = sum(1 for ratio in ratios if ratio >= AR_ONE_LINE_MIN)
    two_line = len(ratios) - one_line
    axis.text(
        AR_ONE_LINE_MIN,
        axis.get_ylim()[1] * 0.55,
        f"  threshold {AR_ONE_LINE_MIN}\n"
        f"  <- est. 2 lines: {two_line}\n"
        f"  -> est. 1 line: {one_line}",
        color=WARN,
        va="top",
        fontsize=9,
    )

    axis.set_title("Plate aspect ratio (line count is a HEURISTIC, not a label)")
    axis.set_xlabel("box width / height")
    axis.set_ylabel("boxes")
    figure.text(
        0.5,
        -0.04,
        "Thresholds from QCVN 08:2024/BCA nominal plate sizes. Perspective and "
        "loose boxes move plates across the 2.5 line.",
        ha="center",
        fontsize=8,
        color="#64748b",
    )
    return [_save(plt, figure, output_dir / "aspect_ratio.png")]


def _chart_image_sizes(plt: Any, records: Sequence[ImageRecord], output_dir: Path) -> list[Path]:
    """Chart the distribution of source image resolutions.

    Args:
        plt: The pyplot module.
        records: The dataset.
        output_dir: Destination directory.

    Returns:
        A single-element list, or empty when there is nothing to plot.
    """
    if not records:
        return []

    widths = [record.width for record in records]
    heights = [record.height for record in records]

    figure, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    axes[0].scatter(widths, heights, s=10, alpha=0.35, color=ACCENT, edgecolors="none")
    axes[0].set_title("Image resolution")
    axes[0].set_xlabel("width (px)")
    axes[0].set_ylabel("height (px)")

    sizes = Counter(f"{w}x{h}" for w, h in zip(widths, heights))
    common = sizes.most_common(10)
    axes[1].barh(
        [name for name, _ in reversed(common)], [n for _, n in reversed(common)], color=ACCENT
    )
    axes[1].set_title("Ten most common resolutions")
    axes[1].set_xlabel("images")
    axes[1].margins(x=0.15)

    figure.suptitle("Source resolutions", fontweight="bold")
    return [_save(plt, figure, output_dir / "image_sizes.png")]


def _chart_heatmap(plt: Any, summary: dict[str, Any], output_dir: Path) -> list[Path]:
    """Chart where in the frame plates tend to appear.

    Args:
        plt: The pyplot module.
        summary: The computed statistics, including ``_centres``.
        output_dir: Destination directory.

    Returns:
        A single-element list, or empty when there are no centres.
    """
    centres = summary.get("_centres") or []
    if not centres:
        return []

    try:
        import numpy as np
    except ImportError:  # pragma: no cover
        return []

    xs = np.array([centre[0] for centre in centres])
    ys = np.array([centre[1] for centre in centres])

    figure, axis = plt.subplots(figsize=(6.2, 5.4))
    heat, _, _, mesh = axis.hist2d(
        xs, ys, bins=HEATMAP_BINS, range=[[0, 1], [0, 1]], cmap="viridis"
    )
    figure.colorbar(mesh, ax=axis, label="boxes")
    axis.invert_yaxis()  # y grows downwards in image coordinates.
    axis.set_title("Plate centre position in the frame")
    axis.set_xlabel("x (fraction of width)")
    axis.set_ylabel("y (fraction of height)")
    axis.grid(False)
    return [_save(plt, figure, output_dir / "box_position_heatmap.png")]


def _chart_characters(plt: Any, summary: dict[str, Any], output_dir: Path) -> list[Path]:
    """Chart character frequency in the plate transcriptions.

    Args:
        plt: The pyplot module.
        summary: The computed statistics.
        output_dir: Destination directory.

    Returns:
        A single-element list, or empty when no transcriptions exist.
    """
    frequency = summary["plate_text"]["character_frequency"]
    if not frequency:
        LOGGER.info("No plate transcriptions found; skipping the character chart.")
        return []

    figure, axis = plt.subplots(figsize=(11, 4.4))
    characters = sorted(frequency)
    counts = [frequency[character] for character in characters]
    colours = [WARN if character in "IJOQW" else ACCENT for character in characters]
    axis.bar(characters, counts, color=colours)
    axis.set_title("Character frequency (red = letters that should never appear on a VN plate)")
    axis.set_xlabel("character")
    axis.set_ylabel("occurrences")

    total = summary["plate_text"].get("reconstructed_strings")
    valid = summary["plate_text"].get("valid_format_strings")
    if total:
        figure.text(
            0.5,
            -0.04,
            f"{total} reconstructed plate strings, {valid} of which match the "
            "Vietnamese plate grammar. Counts cover every string, valid or not.",
            ha="center",
            fontsize=8,
            color="#64748b",
        )
    return [_save(plt, figure, output_dir / "character_frequency.png")]


def _chart_plate_length(plt: Any, summary: dict[str, Any], output_dir: Path) -> list[Path]:
    """Chart the distribution of plate string lengths.

    Args:
        plt: The pyplot module.
        summary: The computed statistics.
        output_dir: Destination directory.

    Returns:
        A single-element list, or empty when no transcriptions exist.
    """
    histogram = summary["plate_text"]["length_histogram"]
    if not histogram:
        return []

    figure, axis = plt.subplots(figsize=(8.5, 4.4))
    keys = [int(key) for key in histogram]
    values = [histogram[key] for key in histogram]
    axis.bar(keys, values, color=MUTED, label="all reconstructed")

    valid_histogram = summary["plate_text"].get("length_histogram_valid_only") or {}
    if valid_histogram:
        axis.bar(
            [int(key) for key in valid_histogram],
            list(valid_histogram.values()),
            color=ACCENT,
            label="matches VN plate grammar",
        )
        axis.legend(frameon=False)

    axis.set_title("Plate string length (separators removed)")
    axis.set_xlabel("characters")
    axis.set_ylabel("plates")
    axis.set_xticks(keys)
    return [_save(plt, figure, output_dir / "plate_length.png")]


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line parser.

    Returns:
        The configured parser.
    """
    parser = argparse.ArgumentParser(
        prog="statistics.py",
        description=(
            "Compute dataset statistics and render the charts that go into the "
            "Phase 2 dataset report."
        ),
        epilog=(
            "Examples:\n"
            "  python statistics.py\n"
            "  python statistics.py --input-dir datasets/processed/merged\n"
            "  python statistics.py --no-charts\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="Dataset to analyse (default: <datasets>/processed/yolo).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="Where to write charts and statistics.json (default: <datasets>/statistics).",
    )
    parser.add_argument(
        "--no-charts",
        action="store_true",
        help="Write statistics.json only, skipping the PNGs.",
    )
    parser.add_argument(
        "--plate-text-csv",
        type=Path,
        default=None,
        metavar="CSV",
        help=(
            "Plate transcriptions from build_plate_text.py, for the character "
            "frequency and string length charts (default: "
            "<datasets>/annotations/plate_text_labels.csv when it exists)."
        ),
    )
    return add_common_arguments(parser)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point.

    Args:
        argv: Argument list, defaulting to ``sys.argv[1:]``.

    Returns:
        ``0`` on success, ``1`` if the input directory is missing or empty.
    """
    args = build_parser().parse_args(argv)
    configure_logging(args.log_level)

    paths = resolve_dataset_paths(args.datasets_dir)
    input_dir = (args.input_dir or (paths.processed / "yolo")).expanduser().resolve()
    output_dir = (args.output_dir or paths.statistics).expanduser().resolve()

    if not input_dir.is_dir():
        LOGGER.error("Input directory does not exist: %s", input_dir)
        LOGGER.error("Run merge.py and split.py first, or pass --input-dir.")
        return 1

    LOGGER.info("Analysing %s", input_dir)
    records = collect_records(input_dir)
    if not records:
        LOGGER.error("No readable images under %s", input_dir)
        return 1

    summary = compute_statistics(records)

    # Detection labels carry no text. When the Charset step has produced a
    # transcription table, fold it in so the character charts have data.
    default_csv = paths.annotations / "plate_text_labels.csv"
    plate_csv = (args.plate_text_csv or default_csv).expanduser().resolve()
    if args.plate_text_csv is not None and not plate_csv.is_file():
        LOGGER.error("Plate text CSV does not exist: %s", plate_csv)
        return 1
    if plate_csv.is_file():
        try:
            external = compute_plate_text_statistics(plate_csv)
        except (OSError, csv.Error) as exc:
            LOGGER.error("Could not read %s: %s", plate_csv, exc)
            external = {}
        if external:
            summary["plate_text"] = {**summary["plate_text"], **external}
            LOGGER.info(
                "Plate transcriptions: %d strings (%d valid format) from %s",
                external["reconstructed_strings"],
                external["valid_format_strings"],
                plate_csv.name,
            )
    else:
        LOGGER.info("No plate transcription CSV found; character charts skipped.")

    charts: list[Path] = []
    if not args.no_charts:
        try:
            charts = render_charts(summary, records, output_dir)
        except ImportError as exc:
            LOGGER.error("%s", exc)
            LOGGER.warning("Continuing without charts.")

    summary.pop("_centres", None)
    summary["input_dir"] = str(input_dir)
    summary["charts"] = [str(path) for path in charts]
    write_json(output_dir / "statistics.json", summary)

    LOGGER.info("=" * 70)
    LOGGER.info("Images         : %d", summary["images_total"])
    LOGGER.info("Boxes          : %d", summary["boxes_total"])
    for split, count in summary["images_per_split"].items():
        LOGGER.info("    %-12s %d", split, count)
    line_estimate = summary["line_count_estimate"]
    LOGGER.info(
        "Line count     : %s (%s, threshold %.1f; %d labelled / %d heuristic)",
        ", ".join(f"{key}-line={value}" for key, value in line_estimate["counts"].items()) or "n/a",
        line_estimate["method"],
        line_estimate["threshold"],
        line_estimate["labelled_boxes"],
        line_estimate["heuristic_boxes"],
    )
    if 0 < line_estimate["two_line_fraction"] < 0.10:
        LOGGER.warning(
            "Only %.1f%% of boxes look like two-line plates. Two-line motorcycle "
            "plates are the known weak point; a corpus this skewed cannot fix it.",
            100 * line_estimate["two_line_fraction"],
        )
    if summary["tiny_boxes_below_0_5_percent"]:
        LOGGER.warning(
            "%d box(es) occupy less than 0.5%% of their image and will be hard to "
            "detect at 640px input.",
            summary["tiny_boxes_below_0_5_percent"],
        )
    LOGGER.info("Charts written : %d", len(charts))
    LOGGER.info("Output         : %s", output_dir)
    LOGGER.info("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
