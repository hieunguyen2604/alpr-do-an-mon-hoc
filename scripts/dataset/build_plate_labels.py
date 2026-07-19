"""Build the OCR evaluation label file from the Phase 2b reconstruction.

Phase 2b reconstructed 4.019 plate strings from the two Roboflow datasets that
carry *character-level* boxes (``roboflow_ocr_plate`` and
``roboflow_ocr_conversion``) and wrote them to
``datasets/annotations/plate_text_labels.csv``. That file is a **reconstruction
audit trail**: it keeps every row, valid or not, together with the reason a row
failed, which is what makes the reconstruction reviewable.

An evaluation harness needs something narrower -- only the rows that are
trustworthy ground truth, in the column layout
:mod:`ai.evaluation.benchmark_ocr` expects. This script performs that
projection, and nothing else. It never invents a label and never repairs one:
a row that Phase 2b could not validate is dropped and counted, not fixed.

Selection rule
--------------
A row is kept when ``is_valid_format`` is ``True``. That flag already encodes
three separate exclusions decided in Phase 2b:

* the source image is not a Vietnamese plate (904 rows -- the OCR datasets mix
  in Czech, Croatian and other European plates);
* the reconstructed string matches no Vietnamese plate grammar (623 rows);
* the reconstruction itself was unsound -- overlapping character boxes, too few
  or too many characters, a three-line clustering (roughly 140 rows).

Critically, it also excludes the 595 rows that become valid **only after the
normalizer corrects them**. Keeping those would be circular: the normalizer
would then be graded on labels it had itself produced.

Why the split column matters
----------------------------
The ``split`` recorded here is the *Roboflow* split of the OCR dataset, not the
project's own detection split. It is carried through so that a future
plate-recogniser training run has a held-out set, and so that any figure
computed on a subset can say which subset it was.

Example:
    python scripts/dataset/build_plate_labels.py
    python scripts/dataset/build_plate_labels.py --min-chars 7 --output /tmp/x.csv
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from collections import Counter
from pathlib import Path
from typing import Final, Iterator

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]

DEFAULT_SOURCE: Final[Path] = (
    PROJECT_ROOT / "datasets" / "annotations" / "plate_text_labels.csv"
)
"""Phase 2b's full reconstruction audit trail, every row kept."""

DEFAULT_OUTPUT: Final[Path] = (
    PROJECT_ROOT / "datasets" / "annotations" / "plate_labels.csv"
)
"""The evaluation label file :mod:`ai.evaluation.benchmark_ocr` reads by default."""

OUTPUT_COLUMNS: Final[tuple[str, ...]] = (
    "image_path",
    "plate_text",
    "line_count",
    "split",
    "source_dataset",
)

LOGGER = logging.getLogger("scripts.dataset.build_plate_labels")

__all__ = [
    "DEFAULT_SOURCE",
    "DEFAULT_OUTPUT",
    "OUTPUT_COLUMNS",
    "extract_split",
    "build_rows",
    "main",
]


def extract_split(confidence_note: str) -> str:
    """Pull the dataset split out of Phase 2b's semicolon-separated note field.

    Phase 2b packed several facts into one ``confidence_note`` cell -- the
    outcome, the failure reasons and, for accepted rows, ``split=<name>``.
    Parsing it here rather than re-deriving the split from the file path keeps
    this script agreeing with the reconstruction by construction.

    Args:
        confidence_note: The raw cell, for example ``"ok;split=train"``.

    Returns:
        The split name, or an empty string when the note carries none.

    Examples:
        >>> extract_split("ok;split=train")
        'train'
        >>> extract_split("non_vietnamese_source_image")
        ''
    """
    for fragment in confidence_note.split(";"):
        fragment = fragment.strip()
        if fragment.startswith("split="):
            return fragment[len("split=") :]
    return ""


