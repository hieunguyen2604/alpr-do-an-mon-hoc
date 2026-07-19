"""Shared plumbing for the Phase 2 dataset scripts.

Everything in here is infrastructure that every CLI in ``scripts/dataset/``
needs and none of them should re-implement: locating the project root, resolving
the dataset directories, configuring logging, listing images, and reading image
dimensions cheaply.

Path policy
-----------
No path is ever hard-coded. Directories resolve in this order, first hit wins:

1. an explicit command-line argument (``--datasets-dir`` and friends);
2. the matching environment variable (``DATN_DATASETS_DIR``);
3. a default derived from the project root, which is itself derived from this
   file's own location.

That last step is what makes the scripts work when invoked from any working
directory, which matters because they get called from ``run_pipeline.py``, from
a shell, and from a notebook.

Import bootstrap
----------------
``scripts/dataset`` is not an installed package and the repository has no
``setup.py``. Importing :mod:`ai.data.schema` therefore requires the project
root on ``sys.path``; :func:`bootstrap_project_path` does that, and every script
calls it before importing anything from ``ai``.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Iterable, Iterator, Mapping, Sequence

__all__ = [
    "IMAGE_EXTENSIONS",
    "PROJECT_ROOT",
    "DatasetPaths",
    "add_common_arguments",
    "bootstrap_project_path",
    "configure_logging",
    "iter_image_files",
    "read_image_size",
    "read_image_sizes",
    "resolve_dataset_paths",
    "summarise_distribution",
    "write_csv",
    "write_json",
]

LOGGER = logging.getLogger(__name__)

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
"""Repository root, derived from this file: ``<root>/scripts/dataset/_common.py``."""

IMAGE_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
)
"""Lowercase suffixes treated as images throughout the pipeline."""

_ENV_DATASETS_DIR: Final[str] = "DATN_DATASETS_DIR"


def _shield_stdlib_statistics() -> None:
    """Make ``import statistics`` resolve to the standard library, not our script.

    ``scripts/dataset/statistics.py`` is one of this phase's required
    deliverables, and Python puts a script's own directory at the front of
    ``sys.path``. Every ``import statistics`` in the process -- including one
    made by a third-party library deep in the dependency tree -- therefore
    resolves to that script and fails with a baffling ``AttributeError: module
    'statistics' has no attribute 'median'``.

    No currently installed dependency imports it, so nothing is broken today.
    But this is a trap armed for whoever adds the next package, and the failure
    would appear far from its cause. Loading the real module by its absolute
    stdlib path and registering it first disarms it: the shadowing script can
    still be loaded deliberately, by path, under the name
    ``dataset_statistics``.
    """
    import importlib.util
    import sysconfig

    existing = sys.modules.get("statistics")
    if existing is not None:
        origin = getattr(existing, "__file__", "") or ""
        # Already the genuine stdlib module: nothing to do.
        if Path(origin).parent != Path(__file__).resolve().parent:
            return

    stdlib_statistics = Path(sysconfig.get_paths()["stdlib"]) / "statistics.py"
    if not stdlib_statistics.is_file():  # pragma: no cover - unusual install
        LOGGER.debug("Cannot locate the stdlib statistics module; skipping shield")
        return

    spec = importlib.util.spec_from_file_location("statistics", stdlib_statistics)
    if spec is None or spec.loader is None:  # pragma: no cover
        return

    module = importlib.util.module_from_spec(spec)
    sys.modules["statistics"] = module
    spec.loader.exec_module(module)


def bootstrap_project_path() -> Path:
    """Put the project root on ``sys.path`` so ``import ai.data`` works.

    Also disarms the ``statistics.py`` shadowing hazard described in
    :func:`_shield_stdlib_statistics`.

    Idempotent -- safe to call from every script even when several of them are
    imported into one process by ``run_pipeline.py``.

    Returns:
        The project root that was added.
    """
    _shield_stdlib_statistics()

    root = str(PROJECT_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    return PROJECT_ROOT


@dataclass(frozen=True, slots=True)
class DatasetPaths:
    """The standard dataset directory layout.

    Mirrors the tree declared in ``CLAUDE.md``. Instances are produced by
    :func:`resolve_dataset_paths`, never constructed by hand in a script, so
    that every CLI agrees on where things live.

    Attributes:
        root: The ``datasets/`` directory.
        raw: Untouched downloads, one subdirectory per source dataset.
        processed: The merged, renamed, split dataset fed to the trainer.
        annotations: Auxiliary annotation files that are not YOLO labels.
        statistics: Charts and ``statistics.json``.
        reports: Machine-readable output of the verification and dedup stages.
    """

    root: Path
    raw: Path
    processed: Path
    annotations: Path
    statistics: Path
    reports: Path

    def ensure(self) -> None:
        """Create every directory in the layout if it does not exist.

        Raises:
            OSError: If a directory cannot be created.
        """
        for path in (
            self.root,
            self.raw,
            self.processed,
            self.annotations,
            self.statistics,
            self.reports,
        ):
            path.mkdir(parents=True, exist_ok=True)


def resolve_dataset_paths(datasets_dir: Path | str | None = None) -> DatasetPaths:
    """Work out where the dataset directories live.

    Args:
        datasets_dir: Explicit root, usually straight from ``--datasets-dir``.
            When ``None``, the ``DATN_DATASETS_DIR`` environment variable is
            consulted, then ``<project root>/datasets``.

    Returns:
        The resolved layout. Directories are *not* created; call
        :meth:`DatasetPaths.ensure` for that.
    """
    if datasets_dir is not None:
        root = Path(datasets_dir)
    else:
        env_value = os.environ.get(_ENV_DATASETS_DIR)
        root = Path(env_value) if env_value else PROJECT_ROOT / "datasets"

    root = root.expanduser().resolve()
    return DatasetPaths(
        root=root,
        raw=root / "raw",
        processed=root / "processed",
        annotations=root / "annotations",
        statistics=root / "statistics",
        reports=root / "reports",
    )


def configure_logging(level: str = "INFO", *, log_file: Path | None = None) -> None:
    """Set up root logging for a CLI run.

    Args:
        level: A :mod:`logging` level name, case-insensitive.
        log_file: Optional file to duplicate the log into. Its parent directory
            is created as needed.

    Raises:
        ValueError: If ``level`` is not a recognised level name.
    """
    numeric_level = logging.getLevelName(level.upper())
    if not isinstance(numeric_level, int):
        raise ValueError(
            f"Unknown log level {level!r}; expected one of "
            "DEBUG, INFO, WARNING, ERROR, CRITICAL"
        )

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
        force=True,
    )


def add_common_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Attach the flags every dataset CLI shares.

    Args:
        parser: The parser to extend.

    Returns:
        The same parser, for chaining.
    """
    parser.add_argument(
        "--datasets-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "Root of the datasets tree. Defaults to the DATN_DATASETS_DIR "
            "environment variable, or <project root>/datasets."
        ),
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Console verbosity (default: %(default)s).",
    )
    return parser


