"""Measure the accuracy and the latency of the OCR stage on plate crops.

This is the Phase 4 measurement harness. It answers three questions that the
thesis has to answer with numbers rather than with argument:

1. **How much does post-processing actually contribute?** The normalizer is the
   project's own technical contribution -- everything else is an off-the-shelf
   model -- so its value has to be quantified, not asserted. The script reports
   full-string accuracy *before* and *after* normalisation as two separate
   figures (NFR-A5 versus NFR-A6); their difference is the contribution.
2. **Does the two-line path work?** Results are broken down by one-line and
   two-line plates (NFR-A8). This is the decisive measurement for project risk
   **R-04**: published work reports 94.3% on single-line car plates against
   45.7% on two-line motorcycle plates, and the split-then-hstack transform in
   :mod:`ai.inference.two_line` exists solely to close that gap. A single
   aggregate accuracy figure would hide whether it did.
3. **Is it fast enough on CPU?** Per-crop p50/p95/p99 latency, measured here,
   on this machine. Third-party CPU numbers are never quoted.

The script additionally emits a **36x36 character-level confusion matrix**.
That matrix is not decoration: the correction tables
:data:`~ai.inference.plate_rules.TO_DIGIT` and
:data:`~ai.inference.plate_rules.TO_LETTER` are currently derived from
glyph-shape reasoning rather than from measurement, and Phase 1 recorded that
explicitly. The matrix is the evidence needed to replace those hypotheses with
measured confusion frequencies.

Three accuracy figures, and why there are three
-----------------------------------------------
Comparing a raw engine string against a ground-truth label is not one
comparison but three, and collapsing them would overstate what the positional
repair rules do:

========================= ================================================
Figure                    Compares
========================= ================================================
``exact_verbatim``        engine output, untouched, against the label
``exact_pre_norm``        cleaned engine output against the cleaned label
``exact_post_norm``       normalised output against the cleaned label
========================= ================================================

``exact_pre_norm`` minus ``exact_verbatim`` is what *cleaning* buys (case
folding, separator stripping). ``exact_post_norm`` minus ``exact_pre_norm`` is
what the *positional repair rules* buy. Reporting only the first and the last
would credit the rules with the separator stripping as well.

Input format
------------
A CSV file, by default ``datasets/annotations/plate_labels.csv``:

=============== ========== ==================================================
Column          Required   Meaning
=============== ========== ==================================================
``image_path``  yes        Path to a **cropped plate** image. Absolute, or
                           relative to the project root, or relative to the
                           CSV's own directory -- all three are tried.
``plate_text``  yes        The true plate string. Separators optional.
``line_count``  no         ``1`` or ``2``. When absent it is estimated from
                           the crop's aspect ratio and the report says so.
``split``       no         Dataset split name, for filtering with ``--split``.
=============== ========== ==================================================

The labels do not exist yet: they are produced by hand. When the file is
missing the script says exactly what to create and exits cleanly with status
``2``. It never invents data.

Example:
    python -m ai.evaluation.benchmark_ocr \\
        --labels datasets/annotations/plate_labels.csv \\
        --output-dir docs/reports/04-ocr-benchmark

Run it with the OCR virtual environment (``.venv-ocr``), which is the only one
carrying PaddleOCR.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import platform
import statistics
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Sequence

from ai.inference.config import PROJECT_ROOT, InferenceConfig
from ai.inference.exceptions import ALPRError
from ai.inference.interfaces import BaseRecognizer
from ai.inference.normalizer import VietnamesePlateNormalizer
from ai.inference.plate_rules import OCR_TRAINING_CHARSET, clean_text
from ai.inference.two_line import estimate_line_count

__all__ = [
    "DEFAULT_LABELS_PATH",
    "DEFAULT_OUTPUT_DIR",
    "LabelRecord",
    "SampleResult",
    "align",
    "character_error_rate",
    "build_recognizer",
    "load_labels",
    "run_benchmark",
    "summarize",
    "build_confusion_matrix",
    "write_reports",
    "main",
]

LOGGER = logging.getLogger("ai.evaluation.benchmark_ocr")

DEFAULT_LABELS_PATH: Final[Path] = PROJECT_ROOT / "datasets" / "annotations" / "plate_labels.csv"
"""Where the hand-made plate transcriptions are expected to live."""

DEFAULT_OUTPUT_DIR: Final[Path] = PROJECT_ROOT / "docs" / "reports" / "04-ocr-benchmark"
"""Directory receiving the JSON payload, the Markdown table and the charts."""

_REQUIRED_COLUMNS: Final[frozenset[str]] = frozenset({"image_path", "plate_text"})

_CHARSET: Final[str] = OCR_TRAINING_CHARSET
"""The 36 symbols of the confusion matrix: ``0``-``9`` then ``A``-``Z``.