def build_rows(
    source: Path, min_chars: int = 7, max_chars: int = 10
) -> tuple[list[dict[str, str]], Counter[str]]:
    """Project the reconstruction audit trail onto evaluation-ready rows.

    Args:
        source: Path to ``plate_text_labels.csv``.
        min_chars: Shortest label accepted. The shortest legal Vietnamese civil
            plate string is 7 characters (``29A1234``); anything shorter is a
            truncated reconstruction, not a plate.
        max_chars: Longest label accepted. 9 characters is the normal maximum;
            10 leaves room for the rarer layouts rather than silently dropping
            them.

    Returns:
        A ``(rows, dropped)`` pair. ``rows`` are ready to write; ``dropped``
        counts why each rejected row was rejected, so the two numbers together
        account for every input row.

    Raises:
        FileNotFoundError: If ``source`` does not exist.
    """
    if not source.is_file():
        raise FileNotFoundError(
            f"Phase 2b label file not found: {source}\n"
            "Run the Phase 2b plate-text reconstruction first."
        )

    rows: list[dict[str, str]] = []
    dropped: Counter[str] = Counter()

    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        for record in csv.DictReader(handle):
            if (record.get("is_valid_format") or "").strip() != "True":
                dropped["not_valid_format"] += 1
                continue

            text = (record.get("plate_text") or "").strip().upper()
            if not (min_chars <= len(text) <= max_chars):
                dropped[f"length_{len(text)}_outside_{min_chars}_{max_chars}"] += 1
                continue

            line_count = (record.get("line_count") or "").strip()
            if line_count not in ("1", "2"):
                dropped["line_count_not_1_or_2"] += 1
                continue

            image_path = (record.get("image_path") or "").strip()
            if not image_path or not Path(image_path).is_file():
                dropped["image_missing"] += 1
                continue

            rows.append(
                {
                    "image_path": image_path,
                    "plate_text": text,
                    "line_count": line_count,
                    "split": extract_split(record.get("confidence_note") or ""),
                    "source_dataset": (record.get("source_dataset") or "").strip(),
                }
            )

    return rows, dropped


def _write(rows: list[dict[str, str]], destination: Path) -> None:
    """Write the evaluation label file.

    Args:
        rows: Rows produced by :func:`build_rows`.
        destination: Output CSV path; parent directories are created.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(OUTPUT_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line parser.

    Returns:
        The configured parser.
    """
    parser = argparse.ArgumentParser(
        prog="python scripts/dataset/build_plate_labels.py",
        description=(
            "Project the Phase 2b plate-text reconstruction onto the label "
            "file the OCR evaluation harness reads. Keeps only rows the "
            "reconstruction validated on its own, before any normalisation."
        ),
    )
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--min-chars", type=int, default=7)
    parser.add_argument("--max-chars", type=int, default=10)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the projection and report what was kept and what was dropped.

    Args:
        argv: Command-line arguments; ``sys.argv[1:]`` when omitted.

    Returns:
        ``0`` on success, ``2`` when the source file is missing.
    """
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = build_parser().parse_args(argv)

    try:
        rows, dropped = build_rows(
            Path(args.source), min_chars=args.min_chars, max_chars=args.max_chars
        )
    except FileNotFoundError as error:
        LOGGER.error("%s", error)
        return 2

    destination = Path(args.output)
    _write(rows, destination)

    by_line = Counter(row["line_count"] for row in rows)
    by_split = Counter(row["split"] or "(none)" for row in rows)
    by_dataset = Counter(row["source_dataset"] for row in rows)

    LOGGER.info("Wrote %d label rows to %s", len(rows), destination)
    LOGGER.info("  by line count : %s", dict(sorted(by_line.items())))
    LOGGER.info("  by split      : %s", dict(sorted(by_split.items())))
    LOGGER.info("  by dataset    : %s", dict(sorted(by_dataset.items())))
    LOGGER.info("  dropped       : %s", dict(dropped.most_common()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