def iter_image_files(
    directory: Path,
    *,
    extensions: Iterable[str] | None = None,
    recursive: bool = True,
) -> Iterator[Path]:
    """Yield image files under a directory in a stable, sorted order.

    Sorted order is not cosmetic: it makes the merge stage's ``<dataset>_<index>``
    naming reproducible across runs and across machines, which in turn makes the
    deduplication and split reports comparable.

    Args:
        directory: Where to look.
        extensions: Lowercase suffixes to accept. Defaults to
            :data:`IMAGE_EXTENSIONS`.
        recursive: Walk subdirectories as well.

    Yields:
        Paths to image files. Nothing is yielded if ``directory`` is missing --
        an absent input directory is reported by the caller, which has the
        context to explain it.
    """
    if not directory.is_dir():
        LOGGER.debug("Not a directory, nothing to iterate: %s", directory)
        return

    allowed = frozenset(extensions) if extensions is not None else IMAGE_EXTENSIONS
    pattern = "**/*" if recursive else "*"
    for path in sorted(directory.glob(pattern)):
        if path.is_file() and path.suffix.lower() in allowed:
            yield path


def read_image_size(image_path: Path) -> tuple[int, int] | None:
    """Read an image's pixel dimensions without decoding the whole file.

    Uses Pillow's lazy header parsing, which is roughly two orders of magnitude
    faster than a full ``cv2.imread`` and is all that most stages need. Note
    that a file whose *header* is intact but whose pixel data is truncated will
    pass here and still fail to decode; ``verify_annotations.py`` deliberately
    does a real decode for exactly that reason.

    Args:
        image_path: File to inspect.

    Returns:
        ``(width, height)``, or ``None`` if the file is missing, is not an
        image, or has an unreadable header. Failures are logged at DEBUG and
        never raised -- a corrupt file in a 37k-image download must not abort
        the run.
    """
    try:
        from PIL import Image  # Imported lazily to keep --help fast.

        with Image.open(image_path) as image:
            width, height = image.size
    except Exception as exc:  # noqa: BLE001 - any decoder failure is "unreadable"
        LOGGER.debug("Cannot read image size for %s: %s", image_path, exc)
        return None

    if width <= 0 or height <= 0:
        LOGGER.debug("Image %s reports a non-positive size %dx%d", image_path, width, height)
        return None
    return width, height


