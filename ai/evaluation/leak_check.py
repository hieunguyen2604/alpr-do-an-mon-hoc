"""Detect train/test contamination in YOLO datasets via perceptual hashing."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

LOGGER = logging.getLogger("leak_check")

IMAGE_SUFFIXES: frozenset[str] = frozenset(
    {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
)

#: Hamming distance at or below which two 64-bit phashes are treated as the
#: same image. 5/64 bits is the conventional "visually identical" band.
DEFAULT_THRESHOLD: int = 5

#: Distance bands reported in the histogram, as (inclusive_low, inclusive_high).
HISTOGRAM_BANDS: tuple[tuple[int, int], ...] = (
    (0, 0),
    (1, 5),
    (6, 10),
    (11, 15),
    (16, 20),
)


@dataclass(frozen=True)
class SplitHashes:
    """Perceptual hashes for one dataset split."""

    name: str
    paths: list[Path]
    #: Shape (n_images, 64), dtype uint8, one bit per column.
    bits: np.ndarray
    unreadable: list[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.paths)


@dataclass(frozen=True)
class DuplicatePair:
    """One cross-split pair whose Hamming distance is within the threshold."""

    split_a: str
    path_a: str
    split_b: str
    path_b: str
    distance: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "split_a": self.split_a,
            "image_a": self.path_a,
            "split_b": self.split_b,
            "image_b": self.path_b,
            "hamming_distance": self.distance,
        }


def discover_images(split_dir: Path) -> list[Path]:
    """Return every image file under ``split_dir``, sorted for reproducibility."""
    if not split_dir.is_dir():
        return []
    found = [
        path
        for path in sorted(split_dir.rglob("*"))
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    ]
    return found


def hash_split(name: str, paths: Sequence[Path], hash_size: int = 8) -> SplitHashes:
    """Compute phash for every image, returning an unpacked bit matrix."""
    import imagehash
    from PIL import Image

    rows: list[np.ndarray] = []
    kept: list[Path] = []
    unreadable: list[str] = []

    for index, path in enumerate(paths):
        if index and index % 500 == 0:
            LOGGER.info("  ... hashed %d/%d of split '%s'", index, len(paths), name)
        try:
            with Image.open(path) as handle:
                digest = imagehash.phash(handle, hash_size=hash_size)
        except Exception as exc:  # noqa: BLE001 - any decode failure is reportable
            unreadable.append(f"{path}: {type(exc).__name__}")
            continue
        rows.append(digest.hash.flatten().astype(np.uint8))
        kept.append(path)

    if rows:
        bits = np.vstack(rows)
    else:
        bits = np.zeros((0, hash_size * hash_size), dtype=np.uint8)

    if unreadable:
        LOGGER.warning("Split '%s': %d unreadable image(s)", name, len(unreadable))

    return SplitHashes(name=name, paths=kept, bits=bits, unreadable=unreadable)


def hamming_matrix(bits_a: np.ndarray, bits_b: np.ndarray) -> np.ndarray:
    """Pairwise Hamming distances between two unpacked bit matrices."""
    if bits_a.size == 0 or bits_b.size == 0:
        return np.zeros((bits_a.shape[0], bits_b.shape[0]), dtype=np.int16)

    a = bits_a.astype(np.int16)
    b = bits_b.astype(np.int16)
    ones_a = np.ones_like(a)
    ones_b = np.ones_like(b)
    differing = a @ (ones_b - b).T + (ones_a - a) @ b.T
    return differing.astype(np.int16)


def find_cross_split_duplicates(
    split_a: SplitHashes,
    split_b: SplitHashes,
    threshold: int,
    max_pairs_recorded: int,
) -> tuple[list[DuplicatePair], dict[str, int], int, int]:
    """Compare two splits: close pairs, histogram, minimum distance, close count."""
    distances = hamming_matrix(split_a.bits, split_b.bits)

    histogram: dict[str, int] = {}
    for low, high in HISTOGRAM_BANDS:
        label = f"{low}" if low == high else f"{low}-{high}"
        histogram[label] = int(np.count_nonzero((distances >= low) & (distances <= high)))
    highest_band = HISTOGRAM_BANDS[-1][1]
    histogram[f">{highest_band}"] = int(np.count_nonzero(distances > highest_band))

    minimum = int(distances.min()) if distances.size else -1

    rows, cols = np.nonzero(distances <= threshold)
    pairs: list[DuplicatePair] = []
    for row, col in zip(rows.tolist(), cols.tolist(), strict=True):
        if len(pairs) >= max_pairs_recorded:
            break
        pairs.append(
            DuplicatePair(
                split_a=split_a.name,
                path_a=str(split_a.paths[row]),
                split_b=split_b.name,
                path_b=str(split_b.paths[col]),
                distance=int(distances[row, col]),
            )
        )

    total_close = int(np.count_nonzero(distances <= threshold))
    return pairs, histogram, minimum, total_close


def find_within_split_duplicates(
    split: SplitHashes, threshold: int, max_pairs_recorded: int
) -> tuple[int, list[DuplicatePair]]:
    """Count near-duplicate pairs *inside* one split (upper triangle only)."""
    distances = hamming_matrix(split.bits, split.bits)
    if distances.size == 0:
        return 0, []
    upper = np.triu(np.ones_like(distances, dtype=bool), k=1)
    close = (distances <= threshold) & upper
    rows, cols = np.nonzero(close)

    pairs: list[DuplicatePair] = []
    for row, col in zip(
        rows.tolist()[:max_pairs_recorded], cols.tolist()[:max_pairs_recorded], strict=True
    ):
        pairs.append(
            DuplicatePair(
                split_a=split.name,
                path_a=str(split.paths[row]),
                split_b=split.name,
                path_b=str(split.paths[col]),
                distance=int(distances[row, col]),
            )
        )
    return int(np.count_nonzero(close)), pairs


def run_leak_check(
    dataset_root: Path,
    splits: Sequence[str],
    threshold: int,
    hash_size: int,
    max_pairs_recorded: int,
    check_within: bool,
) -> dict[str, Any]:
    """Hash every split and compare all split pairs. Returns the report payload."""
    images_root = dataset_root / "images"
    if not images_root.is_dir():
        raise FileNotFoundError(f"No images/ directory under {dataset_root}")

    hashed: dict[str, SplitHashes] = {}
    for split in splits:
        paths = discover_images(images_root / split)
        if not paths:
            LOGGER.warning("Split '%s' has no images -- skipping", split)
            continue
        LOGGER.info("Hashing split '%s' (%d images)...", split, len(paths))
        hashed[split] = hash_split(split, paths, hash_size=hash_size)

    if len(hashed) < 2:
        raise RuntimeError("Need at least two non-empty splits to check for leakage")

    comparisons: list[dict[str, Any]] = []
    all_pairs: list[DuplicatePair] = []
    total_close = 0

    names = list(hashed)
    for i, name_a in enumerate(names):
        for name_b in names[i + 1 :]:
            split_a, split_b = hashed[name_a], hashed[name_b]
            LOGGER.info(
                "Comparing '%s' (%d) x '%s' (%d)...",
                name_a,
                split_a.count,
                name_b,
                split_b.count,
            )
            pairs, histogram, minimum, close_count = find_cross_split_duplicates(
                split_a, split_b, threshold, max_pairs_recorded
            )
            total_close += close_count
            all_pairs.extend(pairs)
            comparisons.append(
                {
                    "split_a": name_a,
                    "split_b": name_b,
                    "images_a": split_a.count,
                    "images_b": split_b.count,
                    "pairs_compared": split_a.count * split_b.count,
                    "near_duplicate_pairs": close_count,
                    "min_hamming_distance": minimum,
                    "distance_histogram": histogram,
                }
            )
            LOGGER.info(
                "  -> %d pair(s) at Hamming <= %d | closest pair = %d",
                close_count,
                threshold,
                minimum,
            )

    within: dict[str, Any] = {}
    if check_within:
        for name, split in hashed.items():
            count, pairs = find_within_split_duplicates(split, threshold, max_pairs_recorded)
            within[name] = {"near_duplicate_pairs": count, "images": split.count}
            LOGGER.info("Within split '%s': %d near-duplicate pair(s)", name, count)

    verdict = "CLEAN" if total_close == 0 else "LEAK_DETECTED"

    return {
        "dataset_root": str(dataset_root),
        "method": "imagehash.phash",
        "hash_bits": hash_size * hash_size,
        "threshold_hamming": threshold,
        "splits": {name: split.count for name, split in hashed.items()},
        "unreadable_images": {
            name: split.unreadable for name, split in hashed.items() if split.unreadable
        },
        "cross_split_comparisons": comparisons,
        "within_split": within,
        "total_cross_split_near_duplicate_pairs": total_close,
        "example_pairs": [pair.to_dict() for pair in all_pairs],
        "verdict": verdict,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m ai.evaluation.leak_check",
        description=(
            "Check a YOLO dataset for train/test contamination using perceptual "
            "hashing and cross-split Hamming distance."
        ),
    )
    parser.add_argument(
        "--dataset",
        default="datasets/processed/yolo",
        help="Dataset root containing an images/ directory (default: %(default)s).",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        default=["train", "val", "test"],
        help="Splits to compare (default: train val test).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_THRESHOLD,
        help="Hamming distance counted as a near-duplicate (default: %(default)s).",
    )
    parser.add_argument(
        "--hash-size",
        type=int,
        default=8,
        help="phash side length; 8 gives a 64-bit hash (default: %(default)s).",
    )
    parser.add_argument(
        "--max-pairs-recorded",
        type=int,
        default=200,
        help="Cap on example pairs written to the report (default: %(default)s).",
    )
    parser.add_argument(
        "--no-within-split",
        action="store_true",
        help="Skip the within-split duplicate scan.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Where to write the JSON report (default: <dataset>/leak_check.json).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    args = build_parser().parse_args(argv)

    dataset_root = Path(args.dataset).expanduser().resolve()
    report = run_leak_check(
        dataset_root=dataset_root,
        splits=args.splits,
        threshold=args.threshold,
        hash_size=args.hash_size,
        max_pairs_recorded=args.max_pairs_recorded,
        check_within=not args.no_within_split,
    )

    destination = (
        Path(args.output).expanduser().resolve()
        if args.output
        else dataset_root / "leak_check.json"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    LOGGER.info("=" * 62)
    LOGGER.info("VERDICT: %s", report["verdict"])
    LOGGER.info(
        "Cross-split near-duplicate pairs (Hamming <= %d): %d",
        report["threshold_hamming"],
        report["total_cross_split_near_duplicate_pairs"],
    )
    if report["verdict"] != "CLEAN":
        LOGGER.error(
            "Test scores computed on this split are NOT trustworthy. Re-split "
            "the dataset grouping by source scene before quoting any accuracy."
        )
    LOGGER.info("Report written to %s", destination)
    LOGGER.info("=" * 62)
    return 0


if __name__ == "__main__":
    sys.exit(main())