The matrix is built over the *training* charset rather than the 31-character
safe charset on purpose. A recogniser trained on 36 symbols can emit ``I``,
``J``, ``O``, ``Q`` and ``W``, which are illegal on a Vietnamese plate; those
emissions are exactly the observable, repairable mistakes the split between
:data:`~ai.inference.plate_rules.OCR_TRAINING_CHARSET` and
:data:`~ai.inference.plate_rules.OCR_SAFE_CHARSET` was designed to expose. A
31-symbol matrix would drop the most interesting column.
"""

_CHAR_INDEX: Final[dict[str, int]] = {char: i for i, char in enumerate(_CHARSET)}


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LabelRecord:
    """One hand-transcribed plate crop.

    Attributes:
        image_path: Resolved absolute path to the crop.
        plate_text: The label exactly as written in the CSV.
        cleaned_text: :func:`~ai.inference.plate_rules.clean_text` applied to
            :attr:`plate_text` -- the canonical form every comparison uses.
        line_count: ``1`` or ``2`` when the CSV stated it, otherwise ``None``.
        split: Dataset split name, or ``None``.
        row_number: 1-based line number in the CSV, for error messages.
    """

    image_path: Path
    plate_text: str
    cleaned_text: str
    line_count: int | None
    split: str | None
    row_number: int


@dataclass(slots=True)
class SampleResult:
    """Everything measured for a single crop.

    Serialised into the JSON report as-is, because
    :mod:`ai.evaluation.error_analysis` consumes these records rather than
    re-running the OCR engine -- OCR is by far the expensive half of the work
    and running it twice for one analysis would be wasteful.

    Attributes:
        image_path: Absolute path to the crop, as a string.
        ground_truth: Cleaned label.
        raw_text: Untouched engine output.
        pre_norm_text: Cleaned engine output, before positional repair.
        post_norm_text: Output of the normalizer.
        is_valid_format: Whether the normalised string matched a civil pattern.
        corrections: ``(index, before, after)`` triples the repair applied.
        line_count: Line count used for the breakdown.
        line_count_source: ``"label"`` or ``"aspect_ratio"``.
        aspect_ratio: Width divided by height of the crop.
        confidence: Aggregated OCR confidence.
        elapsed_ms: Wall-clock recognition time for this crop.
        exact_verbatim: Engine output equals the label, character for character.
        exact_pre_norm: Cleaned engine output equals the cleaned label.
        exact_post_norm: Normalised output equals the cleaned label.
        cer_pre_norm: Character error rate before repair.
        cer_post_norm: Character error rate after repair.
        error: Message when recognition failed for this crop, else ``None``.
            A failed crop is recorded and counted, never silently skipped.
    """

    image_path: str
    ground_truth: str
    raw_text: str
    pre_norm_text: str
    post_norm_text: str
    is_valid_format: bool
    corrections: list[tuple[int, str, str]]
    line_count: int
    line_count_source: str
    aspect_ratio: float
    confidence: float
    elapsed_ms: float
    exact_verbatim: bool
    exact_pre_norm: bool
    exact_post_norm: bool
    cer_pre_norm: float
    cer_post_norm: float
    error: str | None = None


@dataclass(slots=True)
class BenchmarkOutcome:
    """The complete result of one benchmark run.

    Attributes:
        samples: One :class:`SampleResult` per crop, in input order.
        skipped: ``(row_number, reason)`` for every CSV row that could not be
            used, so that the report accounts for the full label file.
        engine_name: Identifier reported by the recogniser.
        settings: The run's parameters, echoed into the report.
    """

    samples: list[SampleResult] = field(default_factory=list)
    skipped: list[tuple[int, str]] = field(default_factory=list)
    engine_name: str = "unknown"
    settings: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# String metrics
# ---------------------------------------------------------------------------


def align(reference: str, hypothesis: str) -> list[tuple[str, str, str]]:
    """Align two strings with Levenshtein edit operations.

    A plain edit *distance* is enough to compute a character error rate, but not
    enough to build a confusion matrix: that needs to know **which** character
    was mistaken for which. This returns the operation trace instead of the
    scalar, so both fall out of one pass.

    Substitution, insertion and deletion all cost 1; ties are resolved in the
    order substitute, delete, insert, which keeps the trace deterministic.

    Args:
        reference: The ground-truth string.
        hypothesis: The predicted string.

    Returns:
        Operations in reading order, each a ``(op, ref_char, hyp_char)`` triple
        where ``op`` is one of ``"equal"``, ``"substitute"``, ``"delete"``
        (present in the reference, missing from the hypothesis) or ``"insert"``
        (absent from the reference, added by the hypothesis). The unused
        character of an insert/delete is the empty string.

    Examples:
        >>> align("30A", "3OA")
        [('equal', '3', '3'), ('substitute', '0', 'O'), ('equal', 'A', 'A')]
    """
    rows, columns = len(reference), len(hypothesis)
    # cost[i][j] = edit distance between reference[:i] and hypothesis[:j].
    cost: list[list[int]] = [[0] * (columns + 1) for _ in range(rows + 1)]
    for i in range(1, rows + 1):
        cost[i][0] = i
    for j in range(1, columns + 1):
        cost[0][j] = j
    for i in range(1, rows + 1):
        for j in range(1, columns + 1):
            substitution = cost[i - 1][j - 1] + (reference[i - 1] != hypothesis[j - 1])
            cost[i][j] = min(substitution, cost[i - 1][j] + 1, cost[i][j - 1] + 1)

    operations: list[tuple[str, str, str]] = []
    i, j = rows, columns
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            same = reference[i - 1] == hypothesis[j - 1]
            if cost[i][j] == cost[i - 1][j - 1] + (not same):
                operations.append(
                    (
                        "equal" if same else "substitute",
                        reference[i - 1],
                        hypothesis[j - 1],
                    )
                )
                i, j = i - 1, j - 1
                continue
        if i > 0 and cost[i][j] == cost[i - 1][j] + 1:
            operations.append(("delete", reference[i - 1], ""))
            i -= 1
            continue
        operations.append(("insert", "", hypothesis[j - 1]))
        j -= 1

    operations.reverse()
    return operations


def character_error_rate(reference: str, hypothesis: str) -> float:
    """Compute the character error rate between a label and a prediction.

    Args:
        reference: The ground-truth string.
        hypothesis: The predicted string.

    Returns:
        ``edit_distance / len(reference)``, **not** capped at 1.0. A prediction
        far longer than the label genuinely has a rate above 1, and clipping it
        would hide a runaway recogniser behind a tidy-looking number. When the
        reference is empty the rate is ``0.0`` for an empty hypothesis and
        ``1.0`` otherwise.
    """
    if not reference:
        return 0.0 if not hypothesis else 1.0
    distance = sum(1 for operation, _, _ in align(reference, hypothesis) if operation != "equal")
    return distance / len(reference)


# ---------------------------------------------------------------------------
# Label loading
# ---------------------------------------------------------------------------


def _resolve_image_path(raw: str, csv_directory: Path) -> Path | None:
    """Resolve an image path from the CSV against the three plausible bases.

    Args:
        raw: The path as written in the CSV.
        csv_directory: Directory holding the CSV file.

    Returns:
        The first candidate that exists, or ``None`` when none does. Absolute
        paths are tried first, then paths relative to the project root, then
        paths relative to the CSV -- the last is what a label file written by
        an annotation tool usually contains.
    """
    candidate = Path(raw.strip()).expanduser()
    if candidate.is_absolute():
        return candidate if candidate.is_file() else None
    for base in (PROJECT_ROOT, csv_directory):
        resolved = base / candidate
        if resolved.is_file():
            return resolved
    return None


def load_labels(
    labels_path: Path, split: str | None = None
) -> tuple[list[LabelRecord], list[tuple[int, str]]]:
    """Read and validate the hand-made plate transcriptions.

    Rows are validated rather than trusted: a missing image or an empty label
    silently dropped would make every accuracy figure computed afterwards
    unverifiable.

    Args:
        labels_path: Path to the CSV file.
        split: When given, keep only rows whose ``split`` column matches.

    Returns:
        A ``(records, skipped)`` pair, where ``skipped`` holds
        ``(row_number, reason)`` for every unusable row.

    Raises:
        FileNotFoundError: If the CSV does not exist.
        ValueError: If the CSV is empty or lacks a required column.
    """
    if not labels_path.is_file():
        raise FileNotFoundError(
            f"Plate label file not found: {labels_path}\n"
            "Phase 4 needs hand-made transcriptions; this script will not "
            "fabricate them. Create a UTF-8 CSV with the header\n"
            "    image_path,plate_text,line_count,split\n"
            "where image_path points at a CROPPED plate image and plate_text is "
            "the true reading (separators optional). line_count (1 or 2) and "
            "split are optional."
        )

    csv_directory = labels_path.parent
    records: list[LabelRecord] = []
    skipped: list[tuple[int, str]] = []

    with labels_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{labels_path} is empty: no header row found")
        columns = {name.strip().lower() for name in reader.fieldnames}
        missing = _REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(
                f"{labels_path} is missing required column(s): "
                f"{', '.join(sorted(missing))}. Found: {', '.join(sorted(columns))}"
            )

        for row_number, row in enumerate(reader, start=2):
            normalised = {
                (key or "").strip().lower(): (value or "").strip() for key, value in row.items()
            }
            row_split = normalised.get("split") or None
            if split is not None and row_split != split:
                continue

            raw_path = normalised.get("image_path", "")
            label = normalised.get("plate_text", "")
            if not raw_path or not label:
                skipped.append((row_number, "image_path or plate_text is empty"))
                continue

            image_path = _resolve_image_path(raw_path, csv_directory)
            if image_path is None:
                skipped.append((row_number, f"image not found: {raw_path}"))
                continue

            cleaned = clean_text(label)
            if not cleaned:
                skipped.append((row_number, f"label has no usable characters: {label!r}"))
                continue

            line_count = _parse_line_count(normalised.get("line_count"))
            if normalised.get("line_count") and line_count is None:
                skipped.append(
                    (row_number, f"line_count must be 1 or 2, got {normalised['line_count']!r}")
                )
                continue

            records.append(
                LabelRecord(
                    image_path=image_path,
                    plate_text=label,
                    cleaned_text=cleaned,
                    line_count=line_count,
                    split=row_split,
                    row_number=row_number,
                )
            )

    return records, skipped


def _parse_line_count(value: str | None) -> int | None:
    """Parse the optional ``line_count`` column.

    Args:
        value: Raw cell content, possibly empty or ``None``.

    Returns:
        ``1`` or ``2``, or ``None`` when the cell is empty or unparsable.
    """
    if not value:
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    return parsed if parsed in (1, 2) else None


# ---------------------------------------------------------------------------
# Engine construction
# ---------------------------------------------------------------------------


def build_recognizer(engine: str, config: InferenceConfig, preprocess: bool) -> BaseRecognizer:
    """Construct the recogniser named on the command line.

    This indirection is the point of :class:`~ai.inference.interfaces.BaseRecognizer`
    made concrete. Phase 1 found **no** public evidence that PaddleOCR beats
    EasyOCR on plate imagery, and the single reproducible comparison that was
    located favoured EasyOCR; the engine choice is therefore an open question
    that this benchmark exists to settle on this project's own data. Adding a
    competitor means writing one subclass and one entry here.

    Args:
        engine: Engine key. Currently only ``"paddleocr"`` is implemented.
        config: Runtime settings handed to the engine.
        preprocess: Whether the engine may run its pre-processing chain. Set to
            ``False`` to measure what that chain contributes.

    Returns:
        A ready-to-use recogniser. Models are loaded lazily on the first call.

    Raises:
        ValueError: If ``engine`` names an implementation that does not exist.
    """
    if engine == "paddleocr":
        from ai.inference.recognizer import PaddleOcrRecognizer

        return PaddleOcrRecognizer(config, preprocess=preprocess)
    raise ValueError(
        f"Unknown OCR engine {engine!r}. Implemented: paddleocr. "
        "To compare another engine, subclass BaseRecognizer and register it here."
    )


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------


def run_benchmark(
    records: Sequence[LabelRecord],
    recognizer: BaseRecognizer,
    normalizer: VietnamesePlateNormalizer,
    aspect_ratio_threshold: float,
    warmup: int = 3,
) -> BenchmarkOutcome:
    """Run the recogniser over every labelled crop and measure the outcome.

    Warm-up passes are run first and discarded: the first inference of a process
    pays one-off model loading and lazy kernel compilation, and letting that
    land in the p99 would make the latency figure describe start-up rather than
    steady state.

    A crop that fails to decode, or on which the engine raises, is recorded with
    an ``error`` and empty predictions. It still counts against accuracy -- an
    unreadable plate is a failure of the system, and excluding it would flatter
    the result.

    Args:
        records: The labelled crops.
        recognizer: The engine under test.
        normalizer: The post-processing stage under test.
        aspect_ratio_threshold: Width/height cut-off below which a crop with no
            labelled line count is treated as two-line.
        warmup: Number of discarded warm-up recognitions.

    Returns:
        A :class:`BenchmarkOutcome`.

    Raises:
        ImportError: If OpenCV is unavailable, which makes the run impossible.
    """
    import cv2

    outcome = BenchmarkOutcome(engine_name=recognizer.name)

    if warmup > 0 and records:
        LOGGER.info("Warming up the engine (%d discarded pass(es))...", warmup)
        for record in records[:warmup]:
            image = cv2.imread(str(record.image_path))
            if image is None:
                continue
            try:
                recognizer.recognize(image)
            except ALPRError as error:
                LOGGER.warning("Warm-up recognition failed: %s", error)

    total = len(records)
    for index, record in enumerate(records, start=1):
        if index % 25 == 0 or index == total:
            LOGGER.info("  %d/%d crops processed", index, total)

        image = cv2.imread(str(record.image_path))
        if image is None:
            outcome.skipped.append((record.row_number, f"cannot decode image: {record.image_path}"))
            continue

        height, width = image.shape[0], image.shape[1]
        aspect_ratio = width / height if height else 0.0
        if record.line_count is not None:
            line_count = record.line_count
            line_count_source = "label"
        else:
            line_count = estimate_line_count(image, aspect_ratio_threshold)
            line_count_source = "aspect_ratio"

        started = time.perf_counter()
        error_message: str | None = None
        raw_text = ""
        confidence = 0.0
        try:
            recognition = recognizer.recognize(image)
            raw_text = recognition.raw_text
            confidence = recognition.confidence
        except ALPRError as error:
            error_message = f"{type(error).__name__}: {error}"
            LOGGER.warning("Recognition failed on %s: %s", record.image_path, error)
        elapsed_ms = (time.perf_counter() - started) * 1000.0

        pre_norm = clean_text(raw_text)
        detailed = normalizer.normalize_detailed(raw_text, line_count=line_count)
        truth = record.cleaned_text

        outcome.samples.append(
            SampleResult(
                image_path=str(record.image_path),
                ground_truth=truth,
                raw_text=raw_text,
                pre_norm_text=pre_norm,
                post_norm_text=detailed.text,
                is_valid_format=detailed.is_valid_format,
                corrections=[list(item) for item in detailed.corrections],  # type: ignore[misc]
                line_count=line_count,
                line_count_source=line_count_source,
                aspect_ratio=round(aspect_ratio, 4),
                confidence=round(confidence, 4),
                elapsed_ms=round(elapsed_ms, 3),
                exact_verbatim=raw_text == record.plate_text,
                exact_pre_norm=pre_norm == truth,
                exact_post_norm=detailed.text == truth,
                cer_pre_norm=round(character_error_rate(truth, pre_norm), 6),
                cer_post_norm=round(character_error_rate(truth, detailed.text), 6),
                error=error_message,
            )
        )

    return outcome


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def _percentile(ordered: Sequence[float], fraction: float) -> float:
    """Return a nearest-rank percentile of an already sorted sequence.

    The nearest-rank definition is used rather than an interpolating one so
    that every reported percentile is a latency that was genuinely observed.

    Args:
        ordered: Values sorted ascending. Must not be empty.
        fraction: Percentile as a fraction in ``(0, 1]``.

    Returns:
        The value at that rank.
    """
    rank = max(1, min(len(ordered), int(round(fraction * len(ordered)))))
    return ordered[rank - 1]


def _accuracy_block(samples: Sequence[SampleResult]) -> dict[str, Any]:
    """Aggregate the accuracy figures over a group of samples.

    Args:
        samples: The samples in the group. May be empty.

    Returns:
        Mapping with the counts, the three exact-match accuracies, the mean
        character accuracies and the post-processing contribution. Every value
        is ``0.0`` for an empty group, and ``count`` says so.
    """
    count = len(samples)
    if count == 0:
        return {
            "count": 0,
            "exact_verbatim": 0.0,
            "exact_pre_norm": 0.0,
            "exact_post_norm": 0.0,
            "postprocessing_gain": 0.0,
            "char_accuracy_pre_norm": 0.0,
            "char_accuracy_post_norm": 0.0,
            "cer_pre_norm": 0.0,
            "cer_post_norm": 0.0,
            "valid_format_rate": 0.0,
            "empty_read_rate": 0.0,
            "mean_confidence": 0.0,
        }

    pre = sum(1 for s in samples if s.exact_pre_norm) / count
    post = sum(1 for s in samples if s.exact_post_norm) / count
    cer_pre = statistics.fmean(s.cer_pre_norm for s in samples)
    cer_post = statistics.fmean(s.cer_post_norm for s in samples)
    return {
        "count": count,
        "exact_verbatim": round(sum(1 for s in samples if s.exact_verbatim) / count, 4),
        "exact_pre_norm": round(pre, 4),
        "exact_post_norm": round(post, 4),
        # The headline number of Phase 4: what the normalizer added.
        "postprocessing_gain": round(post - pre, 4),
        "char_accuracy_pre_norm": round(1.0 - cer_pre, 4),
        "char_accuracy_post_norm": round(1.0 - cer_post, 4),
        "cer_pre_norm": round(cer_pre, 4),
        "cer_post_norm": round(cer_post, 4),
        "valid_format_rate": round(sum(1 for s in samples if s.is_valid_format) / count, 4),
        "empty_read_rate": round(sum(1 for s in samples if not s.raw_text) / count, 4),
        "mean_confidence": round(statistics.fmean(s.confidence for s in samples), 4),
    }


def _latency_block(samples: Sequence[SampleResult]) -> dict[str, Any]:
    """Aggregate the per-crop latency figures.

    Args:
        samples: The samples to time over. May be empty.

    Returns:
        Mapping with mean, p50, p95, p99, min and max in milliseconds, plus the
        implied single-threaded throughput.
    """
    if not samples:
        return {"count": 0}
    ordered = sorted(sample.elapsed_ms for sample in samples)
    mean = statistics.fmean(ordered)
    return {
        "count": len(ordered),
        "mean_ms": round(mean, 2),
        "p50_ms": round(_percentile(ordered, 0.50), 2),
        "p95_ms": round(_percentile(ordered, 0.95), 2),
        "p99_ms": round(_percentile(ordered, 0.99), 2),
        "min_ms": round(ordered[0], 2),
        "max_ms": round(ordered[-1], 2),
        "stdev_ms": round(statistics.stdev(ordered), 2) if len(ordered) > 1 else 0.0,
        "crops_per_second": round(1000.0 / mean, 2) if mean > 0 else 0.0,
    }


def summarize(outcome: BenchmarkOutcome) -> dict[str, Any]:
    """Turn the raw per-crop results into the report's summary section.

    Args:
        outcome: The benchmark result.

    Returns:
        Mapping with an ``overall`` block, a ``by_line_count`` block holding a
        separate entry for one-line and two-line plates (NFR-A8), the latency
        block and the label-quality counters.
    """
    samples = outcome.samples
    one_line = [s for s in samples if s.line_count == 1]
    two_line = [s for s in samples if s.line_count == 2]

    return {
        "overall": _accuracy_block(samples),
        "by_line_count": {
            "one_line": {
                **_accuracy_block(one_line),
                "latency": _latency_block(one_line),
            },
            "two_line": {
                **_accuracy_block(two_line),
                "latency": _latency_block(two_line),
            },
        },
        "latency": _latency_block(samples),
        "line_count_source": dict(Counter(sample.line_count_source for sample in samples)),
        "failed_crops": sum(1 for sample in samples if sample.error is not None),
        "skipped_rows": len(outcome.skipped),
    }


def build_confusion_matrix(
    samples: Sequence[SampleResult], use_post_norm: bool = False
) -> dict[str, Any]:
    """Build the 36x36 character confusion matrix from the aligned strings.

    The matrix is the empirical replacement for the shape-based reasoning
    currently encoded in :data:`~ai.inference.plate_rules.TO_DIGIT` and
    :data:`~ai.inference.plate_rules.TO_LETTER`. Phase 1 flagged those tables as
    hypotheses; this is the measurement that either confirms them or replaces
    them.

    Insertions and deletions are counted **separately** rather than folded into
    the grid. A deletion is not a confusion between two characters -- there is
    no second character -- and giving it a cell would corrupt exactly the
    statistic the correction tables are meant to be derived from.

    Args:
        samples: The samples to aggregate over.
        use_post_norm: Build the matrix from the normalised strings instead of
            the raw ones. The raw matrix is the one that describes the *engine*;
            the post-norm matrix shows which confusions the rules failed to fix.

    Returns:
        Mapping with ``charset``, ``matrix`` (a 36x36 list of rows indexed
        ``[true][predicted]``), ``top_confusions`` (the most frequent off-
        diagonal pairs), ``insertions``/``deletions`` per character and
        ``out_of_charset`` for symbols the engine emitted that are not in the
        36-symbol alphabet.
    """
    size = len(_CHARSET)
    matrix = [[0] * size for _ in range(size)]
    insertions: Counter[str] = Counter()
    deletions: Counter[str] = Counter()
    out_of_charset: Counter[str] = Counter()

    for sample in samples:
        hypothesis = sample.post_norm_text if use_post_norm else sample.pre_norm_text
        for operation, ref_char, hyp_char in align(sample.ground_truth, hypothesis):
            if operation == "delete":
                deletions[ref_char] += 1
                continue
            if operation == "insert":
                if hyp_char in _CHAR_INDEX:
                    insertions[hyp_char] += 1
                else:
                    out_of_charset[hyp_char] += 1
                continue
            ref_index = _CHAR_INDEX.get(ref_char)
            hyp_index = _CHAR_INDEX.get(hyp_char)
            if ref_index is None or hyp_index is None:
                out_of_charset[hyp_char if hyp_index is None else ref_char] += 1
                continue
            matrix[ref_index][hyp_index] += 1

    confusions = [
        (_CHARSET[i], _CHARSET[j], matrix[i][j])
        for i in range(size)
        for j in range(size)
        if i != j and matrix[i][j] > 0
    ]
    confusions.sort(key=lambda item: item[2], reverse=True)

    return {
        "charset": _CHARSET,
        "source": "post_norm" if use_post_norm else "raw",
        "matrix": matrix,
        "top_confusions": [
            {"true": true, "predicted": predicted, "count": count}
            for true, predicted, count in confusions[:30]
        ],
        "insertions": dict(insertions.most_common()),
        "deletions": dict(deletions.most_common()),
        "out_of_charset": dict(out_of_charset.most_common()),
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _environment_info() -> dict[str, Any]:
    """Describe the machine, so the numbers stay interpretable later.

    Returns:
        Mapping with the OS, the CPU identifier and the Python version.
    """
    return {
        "system": f"{platform.system()} {platform.release()}",
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
        "python": platform.python_version(),
    }


def _format_percent(value: float) -> str:
    """Format a fraction as a percentage string with one decimal.

    Args:
        value: A fraction, typically in ``[0, 1]``.

    Returns:
        For example ``"94.3%"``.
    """
    return f"{value * 100:.1f}%"


def _markdown_report(payload: dict[str, Any]) -> str:
    """Render the summary as a Markdown document.

    Args:
        payload: The full JSON payload.

    Returns:
        The Markdown source, ready to be pasted into the Phase 4 report.
    """
    summary = payload["summary"]
    overall = summary["overall"]
    one_line = summary["by_line_count"]["one_line"]
    two_line = summary["by_line_count"]["two_line"]
    latency = summary["latency"]

    lines: list[str] = [
        "# Ket qua benchmark OCR",
        "",
        f"- Sinh luc: `{payload['generated_at']}`",
        f"- Engine: `{payload['engine']}`",
        f"- Nhan: `{payload['settings']['labels_path']}`",
        f"- So anh do duoc: **{overall['count']}**",
        f"- Anh bi bo qua: **{summary['skipped_rows']}**"
        f" / loi nhan dang: **{summary['failed_crops']}**",
        "",
        "## 1. Do chinh xac tong the",
        "",
        "| Chi so | Gia tri |",
        "|---|---|",
        f"| Chuoi day du, nguyen van engine | {_format_percent(overall['exact_verbatim'])} |",
        f"| Chuoi day du, TRUOC chuan hoa (NFR-A5) | **{_format_percent(overall['exact_pre_norm'])}** |",
        f"| Chuoi day du, SAU chuan hoa (NFR-A6) | **{_format_percent(overall['exact_post_norm'])}** |",
        f"| **Dong gop cua khoi hau xu ly** | **{overall['postprocessing_gain'] * 100:+.1f} diem** |",
        f"| Do chinh xac ky tu truoc chuan hoa (1 - CER) | {_format_percent(overall['char_accuracy_pre_norm'])} |",
        f"| Do chinh xac ky tu sau chuan hoa (1 - CER) | {_format_percent(overall['char_accuracy_post_norm'])} |",
        f"| Ty le dung dinh dang hop le | {_format_percent(overall['valid_format_rate'])} |",
        f"| Ty le doc rong (khong ra chu nao) | {_format_percent(overall['empty_read_rate'])} |",
        f"| Do tin cay OCR trung binh | {overall['mean_confidence']:.3f} |",
        "",
        "## 2. Tach theo so dong (NFR-A8, rui ro R-04)",
        "",
        "| Chi so | Bien 1 dong | Bien 2 dong |",
        "|---|---|---|",
        f"| So mau | {one_line['count']} | {two_line['count']} |",
        f"| Chuoi day du truoc chuan hoa | {_format_percent(one_line['exact_pre_norm'])} "
        f"| {_format_percent(two_line['exact_pre_norm'])} |",
        f"| Chuoi day du sau chuan hoa | **{_format_percent(one_line['exact_post_norm'])}** "
        f"| **{_format_percent(two_line['exact_post_norm'])}** |",
        f"| Dong gop hau xu ly | {one_line['postprocessing_gain'] * 100:+.1f} diem "
        f"| {two_line['postprocessing_gain'] * 100:+.1f} diem |",
        f"| Do chinh xac ky tu sau chuan hoa | {_format_percent(one_line['char_accuracy_post_norm'])} "
        f"| {_format_percent(two_line['char_accuracy_post_norm'])} |",
        f"| Ty le doc rong | {_format_percent(one_line['empty_read_rate'])} "
        f"| {_format_percent(two_line['empty_read_rate'])} |",
        "",
        "## 3. Do tre moi anh crop (CPU)",
        "",
        "| Chi so | ms |",
        "|---|---|",
    ]

    if latency.get("count"):
        lines.extend(
            [
                f"| Trung binh | {latency['mean_ms']:.2f} |",
                f"| p50 | {latency['p50_ms']:.2f} |",
                f"| p95 | {latency['p95_ms']:.2f} |",
                f"| p99 | {latency['p99_ms']:.2f} |",
                f"| Nho nhat | {latency['min_ms']:.2f} |",
                f"| Lon nhat | {latency['max_ms']:.2f} |",
                f"| Thong luong (1 luong) | {latency['crops_per_second']:.2f} anh/giay |",
            ]
        )
    else:
        lines.append("| _khong co du lieu_ | - |")

    confusions = payload["confusion_matrix"]["top_confusions"]
    lines.extend(
        [
            "",
            "## 4. Cac cap ky tu bi nham nhieu nhat (do that, chua chuan hoa)",
            "",
            "| That | Doc thanh | So lan |",
            "|---|---|---|",
        ]
    )
    if confusions:
        lines.extend(
            f"| `{item['true']}` | `{item['predicted']}` | {item['count']} |"
            for item in confusions[:15]
        )
    else:
        lines.append("| _khong ghi nhan nham lan nao_ | - | - |")

    lines.extend(
        [
            "",
            "> Bang tren la **so lieu do duoc**, dung de thay the cac bang suy luan",
            "> theo hinh dang ky tu (`TO_DIGIT` / `TO_LETTER`) trong",
            "> `ai/inference/plate_rules.py`.",
            "",
            f"Moi truong do: {payload['environment']['system']}, "
            f"{payload['environment']['processor']}, "
            f"Python {payload['environment']['python']}.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_charts(payload: dict[str, Any], output_dir: Path) -> list[Path]:
    """Render the PNG charts that accompany the report.

    Charts are best-effort: a missing or misbehaving Matplotlib must not lose a
    benchmark run whose numbers are already in the JSON payload.

    Args:
        payload: The full JSON payload.
        output_dir: Directory to write the PNGs into.

    Returns:
        Paths actually written, possibly empty.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as error:
        LOGGER.warning("Charts skipped, Matplotlib unavailable: %s", error)
        return []

    written: list[Path] = []
    summary = payload["summary"]

    try:
        # Chart 1 -- accuracy before/after normalisation, split by line count.
        groups = ["Tong the", "1 dong", "2 dong"]
        blocks = [
            summary["overall"],
            summary["by_line_count"]["one_line"],
            summary["by_line_count"]["two_line"],
        ]
        pre = [block["exact_pre_norm"] * 100 for block in blocks]
        post = [block["exact_post_norm"] * 100 for block in blocks]
        positions = np.arange(len(groups))
        width = 0.38

        figure, axes = plt.subplots(figsize=(8, 5))
        axes.bar(positions - width / 2, pre, width, label="Truoc chuan hoa")
        axes.bar(positions + width / 2, post, width, label="Sau chuan hoa")
        for x, value in zip(positions - width / 2, pre):
            axes.text(x, value + 1, f"{value:.1f}", ha="center", fontsize=9)
        for x, value in zip(positions + width / 2, post):
            axes.text(x, value + 1, f"{value:.1f}", ha="center", fontsize=9)
        axes.set_xticks(positions, groups)
        axes.set_ylabel("Do chinh xac chuoi day du (%)")
        axes.set_ylim(0, 105)
        axes.set_title("Dong gop cua khoi hau xu ly, tach theo so dong")
        axes.legend()
        axes.grid(axis="y", alpha=0.3)
        figure.tight_layout()
        destination = output_dir / "accuracy_by_line_count.png"
        figure.savefig(destination, dpi=150)
        plt.close(figure)
        written.append(destination)
    except Exception as error:  # noqa: BLE001 - charts are best-effort
        LOGGER.warning("Could not render the accuracy chart: %s", error)

    try:
        # Chart 2 -- latency distribution with the percentile markers.
        latencies = [sample["elapsed_ms"] for sample in payload["samples"]]
        latency = summary["latency"]
        if latencies and latency.get("count"):
            figure, axes = plt.subplots(figsize=(8, 4.5))
            axes.hist(latencies, bins=40, color="#4C78A8", alpha=0.85)
            for key, colour in (
                ("p50_ms", "#2E7D32"),
                ("p95_ms", "#EF6C00"),
                ("p99_ms", "#C62828"),
            ):
                axes.axvline(
                    latency[key],
                    color=colour,
                    linestyle="--",
                    label=f"{key[:3]} = {latency[key]:.1f} ms",
                )
            axes.set_xlabel("Thoi gian nhan dang moi anh crop (ms)")
            axes.set_ylabel("So anh")
            axes.set_title("Phan bo do tre OCR tren CPU")
            axes.legend()
            figure.tight_layout()
            destination = output_dir / "latency_distribution.png"
            figure.savefig(destination, dpi=150)
            plt.close(figure)
            written.append(destination)
    except Exception as error:  # noqa: BLE001
        LOGGER.warning("Could not render the latency chart: %s", error)

    try:
        # Chart 3 -- the 36x36 confusion matrix.
        charset = payload["confusion_matrix"]["charset"]
        matrix = np.asarray(payload["confusion_matrix"]["matrix"], dtype=float)
        # The diagonal dwarfs everything else by orders of magnitude, so a
        # linear scale would render every confusion as the same shade of white.
        # log1p keeps the correct readings visible without flattening the
        # off-diagonal structure, which is the part that matters here.
        figure, axes = plt.subplots(figsize=(11, 9.5))
        image = axes.imshow(np.log1p(matrix), cmap="viridis", aspect="auto")
        axes.set_xticks(range(len(charset)), list(charset), fontsize=7)
        axes.set_yticks(range(len(charset)), list(charset), fontsize=7)
        axes.set_xlabel("Ky tu OCR doc ra")
        axes.set_ylabel("Ky tu that")
        axes.set_title("Ma tran nham lan ky tu 36x36 (thang do log(1+n))")
        figure.colorbar(image, ax=axes, label="log(1 + so lan)")
        figure.tight_layout()
        destination = output_dir / "confusion_matrix.png"
        figure.savefig(destination, dpi=150)
        plt.close(figure)
        written.append(destination)
    except Exception as error:  # noqa: BLE001
        LOGGER.warning("Could not render the confusion matrix: %s", error)

    return written


