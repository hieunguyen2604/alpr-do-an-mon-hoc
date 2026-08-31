"""Measure OCR and end-to-end plate-reading accuracy metrics (NFR-A4 through NFR-A8)."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import platform
import statistics
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Sequence

import cv2
import numpy as np

from ai.evaluation.benchmark_ocr import align, build_confusion_matrix
from ai.inference.config import PROJECT_ROOT, InferenceConfig
from ai.inference.exceptions import ALPRError
from ai.inference.normalizer import VietnamesePlateNormalizer
from ai.inference.pipeline import (
    rescue_two_line_upper,
    retry_skewed_variants,
    should_rescue_two_line,
    should_retry_skewed,
)
from ai.inference.plate_color import classify_plate_color
from ai.inference.plate_rules import TO_DIGIT, TO_LETTER, clean_text
from ai.inference.recognizer import PaddleOcrRecognizer
from ai.inference.types import PlateRecognition

__all__ = [
    "CANONICAL_ASPECT_RATIO",
    "DEFAULT_LABELS_PATH",
    "DEFAULT_OUTPUT_PATH",
    "Sample",
    "restore_aspect_ratio",
    "corpus_cer",
    "classify_error",
    "accuracy_block",
    "measure_crops",
    "measure_end_to_end",
    "confusion_recommendations",
    "main",
]

LOGGER = logging.getLogger("ai.evaluation.ocr_accuracy")

CANONICAL_ASPECT_RATIO: Final[dict[int, float]] = {1: 4.727, 2: 1.357}
"""Width/height a plate crop is reshaped to, per line count.

