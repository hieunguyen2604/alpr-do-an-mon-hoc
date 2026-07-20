"""Measure near-duplicate leakage across the splits of a YOLO dataset.

Usage examples::

    python scripts/dataset/verify_split_leakage.py --dataset-dir datasets/processed/yolo_v3
    python scripts/dataset/verify_split_leakage.py --dataset-dir datasets/processed/yolo_v3 \
        --thresholds 5 10 12 15 20 --grouped-at 10

Reading the output honestly
---------------------------
This script exists because the previous audit of this project drew a circular
conclusion. The corpus had been grouped with ``deduplicate.py`` at threshold 5
and split by group, and the split was then "verified" by looking for cross-split
pairs at threshold 5 -- which of course found none. A result that is *entailed by
the construction* is not evidence about the construction.

The tell was visible in the numbers: the smallest cross-split Hamming distance
came out at exactly 6 in all three split pairs. A distribution that stops dead
one step past the grouping threshold has been cut, not observed. (It reads as
"one step" rather than "one bit" because DCT perceptual hashes on this corpus
only ever produce *even* distances, so 6 is the first value above 5.)

The report therefore labels every threshold at or below ``--grouped-at`` as
``guaranteed-by-construction`` and only the thresholds above it as
``independent``. Only the independent rows carry information. A zero in a
guaranteed row means the splitter did its job; it says nothing about whether the
threshold was the right one.

The second trap, which the independent rows expose
--------------------------------------------------
A non-zero count above the grouping threshold is not automatically leakage.
Much of this corpus comes from fixed cameras -- a parking-barrier CCTV, a
traffic camera -- where every frame shares a background, a viewpoint and a
colour cast. A perceptual hash summarises exactly those global properties, so
two frames of *different* vehicles from one camera land close together. Above
roughly distance 10 on this corpus, that is what the matches are: same scene,
different car, different plate. Counting them as leakage would push the grouping
threshold up until transitive closure swallowed the whole dataset.

So the counts below are an upper bound on leakage, not a measurement of it.
Deciding which side of the line a given distance falls on requires looking at
the images, which is what ``--sample-pairs`` writes contact sheets for.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any, Final, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    add_common_arguments,
    bootstrap_project_path,
    configure_logging,
    iter_image_files,
    resolve_dataset_paths,
    write_csv,
    write_json,
)

bootstrap_project_path()

from deduplicate import compute_phash_and_size  # noqa: E402

LOGGER = logging.getLogger("dataset.verify_split_leakage")

SPLIT_NAMES: Final[tuple[str, str, str]] = ("train", "val", "test")
DEFAULT_THRESHOLDS: Final[tuple[int, ...]] = (5, 10, 12, 15, 20)


@dataclass(slots=True)
class HashedSplit:
    """The hashed contents of one dataset, tagged by split.

    Attributes:
        paths: Image paths, index-aligned with ``hashes`` and ``splits``.
        hashes: 64-bit perceptual hashes.
        splits: Split name per image.
    """

    paths: list[Path]
    hashes: list[int]
    splits: list[str]

    def __len__(self) -> int:
        """Return the number of hashed images."""
        return len(self.paths)


def hash_splits(dataset_dir: Path, *, workers: int = 8) -> HashedSplit:
    """Hash every image in a split dataset, remembering which split it is in.

    Args:
        dataset_dir: Root containing ``images/train``, ``images/val``,
            ``images/test``.
        workers: Threads used for decoding.

    Returns:
        The hashed corpus.

    Raises:
        FileNotFoundError: If no split directory exists under ``dataset_dir``.
    """
    from concurrent.futures import ThreadPoolExecutor

    paths: list[Path] = []
    splits: list[str] = []
    for name in SPLIT_NAMES:
        split_dir = dataset_dir / "images" / name
        if not split_dir.is_dir():
            LOGGER.warning("No %s split under %s", name, dataset_dir)
            continue
        found = sorted(iter_image_files(split_dir))
        paths.extend(found)
        splits.extend([name] * len(found))
        LOGGER.info("%-6s %6d images", name, len(found))

    if not paths:
        raise FileNotFoundError(f"No split images found under {dataset_dir}")

    hashes: list[int] = []
    kept_paths: list[Path] = []
    kept_splits: list[str] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for path, split, value in zip(paths, splits, pool.map(compute_phash_and_size, paths)):
            if value is None:
                continue
            hashes.append(value[0])
            kept_paths.append(path)
            kept_splits.append(split)

    LOGGER.info("Hashed %d of %d images", len(hashes), len(paths))
    return HashedSplit(paths=kept_paths, hashes=hashes, splits=kept_splits)


def cross_split_pairs(
    corpus: HashedSplit, max_threshold: int, *, chunk: int = 2048
) -> list[tuple[int, int, int]]:
    """Find every cross-split image pair within ``max_threshold`` bits.

    Uses the same vectorised popcount as ``deduplicate.py``: hashes are unpacked
    to bytes, each chunk of rows is XORed against the whole corpus at once, and
    a 256-entry lookup table turns the XOR bytes into bit counts. No Python loop
    runs over pairs, which is what makes a 15,000 image corpus -- 114 million
    pairs -- finish in seconds instead of hours.

    Args:
        corpus: The hashed, split-tagged images.
        max_threshold: Largest distance to record.
        chunk: Rows per iteration; controls peak memory.

    Returns:
        ``(left, right, distance)`` triples with ``left < right``, restricted to
        pairs whose two images are in *different* splits.

    Raises:
        ImportError: If numpy is unavailable.
    """
    import numpy as np

    count = len(corpus)
    matrix = np.array(
        [list(int(value).to_bytes(8, "big")) for value in corpus.hashes], dtype=np.uint8
    )
    split_codes = np.array([SPLIT_NAMES.index(name) for name in corpus.splits], dtype=np.int8)
    popcount = (
        np.unpackbits(np.arange(256, dtype=np.uint8)[:, None], axis=1).sum(axis=1).astype(np.uint8)
    )

    results: list[tuple[int, int, int]] = []
    for start in range(0, count, chunk):
        stop = min(start + chunk, count)
        block = np.bitwise_xor(matrix[start:stop, None, :], matrix[None, :, :])
        distances = popcount[block].sum(axis=2)

        close = distances <= max_threshold
        # Upper triangle only, and only pairs straddling two splits.
        cross = split_codes[start:stop, None] != split_codes[None, :]
        rows, cols = np.nonzero(close & cross)
        absolute = rows + start
        keep = absolute < cols
        for row, left, right in zip(rows[keep], absolute[keep], cols[keep]):
            results.append((int(left), int(right), int(distances[row, right])))

    results.sort()
    LOGGER.info("Found %d cross-split pairs within distance %d", len(results), max_threshold)
    return results


def tally(
    corpus: HashedSplit,
    pairs: Sequence[tuple[int, int, int]],
    thresholds: Sequence[int],
    grouped_at: int | None,
) -> list[dict[str, Any]]:
    """Build the per-threshold leakage table.

    Args:
        corpus: The hashed corpus, for split lookup.
        pairs: Cross-split pairs from :func:`cross_split_pairs`.
        thresholds: Distances to report at, ascending.
        grouped_at: The threshold the corpus was grouped at, or ``None``. Rows
            at or below it are marked ``guaranteed-by-construction`` because
            grouping forced those pairs into one split; they cannot appear
            cross-split no matter how good or bad the split is.

    Returns:
        One row per threshold, each carrying the three split-pair counts, the
        minimum distance seen, and the evidence status.
    """
    combos = [f"{a}-{b}" for a, b in combinations(SPLIT_NAMES, 2)]

    def combo_of(left: int, right: int) -> str:
        pair = tuple(sorted((corpus.splits[left], corpus.splits[right]), key=SPLIT_NAMES.index))
        return f"{pair[0]}-{pair[1]}"

    rows: list[dict[str, Any]] = []
    for threshold in sorted(thresholds):
        counts: dict[str, int] = {name: 0 for name in combos}
        minimum: int | None = None
        for left, right, distance in pairs:
            if distance > threshold:
                continue
            counts[combo_of(left, right)] += 1
            if minimum is None or distance < minimum:
                minimum = distance

        status = (
            "guaranteed-by-construction"
            if grouped_at is not None and threshold <= grouped_at
            else "independent"
        )
        row: dict[str, Any] = {
            "threshold": threshold,
            "status": status,
            "total_cross_split_pairs": sum(counts.values()),
            "min_distance": minimum if minimum is not None else "",
        }
        row.update(counts)
        rows.append(row)
    return rows


def sample_sheets(
    corpus: HashedSplit,
    pairs: Sequence[tuple[int, int, int]],
    distances: Sequence[int],
    output_dir: Path,
    *,
    per_distance: int = 5,
    seed: int = 11,
) -> list[dict[str, Any]]:
    """Write side-by-side contact sheets so pairs can be judged by eye.

    A count cannot distinguish "the same photograph in two splits" from "two
    different cars photographed by the same fixed camera". Only looking can.

    Args:
        corpus: The hashed corpus.
        pairs: Cross-split pairs.
        distances: Which exact distances to sample.
        output_dir: Directory for the PNG sheets.
        per_distance: Pairs sampled per distance.
        seed: Sampling seed, for reproducibility.

    Returns:
        One row per sampled pair, recording what was rendered.
    """
    import random

    from PIL import Image

    output_dir.mkdir(parents=True, exist_ok=True)
    by_distance: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for left, right, distance in pairs:
        by_distance[distance].append((left, right))

    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    cell = 260

    for distance in distances:
        candidates = by_distance.get(distance, [])
        if not candidates:
            LOGGER.info("No cross-split pairs at distance %d to sample", distance)
            continue
        chosen = rng.sample(candidates, min(per_distance, len(candidates)))
        sheet = Image.new("RGB", (cell * 2 + 30, cell * len(chosen) + 10), "white")
        for index, (left, right) in enumerate(chosen):
            for column, item in enumerate((left, right)):
                try:
                    with Image.open(corpus.paths[item]) as image:
                        thumbnail = image.convert("RGB")
                        thumbnail.thumbnail((cell - 10, cell - 10))
                        sheet.paste(thumbnail, (column * (cell + 20) + 5, index * cell + 5))
                except OSError as exc:
                    LOGGER.warning("Cannot render %s: %s", corpus.paths[item], exc)
            rows.append(
                {
                    "distance": distance,
                    "image_a": corpus.paths[left].name,
                    "split_a": corpus.splits[left],
                    "image_b": corpus.paths[right].name,
                    "split_b": corpus.splits[right],
                }
            )
        destination = output_dir / f"cross_split_d{distance}.png"
        sheet.save(destination)
        LOGGER.info("Wrote %s (%d pairs)", destination, len(chosen))

    return rows


def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line parser.

    Returns:
        The configured parser.
    """
    parser = argparse.ArgumentParser(
        prog="verify_split_leakage.py",
        description=(
            "Measure cross-split near-duplicate pairs at several thresholds, "
            "separating results that are guaranteed by the grouping from those "
            "that carry independent evidence."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        required=True,
        metavar="DIR",
        help="Split dataset root containing images/{train,val,test}.",
    )
    parser.add_argument(
        "--thresholds",
        nargs="+",
        type=int,
        default=list(DEFAULT_THRESHOLDS),
        metavar="N",
        help="Hamming distances to report at (default: %(default)s).",
    )
    parser.add_argument(
        "--grouped-at",
        type=int,
        default=None,
        metavar="N",
        help=(
            "The threshold this dataset was grouped at. Rows at or below it are "
            "labelled guaranteed-by-construction and must not be cited as "
            "evidence that the split is clean."
        ),
    )
    parser.add_argument(
        "--sample-pairs",
        nargs="*",
        type=int,
        default=None,
        metavar="D",
        help=(
            "Exact distances to render contact sheets for, so pairs can be "
            "judged by eye. Give no values to skip."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="Where to write the report (default: <datasets>/reports).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        metavar="N",
        help="Threads used for hashing (default: %(default)s).",
    )
    return add_common_arguments(parser)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point.

    Args:
        argv: Argument list, defaulting to ``sys.argv[1:]``.

    Returns:
        ``0`` on success, ``1`` if the dataset directory has no images.
    """
    args = build_parser().parse_args(argv)
    configure_logging(args.log_level)

    paths = resolve_dataset_paths(args.datasets_dir)
    dataset_dir = args.dataset_dir.expanduser().resolve()
    output_dir = (args.output_dir or paths.reports).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        corpus = hash_splits(dataset_dir, workers=max(1, args.workers))
    except FileNotFoundError as exc:
        LOGGER.error("%s", exc)
        return 1

    thresholds = sorted(set(args.thresholds))
    pairs = cross_split_pairs(corpus, max(thresholds))
    rows = tally(corpus, pairs, thresholds, args.grouped_at)

    sampled: list[dict[str, Any]] = []
    if args.sample_pairs:
        sampled = sample_sheets(
            corpus, pairs, args.sample_pairs, output_dir / "cross_split_samples"
        )
        write_csv(
            output_dir / "cross_split_samples.csv",
            sampled,
            fieldnames=["distance", "image_a", "split_a", "image_b", "split_b"],
        )

    combos = [f"{a}-{b}" for a, b in combinations(SPLIT_NAMES, 2)]
    write_csv(
        output_dir / "leakage_by_threshold.csv",
        rows,
        fieldnames=["threshold", "status", "total_cross_split_pairs", "min_distance", *combos],
    )
    write_json(
        output_dir / "leakage_by_threshold.json",
        {
            "dataset_dir": str(dataset_dir),
            "images_hashed": len(corpus),
            "images_per_split": {
                name: sum(1 for item in corpus.splits if item == name) for name in SPLIT_NAMES
            },
            "grouped_at": args.grouped_at,
            "rows": rows,
            "interpretation": (
                "Rows with status 'guaranteed-by-construction' are entailed by "
                "grouping the corpus at --grouped-at and splitting by group; a "
                "zero there confirms the splitter worked but is NOT evidence "
                "that the threshold was adequate. Only 'independent' rows carry "
                "information, and even those are an upper bound: on a corpus "
                "dominated by fixed cameras, two frames of different vehicles "
                "from one camera are perceptually close without being duplicates."
            ),
        },
    )

    LOGGER.info("=" * 78)
    LOGGER.info(
        "%-10s %-28s %10s %10s %10s %6s",
        "threshold",
        "status",
        "train-val",
        "train-test",
        "val-test",
        "min-d",
    )
    for row in rows:
        LOGGER.info(
            "%-10d %-28s %10d %10d %10d %6s",
            row["threshold"],
            row["status"],
            row["train-val"],
            row["train-test"],
            row["val-test"],
            row["min_distance"],
        )
    LOGGER.info("=" * 78)
    LOGGER.info("Report written to %s", output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
