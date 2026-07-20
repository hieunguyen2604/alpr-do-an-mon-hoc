"""Find near-duplicate images with perceptual hashing, across and within datasets.

Usage examples::

    python scripts/dataset/deduplicate.py --input-dir datasets/raw
    python scripts/dataset/deduplicate.py --input-dir datasets/raw --threshold 3
    python scripts/dataset/deduplicate.py --input-dir datasets/raw --apply

Why this matters more than it looks
-----------------------------------
The public Vietnamese plate datasets are not independent. Roboflow projects fork
each other, Kaggle uploads repackage Roboflow exports, and the same dashcam
footage surfaces in several collections. If the same photo ends up in ``train``
under one dataset's name and in ``test`` under another's, the reported test
accuracy is measuring memorisation. That is why this script's headline number is
the count of **cross-dataset** duplicate groups, not the total: within-dataset
duplicates cost training time, cross-dataset duplicates invalidate results.

The output is consumed by ``split.py``, which keeps every member of a duplicate
group inside the same split. Even the duplicates this script does *not* delete
are therefore prevented from leaking.

How the search stays tractable
------------------------------
A brute-force comparison of 37,000 images is ~690 million pairs, which Python
will not finish in reasonable time. This uses **multi-index hashing**: a 64-bit
hash is cut into ``threshold + 1`` bands, and two hashes that differ in at most
``threshold`` bits must, by the pigeonhole principle, agree *exactly* on at least
one band. Grouping by band value therefore produces a candidate set guaranteed
to contain every true pair, which is then verified exactly. No true duplicate is
missed -- this is an exact algorithm, not an approximation.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Iterable, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    DatasetPaths,
    add_common_arguments,
    bootstrap_project_path,
    configure_logging,
    iter_image_files,
    resolve_dataset_paths,
    write_csv,
    write_json,
)

bootstrap_project_path()

from ai.data.schema import image_path_to_label_path  # noqa: E402

LOGGER = logging.getLogger("dataset.deduplicate")

DEFAULT_THRESHOLD: Final[int] = 5
HASH_SIZE: Final[int] = 8
HASH_BITS: Final[int] = HASH_SIZE * HASH_SIZE  # 64


@dataclass(slots=True)
class HashedImage:
    """One image reduced to a perceptual hash.

    Attributes:
        path: Absolute path to the image.
        dataset: Slug of the dataset it belongs to.
        phash: The perceptual hash as a 64-bit integer.
        pixels: Width times height, or ``0`` when the size could not be read.
            Used by the ``resolution`` keeper strategy: when the same photo
            appears in several datasets, the re-exported copies are usually
            downscaled, so the largest one is the least degraded original.
        boxes: Number of annotation boxes on the image, or ``0`` when no label
            was found. A duplicate whose label file is missing or empty is the
            worse copy regardless of its resolution.
    """

    path: Path
    dataset: str
    phash: int
    pixels: int = 0
    boxes: int = 0


@dataclass(slots=True)
class DuplicateGroup:
    """A set of images judged to be near-identical.

    Attributes:
        group_id: Stable 1-based identifier used across all reports.
        members: The images in the group, in the order they were hashed.
        keeper: The member chosen to survive ``--apply``.
    """

    group_id: int
    members: list[HashedImage] = field(default_factory=list)
    keeper: HashedImage | None = None

    @property
    def datasets(self) -> list[str]:
        """Return the distinct dataset slugs represented, sorted."""
        return sorted({member.dataset for member in self.members})

    @property
    def is_cross_dataset(self) -> bool:
        """Return ``True`` if the group spans more than one dataset.

        These are the dangerous ones: they are how an image reaches two splits.
        """
        return len(self.datasets) > 1

    @property
    def removable(self) -> list[HashedImage]:
        """Return the members that ``--apply`` would delete."""
        return [member for member in self.members if member is not self.keeper]


class UnionFind:
    """Disjoint-set forest over integer indices, with path compression.

    Duplicate detection produces *pairs*, but the useful unit is a *group*: if
    A matches B and B matches C, all three must stay together even when A and C
    are further apart than the threshold. Transitive closure via union-find is
    what turns pairs into groups.
    """

    __slots__ = ("_parent", "_rank")

    def __init__(self, size: int) -> None:
        """Create ``size`` singleton sets.

        Args:
            size: Number of elements.
        """
        self._parent = list(range(size))
        self._rank = [0] * size

    def find(self, item: int) -> int:
        """Return the representative of ``item``'s set.

        Args:
            item: Element index.

        Returns:
            The root index.
        """
        root = item
        while self._parent[root] != root:
            root = self._parent[root]
        while self._parent[item] != root:
            self._parent[item], item = root, self._parent[item]
        return root

    def union(self, left: int, right: int) -> None:
        """Merge the sets containing two elements.

        Args:
            left: First element index.
            right: Second element index.
        """
        left_root, right_root = self.find(left), self.find(right)
        if left_root == right_root:
            return
        if self._rank[left_root] < self._rank[right_root]:
            left_root, right_root = right_root, left_root
        self._parent[right_root] = left_root
        if self._rank[left_root] == self._rank[right_root]:
            self._rank[left_root] += 1


# --------------------------------------------------------------------------
# Hashing
# --------------------------------------------------------------------------


def dataset_of(image_path: Path, root: Path, mode: str) -> str:
    """Work out which dataset an image belongs to.

    Args:
        image_path: The image.
        root: Directory the scan started from.
        mode: ``"top-dir"`` uses the first path component below ``root``, which
            matches the ``datasets/raw/<name>/`` layout. ``"filename-prefix"``
            uses the part of the file stem before the last underscore, which
            matches the ``<dataset>_<index>`` names that ``merge.py`` produces.

    Returns:
        The dataset slug, or ``"unknown"`` when it cannot be determined.

    Raises:
        ValueError: If ``mode`` is not recognised.
    """
    if mode == "top-dir":
        try:
            relative = image_path.relative_to(root)
        except ValueError:
            return "unknown"
        return relative.parts[0] if len(relative.parts) > 1 else "unknown"

    if mode == "filename-prefix":
        stem = image_path.stem
        return stem.rsplit("_", 1)[0] if "_" in stem else "unknown"

    raise ValueError(f"Unknown dataset attribution mode {mode!r}")


def count_label_boxes(image_path: Path) -> int:
    """Count annotation lines belonging to an image.

    Args:
        image_path: The image whose label file should be located.

    Returns:
        The number of non-empty label lines, or ``0`` when the label file is
        absent or unreadable. Absence is deliberately not an error here: this
        figure only ranks duplicate copies against each other.
    """
    try:
        label_path = image_path_to_label_path(image_path)
    except Exception:  # noqa: BLE001 - layout guessing must never break a scan
        return 0
    if not label_path.is_file():
        return 0
    try:
        text = label_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return 0
    return sum(1 for line in text.splitlines() if line.strip())


def compute_phash_and_size(image_path: Path) -> tuple[int, int] | None:
    """Compute an image's perceptual hash and its pixel count in one open.

    ``phash`` (DCT-based) is used rather than ``ahash`` or ``dhash`` because it
    is the one that stays stable under the transformations that actually create
    duplicates here: JPEG re-compression, resizing, and mild brightness shifts
    from a dataset being re-exported by a different tool.

    Args:
        image_path: The image to read.

    Returns:
        ``(phash, pixels)``, or ``None`` if the file cannot be read.
        Unreadable files are logged and skipped rather than raising -- one
        corrupt JPEG must not stop a 37,000 image scan.
    """
    try:
        import imagehash
        from PIL import Image

        with Image.open(image_path) as image:
            width, height = image.size
            # Convert before hashing: phash on a palette or CMYK image goes
            # through a different code path and produces incomparable values.
            hashed = imagehash.phash(image.convert("RGB"), hash_size=HASH_SIZE)
    except Exception as exc:  # noqa: BLE001 - any decode failure means "skip"
        LOGGER.warning("Cannot hash %s: %s", image_path, exc)
        return None

    value = 0
    for bit in hashed.hash.flatten():
        value = (value << 1) | int(bool(bit))
    return value, width * height


def hash_directory(
    root: Path, *, attribution: str, workers: int = 1
) -> tuple[list[HashedImage], list[Path]]:
    """Hash every image under a directory tree.

    Args:
        root: Directory to scan recursively.
        attribution: Dataset attribution mode, see :func:`dataset_of`.
        workers: Thread count. Decoding releases the GIL, so threads do help;
            values above the core count rarely do.

    Returns:
        ``(hashed, failures)`` -- the successfully hashed images and the paths
        that could not be read.

    Raises:
        FileNotFoundError: If ``root`` does not exist.
    """
    if not root.is_dir():
        raise FileNotFoundError(f"Input directory does not exist: {root}")

    paths = list(iter_image_files(root))
    LOGGER.info("Found %d images under %s", len(paths), root)
    if not paths:
        return [], []

    hashed: list[HashedImage] = []
    failures: list[Path] = []

    def _consume(path: Path, value: tuple[int, int] | None) -> None:
        if value is None:
            failures.append(path)
        else:
            phash, pixels = value
            hashed.append(
                HashedImage(
                    path=path,
                    dataset=dataset_of(path, root, attribution),
                    phash=phash,
                    pixels=pixels,
                    boxes=count_label_boxes(path),
                )
            )

    bar = _progress_bar(len(paths), "Hashing images")
    try:
        if workers > 1:
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=workers) as pool:
                for path, value in zip(paths, pool.map(compute_phash_and_size, paths)):
                    _consume(path, value)
                    if bar is not None:
                        bar.update(1)
        else:
            for path in paths:
                _consume(path, compute_phash_and_size(path))
                if bar is not None:
                    bar.update(1)
    finally:
        if bar is not None:
            bar.close()

    # Sorting makes group membership and keeper selection reproducible across
    # runs, which matters because split.py depends on these group ids.
    hashed.sort(key=lambda item: str(item.path))
    if failures:
        LOGGER.warning("%d images could not be hashed and are excluded", len(failures))
    return hashed, failures


def _progress_bar(total: int, description: str) -> Any | None:
    """Return a ``tqdm`` bar, or ``None`` when unavailable or unhelpful.

    Args:
        total: Expected iteration count.
        description: Bar label.

    Returns:
        A ``tqdm`` instance or ``None``.
    """
    if total < 200:
        return None
    try:
        from tqdm import tqdm
    except ImportError:
        return None
    return tqdm(total=total, desc=description, unit="img")


# --------------------------------------------------------------------------
# Duplicate search
# --------------------------------------------------------------------------


def hamming_distance(left: int, right: int) -> int:
    """Return the number of differing bits between two hashes.

    Args:
        left: First hash.
        right: Second hash.

    Returns:
        Population count of the XOR, in ``[0, 64]``.
    """
    return (left ^ right).bit_count()


def find_candidate_pairs(hashes: Sequence[int], threshold: int) -> set[tuple[int, int]]:
    """Return index pairs that might be within ``threshold`` bits of each other.

    Implements the banding step of multi-index hashing. The 64-bit hash is split
    into ``threshold + 1`` bands; any two hashes differing in at most
    ``threshold`` bits must agree exactly on at least one band, because
    ``threshold`` differing bits cannot touch ``threshold + 1`` disjoint bands.
    The returned set is therefore a superset of the true pairs -- exact, not
    probabilistic.

    Args:
        hashes: The hashes, indexed positionally.
        threshold: Maximum Hamming distance considered a duplicate.

    Returns:
        Candidate index pairs, each with the smaller index first.

    Raises:
        ValueError: If ``threshold`` is negative or not below :data:`HASH_BITS`.
    """
    if threshold < 0:
        raise ValueError(f"Threshold must be non-negative, got {threshold}")
    if threshold >= HASH_BITS:
        raise ValueError(
            f"Threshold {threshold} is >= the {HASH_BITS}-bit hash width; every "
            "image would match every other image."
        )

    band_count = threshold + 1
    band_width = HASH_BITS // band_count
    remainder = HASH_BITS % band_count

    candidates: set[tuple[int, int]] = set()
    offset = 0
    for band in range(band_count):
        # Spread the remainder bits over the first few bands so no band is empty.
        width = band_width + (1 if band < remainder else 0)
        mask = ((1 << width) - 1) << offset
        offset += width

        buckets: dict[int, list[int]] = defaultdict(list)
        for index, value in enumerate(hashes):
            buckets[value & mask].append(index)

        for bucket in buckets.values():
            if len(bucket) < 2:
                continue
            # A bucket holding a large share of the corpus means the band is not
            # discriminating (e.g. thousands of near-blank images). Comparing it
            # fully is still correct, just slow; warn rather than skip, because
            # skipping would silently miss duplicates.
            if len(bucket) > 5000:
                LOGGER.debug(
                    "Band %d has a bucket of %d images; comparison will be slow",
                    band,
                    len(bucket),
                )
            for position, left in enumerate(bucket):
                for right in bucket[position + 1 :]:
                    candidates.add((left, right) if left < right else (right, left))

    LOGGER.info("Multi-index hashing produced %d candidate pairs", len(candidates))
    return candidates


VECTORISED_THRESHOLD: Final[int] = 8
"""Threshold at or above which :func:`find_pairs_vectorised` replaces banding.