def write_reports(payload: dict[str, Any], output_dir: Path) -> dict[str, Path]:
    """Write the JSON payload, the Markdown table and the charts.

    Args:
        payload: The full result payload.
        output_dir: Destination directory, created when missing.

    Returns:
        Mapping from artefact kind to the path written.

    Raises:
        OSError: If the directory or the JSON file cannot be written. The JSON
            is the primary artefact -- losing it silently would waste the run.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "ocr_benchmark.json"
    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    written: dict[str, Path] = {"json": json_path}

    markdown_path = output_dir / "ocr_benchmark.md"
    try:
        markdown_path.write_text(_markdown_report(payload), encoding="utf-8")
        written["markdown"] = markdown_path
    except OSError as error:
        LOGGER.error("Could not write the Markdown report: %s", error)

    for index, chart in enumerate(_write_charts(payload, output_dir)):
        written[f"chart_{index}"] = chart
    return written


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line parser.

    Returns:
        The configured :class:`argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(
        prog="python -m ai.evaluation.benchmark_ocr",
        description=(
            "Measure OCR accuracy and CPU latency on hand-labelled plate crops. "
            "Reports full-string accuracy before and after normalisation as two "
            "separate figures, and breaks the result down by one-line and "
            "two-line plates."
        ),
        epilog=(
            "Run with the OCR virtual environment (.venv-ocr), the only one that "
            "carries PaddleOCR:\n"
            "  .venv-ocr/Scripts/python -m ai.evaluation.benchmark_ocr\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--labels",
        default=str(DEFAULT_LABELS_PATH),
        help=f"CSV of hand-made transcriptions (default: {DEFAULT_LABELS_PATH}).",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Where the report is written (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--engine",
        default="paddleocr",
        help="OCR engine to benchmark (implemented: paddleocr).",
    )
    parser.add_argument(
        "--split",
        default=None,
        help="Only use rows whose 'split' column equals this value.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Cap on the number of crops (0 = all). Useful for a smoke run.",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=3,
        help="Discarded warm-up recognitions before timing starts (default: 3).",
    )
    parser.add_argument(
        "--no-preprocess",
        action="store_true",
        help=(
            "Disable the CLAHE/denoise chain, to measure what it contributes. "
            "Run twice and compare the two JSON files."
        ),
    )
    parser.add_argument(
        "--aspect-ratio-threshold",
        type=float,
        default=InferenceConfig().two_line_aspect_ratio_threshold,
        help=(
            "Width/height cut-off below which a crop with no labelled line "
            "count is treated as two-line (heuristic, not a legal rule)."
        ),
    )
    return parser


def _resolve(path: str | Path) -> Path:
    """Resolve a path against the repository root when it is relative.

    Args:
        path: Absolute or relative path.

    Returns:
        An absolute path.
    """
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point.

    Args:
        argv: Argument list; defaults to :data:`sys.argv`.

    Returns:
        ``0`` on success, ``1`` on a runtime failure, ``2`` when the label file
        is missing or unusable -- a distinct code, because "the labels do not
        exist yet" is an expected state of the project, not a crash.
    """
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )

    labels_path = _resolve(args.labels)
    try:
        records, skipped = load_labels(labels_path, split=args.split)
    except FileNotFoundError as error:
        LOGGER.error("%s", error)
        return 2
    except (ValueError, OSError, csv.Error) as error:
        LOGGER.error("Cannot read %s: %s", labels_path, error)
        return 2

    for row_number, reason in skipped:
        LOGGER.warning("Skipping label row %d: %s", row_number, reason)

    if not records:
        LOGGER.error(
            "No usable rows in %s%s. Nothing can be measured; add "
            "transcriptions before running the benchmark.",
            labels_path,
            f" for split {args.split!r}" if args.split else "",
        )
        return 2

    if args.limit > 0:
        records = records[: args.limit]

    LOGGER.info("=" * 78)
    LOGGER.info("OCR benchmark -- measured on THIS machine")
    LOGGER.info("=" * 78)
    LOGGER.info("Labels        : %s", labels_path)
    LOGGER.info("Crops         : %d (%d row(s) skipped)", len(records), len(skipped))
    LOGGER.info("Engine        : %s", args.engine)
    LOGGER.info("Pre-processing: %s", "off" if args.no_preprocess else "on")

    config = InferenceConfig(two_line_aspect_ratio_threshold=args.aspect_ratio_threshold)
    try:
        recognizer = build_recognizer(args.engine, config, preprocess=not args.no_preprocess)
    except ValueError as error:
        LOGGER.error("%s", error)
        return 2

    normalizer = VietnamesePlateNormalizer()
    started = time.perf_counter()
    try:
        outcome = run_benchmark(
            records,
            recognizer,
            normalizer,
            args.aspect_ratio_threshold,
            warmup=args.warmup,
        )
    except ImportError as error:
        LOGGER.error("A required package is missing: %s", error)
        return 1
    except ALPRError as error:
        LOGGER.error("The OCR stage could not be run: %s", error)
        return 1
    wall_clock = time.perf_counter() - started

    outcome.skipped.extend(skipped)
    if not outcome.samples:
        LOGGER.error("Every crop failed to load; no measurement was produced.")
        return 1

    summary = summarize(outcome)
    payload: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "engine": outcome.engine_name,
        "environment": _environment_info(),
        "settings": {
            "labels_path": str(labels_path),
            "split": args.split,
            "limit": args.limit or None,
            "preprocess": not args.no_preprocess,
            "warmup": args.warmup,
            "aspect_ratio_threshold": args.aspect_ratio_threshold,
            "wall_clock_seconds": round(wall_clock, 2),
        },
        "summary": summary,
        "confusion_matrix": build_confusion_matrix(outcome.samples),
        "confusion_matrix_post_norm": build_confusion_matrix(outcome.samples, use_post_norm=True),
        "skipped": [
            {"row": row_number, "reason": reason} for row_number, reason in outcome.skipped
        ],
        "samples": [asdict(sample) for sample in outcome.samples],
    }

    overall = summary["overall"]
    one_line = summary["by_line_count"]["one_line"]
    two_line = summary["by_line_count"]["two_line"]
    LOGGER.info("-" * 78)
    LOGGER.info("Crops measured           : %d", overall["count"])
    LOGGER.info(
        "Exact match, pre-norm    : %s   (NFR-A5)",
        _format_percent(overall["exact_pre_norm"]),
    )
    LOGGER.info(
        "Exact match, post-norm   : %s   (NFR-A6)",
        _format_percent(overall["exact_post_norm"]),
    )
    LOGGER.info(
        "Post-processing gain     : %+.1f points  <-- the Phase 4 headline number",
        overall["postprocessing_gain"] * 100,
    )
    LOGGER.info(
        "Character accuracy       : %s -> %s",
        _format_percent(overall["char_accuracy_pre_norm"]),
        _format_percent(overall["char_accuracy_post_norm"]),
    )
    LOGGER.info(
        "One-line  (n=%d)          : %s post-norm",
        one_line["count"],
        _format_percent(one_line["exact_post_norm"]),
    )
    LOGGER.info(
        "Two-line  (n=%d)          : %s post-norm   <-- risk R-04",
        two_line["count"],
        _format_percent(two_line["exact_post_norm"]),
    )
    latency = summary["latency"]
    LOGGER.info(
        "Latency p50/p95/p99      : %.1f / %.1f / %.1f ms",
        latency["p50_ms"],
        latency["p95_ms"],
        latency["p99_ms"],
    )
    LOGGER.info("-" * 78)

    output_dir = _resolve(args.output_dir)
    try:
        written = write_reports(payload, output_dir)
    except OSError as error:
        LOGGER.error("Cannot write the report into %s: %s", output_dir, error)
        return 1
    for kind, path in written.items():
        LOGGER.info("  %-10s %s", kind, path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