Straight from QCVN 08:2024/BCA: the long car plate is 110 x 520 mm (4.727) and
the motorcycle plate is 140 x 190 mm (1.357). Applied only because the label
corpus was exported as squares; see the module docstring.
"""

DEFAULT_LABELS_PATH: Final[Path] = PROJECT_ROOT / "datasets" / "annotations" / "plate_labels.csv"
DEFAULT_OUTPUT_PATH: Final[Path] = PROJECT_ROOT / "docs" / "reports" / "04-ocr-accuracy.json"
DEFAULT_FIGURE_DIR: Final[Path] = PROJECT_ROOT / "docs" / "reports" / "figures"
DEFAULT_ERROR_DIR: Final[Path] = PROJECT_ROOT / "docs" / "reports" / "04-ocr-errors"

TARGETS: Final[dict[str, tuple[float, float]]] = {
    "NFR-A4": (0.95, 0.92),
    "NFR-A5": (0.85, 0.80),
    "NFR-A6": (0.90, 0.85),
    "NFR-A7": (0.88, 0.82),
}
"""``(target, minimum)`` per requirement, copied from
``docs/00-requirements/non-functional-requirements.md``."""

ERROR_CLASSES: Final[tuple[str, ...]] = (
    "correct",
    "empty_read",
    "substitution",
    "missing_chars",
    "extra_chars",
    "transposition",
    "mixed",
)


@dataclass(slots=True)
class Sample:
    """One labelled crop, measured through both paths.

    Attributes:
        image_path: Absolute path to the crop.
        truth: Cleaned ground-truth plate string.
        line_count: ``1`` or ``2``, from the label -- never estimated, because
            the corpus geometry makes estimation impossible.
        source_dataset: Which Roboflow dataset the crop came from.
        split: The Roboflow split recorded for the crop.
        raw_ocr_text: Engine output after case folding and separator stripping.
            This is the NFR-A5 string.
        plate_number: Normalised output. This is the NFR-A6 string.
        is_valid_format: Whether the normalised string matched a civil pattern.
        confidence: Aggregated OCR confidence.
        ocr_ms: Wall-clock recognition time for the crop path.
        e2e_text: Normalised plate string produced by the full pipeline on the
            aspect-repaired image, or ``""`` when the detector found nothing.
        e2e_detected: Whether the detector produced at least one box.
        e2e_ms: Wall-clock time for the end-to-end path.
        e2e_raw_text: The same pipeline run on the **unrepaired** square image,
            or ``None`` when that pass was not run.
        e2e_raw_detected: Whether the detector fired on the unrepaired image.
        no_repair_text: Normalised output when the aspect-ratio repair is
            skipped -- the ablation of caveat 1.
        rescued_upper_line: Whether the two-line upper-half rescue supplied the
            final answer. Recorded per sample so the contribution of that step
            can be reported separately instead of being folded silently into
            NFR-A6.
        retried_skewed: Whether the failure-retry ladder
            (:func:`~ai.inference.pipeline.retry_skewed_variants`) supplied the
            final answer. Recorded for the same reason as
            :attr:`rescued_upper_line`, and because the ladder is the most
            expensive rung in the chain -- its cost is only justifiable against
            a measured contribution.
        error: Message when a stage raised, else ``None``.
    """

    image_path: str
    truth: str
    line_count: int
    source_dataset: str
    split: str
    raw_ocr_text: str = ""
    plate_number: str = ""
    is_valid_format: bool = False
    confidence: float = 0.0
    ocr_ms: float = 0.0
    e2e_text: str = ""
    e2e_detected: bool = False
    e2e_ms: float = 0.0
    e2e_raw_text: str | None = None
    e2e_raw_detected: bool = False
    no_repair_text: str | None = None
    rescued_upper_line: bool = False
    retried_skewed: bool = False
    error: str | None = None


# --- Geometry repair ---


def restore_aspect_ratio(image: np.ndarray, line_count: int) -> np.ndarray:
    """Reshape a square-exported plate crop to a physically plausible ratio.

    The Roboflow OCR exports stretch every crop onto a square canvas, which
    destroys the aspect ratio the pipeline uses to tell a one-line plate from a
    two-line one. Reshaping to the regulation ratio for the *labelled* line
    count restores that signal.

    Only the width is changed; the height, and therefore the vertical sampling
    of the glyphs, is left alone.

    Args:
        image: The crop, BGR or grayscale.
        line_count: ``1`` or ``2``. Anything else leaves the image untouched,
            so an unexpected label degrades to a no-op rather than an
            exception.

    Returns:
        The reshaped crop, or ``image`` itself when no ratio is known.
    """
    ratio = CANONICAL_ASPECT_RATIO.get(line_count)
    if ratio is None:
        return image
    height = image.shape[0]
    width = max(8, int(round(height * ratio)))
    interpolation = cv2.INTER_CUBIC if width > image.shape[1] else cv2.INTER_AREA
    return cv2.resize(image, (width, height), interpolation=interpolation)


# --- Metrics ---


def corpus_cer(pairs: Sequence[tuple[str, str]]) -> float:
    """Compute the corpus-level character error rate.

    Args:
        pairs: ``(truth, prediction)`` pairs.

    Returns:
        Total edit distance divided by total reference length. ``0.0`` when the
        corpus is empty or carries no reference characters.
    """
    distance = 0
    length = 0
    for truth, prediction in pairs:
        distance += sum(1 for operation, _, _ in align(truth, prediction) if operation != "equal")
        length += len(truth)
    return distance / length if length else 0.0


def classify_error(truth: str, prediction: str) -> str:
    """Place a misread into exactly one error class.

    The classes map onto distinct root causes, which is what makes the taxonomy
    actionable: a substitution is a glyph problem, a missing character is a
    framing or split problem, and a transposition on a two-line plate is the
    signature of the halves being merged in the wrong order (risk R-04).

    Args:
        truth: Ground-truth string.
        prediction: Predicted string.

    Returns:
        One of :data:`ERROR_CLASSES`.

    Examples:
        >>> classify_error("30A1234", "30A1234")
        'correct'
        >>> classify_error("30A1234", "3OA1234")
        'substitution'
        >>> classify_error("30A1234", "")
        'empty_read'
    """
    if truth == prediction:
        return "correct"
    if not prediction:
        return "empty_read"
    if sorted(truth) == sorted(prediction):
        return "transposition"

    operations = Counter(
        operation for operation, _, _ in align(truth, prediction) if operation != "equal"
    )
    present = [name for name in ("substitute", "delete", "insert") if operations[name]]
    if len(present) > 1:
        return "mixed"
    if present == ["substitute"]:
        return "substitution"
    if present == ["delete"]:
        return "missing_chars"
    return "extra_chars"


def accuracy_block(samples: Sequence[Sample]) -> dict[str, Any]:
    """Aggregate every accuracy figure over one group of samples.

    Args:
        samples: The group. May be empty, in which case ``count`` is ``0`` and
            every rate is ``None`` -- not ``0.0``, because "no data" and "zero
            per cent" are different statements and the report must not blur
            them.

    Returns:
        Mapping carrying the NFR-A4 to NFR-A7 figures for this group.
    """
    count = len(samples)
    if count == 0:
        return {"count": 0}

    a5_hits = sum(1 for s in samples if s.raw_ocr_text == s.truth)
    a6_hits = sum(1 for s in samples if s.plate_number == s.truth)
    measured_e2e = [s for s in samples if s.e2e_ms > 0.0]
    a7_hits = sum(1 for s in measured_e2e if s.e2e_text == s.truth)

    cer_pre = corpus_cer([(s.truth, s.raw_ocr_text) for s in samples])
    cer_post = corpus_cer([(s.truth, s.plate_number) for s in samples])

    block: dict[str, Any] = {
        "count": count,
        # NFR-A4
        "char_accuracy_pre_norm": round(1.0 - cer_pre, 4),
        "char_accuracy_post_norm": round(1.0 - cer_post, 4),
        "cer_pre_norm": round(cer_pre, 4),
        "cer_post_norm": round(cer_post, 4),
        "mean_per_sample_cer_post_norm": round(
            statistics.fmean(corpus_cer([(s.truth, s.plate_number)]) for s in samples),
            4,
        ),
        # NFR-A5 / NFR-A6
        "exact_pre_norm": round(a5_hits / count, 4),
        "exact_post_norm": round(a6_hits / count, 4),
        "postprocessing_gain_points": round((a6_hits - a5_hits) / count * 100, 2),
        "postprocessing_fixed": sum(
            1 for s in samples if s.plate_number == s.truth and s.raw_ocr_text != s.truth
        ),
        "postprocessing_broke": sum(
            1 for s in samples if s.raw_ocr_text == s.truth and s.plate_number != s.truth
        ),
        # Diagnostics
        "valid_format_rate": round(sum(1 for s in samples if s.is_valid_format) / count, 4),
        "empty_read_rate": round(sum(1 for s in samples if not s.raw_ocr_text) / count, 4),
        "mean_confidence": round(statistics.fmean(s.confidence for s in samples), 4),
        "error_classes": {
            name: sum(1 for s in samples if classify_error(s.truth, s.plate_number) == name)
            for name in ERROR_CLASSES
        },
    }

    if measured_e2e:
        block["e2e"] = {
            "count": len(measured_e2e),
            "exact": round(a7_hits / len(measured_e2e), 4),
            "detection_rate": round(
                sum(1 for s in measured_e2e if s.e2e_detected) / len(measured_e2e), 4
            ),
            "char_accuracy": round(
                1.0 - corpus_cer([(s.truth, s.e2e_text) for s in measured_e2e]), 4
            ),
        }
        # Tach 'detector khong tim thay' khoi 'tim thay nhung doc sai' — thieu no
        # thi con so tong khong quy duoc ve tang nao.
        detected = [s for s in measured_e2e if s.e2e_detected]
        if detected:
            block["e2e"]["exact_given_detected"] = round(
                sum(1 for s in detected if s.e2e_text == s.truth) / len(detected), 4
            )
            block["e2e"]["missed_by_detector"] = len(measured_e2e) - len(detected)
        unrepaired = [s for s in measured_e2e if s.e2e_raw_text is not None]
        if unrepaired:
            block["e2e"]["unrepaired_input"] = {
                "count": len(unrepaired),
                "exact": round(
                    sum(1 for s in unrepaired if s.e2e_raw_text == s.truth) / len(unrepaired),
                    4,
                ),
                "detection_rate": round(
                    sum(1 for s in unrepaired if s.e2e_raw_detected) / len(unrepaired),
                    4,
                ),
            }
    return block


def _percentile(values: Sequence[float], fraction: float) -> float:
    """Nearest-rank percentile of an unsorted sequence.

    Args:
        values: The values. Must not be empty.
        fraction: Percentile as a fraction in ``(0, 1]``.

    Returns:
        A value that was genuinely observed.
    """
    ordered = sorted(values)
    rank = max(1, min(len(ordered), int(round(fraction * len(ordered)))))
    return ordered[rank - 1]


# --- Label loading ---


def _load_labels(path: Path, limit: int = 0) -> list[Sample]:
    """Read the evaluation label file into unmeasured samples.

    Args:
        path: CSV produced by ``scripts/dataset/build_plate_labels.py``.
        limit: Cap on the number of rows kept (``0`` = all). The cap is applied
            after a deterministic shuffle so a smoke run is not biased towards
            whichever dataset happens to sort first.

    Returns:
        Samples with only the label fields populated.

    Raises:
        FileNotFoundError: If the label file is missing.
    """
    if not path.is_file():
        raise FileNotFoundError(
            f"Label file not found: {path}\n"
            "Generate it first:  python scripts/dataset/build_plate_labels.py"
        )

    samples: list[Sample] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            image_path = (row.get("image_path") or "").strip()
            truth = clean_text((row.get("plate_text") or "").strip())
            try:
                line_count = int((row.get("line_count") or "0").strip())
            except ValueError:
                continue
            if not image_path or not truth or line_count not in (1, 2):
                continue
            samples.append(
                Sample(
                    image_path=image_path,
                    truth=truth,
                    line_count=line_count,
                    source_dataset=(row.get("source_dataset") or "").strip(),
                    split=(row.get("split") or "").strip(),
                )
            )

    if limit and limit < len(samples):
        import random

        random.Random(20260719).shuffle(samples)
        samples = samples[:limit]
    return samples


# --- Measurement passes ---


def _crop_color_name(crop: np.ndarray) -> str:
    """Return the crop's background colour the way the pipeline sees it.

    The retry ladder refuses to upgrade a read off a red crop, because red is
    an army plate and no army plate may be turned into a valid civil string.
    Measuring without that gate would credit the ladder with recoveries the
    deployed system refuses to make.

    Args:
        crop: The plate image, BGR.

    Returns:
        The colour name, or ``""`` when classification fails -- a failure here
        must not abort a measurement run.
    """
    try:
        color = classify_plate_color(crop)
    except ALPRError:
        return ""
    return color.color.value if color is not None else ""


def measure_crops(
    samples: Sequence[Sample],
    recognizer: PaddleOcrRecognizer,
    normalizer: VietnamesePlateNormalizer,
    ablate_repair: bool = True,
) -> None:
    """Run the crop path (NFR-A4 to NFR-A6) over every sample, in place.

    A crop the engine cannot read is recorded with an empty string and counted
    as a failure. Skipping it would make the accuracy figure describe only the
    images that happened to work.

    Args:
        samples: Samples to fill in. Mutated.
        recognizer: The OCR engine under test.
        normalizer: The post-processing stage under test.
        ablate_repair: Also run each crop without the aspect-ratio repair, to
            quantify what the repair is worth. Roughly doubles the runtime.
    """
    total = len(samples)
    for index, sample in enumerate(samples, start=1):
        if index % 100 == 0 or index == total:
            LOGGER.info("  OCR %d/%d", index, total)

        image = cv2.imread(sample.image_path)
        if image is None:
            sample.error = f"cannot decode image: {sample.image_path}"
            continue

        repaired = restore_aspect_ratio(image, sample.line_count)
        started = time.perf_counter()
        try:
            recognition = recognizer.recognize(repaired)
            sample.raw_ocr_text = clean_text(recognition.raw_text)
            sample.confidence = round(recognition.confidence, 4)
        except ALPRError as error:
            sample.error = f"{type(error).__name__}: {error}"
        sample.ocr_ms = round((time.perf_counter() - started) * 1000.0, 3)

        outcome = normalizer.normalize_detailed(sample.raw_ocr_text, line_count=sample.line_count)
        sample.plate_number = outcome.text
        sample.is_valid_format = outcome.is_valid_format

        # Cung ham rescue ma pipeline goi: do thieu no la cong bo so cho mot duong
        # chay ngan hon ban giao hang (~2 diem tren bien hai dong).
        candidate = PlateRecognition(
            text=outcome.text,
            raw_text=sample.raw_ocr_text,
            confidence=sample.confidence,
            line_count=sample.line_count,
            is_valid_format=outcome.is_valid_format,
        )
        color_name = _crop_color_name(repaired)
        if should_rescue_two_line(candidate):
            rescued = rescue_two_line_upper(
                recognizer, normalizer, repaired, candidate, color=color_name
            )
            if rescued.is_valid_format:
                sample.plate_number = rescued.text
                sample.is_valid_format = True
                sample.rescued_upper_line = True
                candidate = rescued

        # Bac thang thu lai, dung vi tri va dieu kien nhu ALPRPipeline._process_one
        # — thieu no thi A4/A5/A6 mo ta mot pipeline ngan hon hai bac.
        if recognizer.config.rectify_enabled and should_retry_skewed(candidate):
            retried = retry_skewed_variants(
                recognizer, normalizer, repaired, candidate, color=color_name
            )
            if retried.is_valid_format:
                sample.plate_number = retried.text
                sample.is_valid_format = True
                sample.retried_skewed = True

        if ablate_repair:
            try:
                bare = recognizer.recognize(image)
                sample.no_repair_text = normalizer.normalize_detailed(
                    clean_text(bare.raw_text), line_count=sample.line_count
                ).text
            except ALPRError:
                sample.no_repair_text = ""


def _run_pipeline(
    image: np.ndarray,
    detector: Any,
    recognizer: PaddleOcrRecognizer,
    normalizer: VietnamesePlateNormalizer,
) -> tuple[str, bool]:
    """Run detect, crop, recognise and normalise over one image.

    Everything after the input image is blind: the line count comes from the
    detected box's own aspect ratio, exactly as in deployment. Nothing here
    consults the label.

    Args:
        image: The image to process, BGR.
        detector: A :class:`~ai.inference.detector.YoloPlateDetector`.
        recognizer: The OCR engine.
        normalizer: The post-processing stage.

    Returns:
        A ``(plate_string, detected)`` pair. The string is empty when the
        detector found nothing or the crop could not be read -- both are
        end-to-end failures and are counted as such.
    """
    try:
        detections = detector.detect(image)
    except ALPRError as error:
        LOGGER.warning("Detection failed: %s", error)
        return "", False

    if not detections:
        return "", False

    best = max(detections, key=lambda detection: detection.confidence)
    x1, y1, x2, y2 = best.bbox.to_xyxy()
    crop = image[y1:y2, x1:x2]
    if not crop.size:
        return "", True

    try:
        recognition = recognizer.recognize(crop)
    except ALPRError as error:
        LOGGER.warning("E2E OCR failed: %s", error)
        return "", True

    outcome = normalizer.normalize_detailed(
        clean_text(recognition.raw_text), line_count=recognition.line_count
    )

    # So dau-cuoi phai do san pham dau-cuoi. Dau hieu tung lo: A6 tang +1,75 ma
    # A7 dung yen — mot buoc cai thien nhan dang khong the khong cham chi so
    # chua nhan dang.
    candidate = PlateRecognition(
        text=outcome.text,
        raw_text=clean_text(recognition.raw_text),
        confidence=recognition.confidence,
        line_count=recognition.line_count,
        is_valid_format=outcome.is_valid_format,
    )
    color_name = _crop_color_name(crop)
    if should_rescue_two_line(candidate):
        rescued = rescue_two_line_upper(
            recognizer, normalizer, crop, candidate, color=color_name
        )
        if rescued.is_valid_format:
            return rescued.text, True
        candidate = rescued

    # Same omission as in measure_crops, same fix: the ladder is part of the
    # product, so it is part of the end-to-end number.
    if recognizer.config.rectify_enabled and should_retry_skewed(candidate):
        retried = retry_skewed_variants(
            recognizer, normalizer, crop, candidate, color=color_name
        )
        if retried.is_valid_format:
            return retried.text, True

    return candidate.text, True


def measure_end_to_end(
    samples: Sequence[Sample],
    detector: Any,
    recognizer: PaddleOcrRecognizer,
    normalizer: VietnamesePlateNormalizer,
    also_unrepaired: bool = True,
) -> None:
    """Run the full detect-crop-recognise-normalise chain (NFR-A7), in place.

    Two passes, because one number would be misleading either way:

    ``e2e_text``
        The pipeline over the **aspect-repaired** image. The repair is applied
        to the *input photograph*, undoing the square export the label corpus
        was published with; everything downstream -- localisation, cropping,
        line-count estimation, recognition, normalisation -- then runs blind.
        This is the figure NFR-A7 is judged on.

    ``e2e_raw_text``
        The pipeline over the image exactly as the dataset ships it. This
        measures the square export, not the system, and is reported only so
        that the size of the artefact is on the record rather than asserted.

    A plate the detector misses is recorded with an empty string and
    ``detected=False``. A miss is an end-to-end failure and must be counted as
    one; excluding it would turn NFR-A7 into a second measurement of the OCR
    stage.

    Args:
        samples: Samples to fill in. Mutated.
        detector: A :class:`~ai.inference.detector.YoloPlateDetector`.
        recognizer: The OCR engine.
        normalizer: The post-processing stage.
        also_unrepaired: Whether to run the second, unrepaired pass.
    """
    total = len(samples)
    for index, sample in enumerate(samples, start=1):
        if index % 100 == 0 or index == total:
            LOGGER.info("  E2E %d/%d", index, total)

        image = cv2.imread(sample.image_path)
        if image is None:
            continue

        started = time.perf_counter()
        repaired = restore_aspect_ratio(image, sample.line_count)
        sample.e2e_text, sample.e2e_detected = _run_pipeline(
            repaired, detector, recognizer, normalizer
        )
        sample.e2e_ms = round((time.perf_counter() - started) * 1000.0, 3)

        if also_unrepaired:
            sample.e2e_raw_text, sample.e2e_raw_detected = _run_pipeline(
                image, detector, recognizer, normalizer
            )


# --- Confusion table recommendations ---


def confusion_recommendations(confusion: dict[str, Any]) -> dict[str, Any]:
    """Compare the measured confusions against the shape-based repair tables.

    ``docs/reports/01-vn-plate-standards.md`` states that
    :data:`~ai.inference.plate_rules.TO_DIGIT` and
    :data:`~ai.inference.plate_rules.TO_LETTER` were derived from glyph-shape
    reasoning, not from measurement. This function is the confrontation: which
    entries the data supports, which it does not exercise, and which frequent
    confusions the tables do not cover at all.

    Args:
        confusion: Payload from
            :func:`~ai.evaluation.benchmark_ocr.build_confusion_matrix`.

    Returns:
        Mapping with ``confirmed``, ``unobserved`` and ``missing_from_tables``.
        ``missing_from_tables`` lists only *directional* confusions -- true
        character ``t`` read as ``p`` -- since that is the direction a repair
        table has to invert.
    """
    observed: dict[tuple[str, str], int] = {
        (item["true"], item["predicted"]): item["count"] for item in confusion["top_confusions"]
    }
    charset = confusion["charset"]
    matrix = confusion["matrix"]
    for i, true_char in enumerate(charset):
        for j, predicted in enumerate(charset):
            if i != j and matrix[i][j] > 0:
                observed[(true_char, predicted)] = matrix[i][j]

    # A TO_DIGIT entry {"O": "0"} claims "a character read as O at a digit
    # position was really a 0", i.e. the confusion truth=0 -> predicted=O.
    tables = [("TO_DIGIT", TO_DIGIT), ("TO_LETTER", TO_LETTER)]
    confirmed: list[dict[str, Any]] = []
    unobserved: list[dict[str, Any]] = []
    covered: set[tuple[str, str]] = set()

    for table_name, table in tables:
        for wrong, right in table.items():
            covered.add((right, wrong))
            count = observed.get((right, wrong), 0)
            entry = {
                "table": table_name,
                "rule": f"{wrong} -> {right}",
                "observed_confusions": count,
            }
            (confirmed if count > 0 else unobserved).append(entry)

    missing = [
        {"true": true_char, "predicted": predicted, "count": count}
        for (true_char, predicted), count in sorted(
            observed.items(), key=lambda item: item[1], reverse=True
        )
        if (true_char, predicted) not in covered
    ][:20]

    confirmed.sort(key=lambda item: item["observed_confusions"], reverse=True)
    return {
        "confirmed": confirmed,
        "unobserved": unobserved,
        "missing_from_tables": missing,
        "proposed_updates": propose_table_updates(confusion),
    }


def propose_table_updates(confusion: dict[str, Any]) -> dict[str, Any]:
    """Derive what each repair table *should* map, from the measured data.

    :func:`confusion_recommendations` only says whether an existing rule was
    ever exercised. This answers the sharper question the tables actually pose:
    **given that the engine emitted character ``p`` at a position where ``p`` is
    illegal, which legal character was most often the truth?** That is a
    maximum-likelihood repair, and it is decidable straight from the matrix.

    Candidate targets are constrained to what the position permits, which is
    what makes the answer usable:

    * at a ``D`` position the target must be a digit;
    * at an ``L`` position it must be a letter that is legal in a serial --
      ``I``, ``J``, ``O``, ``Q`` and ``W`` are excluded by the plate standard,
      so proposing them would produce a string no pattern can match.

    Args:
        confusion: Payload from
            :func:`~ai.evaluation.benchmark_ocr.build_confusion_matrix`.

    Returns:
        Mapping with one entry per table. Each entry lists, per emitted
        character, the current rule, the best-supported target, the counts
        behind both, and whether the data ``agrees``, asks to ``change`` the
        rule, or proposes to ``add`` one that does not exist yet.

        Nothing here is applied automatically. Changing a repair table changes
        NFR-A6, so the proposal has to be adopted deliberately and the accuracy
        re-measured afterwards -- otherwise the reported gain would describe
        rules that were themselves fitted to the evaluation set.
    """
    charset: str = confusion["charset"]
    matrix = confusion["matrix"]
    index = {char: i for i, char in enumerate(charset)}

    digits = [c for c in charset if c.isdigit()]
    legal_letters = [c for c in charset if c.isalpha() and c not in "IJOQW"]

    def best_target(predicted: str, candidates: Sequence[str]) -> tuple[str | None, int]:
        """Return the candidate most often mistaken for ``predicted``.

        Args:
            predicted: The character the engine emitted.
            candidates: Legal true characters for the position.

        Returns:
            A ``(character, count)`` pair, or ``(None, 0)`` when never observed.
        """
        column = index[predicted]
        scored = [(candidate, matrix[index[candidate]][column]) for candidate in candidates]
        scored = [item for item in scored if item[1] > 0]
        if not scored:
            return None, 0
        return max(scored, key=lambda item: item[1])

    proposals: dict[str, list[dict[str, Any]]] = {}
    for table_name, table, emitted_class, candidates in (
        ("TO_DIGIT", TO_DIGIT, str.isalpha, digits),
        ("TO_LETTER", TO_LETTER, str.isdigit, legal_letters),
    ):
        rows: list[dict[str, Any]] = []
        for predicted in charset:
            if not emitted_class(predicted):
                continue
            target, support = best_target(predicted, candidates)
            if target is None:
                continue
            current = table.get(predicted)
            current_support = 0
            if current is not None:
                current_support = matrix[index[current]][index[predicted]]
            if current is None:
                action = "add"
            elif current == target:
                action = "agree"
            else:
                action = "change"
            rows.append(
                {
                    "emitted": predicted,
                    "current_target": current,
                    "current_support": current_support,
                    "proposed_target": target,
                    "proposed_support": support,
                    "action": action,
                }
            )
        rows.sort(key=lambda row: row["proposed_support"], reverse=True)
        proposals[table_name] = rows

    return {
        "note": (
            "Suy ra tu ma tran nham lan do that: voi moi ky tu engine doc ra tai "
            "vi tri KHONG hop le cho no, ky tu that nao xuat hien nhieu nhat. "
            "CHUA ap dung vao plate_rules.py -- doi bang se lam thay doi NFR-A6, "
            "nen phai ap dung co chu dich va DO LAI, neu khong con so bao cao se "
            "la ket qua cua luat duoc khop tren chinh tap danh gia."
        ),
        **proposals,
    }


# --- Error export ---


def _export_errors(
    samples: Sequence[Sample], destination: Path, per_class: int = 8
) -> dict[str, int]:
    """Copy a handful of failing crops per error class for visual review.

    An aggregate figure says how often the system is wrong; only looking at the
    images says why. Each exported file is annotated in its own name with the
    truth and the prediction, so a directory listing is already a summary.

    Args:
        samples: All measured samples.
        destination: Directory to write into; created, and cleared of previous
            exports for the same classes.
        per_class: How many crops to export per class.

    Returns:
        Number of files written per class.
    """
    grouped: dict[str, list[Sample]] = defaultdict(list)
    for sample in samples:
        error_class = classify_error(sample.truth, sample.plate_number)
        if error_class != "correct":
            grouped[error_class].append(sample)

    written: dict[str, int] = {}
    for error_class, group in grouped.items():
        folder = destination / error_class
        folder.mkdir(parents=True, exist_ok=True)
        count = 0
        for ordinal, sample in enumerate(group[:per_class], start=1):
            image = cv2.imread(sample.image_path)
            if image is None:
                continue
            image = restore_aspect_ratio(image, sample.line_count)
            predicted = sample.plate_number or "EMPTY"
            # The ordinal keeps two samples that share a truth/prediction pair
            # from writing to the same file. Without it the exported count and
            # the files on disk disagree, and the report says so wrongly.
            name = (
                f"{ordinal:02d}_{sample.line_count}line" f"_true-{sample.truth}_got-{predicted}.jpg"
            )
            safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)
            if cv2.imwrite(str(folder / safe), image):
                count += 1
        written[error_class] = count
    return written


# --- Charts ---


def _write_charts(
    payload: dict[str, Any], samples: Sequence[Sample], figure_dir: Path
) -> list[str]:
    """Render the report's PNG charts.

    Charts are best-effort: a Matplotlib problem must not lose a measurement
    whose numbers are already in the JSON.

    Args:
        payload: The finished JSON payload.
        samples: All measured samples.
        figure_dir: Destination directory.

    Returns:
        Names of the files actually written.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as error:
        LOGGER.warning("Charts skipped, Matplotlib unavailable: %s", error)
        return []

    figure_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    overall = payload["by_line_count"]["overall"]
    one = payload["by_line_count"]["one_line"]
    two = payload["by_line_count"]["two_line"]

    try:
        groups = ["Tong the", "1 dong", "2 dong"]
        blocks = [overall, one, two]
        pre = [b.get("exact_pre_norm", 0.0) * 100 for b in blocks]
        post = [b.get("exact_post_norm", 0.0) * 100 for b in blocks]
        e2e = [b.get("e2e", {}).get("exact", 0.0) * 100 for b in blocks]
        x = np.arange(len(groups))
        w = 0.26
        fig, ax = plt.subplots(figsize=(9, 5.2))
        for offset, values, label, colour in (
            (-w, pre, "NFR-A5 truoc chuan hoa", "#8C8C8C"),
            (0.0, post, "NFR-A6 sau chuan hoa", "#4C78A8"),
            (w, e2e, "NFR-A7 E2E", "#E45756"),
        ):
            ax.bar(x + offset, values, w, label=label, color=colour)
            for xi, value in zip(x + offset, values):
                ax.text(xi, value + 1.2, f"{value:.1f}", ha="center", fontsize=8)
        ax.set_xticks(x, groups)
        ax.set_ylabel("Ty le khop chuoi tuyet doi (%)")
        ax.set_ylim(0, 105)
        ax.set_title("Do chinh xac OCR tach theo so dong (NFR-A5/A6/A7/A8)")
        ax.legend(fontsize=9)
        ax.grid(axis="y", alpha=0.3)
        fig.tight_layout()
        fig.savefig(figure_dir / "04-ocr-accuracy-by-line-count.png", dpi=150)
        plt.close(fig)
        written.append("04-ocr-accuracy-by-line-count.png")
    except Exception as error:  # noqa: BLE001
        LOGGER.warning("Accuracy chart failed: %s", error)

    try:
        charset = payload["confusion_matrix"]["charset"]
        matrix = np.asarray(payload["confusion_matrix"]["matrix"], dtype=float)
        fig, ax = plt.subplots(figsize=(11, 9.5))
        image = ax.imshow(np.log1p(matrix), cmap="viridis", aspect="auto")
        ax.set_xticks(range(len(charset)), list(charset), fontsize=7)
        ax.set_yticks(range(len(charset)), list(charset), fontsize=7)
        ax.set_xlabel("Ky tu OCR doc ra")
        ax.set_ylabel("Ky tu that")
        ax.set_title("Ma tran nham lan ky tu 36x36, do thuc nghiem (thang log(1+n))")
        fig.colorbar(image, ax=ax, label="log(1 + so lan)")
        fig.tight_layout()
        fig.savefig(figure_dir / "04-ocr-confusion-matrix.png", dpi=150)
        plt.close(fig)
        written.append("04-ocr-confusion-matrix.png")
    except Exception as error:  # noqa: BLE001
        LOGGER.warning("Confusion chart failed: %s", error)

    try:
        classes = [c for c in ERROR_CLASSES if c != "correct"]
        one_counts = [one.get("error_classes", {}).get(c, 0) for c in classes]
        two_counts = [two.get("error_classes", {}).get(c, 0) for c in classes]
        x = np.arange(len(classes))
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.bar(x - 0.2, one_counts, 0.4, label="1 dong", color="#54A24B")
        ax.bar(x + 0.2, two_counts, 0.4, label="2 dong", color="#E45756")
        ax.set_xticks(x, classes, rotation=20, ha="right")
        ax.set_ylabel("So ca")
        ax.set_title("Phan loai loi OCR sau chuan hoa")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)
        fig.tight_layout()
        fig.savefig(figure_dir / "04-ocr-error-classes.png", dpi=150)
        plt.close(fig)
        written.append("04-ocr-error-classes.png")
    except Exception as error:  # noqa: BLE001
        LOGGER.warning("Error-class chart failed: %s", error)

    try:
        top = payload["confusion_matrix"]["top_confusions"][:15]
        if top:
            labels = [f"{i['true']}->{i['predicted']}" for i in top][::-1]
            counts = [i["count"] for i in top][::-1]
            fig, ax = plt.subplots(figsize=(7.5, 6))
            ax.barh(labels, counts, color="#4C78A8")
            for i, value in enumerate(counts):
                ax.text(value, i, f" {value}", va="center", fontsize=8)
            ax.set_xlabel("So lan nham")
            ax.set_title("15 cap ky tu bi nham nhieu nhat (do thuc nghiem)")
            fig.tight_layout()
            fig.savefig(figure_dir / "04-ocr-top-confusions.png", dpi=150)
            plt.close(fig)
            written.append("04-ocr-top-confusions.png")
    except Exception as error:  # noqa: BLE001
        LOGGER.warning("Top-confusion chart failed: %s", error)

    return written