Multi-index hashing degrades badly as the threshold grows: it needs
``threshold + 1`` bands, so each band shrinks to ~5 bits, holds only 32 distinct
values, and every bucket becomes a large fraction of the corpus. At threshold 12
over 15,000 images the candidate *set* alone reaches tens of millions of Python
tuples -- gigabytes of memory to enumerate a superset of an answer that a
vectorised full scan computes exactly in seconds.
"""


def find_pairs_vectorised(
    hashes: Sequence[int], threshold: int, *, chunk: int = 2048
) -> list[tuple[int, int, int]]:
    """Return every pair within ``threshold`` bits, by exhaustive numpy scan.

    The 64-bit hashes are unpacked to bytes, and each chunk of rows is XORed
    against the whole corpus at once. Population count comes from a 256-entry
    lookup table indexed by the XOR bytes, which is a plain array gather -- no
    Python-level loop runs over pairs. For 15,000 images this is 114 million
    pairs evaluated in a few seconds, versus minutes and gigabytes for the
    banding path at a high threshold.

    This is exhaustive, so unlike banding it needs no pigeonhole argument to
    justify completeness: every pair is actually compared.

    Args:
        hashes: The hashes, indexed positionally.
        threshold: Maximum Hamming distance treated as duplicate.
        chunk: Rows compared per iteration. Controls peak memory, which is
            roughly ``chunk * len(hashes)`` bytes.

    Returns:
        ``(left, right, distance)`` triples with ``left < right``, sorted.

    Raises:
        ValueError: If ``threshold`` is negative.
        ImportError: If numpy is unavailable.
    """
    if threshold < 0:
        raise ValueError(f"Threshold must be non-negative, got {threshold}")

    import numpy as np

    count = len(hashes)
    if count < 2:
        return []

    # Big-endian byte view: bit order does not matter, only that it is consistent,
    # because Hamming distance is invariant under any fixed permutation of bits.
    matrix = np.array([list(int(value).to_bytes(8, "big")) for value in hashes], dtype=np.uint8)
    popcount = (
        np.unpackbits(np.arange(256, dtype=np.uint8)[:, None], axis=1).sum(axis=1).astype(np.uint8)
    )

    pairs: list[tuple[int, int, int]] = []
    for start in range(0, count, chunk):
        stop = min(start + chunk, count)
        block = np.bitwise_xor(matrix[start:stop, None, :], matrix[None, :, :])
        distances = popcount[block].sum(axis=2)

        # Keep the upper triangle only, so each pair is emitted exactly once.
        rows, cols = np.nonzero(distances <= threshold)
        absolute_rows = rows + start
        keep = absolute_rows < cols
        for left, right in zip(absolute_rows[keep], cols[keep]):
            pairs.append((int(left), int(right), int(distances[left - start, right])))

    pairs.sort()
    LOGGER.info("Vectorised exact scan found %d pairs within distance %d", len(pairs), threshold)
    return pairs


KEEP_STRATEGIES: Final[tuple[str, ...]] = ("priority", "quality")
"""Available keeper-selection strategies, see :func:`make_keeper_key`."""


def make_keeper_key(strategy: str, priority_rank: dict[str, int]) -> Any:
    """Build the sort key that decides which copy of a duplicate survives.

    Args:
        strategy: ``"priority"`` ranks by dataset preference alone, the
            historical behaviour. ``"quality"`` ranks by annotation richness
            first, then pixel count, and only then falls back to dataset
            preference -- appropriate when the same photo has been re-exported
            between datasets at different resolutions, because the re-exports
            are downscaled and sometimes lose boxes.
        priority_rank: Dataset slug to rank, lower being preferred.

    Returns:
        A callable suitable for ``min(..., key=...)``. Every key ends with the
        path string so the choice is deterministic across runs.

    Raises:
        ValueError: If ``strategy`` is not recognised.
    """
    unknown_rank = len(priority_rank)

    if strategy == "priority":
        return lambda member: (
            priority_rank.get(member.dataset, unknown_rank),
            str(member.path),
        )

    if strategy == "quality":
        # Negated so that "more boxes" and "more pixels" sort first under min().
        return lambda member: (
            -member.boxes,
            -member.pixels,
            priority_rank.get(member.dataset, unknown_rank),
            str(member.path),
        )

    raise ValueError(
        f"Unknown keeper strategy {strategy!r}; expected one of {', '.join(KEEP_STRATEGIES)}"
    )


def find_duplicate_groups(
    images: Sequence[HashedImage],
    threshold: int,
    *,
    priority: Sequence[str] = (),
    keep_strategy: str = "priority",
    search: str = "auto",
) -> tuple[list[DuplicateGroup], list[dict[str, Any]]]:
    """Group near-duplicate images and pick a survivor for each group.

    Grouping is transitive: pairs are fed through a union-find forest, so if
    A matches B and B matches C then A, B and C form one group even when A and C
    are further apart than the threshold. Splitting per-pair instead of per-group
    would leave chains of near-duplicates straddling two splits.

    Args:
        images: The hashed corpus.
        threshold: Maximum Hamming distance treated as duplicate.
        priority: Dataset slugs in descending order of preference. When a group
            spans several datasets, the member from the earliest listed dataset
            is kept. This is how the primary dataset (VNLP, the only one with
            character labels) survives a collision with a detection-only
            dataset -- deleting the labelled copy would throw away the
            transcription.
        keep_strategy: How to rank the members of a group, see
            :func:`make_keeper_key`.
        search: ``"banding"`` forces multi-index hashing, ``"vectorised"``
            forces the exhaustive numpy scan, ``"auto"`` picks banding below
            :data:`VECTORISED_THRESHOLD` and the vectorised scan at or above it.
            Both are exact; they differ only in cost.

    Returns:
        ``(groups, pair_rows)``: the duplicate groups with two or more members,
        and one report row per confirmed duplicate pair.
    """
    if not images:
        return [], []

    hashes = [image.phash for image in images]

    use_vectorised = search == "vectorised" or (
        search == "auto" and threshold >= VECTORISED_THRESHOLD
    )
    confirmed: list[tuple[int, int, int]]
    if use_vectorised:
        try:
            confirmed = find_pairs_vectorised(hashes, threshold)
        except ImportError:
            LOGGER.warning(
                "numpy is unavailable; falling back to multi-index hashing, which "
                "is slow and memory-hungry at threshold %d.",
                threshold,
            )
            use_vectorised = False
    if not use_vectorised:
        candidates = find_candidate_pairs(hashes, threshold)
        confirmed = []
        for left, right in sorted(candidates):
            distance = hamming_distance(hashes[left], hashes[right])
            if distance <= threshold:
                confirmed.append((left, right, distance))

    union = UnionFind(len(images))
    pair_rows: list[dict[str, Any]] = []

    for left, right, distance in confirmed:
        union.union(left, right)
        first, second = images[left], images[right]
        pair_rows.append(
            {
                "image_a": first.path,
                "dataset_a": first.dataset,
                "image_b": second.path,
                "dataset_b": second.dataset,
                "hamming_distance": distance,
                "is_exact_match": distance == 0,
                "is_cross_dataset": first.dataset != second.dataset,
            }
        )

    members_by_root: dict[int, list[int]] = defaultdict(list)
    for index in range(len(images)):
        members_by_root[union.find(index)].append(index)

    priority_rank = {name: rank for rank, name in enumerate(priority)}
    keeper_key = make_keeper_key(keep_strategy, priority_rank)

    groups: list[DuplicateGroup] = []
    for root in sorted(members_by_root):
        indices = members_by_root[root]
        if len(indices) < 2:
            continue
        group = DuplicateGroup(group_id=len(groups) + 1, members=[images[i] for i in indices])
        group.keeper = min(group.members, key=keeper_key)
        groups.append(group)

    LOGGER.info(
        "Confirmed %d duplicate pairs forming %d groups",
        len(pair_rows),
        len(groups),
    )
    return groups, pair_rows


# --------------------------------------------------------------------------
# Reporting and application
# --------------------------------------------------------------------------


def summarise(
    images: Sequence[HashedImage],
    groups: Sequence[DuplicateGroup],
    pair_rows: Sequence[dict[str, Any]],
    failures: Sequence[Path],
    threshold: int,
) -> dict[str, Any]:
    """Build the JSON summary of a deduplication run.

    Args:
        images: Every hashed image.
        groups: The duplicate groups found.
        pair_rows: The confirmed duplicate pairs.
        failures: Images that could not be hashed.
        threshold: The distance threshold used.

    Returns:
        A JSON-serialisable summary. The cross-dataset figures are listed first
        because they are the ones that decide whether the split is trustworthy.
    """
    cross_groups = [group for group in groups if group.is_cross_dataset]
    per_dataset_total: dict[str, int] = defaultdict(int)
    for image in images:
        per_dataset_total[image.dataset] += 1

    per_dataset_duplicates: dict[str, int] = defaultdict(int)
    for group in groups:
        for member in group.removable:
            per_dataset_duplicates[member.dataset] += 1

    cross_pairs: dict[str, int] = defaultdict(int)
    for row in pair_rows:
        if row["is_cross_dataset"]:
            key = " <-> ".join(sorted((str(row["dataset_a"]), str(row["dataset_b"]))))
            cross_pairs[key] += 1

    removable = sum(len(group.removable) for group in groups)
    return {
        "threshold": threshold,
        "hash": f"phash-{HASH_BITS}bit",
        "images_scanned": len(images),
        "images_unreadable": len(failures),
        "duplicate_pairs": len(pair_rows),
        "duplicate_groups": len(groups),
        "cross_dataset_groups": len(cross_groups),
        "cross_dataset_pairs_by_dataset": dict(sorted(cross_pairs.items())),
        "removable_images": removable,
        "unique_images_after_dedup": len(images) - removable,
        "images_per_dataset": dict(sorted(per_dataset_total.items())),
        "removable_per_dataset": dict(sorted(per_dataset_duplicates.items())),
        "unreadable_images": [str(path) for path in failures[:100]],
        "leakage_warning": (
            "Cross-dataset duplicate groups place the same photograph under two "
            "dataset names. split.py must keep every group member in one split, "
            "otherwise test accuracy measures memorisation."
        ),
    }


def group_rows(groups: Iterable[DuplicateGroup]) -> list[dict[str, Any]]:
    """Flatten duplicate groups into CSV rows, one per member.

    Args:
        groups: The groups to flatten.

    Returns:
        Report rows carrying the group id, the member, and whether it survives.
    """
    rows: list[dict[str, Any]] = []
    for group in groups:
        for member in group.members:
            rows.append(
                {
                    "group_id": group.group_id,
                    "image": member.path,
                    "dataset": member.dataset,
                    "group_size": len(group.members),
                    "datasets_in_group": "|".join(group.datasets),
                    "is_cross_dataset": group.is_cross_dataset,
                    "action": "keep" if member is group.keeper else "remove",
                }
            )
    return rows


def build_group_index(groups: Iterable[DuplicateGroup]) -> dict[str, int]:
    """Map each duplicated image path to its group id.

    This file is the contract with ``split.py``: it is what lets the splitter
    treat a duplicate group as one indivisible unit.

    Args:
        groups: The duplicate groups.

    Returns:
        A mapping from image path string to group id.
    """
    index: dict[str, int] = {}
    for group in groups:
        for member in group.members:
            index[str(member.path)] = group.group_id
    return index


def apply_removals(groups: Sequence[DuplicateGroup], *, remove_labels: bool = True) -> int:
    """Delete the redundant members of every duplicate group.

    Args:
        groups: The groups to prune.
        remove_labels: Also delete each removed image's YOLO label file. Leaving
            an orphan label behind would make the next verification run report
            phantom errors.

    Returns:
        The number of image files actually deleted.
    """
    deleted = 0
    for group in groups:
        for member in group.removable:
            try:
                member.path.unlink(missing_ok=True)
                deleted += 1
            except OSError as exc:
                LOGGER.error("Could not delete %s: %s", member.path, exc)
                continue
            if remove_labels:
                label_path = image_path_to_label_path(member.path)
                try:
                    label_path.unlink(missing_ok=True)
                except OSError as exc:
                    LOGGER.warning("Could not delete label %s: %s", label_path, exc)
    LOGGER.info("Deleted %d duplicate images", deleted)
    return deleted


def log_headline(summary: dict[str, Any]) -> None:
    """Print the findings a human needs to see, whatever the log level.

    Args:
        summary: The summary produced by :func:`summarise`.
    """
    LOGGER.info("=" * 70)
    LOGGER.info("Images scanned            : %d", summary["images_scanned"])
    LOGGER.info("Duplicate groups          : %d", summary["duplicate_groups"])
    LOGGER.info("  of which CROSS-DATASET  : %d", summary["cross_dataset_groups"])
    LOGGER.info("Removable duplicates      : %d", summary["removable_images"])
    LOGGER.info("Unique images after dedup : %d", summary["unique_images_after_dedup"])
    if summary["cross_dataset_pairs_by_dataset"]:
        LOGGER.warning("Cross-dataset overlap detected:")
        for pair, count in summary["cross_dataset_pairs_by_dataset"].items():
            LOGGER.warning("    %-40s %d pair(s)", pair, count)
        LOGGER.warning(
            "These are the train/test leakage risk. split.py reads "
            "duplicate_groups.json to keep each group in a single split."
        )
    LOGGER.info("=" * 70)


def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line parser.

    Returns:
        The configured parser.
    """
    parser = argparse.ArgumentParser(
        prog="deduplicate.py",
        description=(
            "Detect near-duplicate images with perceptual hashing and report "
            "cross-dataset overlap, the main source of train/test leakage."
        ),
        epilog=(
            "Examples:\n"
            "  python deduplicate.py --input-dir datasets/raw\n"
            "  python deduplicate.py --input-dir datasets/raw --threshold 3 --workers 8\n"
            "  python deduplicate.py --input-dir datasets/raw --apply\n\n"
            "Without --apply nothing is deleted; the run only writes reports."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="Directory to scan recursively (default: <datasets>/raw).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_THRESHOLD,
        metavar="N",
        help=(
            "Maximum Hamming distance between 64-bit perceptual hashes for two "
            "images to count as duplicates. 0 means bit-identical hashes; higher "
            "values catch more re-encodings but risk merging genuinely different "
            "photos of the same scene (default: %(default)s)."
        ),
    )
    parser.add_argument(
        "--dataset-from",
        choices=["top-dir", "filename-prefix"],
        default="top-dir",
        help=(
            "How to attribute an image to a dataset. 'top-dir' suits "
            "datasets/raw/<name>/...; 'filename-prefix' suits the merged "
            "<dataset>_<index> naming (default: %(default)s)."
        ),
    )
    parser.add_argument(
        "--priority",
        nargs="+",
        default=["vnlp"],
        metavar="DATASET",
        help=(
            "Dataset preference order when choosing which copy to keep. Earlier "
            "wins. Keep the dataset that carries character labels first "
            "(default: %(default)s)."
        ),
    )
    parser.add_argument(
        "--keep-strategy",
        choices=list(KEEP_STRATEGIES),
        default="priority",
        help=(
            "Which copy of a duplicate group survives. 'priority' uses the "
            "--priority dataset order only. 'quality' prefers the copy with "
            "the most annotation boxes, then the highest resolution, and uses "
            "--priority only to break ties -- the right choice when datasets "
            "have re-exported each other's photos at reduced size "
            "(default: %(default)s)."
        ),
    )
    parser.add_argument(
        "--search",
        choices=["auto", "banding", "vectorised"],
        default="auto",
        help=(
            "Pair-search algorithm. Both are exact. 'banding' is multi-index "
            "hashing, fast at low thresholds but explosive above ~8 where the "
            "bands stop discriminating. 'vectorised' is an exhaustive numpy "
            "scan, the right choice at high thresholds. 'auto' switches to "
            f"vectorised at threshold >= {VECTORISED_THRESHOLD} "
            "(default: %(default)s)."
        ),
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        metavar="N",
        help="Threads used for hashing (default: %(default)s).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Actually delete the redundant copies and their label files. "
            "Without this flag the script only reports."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="Where to write the reports (default: <datasets>/reports).",
    )
    return add_common_arguments(parser)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point.

    Args:
        argv: Argument list, defaulting to ``sys.argv[1:]``.

    Returns:
        ``0`` on success, ``1`` if the input directory is missing or the
        threshold is invalid.
    """
    args = build_parser().parse_args(argv)
    configure_logging(args.log_level)

    paths: DatasetPaths = resolve_dataset_paths(args.datasets_dir)
    input_dir = (args.input_dir or paths.raw).expanduser().resolve()
    output_dir = (args.output_dir or paths.reports).expanduser().resolve()

    try:
        images, failures = hash_directory(
            input_dir, attribution=args.dataset_from, workers=max(1, args.workers)
        )
    except FileNotFoundError as exc:
        LOGGER.error("%s", exc)
        LOGGER.error("Run download.py first, or pass --input-dir.")
        return 1

    if not images:
        LOGGER.warning("No readable images found under %s; nothing to do.", input_dir)
        return 0

    try:
        groups, pair_rows = find_duplicate_groups(
            images,
            args.threshold,
            priority=tuple(args.priority),
            keep_strategy=args.keep_strategy,
            search=args.search,
        )
    except ValueError as exc:
        LOGGER.error("%s", exc)
        return 1

    summary = summarise(images, groups, pair_rows, failures, args.threshold)
    summary["input_dir"] = str(input_dir)
    summary["applied"] = bool(args.apply)
    summary["search"] = args.search

    write_csv(
        output_dir / "duplicate_pairs.csv",
        pair_rows,
        fieldnames=[
            "image_a",
            "dataset_a",
            "image_b",
            "dataset_b",
            "hamming_distance",
            "is_exact_match",
            "is_cross_dataset",
        ],
    )
    write_csv(
        output_dir / "duplicate_groups.csv",
        group_rows(groups),
        fieldnames=[
            "group_id",
            "image",
            "dataset",
            "group_size",
            "datasets_in_group",
            "is_cross_dataset",
            "action",
        ],
    )
    write_json(
        output_dir / "duplicate_groups.json",
        {
            "threshold": args.threshold,
            "input_dir": str(input_dir),
            "groups": build_group_index(groups),
        },
    )

    if args.apply:
        summary["deleted_images"] = apply_removals(groups)
    else:
        LOGGER.info(
            "Report-only run. %d images would be removed; re-run with --apply to delete them.",
            summary["removable_images"],
        )

    write_json(output_dir / "deduplication_report.json", summary)
    log_headline(summary)
    LOGGER.info("Reports written to %s", output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