def read_image_sizes(
    image_paths: Iterable[Path], *, show_progress: bool = True
) -> tuple[dict[Path, tuple[int, int]], list[Path]]:
    """Read dimensions for many images, separating the failures.

    Args:
        image_paths: Files to inspect.
        show_progress: Display a ``tqdm`` bar when the library is available.

    Returns:
        A ``(sizes, failures)`` pair: a mapping from path to ``(width, height)``
        for everything that could be read, and the list of paths that could not.
        Returning failures rather than dropping them keeps "this file is broken"
        reportable.
    """
    paths = list(image_paths)
    sizes: dict[Path, tuple[int, int]] = {}
    failures: list[Path] = []

    for path in _progress(paths, description="Reading image sizes", enabled=show_progress):
        size = read_image_size(path)
        if size is None:
            failures.append(path)
        else:
            sizes[path] = size

    if failures:
        LOGGER.warning("%d of %d images could not be read", len(failures), len(paths))
    return sizes, failures


def write_json(destination: Path, payload: Any, *, indent: int = 2) -> Path:
    """Serialise a payload to a UTF-8 JSON file.

    ``ensure_ascii`` is off so Vietnamese text stays readable in the report
    rather than turning into escape sequences.

    Args:
        destination: File to write. Parent directories are created.
        payload: Any JSON-serialisable object. :class:`~pathlib.Path` values are
            converted to strings automatically.
        indent: Indentation passed to :func:`json.dump`.

    Returns:
        The path written to.

    Raises:
        OSError: If the file cannot be written.
        TypeError: If the payload contains a value that is not serialisable.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=indent, ensure_ascii=False, default=_json_default)
    LOGGER.debug("Wrote JSON report: %s", destination)
    return destination


def write_csv(
    destination: Path, rows: Sequence[Mapping[str, Any]], *, fieldnames: Sequence[str] | None = None
) -> Path:
    """Write a list of dictionaries to a CSV file.

    ``newline=""`` plus ``utf-8-sig`` is intentional: the first avoids the blank
    lines Python otherwise writes on Windows, the second makes Excel open the
    file with the right encoding, and these reports are meant to be read in
    Excel.

    Args:
        destination: File to write. Parent directories are created.
        rows: The records. An empty sequence still produces a header row when
            ``fieldnames`` is supplied, so downstream tools see a valid file.
        fieldnames: Column order. Defaults to the keys of the first row.

    Returns:
        The path written to.

    Raises:
        OSError: If the file cannot be written.
        ValueError: If the rows are non-empty but no field names can be derived.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)

    columns = list(fieldnames) if fieldnames is not None else (list(rows[0]) if rows else [])
    if rows and not columns:
        raise ValueError("Cannot write CSV: rows are present but no field names were derived")

    with destination.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        if columns:
            writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(value) for key, value in row.items()})

    LOGGER.debug("Wrote CSV report with %d rows: %s", len(rows), destination)
    return destination