# --- Verdicts ---


def _verdict(requirement: str, value: float | None) -> dict[str, Any]:
    """State pass, marginal or fail against the requirement thresholds.

    Args:
        requirement: Key into :data:`TARGETS`.
        value: Measured value, or ``None`` when not measured.

    Returns:
        Mapping with the measured value, both thresholds and a verdict string.
        ``"khong do duoc"`` when the value is missing -- never a silent pass.
    """
    target, minimum = TARGETS[requirement]
    if value is None:
        status = "khong do duoc"
    elif value >= target:
        status = "DAT"
    elif value >= minimum:
        status = "DAT NGUONG TOI THIEU"
    else:
        status = "KHONG DAT"
    return {
        "measured": None if value is None else round(value, 4),
        "target": target,
        "minimum": minimum,
        "verdict": status,
    }


# --- Command line ---


def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line parser.

    Returns:
        The configured parser.
    """
    parser = argparse.ArgumentParser(
        prog="python -m ai.evaluation.ocr_accuracy",
        description=("Measure NFR-A4 to NFR-A8 on the reconstructed plate-string labels."),
    )
    parser.add_argument("--labels", default=str(DEFAULT_LABELS_PATH))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument("--figures", default=str(DEFAULT_FIGURE_DIR))
    parser.add_argument("--errors-dir", default=str(DEFAULT_ERROR_DIR))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--detector",
        default="runs/cpu-finetune-416/weights/best.pt",
        help="Detector weights for the NFR-A7 pass. Empty string skips E2E.",
    )
    # Mac dinh doc tu cau hinh ban giao hang, cam gan cung: do 416 khi best.pt
    # huan luyen o 640 lam ty le phat hien tut 0,8804 -> 0,6109.
    parser.add_argument(
        "--detector-imgsz", type=int, default=InferenceConfig.from_env().imgsz
    )
    parser.add_argument(
        "--e2e-limit",
        type=int,
        default=0,
        help="Cap on the E2E subset (0 = every sample).",
    )
    parser.add_argument(
        "--no-ablation",
        action="store_true",
        help="Skip the aspect-ratio-repair ablation pass (halves the runtime).",
    )
    parser.add_argument("--errors-per-class", type=int, default=8)
    parser.add_argument(
        "--reanalyse",
        action="store_true",
        help=(
            "Recompute the aggregates, the confusion matrix, the repair-table "
            "review and the charts from the per-sample records already in "
            "--output, without re-running any model. Use after extending the "
            "analysis; re-running OCR would publish different predictions."
        ),
    )
    parser.add_argument(
        "--conditions",
        default="",
        help=(
            "Free-text note about the machine's state during the run, recorded "
            "verbatim in the report. Use it whenever anything else was "
            "competing for the CPU -- a training job in another virtualenv "
            "makes every latency figure here unattributable, and a reader has "
            "no way to know that from the numbers alone."
        ),
    )
    return parser


def _reanalyse(report_path: Path, figure_dir: Path) -> int:
    """Recompute the derived sections of an existing report and rewrite it.

    Everything downstream of the per-sample records -- the aggregates, the
    confusion matrix, the repair-table review, the charts -- is a pure function
    of ``samples``. When that analysis is extended, re-running it must not mean
    re-running OCR: that would cost an hour and, worse, would publish a
    *different* set of predictions from the ones already reported.

    The measured fields are never touched.

    Args:
        report_path: An existing report written by :func:`main`.
        figure_dir: Where the charts are rewritten.

    Returns:
        ``0`` on success, ``2`` when the report is missing or carries no
        samples.
    """
    if not report_path.is_file():
        LOGGER.error("No report to reanalyse at %s", report_path)
        return 2

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    raw_samples = payload.get("samples")
    if not raw_samples:
        LOGGER.error("%s carries no per-sample records", report_path)
        return 2

    fields = {f for f in Sample.__slots__}
    samples = [Sample(**{k: v for k, v in row.items() if k in fields}) for row in raw_samples]

    one_line = [s for s in samples if s.line_count == 1]
    two_line = [s for s in samples if s.line_count == 2]
    overall = accuracy_block(samples)

    class _Shim:
        __slots__ = ("ground_truth", "pre_norm_text", "post_norm_text")

        def __init__(self, sample: Sample) -> None:
            self.ground_truth = sample.truth
            self.pre_norm_text = sample.raw_ocr_text
            self.post_norm_text = sample.plate_number

    shims = [_Shim(s) for s in samples]
    confusion = build_confusion_matrix(shims, use_post_norm=False)

    payload["by_line_count"].update(
        {
            "overall": overall,
            "one_line": accuracy_block(one_line),
            "two_line": accuracy_block(two_line),
        }
    )
    payload["confusion_matrix"] = confusion
    payload["confusion_matrix_post_norm"] = build_confusion_matrix(shims, use_post_norm=True)
    payload["plate_rules_review"] = confusion_recommendations(confusion)
    payload["reanalysed_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload["figures"] = _write_charts(payload, samples, figure_dir)
    payload["exported_error_cases"] = _export_errors(samples, DEFAULT_ERROR_DIR)

    report_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    LOGGER.info("Reanalysed %s over %d samples", report_path, len(samples))
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run every measurement and write the JSON report and the charts.

    Args:
        argv: Command-line arguments; ``sys.argv[1:]`` when omitted.

    Returns:
        ``0`` on success, ``2`` when the label file is missing.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("ai.inference").setLevel(logging.ERROR)
    args = build_parser().parse_args(argv)

    if args.reanalyse:
        return _reanalyse(Path(args.output), Path(args.figures))

    try:
        samples = _load_labels(Path(args.labels), limit=args.limit)
    except FileNotFoundError as error:
        LOGGER.error("%s", error)
        return 2
    LOGGER.info("Loaded %d labelled crops", len(samples))

    # from_env() de ALPR_RECTIFY/SR_RETRY boc tach duoc tai day — cung loi,
    # cung ngay sua voi benchmark_system.py (28/07).
    config = InferenceConfig.from_env()
    recognizer = PaddleOcrRecognizer(config)
    normalizer = VietnamesePlateNormalizer()
    recognizer.warmup()

    started = time.perf_counter()
    LOGGER.info("Pass 1/2: crop-level OCR (NFR-A4/A5/A6/A8)")
    measure_crops(samples, recognizer, normalizer, ablate_repair=not args.no_ablation)

    detector_name = None
    if args.detector:
        from ai.inference.detector import YoloPlateDetector

        weights = Path(args.detector)
        if not weights.is_absolute():
            weights = PROJECT_ROOT / weights
        e2e_config = replace(
            InferenceConfig.from_env(),
            model_path=weights,
            imgsz=args.detector_imgsz,
        )
        detector = YoloPlateDetector(e2e_config)
        detector.warmup()
        detector_name = detector.name
        subset = samples[: args.e2e_limit] if args.e2e_limit else samples
        LOGGER.info("Pass 2/2: end-to-end (NFR-A7) over %d images", len(subset))
        measure_end_to_end(
            subset,
            detector,
            recognizer,
            normalizer,
            also_unrepaired=not args.no_ablation,
        )
    else:
        LOGGER.warning("Detector not given, NFR-A7 will be reported as not measured")

    elapsed = time.perf_counter() - started

    one_line = [s for s in samples if s.line_count == 1]
    two_line = [s for s in samples if s.line_count == 2]
    overall = accuracy_block(samples)
    block_one = accuracy_block(one_line)
    block_two = accuracy_block(two_line)

    # The confusion matrix wants the benchmark's SampleResult shape.
    class _Shim:
        __slots__ = ("ground_truth", "pre_norm_text", "post_norm_text")

        def __init__(self, sample: Sample) -> None:
            self.ground_truth = sample.truth
            self.pre_norm_text = sample.raw_ocr_text
            self.post_norm_text = sample.plate_number

    shims = [_Shim(s) for s in samples]
    confusion = build_confusion_matrix(shims, use_post_norm=False)
    confusion_post = build_confusion_matrix(shims, use_post_norm=True)

    ablation = None
    measured_ablation = [s for s in samples if s.no_repair_text is not None]
    if measured_ablation:
        ablation = {
            "count": len(measured_ablation),
            "exact_post_norm_with_repair": round(
                sum(1 for s in measured_ablation if s.plate_number == s.truth)
                / len(measured_ablation),
                4,
            ),
            "exact_post_norm_without_repair": round(
                sum(1 for s in measured_ablation if s.no_repair_text == s.truth)
                / len(measured_ablation),
                4,
            ),
        }

    latencies = [s.ocr_ms for s in samples if s.ocr_ms > 0]
    e2e_latencies = [s.e2e_ms for s in samples if s.e2e_ms > 0]

    payload: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "elapsed_seconds": round(elapsed, 1),
        "environment": {
            "system": f"{platform.system()} {platform.release()}",
            "processor": platform.processor() or "unknown",
            "logical_cores": __import__("os").cpu_count(),
            "python": platform.python_version(),
            "venv": sys.prefix,
        },
        "engines": {
            "recognizer": recognizer.name,
            "normalizer": "VietnamesePlateNormalizer",
            "detector": detector_name,
            "detector_imgsz": args.detector_imgsz if detector_name else None,
        },
        "corpus": {
            "labels_path": str(Path(args.labels)),
            "count": len(samples),
            "one_line": len(one_line),
            "two_line": len(two_line),
            "by_dataset": dict(Counter(s.source_dataset for s in samples)),
            "by_split": dict(Counter(s.split or "(none)" for s in samples)),
            "provenance": (
                "Phase 2b reconstructed these strings from character-level boxes "
                "in roboflow_ocr_plate and roboflow_ocr_conversion; only rows the "
                "reconstruction validated WITHOUT the normalizer are kept, so the "
                "normalizer is not graded on labels it produced."
            ),
        },
        "requirements": {
            "NFR-A4": _verdict("NFR-A4", overall.get("char_accuracy_post_norm")),
            "NFR-A5": _verdict("NFR-A5", overall.get("exact_pre_norm")),
            "NFR-A6": _verdict("NFR-A6", overall.get("exact_post_norm")),
            "NFR-A7": {
                **_verdict("NFR-A7", overall.get("e2e", {}).get("exact")),
                "validity": "KHONG DAI DIEN",
                "validity_reason": (
                    "Con so nay do tren anh CROP bien so, khong phai anh hien "
                    "truong, vi khong bo du lieu nao trong do an co dong thoi "
                    "anh toan canh va chuoi bien so. Bo detect duoc huan luyen "
                    "tren anh giao thong day du nen mot tam anh chi co bien so "
                    "chiem gan het khung la NGOAI PHAN BO: phan lon that bai la "
                    "do detect khong bat duoc box, khong phai do OCR doc sai "
                    "(xem e2e.exact_given_detected va e2e.missed_by_detector). "
                    "Mo hinh chinh thuc best.pt dat mAP@0.5 = 0,9829 tren tap "
                    "test v3 (1.514 anh) — tuc bo phat hien hoat dong tot tren "
                    "anh hien truong; that bai o phep do A7 den tu viec dua anh "
                    "CROP vao bo phat hien, ngoai phan bo huan luyen cua no. De do NFR-A7 dung cach can gan nhan chuoi bien "
                    "so cho mot phan bo test cua yolo_v2 -- viec nay CHUA lam."
                ),
            },
        },
        "postprocessing_contribution": {
            "nfr_a5_exact_before": overall.get("exact_pre_norm"),
            "nfr_a6_exact_after": overall.get("exact_post_norm"),
            "gain_points": overall.get("postprocessing_gain_points"),
            "plates_fixed": overall.get("postprocessing_fixed"),
            "plates_broken": overall.get("postprocessing_broke"),
            "note": (
                "gain_points = (NFR-A6 - NFR-A5) x 100. plates_broken counts "
                "strings the raw engine already had right and normalisation then "
                "changed; a positive value means the rules are not loss-free."
            ),
        },
        # Tung bac cuu duoc bao nhieu bien tren ngu lieu nay — chi phi p95 cua bac
        # thang chi bien minh duoc bang con so nay.
        "recovery_contribution": {
            "rescue_upper_line_plates": sum(1 for s in samples if s.rescued_upper_line),
            "retry_ladder_plates": sum(1 for s in samples if s.retried_skewed),
            "config": {
                "rectify_enabled": config.rectify_enabled,
                "sr_retry_enabled": config.sr_retry_enabled,
            },
            "note": (
                "Counts are plates where that rung supplied the final, "
                "validating answer. Both rungs run only after a failed read and "
                "keep a result only when it validates, so neither can lower the "
                "figures above -- a zero count means no contribution, never a "
                "regression."
            ),
        },
        "by_line_count": {
            "overall": overall,
            "one_line": block_one,
            "two_line": block_two,
            "gap_points_post_norm": (
                None
                if block_one.get("count", 0) == 0 or block_two.get("count", 0) == 0
                else round(
                    (block_one["exact_post_norm"] - block_two["exact_post_norm"]) * 100,
                    2,
                )
            ),
            "reference_point": (
                "Moc tham chieu quoc te: tren bo RodoSol-ALPR (Brazil), OpenALPR "
                "dat 94,3% tren bien 1 dong so voi 45,7% tren bien 2 dong, chenh "
                "48,6 diem (Laroca et al., VISAPP 2022). Day KHONG phai so do tren "
                "du lieu Viet Nam va khong dung de so sanh truc tiep; no chi cho "
                "thay do lon cua khoang cach 1 dong / 2 dong khi khong xu ly rieng."
            ),
        },
        "latency": {
            "ocr_crop_ms": {
                "count": len(latencies),
                "mean": round(statistics.fmean(latencies), 2) if latencies else None,
                "p50": round(_percentile(latencies, 0.50), 2) if latencies else None,
                "p95": round(_percentile(latencies, 0.95), 2) if latencies else None,
            },
            "e2e_ms": {
                "count": len(e2e_latencies),
                "mean": (round(statistics.fmean(e2e_latencies), 2) if e2e_latencies else None),
                "p50": (round(_percentile(e2e_latencies, 0.50), 2) if e2e_latencies else None),
                "p95": (round(_percentile(e2e_latencies, 0.95), 2) if e2e_latencies else None),
            },
            "note": (
                "Do tren cac anh crop 640x640 cua bo nhan, KHONG phai anh hien "
                "truong. Khong dung de so sanh voi NFR-P1."
            ),
            "measurement_conditions": args.conditions or "khong ghi nhan",
        },
        "aspect_ratio_repair_ablation": ablation,
        "confusion_matrix": confusion,
        "confusion_matrix_post_norm": confusion_post,
        "plate_rules_review": confusion_recommendations(confusion),
        "caveats": [
            "Bo nhan bi PHA HUY TY LE KHUNG: ca hai bo Roboflow xuat anh crop ve "
            "khung vuong (640x640 va 416x416). Danh gia phai khoi phuc ty le "
            "chuan tu line_count cua nhan -- day la mot buoc DUNG NHAN THAT ma he "
            "thong that khong co. Muc anh huong xem aspect_ratio_repair_ablation.",
            "NFR-A7 KHONG do tren anh hien truong: khong bo du lieu nao trong do "
            "an co dong thoi anh toan canh VA chuoi bien so. Con so E2E do tren "
            "chinh cac anh crop, tuc bo detect phai tim lai bien so chiem gan het "
            "khung hinh. De hon thuc te ve bo cuc, kho hon ve do phan giai.",
            "Bu lai, NFR-A7 KHONG bi ro ri: roboflow_ocr_plate va "
            "roboflow_ocr_conversion khong nam trong merged_v2 hay bat ky split "
            "YOLO nao, nen bo detect chua tung nhin thay cac anh nay.",
            "Nhan la chuoi TAI TAO tu hop ky tu, khong phai nguoi doc tay. Sai sot "
            "cua buoc tai tao se hien ra thanh loi OCR gia.",
        ],
        "samples": [asdict(s) for s in samples],
    }

    charts = _write_charts(payload, samples, Path(args.figures))
    payload["figures"] = charts
    payload["exported_error_cases"] = _export_errors(
        samples, Path(args.errors_dir), per_class=args.errors_per_class
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    LOGGER.info("Wrote %s", output)

    for key, value in payload["requirements"].items():
        LOGGER.info("  %s: %s (%s)", key, value["measured"], value["verdict"])
    LOGGER.info(
        "  post-processing gain: %+.2f points",
        payload["postprocessing_contribution"]["gain_points"] or 0.0,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