def summarise_distribution(values: Sequence[float], name: str) -> dict[str, Any]:
    """Summarise a numeric distribution: count, min, median, mean, max, stdev.

    Implemented without the standard library's :mod:`statistics` module on
    purpose. ``scripts/dataset/statistics.py`` is a sibling of this file, and a
    script's own directory sits at the front of ``sys.path``, so ``import
    statistics`` anywhere in this package resolves to *that script* rather than
    the standard library and fails with a confusing ``AttributeError``. The
    handful of aggregates needed here are cheaper to compute than that hazard is
    to work around.

    Args:
        values: The samples. May be empty.
        name: Label echoed back in the result.

    Returns:
        A JSON-serialisable summary. An empty input yields ``{"name": ..., "count": 0}``
        so callers can render it without a special case.
    """
    if not values:
        return {"name": name, "count": 0}

    ordered = sorted(float(value) for value in values)
    count = len(ordered)
    mean = sum(ordered) / count

    middle = count // 2
    median = (
        ordered[middle] if count % 2 else (ordered[middle - 1] + ordered[middle]) / 2.0
    )

    variance = sum((value - mean) ** 2 for value in ordered) / count
    return {
        "name": name,
        "count": count,
        "min": round(ordered[0], 6),
        "median": round(median, 6),
        "mean": round(mean, 6),
        "max": round(ordered[-1], 6),
        "stdev": round(variance**0.5, 6),
        "p05": round(ordered[max(0, int(0.05 * (count - 1)))], 6),
        "p95": round(ordered[min(count - 1, int(round(0.95 * (count - 1))))], 6),
    }


def format_count(count: int, total: int) -> str:
    """Format a count as ``n/total (p%)`` for log messages.

    Args:
        count: The numerator.
        total: The denominator. Zero is handled without dividing.

    Returns:
        A display string such as ``"12/50 (24.0%)"``.
    """
    if total <= 0:
        return f"{count}/0 (n/a)"
    return f"{count}/{total} ({100.0 * count / total:.1f}%)"


def _progress(items: Sequence[Any], *, description: str, enabled: bool) -> Iterable[Any]:
    """Wrap a sequence in a ``tqdm`` bar when possible.

    Args:
        items: The sequence to iterate.
        description: Bar label.
        enabled: Set ``False`` to skip the bar entirely.

    Returns:
        Either a ``tqdm`` iterator or the original sequence. A missing ``tqdm``
        degrades to no progress bar rather than an ImportError -- progress
        reporting is a convenience, not a dependency.
    """
    if not enabled or len(items) < 200:
        return items
    try:
        from tqdm import tqdm
    except ImportError:
        return items
    return tqdm(items, desc=description, unit="img")


def _json_default(value: Any) -> Any:
    """Convert values :mod:`json` cannot serialise on its own.

    Args:
        value: The offending object.

    Returns:
        A serialisable stand-in.

    Raises:
        TypeError: If no conversion is known, matching :mod:`json` behaviour.
    """
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serialisable")


def _csv_value(value: Any) -> Any:
    """Render a value for a CSV cell.

    Args:
        value: The cell value.

    Returns:
        ``value`` unchanged, except that ``None`` becomes an empty string and
        paths become strings.
    """
    if value is None:
        return ""
    if isinstance(value, Path):
        return str(value)
    return value
