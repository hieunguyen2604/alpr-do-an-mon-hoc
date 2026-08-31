"""Evaluate trained YOLO11 license-plate detector on held-out splits with 1-line/2-line breakdowns (NFR-A8)."""

from __future__ import annotations

import argparse
import json
import logging
import platform
import shutil
import statistics
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Sequence

from ai.training.config import DEFAULT_MODELS_DIR, PROJECT_ROOT

__all__ = [
    "DEFAULT_AR_THRESHOLD",
    "SINGLE_LINE",
    "TWO_LINE",
    "GroundTruthBox",
    "PredictionBox",
    "compute_average_precision",
    "evaluate_group",
    "main",
]

LOGGER = logging.getLogger("ai.evaluation.evaluate")

SINGLE_LINE: Final[str] = "single_line"
TWO_LINE: Final[str] = "two_line"

# QCVN 08:2024/BCA aspect ratios: 4.727 (single line) vs 2.000 / 1.357 (two
# lines). Anything below the threshold is treated as a two-line plate. 2.5 is
# used rather than the midpoint so that the value matches
# InferenceConfig.two_line_aspect_ratio_threshold -- evaluation must classify
# plates the same way the deployed pipeline does, or the reported per-group
# accuracy would not describe the shipped system.
DEFAULT_AR_THRESHOLD: Final[float] = 2.5

DEFAULT_OUTPUT_DIR: Final[Path] = PROJECT_ROOT / "docs" / "reports"
DEFAULT_DATA_YAML: Final[Path] = PROJECT_ROOT / "datasets" / "processed" / "data.yaml"

_IMAGE_SUFFIXES: Final[frozenset[str]] = frozenset(
    {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
)

# Class-name fragments that explicitly declare the plate layout.
_SINGLE_LINE_TOKENS: Final[tuple[str, ...]] = (
    "1line",
    "1_line",
    "one_line",
    "oneline",
    "single",
    "long",
)
_TWO_LINE_TOKENS: Final[tuple[str, ...]] = (
    "2line",
    "2_line",
    "two_line",
    "twoline",
    "double",
    "square",
    "motorbike",
    "motorcycle",
)

# IoU thresholds used for the mAP@0.5:0.95 average, matching the COCO protocol.
_COCO_IOU_THRESHOLDS: Final[tuple[float, ...]] = tuple(round(0.5 + 0.05 * i, 2) for i in range(10))


# --- Data containers ---
@dataclass(slots=True)
class GroundTruthBox:
    """One annotated plate in one image.

    Attributes:
        image: Path of the image the box belongs to.
        class_id: Class index from the label file.
        xyxy: Absolute pixel coordinates ``(x1, y1, x2, y2)``.
        group: :data:`SINGLE_LINE` or :data:`TWO_LINE`.
        group_source: How :attr:`group` was decided -- ``"label"``, ``"class"``
            or ``"aspect_ratio"``. Recorded so the report states how much of the
            breakdown rests on a heuristic.
        matched: Set during matching; ``True`` once a prediction has claimed it.
    """

    image: Path
    class_id: int
    xyxy: tuple[float, float, float, float]
    group: str
    group_source: str
    matched: bool = False


@dataclass(slots=True)
class PredictionBox:
    """One detection produced by the model.

    Attributes:
        image: Path of the image the detection came from.
        class_id: Predicted class index.
        confidence: Detector confidence in ``[0, 1]``.
        xyxy: Absolute pixel coordinates ``(x1, y1, x2, y2)``.
        group: Layout group inferred from the predicted box shape; overwritten
            with the matched ground-truth group during matching, because the
            ground-truth label is the more reliable assignment when available.
    """

    image: Path
    class_id: int
    confidence: float
    xyxy: tuple[float, float, float, float]
    group: str


@dataclass(slots=True)
class GroupMetrics:
    """Detection metrics for one population of plates.

    Attributes:
        group: Group name.
        num_ground_truth: Number of annotated boxes in the group.
        num_predictions: Number of detections assigned to the group.
        true_positives: Detections matched to a ground-truth box at IoU >= 0.5.
        false_positives: Detections with no ground-truth match.
        false_negatives: Ground-truth boxes never detected.
        precision: TP / (TP + FP) at the operating confidence threshold.
        recall: TP / (TP + FN) at the operating confidence threshold.
        f1: Harmonic mean of precision and recall.
        ap50: Average precision at IoU 0.5.
        ap50_95: Average precision averaged over IoU 0.50:0.05:0.95.
        pr_curve: Sampled ``(recall, precision)`` points for plotting.
    """

    group: str
    num_ground_truth: int = 0
    num_predictions: int = 0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    ap50: float = 0.0
    ap50_95: float = 0.0
    pr_curve: list[tuple[float, float]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Render as a JSON-serialisable mapping.

        Returns:
            Metrics without the (large) PR curve samples.
        """
        return {
            "group": self.group,
            "num_ground_truth": self.num_ground_truth,
            "num_predictions": self.num_predictions,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "precision": round(self.precision, 5),
            "recall": round(self.recall, 5),
            "f1": round(self.f1, 5),
            "mAP@0.5": round(self.ap50, 5),
            "mAP@0.5:0.95": round(self.ap50_95, 5),
        }


# --- Dataset reading ---
def load_dataset_descriptor(data_yaml: Path) -> dict[str, Any]:
    """Read and sanity-check an Ultralytics ``data.yaml``.

    Args:
        data_yaml: Path to the descriptor.

    Returns:
        The parsed mapping.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If it is unreadable, not a mapping, or missing ``names``.
    """
    import yaml

    if not data_yaml.is_file():
        raise FileNotFoundError(
            f"Dataset descriptor not found: {data_yaml}\n"
            "Run the Phase 2 dataset pipeline, or pass --data explicitly."
        )
    try:
        payload = yaml.safe_load(data_yaml.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise ValueError(f"Cannot read {data_yaml}: {error}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"{data_yaml} must contain a YAML mapping")
    if "names" not in payload:
        raise ValueError(f"{data_yaml} is missing the required 'names' key")
    return payload


def resolve_split_images(data_yaml: Path, descriptor: dict[str, Any], split: str) -> list[Path]:
    """List the image files belonging to one dataset split.

    Handles both Ultralytics conventions: a directory of images, or a text file
    listing image paths one per line.

    Args:
        data_yaml: Path to the descriptor (used to resolve relative entries).
        descriptor: Parsed descriptor mapping.
        split: ``"train"``, ``"val"`` or ``"test"``.

    Returns:
        Sorted list of existing image paths.

    Raises:
        ValueError: If the split is absent from the descriptor, or resolves to
            nothing usable.
    """
    if split not in descriptor:
        available = [k for k in ("train", "val", "test") if k in descriptor]
        raise ValueError(
            f"Split {split!r} is not defined in {data_yaml}. Available: {available}. "
            "Evaluating on 'val' instead of a held-out 'test' split would report "
            "an optimistic number."
        )

    root = Path(str(descriptor.get("path", data_yaml.parent))).expanduser()
    if not root.is_absolute():
        root = (data_yaml.parent / root).resolve()

    entries = descriptor[split]
    if isinstance(entries, str):
        entries = [entries]
    if not isinstance(entries, list):
        raise ValueError(f"{data_yaml}: '{split}' must be a string or a list of strings")

    images: list[Path] = []
    for entry in entries:
        candidate = Path(str(entry)).expanduser()
        if not candidate.is_absolute():
            candidate = (root / candidate).resolve()
        if candidate.is_dir():
            images.extend(p for p in candidate.rglob("*") if p.suffix.lower() in _IMAGE_SUFFIXES)
        elif candidate.is_file() and candidate.suffix.lower() == ".txt":
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                listed = Path(line).expanduser()
                if not listed.is_absolute():
                    listed = (root / listed).resolve()
                images.append(listed)
        else:
            LOGGER.warning("Split entry does not exist, skipping: %s", candidate)

    existing = sorted({p for p in images if p.is_file()})
    missing = len(images) - len(existing)
    if missing:
        LOGGER.warning("%d listed image(s) are missing from disk", missing)
    if not existing:
        raise ValueError(
            f"No images found for split {split!r} under {root}. Check the paths " f"in {data_yaml}."
        )
    return existing


def label_path_for(image: Path) -> Path:
    """Map an image path to its YOLO label file.

    Follows the Ultralytics convention of swapping the last ``/images/``
    directory component for ``/labels/`` and the suffix for ``.txt``.

    Args:
        image: Path to an image file.

    Returns:
        Path to the corresponding ``.txt`` label file (which may not exist --
        an empty/absent label file legitimately means "no objects").
    """
    parts = list(image.parts)
    for index in range(len(parts) - 1, -1, -1):
        if parts[index] == "images":
            parts[index] = "labels"
            break
    return Path(*parts).with_suffix(".txt")


def classify_group(
    width: float,
    height: float,
    class_name: str,
    explicit_line_count: int | None,
    ar_threshold: float,
) -> tuple[str, str]:
    """Decide whether a box is a single-line or a two-line plate.

    Args:
        width: Box width in pixels.
        height: Box height in pixels.
        class_name: Name of the box's class, lower-cased by the caller or not.
        explicit_line_count: Line count read from the label file, if present.
        ar_threshold: Width/height ratio below which a box is two-line.

    Returns:
        A ``(group, source)`` pair, where ``source`` is ``"label"``, ``"class"``
        or ``"aspect_ratio"``.
    """
    if explicit_line_count is not None:
        return (SINGLE_LINE if explicit_line_count == 1 else TWO_LINE), "label"

    lowered = class_name.lower().replace("-", "_").replace(" ", "_")
    if any(token in lowered for token in _TWO_LINE_TOKENS):
        return TWO_LINE, "class"
    if any(token in lowered for token in _SINGLE_LINE_TOKENS):
        return SINGLE_LINE, "class"

    if height <= 0.0:
        return TWO_LINE, "aspect_ratio"
    return (SINGLE_LINE if (width / height) >= ar_threshold else TWO_LINE), "aspect_ratio"


def read_ground_truth(
    images: Sequence[Path],
    class_names: dict[int, str],
    ar_threshold: float,
) -> tuple[list[GroundTruthBox], dict[str, int]]:
    """Load ground-truth boxes for a set of images and assign layout groups.

    Malformed label lines are reported and skipped rather than aborting the
    whole evaluation: on a merged multi-source dataset a handful of bad rows is
    normal, and losing the entire report to one of them helps nobody.

    Args:
        images: Image paths to read labels for.
        class_names: Mapping of class index to class name.
        ar_threshold: Aspect-ratio threshold for the layout heuristic.

    Returns:
        A ``(boxes, stats)`` pair. ``stats`` counts ``images_without_labels``,
        ``malformed_lines`` and how many boxes were grouped by each source.

    Raises:
        RuntimeError: If Pillow is unavailable (needed for image dimensions).
    """
    try:
        from PIL import Image
    except ImportError as error:  # pragma: no cover - environment problem
        raise RuntimeError("Pillow is required to read image dimensions") from error

    boxes: list[GroundTruthBox] = []
    stats = {
        "images_without_labels": 0,
        "malformed_lines": 0,
        "grouped_by_label": 0,
        "grouped_by_class": 0,
        "grouped_by_aspect_ratio": 0,
    }

    for image in images:
        label_file = label_path_for(image)
        if not label_file.is_file():
            stats["images_without_labels"] += 1
            continue
        try:
            with Image.open(image) as handle:
                img_w, img_h = handle.size
        except Exception as error:  # noqa: BLE001 - a corrupt image is data, not a crash
            LOGGER.warning("Cannot read image %s (%s); skipped", image, error)
            stats["malformed_lines"] += 1
            continue

        try:
            lines = label_file.read_text(encoding="utf-8").splitlines()
        except OSError as error:
            LOGGER.warning("Cannot read label %s (%s); skipped", label_file, error)
            continue

        for line_no, raw in enumerate(lines, start=1):
            raw = raw.strip()
            if not raw:
                continue
            parts = raw.split()
            if len(parts) < 5:
                LOGGER.warning("%s:%d malformed label line: %r", label_file, line_no, raw)
                stats["malformed_lines"] += 1
                continue
            try:
                class_id = int(float(parts[0]))
                cx, cy, w, h = (float(v) for v in parts[1:5])
                # Optional 6th column: an explicit line count produced by the
                # dataset pipeline. This is the authoritative signal when present.
                explicit = int(float(parts[5])) if len(parts) >= 6 else None
            except ValueError:
                LOGGER.warning("%s:%d unparsable numbers: %r", label_file, line_no, raw)
                stats["malformed_lines"] += 1
                continue

            box_w, box_h = w * img_w, h * img_h
            x1 = (cx - w / 2.0) * img_w
            y1 = (cy - h / 2.0) * img_h
            group, source = classify_group(
                box_w, box_h, class_names.get(class_id, ""), explicit, ar_threshold
            )
            stats[f"grouped_by_{source}"] += 1
            boxes.append(
                GroundTruthBox(
                    image=image,
                    class_id=class_id,
                    xyxy=(x1, y1, x1 + box_w, y1 + box_h),
                    group=group,
                    group_source=source,
                )
            )

    return boxes, stats


# --- Metric computation ---
def iou(
    box_a: tuple[float, float, float, float], box_b: tuple[float, float, float, float]
) -> float:
    """Intersection-over-union of two axis-aligned boxes.

    Args:
        box_a: ``(x1, y1, x2, y2)``.
        box_b: ``(x1, y1, x2, y2)``.

    Returns:
        IoU in ``[0.0, 1.0]``; ``0.0`` when either box is degenerate.
    """
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_w = min(ax2, bx2) - max(ax1, bx1)
    inter_h = min(ay2, by2) - max(ay1, by1)
    if inter_w <= 0.0 or inter_h <= 0.0:
        return 0.0
    intersection = inter_w * inter_h
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - intersection
    return intersection / union if union > 0.0 else 0.0


def compute_average_precision(
    matches: Sequence[tuple[float, bool]], num_ground_truth: int
) -> tuple[float, list[tuple[float, float]]]:
    """Compute average precision from confidence-ranked match outcomes.

    Uses all-point interpolation (the COCO/VOC-2010 convention): the precision
    envelope is made monotonically decreasing before integration, so a single
    noisy point cannot depress the score.

    Args:
        matches: ``(confidence, is_true_positive)`` for every prediction.
        num_ground_truth: Total ground-truth boxes; the recall denominator.

    Returns:
        A ``(ap, pr_curve)`` pair. ``pr_curve`` holds ``(recall, precision)``
        points in increasing-recall order, suitable for plotting.
    """
    if num_ground_truth == 0:
        return 0.0, []
    if not matches:
        return 0.0, [(0.0, 1.0), (0.0, 0.0)]

    ordered = sorted(matches, key=lambda item: item[0], reverse=True)
    recalls: list[float] = []
    precisions: list[float] = []
    tp = 0
    for index, (_, is_tp) in enumerate(ordered, start=1):
        tp += int(is_tp)
        recalls.append(tp / num_ground_truth)
        precisions.append(tp / index)

    # Monotonic precision envelope, computed right to left.
    envelope = list(precisions)
    for index in range(len(envelope) - 2, -1, -1):
        envelope[index] = max(envelope[index], envelope[index + 1])

    ap = 0.0
    previous_recall = 0.0
    for recall, precision in zip(recalls, envelope):
        ap += (recall - previous_recall) * precision
        previous_recall = recall

    curve = [(0.0, envelope[0])] + list(zip(recalls, envelope))
    return ap, curve


def _match_at_iou(
    ground_truth: Sequence[GroundTruthBox],
    predictions: Sequence[PredictionBox],
    iou_threshold: float,
) -> list[tuple[float, bool]]:
    """Greedily match predictions to ground truth, highest confidence first.

    Args:
        ground_truth: Ground-truth boxes to match against.
        predictions: Predictions to score.
        iou_threshold: Minimum IoU for a match.

    Returns:
        ``(confidence, is_true_positive)`` per prediction, in confidence order.
    """
    by_image: dict[Path, list[tuple[int, GroundTruthBox]]] = {}
    for index, box in enumerate(ground_truth):
        by_image.setdefault(box.image, []).append((index, box))

    claimed: set[int] = set()
    outcomes: list[tuple[float, bool]] = []
    for prediction in sorted(predictions, key=lambda p: p.confidence, reverse=True):
        best_iou = 0.0
        best_index = -1
        for index, gt in by_image.get(prediction.image, ()):
            if index in claimed:
                continue
            score = iou(prediction.xyxy, gt.xyxy)
            if score > best_iou:
                best_iou, best_index = score, index
        if best_index >= 0 and best_iou >= iou_threshold:
            claimed.add(best_index)
            outcomes.append((prediction.confidence, True))
        else:
            outcomes.append((prediction.confidence, False))
    return outcomes


def evaluate_group(
    group: str,
    ground_truth: Sequence[GroundTruthBox],
    predictions: Sequence[PredictionBox],
) -> GroupMetrics:
    """Compute detection metrics for one population of plates.

    Args:
        group: Group label, used only for reporting.
        ground_truth: Ground-truth boxes in this group.
        predictions: Predictions assigned to this group.

    Returns:
        Populated :class:`GroupMetrics`.
    """
    metrics = GroupMetrics(
        group=group,
        num_ground_truth=len(ground_truth),
        num_predictions=len(predictions),
    )
    if not ground_truth:
        LOGGER.warning(
            "Group %r has no ground-truth boxes; its metrics are meaningless. "
            "Check the dataset balance or the grouping threshold.",
            group,
        )
        metrics.false_positives = len(predictions)
        return metrics

    outcomes = _match_at_iou(ground_truth, predictions, 0.5)
    metrics.true_positives = sum(1 for _, ok in outcomes if ok)
    metrics.false_positives = len(outcomes) - metrics.true_positives
    metrics.false_negatives = len(ground_truth) - metrics.true_positives

    denominator = metrics.true_positives + metrics.false_positives
    metrics.precision = metrics.true_positives / denominator if denominator else 0.0
    metrics.recall = metrics.true_positives / len(ground_truth)
    if metrics.precision + metrics.recall > 0.0:
        metrics.f1 = 2.0 * metrics.precision * metrics.recall / (metrics.precision + metrics.recall)

    metrics.ap50, metrics.pr_curve = compute_average_precision(outcomes, len(ground_truth))
    per_threshold = []
    for threshold in _COCO_IOU_THRESHOLDS:
        matched = _match_at_iou(ground_truth, predictions, threshold)
        ap, _ = compute_average_precision(matched, len(ground_truth))
        per_threshold.append(ap)
    metrics.ap50_95 = sum(per_threshold) / len(per_threshold)
    return metrics


# --- Inference ---
def run_predictions(
    model: Any,
    images: Sequence[Path],
    imgsz: int,
    conf: float,
    iou_threshold: float,
    device: str,
    ar_threshold: float,
) -> tuple[list[PredictionBox], list[float]]:
    """Run the detector over every image, one at a time, recording latency.

    Images are processed singly (batch size 1) on purpose: that is how the
    deployed API serves an upload, so the per-image timings collected here are
    the ones a user would actually experience.

    Args:
        model: Loaded Ultralytics model.
        images: Images to run over.
        imgsz: Inference input size.
        conf: Confidence threshold.
        iou_threshold: NMS IoU threshold.
        device: Torch device string.
        ar_threshold: Aspect-ratio threshold used to pre-assign a layout group
            to each detection (refined later by ground-truth matching).

    Returns:
        A ``(predictions, latencies_ms)`` pair.
    """
    predictions: list[PredictionBox] = []
    latencies: list[float] = []
    failures = 0

    for index, image in enumerate(images, start=1):
        started = time.perf_counter()
        try:
            results = model.predict(
                str(image),
                imgsz=imgsz,
                conf=conf,
                iou=iou_threshold,
                device=device,
                verbose=False,
            )
        except Exception as error:  # noqa: BLE001 - one bad image must not kill the run
            LOGGER.warning("Inference failed on %s: %s", image, error)
            failures += 1
            continue
        latencies.append((time.perf_counter() - started) * 1000.0)

        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            for xyxy, confidence, class_id in zip(
                boxes.xyxy.tolist(), boxes.conf.tolist(), boxes.cls.tolist()
            ):
                x1, y1, x2, y2 = (float(v) for v in xyxy)
                width, height = x2 - x1, y2 - y1
                group = (
                    SINGLE_LINE if height > 0.0 and (width / height) >= ar_threshold else TWO_LINE
                )
                predictions.append(
                    PredictionBox(
                        image=image,
                        class_id=int(class_id),
                        confidence=float(confidence),
                        xyxy=(x1, y1, x2, y2),
                        group=group,
                    )
                )

        if index % 200 == 0:
            LOGGER.info("  ... %d/%d images", index, len(images))

    if failures:
        LOGGER.error("%d image(s) could not be processed", failures)
    return predictions, latencies


def assign_predictions_to_groups(
    ground_truth: Sequence[GroundTruthBox], predictions: Sequence[PredictionBox]
) -> None:
    """Re-assign each prediction to the group of the ground-truth box it hits.

    A prediction carries no layout label of its own, so it is initially grouped
    by its own aspect ratio. Where it overlaps an annotated plate, the
    annotation is the better authority: a detection that is slightly too tall
    should still be counted against the single-line population it was trying to
    find. Predictions that match nothing keep their shape-based group, which is
    the only information available for a false positive.

    Args:
        ground_truth: All ground-truth boxes.
        predictions: Predictions to relabel, mutated in place.
    """
    by_image: dict[Path, list[GroundTruthBox]] = {}
    for box in ground_truth:
        by_image.setdefault(box.image, []).append(box)

    for prediction in predictions:
        best_iou = 0.0
        best_group = prediction.group
        for gt in by_image.get(prediction.image, ()):
            score = iou(prediction.xyxy, gt.xyxy)
            if score > best_iou:
                best_iou, best_group = score, gt.group
        if best_iou >= 0.5:
            prediction.group = best_group


def summarise_latency(latencies: Sequence[float]) -> dict[str, float | int]:
    """Summarise per-image latency measurements.

    Percentiles are computed by nearest-rank on the sorted samples, which is
    unambiguous and does not interpolate between measurements that were never
    observed.

    Args:
        latencies: Per-image latencies in milliseconds.

    Returns:
        Mapping with ``samples``, ``mean_ms``, ``p50_ms``, ``p95_ms``,
        ``p99_ms``, ``min_ms``, ``max_ms`` and ``fps_p50``.
    """
    if not latencies:
        return {"samples": 0}
    ordered = sorted(latencies)

    def percentile(fraction: float) -> float:
        rank = max(1, min(len(ordered), int(round(fraction * len(ordered)))))
        return ordered[rank - 1]

    p50 = percentile(0.50)
    return {
        "samples": len(ordered),
        "mean_ms": round(statistics.fmean(ordered), 2),
        "p50_ms": round(p50, 2),
        "p95_ms": round(percentile(0.95), 2),
        "p99_ms": round(percentile(0.99), 2),
        "min_ms": round(ordered[0], 2),
        "max_ms": round(ordered[-1], 2),
        "fps_p50": round(1000.0 / p50, 2) if p50 > 0 else 0.0,
    }


# --- Plots ---
def plot_pr_curves(
    metrics_by_group: dict[str, GroupMetrics], destination: Path, title: str
) -> Path | None:
    """Plot precision/recall curves, one line per plate layout.

    Args:
        metrics_by_group: Metrics keyed by group name.
        destination: PNG file to write.
        title: Plot title.

    Returns:
        The written path, or ``None`` if matplotlib is unavailable.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        LOGGER.error("matplotlib is not installed; skipping PR curve plot")
        return None

    figure, axes = plt.subplots(figsize=(7.0, 5.5), dpi=150)
    for group, metrics in sorted(metrics_by_group.items()):
        if not metrics.pr_curve:
            continue
        recalls = [point[0] for point in metrics.pr_curve]
        precisions = [point[1] for point in metrics.pr_curve]
        axes.plot(
            recalls,
            precisions,
            linewidth=2.0,
            label=f"{group} (AP@0.5 = {metrics.ap50:.3f}, n = {metrics.num_ground_truth})",
        )
    axes.set_xlabel("Recall")
    axes.set_ylabel("Precision")
    axes.set_xlim(0.0, 1.02)
    axes.set_ylim(0.0, 1.02)
    axes.set_title(title)
    axes.grid(alpha=0.3, linestyle="--")
    axes.legend(loc="lower left", fontsize=8)
    figure.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination)
    plt.close(figure)
    LOGGER.info("Wrote %s", destination)
    return destination


def plot_confusion_matrix(
    ground_truth: Sequence[GroundTruthBox],
    predictions: Sequence[PredictionBox],
    destination: Path,
) -> Path | None:
    """Plot a layout-aware confusion matrix.

    Rows are the ground-truth population (single-line, two-line, or
    ``background`` for a false positive); columns are what the detector
    produced. The ``background`` row/column is what makes the matrix useful for
    detection: it separates "found the wrong kind of plate" from "hallucinated a
    plate" and "missed a plate entirely".

    Args:
        ground_truth: All ground-truth boxes.
        predictions: All predictions.
        destination: PNG file to write.

    Returns:
        The written path, or ``None`` if matplotlib is unavailable.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        LOGGER.error("matplotlib/numpy not installed; skipping confusion matrix")
        return None

    labels = [SINGLE_LINE, TWO_LINE, "background"]
    index_of = {name: i for i, name in enumerate(labels)}
    matrix = np.zeros((3, 3), dtype=int)

    by_image: dict[Path, list[tuple[int, GroundTruthBox]]] = {}
    for index, box in enumerate(ground_truth):
        by_image.setdefault(box.image, []).append((index, box))

    claimed: set[int] = set()
    for prediction in sorted(predictions, key=lambda p: p.confidence, reverse=True):
        best_iou, best_index, best_group = 0.0, -1, None
        for index, gt in by_image.get(prediction.image, ()):
            if index in claimed:
                continue
            score = iou(prediction.xyxy, gt.xyxy)
            if score > best_iou:
                best_iou, best_index, best_group = score, index, gt.group
        if best_index >= 0 and best_iou >= 0.5 and best_group is not None:
            claimed.add(best_index)
            matrix[index_of[best_group], index_of[prediction.group]] += 1
        else:
            # Predicted something where nothing was annotated.
            matrix[index_of["background"], index_of[prediction.group]] += 1

    for index, box in enumerate(ground_truth):
        if index not in claimed:
            # Annotated plate the detector never found.
            matrix[index_of[box.group], index_of["background"]] += 1

    figure, axes = plt.subplots(figsize=(6.0, 5.0), dpi=150)
    image = axes.imshow(matrix, cmap="Blues")
    axes.set_xticks(range(3), labels, rotation=20, ha="right")
    axes.set_yticks(range(3), labels)
    axes.set_xlabel("Predicted")
    axes.set_ylabel("Ground truth")
    axes.set_title("Confusion matrix (IoU >= 0.5)")
    threshold = matrix.max() / 2.0 if matrix.max() else 0.5
    for row in range(3):
        for column in range(3):
            axes.text(
                column,
                row,
                str(matrix[row, column]),
                ha="center",
                va="center",
                color="white" if matrix[row, column] > threshold else "black",
            )
    figure.colorbar(image, ax=axes, shrink=0.8)
    figure.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination)
    plt.close(figure)
    LOGGER.info("Wrote %s", destination)
    return destination


def plot_latency(latencies: Sequence[float], destination: Path, device: str) -> Path | None:
    """Plot the distribution of per-image inference latency.

    Args:
        latencies: Per-image latencies in milliseconds.
        destination: PNG file to write.
        device: Device label for the title.

    Returns:
        The written path, or ``None`` if matplotlib is unavailable or there is
        no data.
    """
    if not latencies:
        return None
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        LOGGER.error("matplotlib is not installed; skipping latency plot")
        return None

    summary = summarise_latency(latencies)
    figure, axes = plt.subplots(figsize=(7.0, 4.5), dpi=150)
    axes.hist(latencies, bins=40, color="#4878a8", edgecolor="white")
    for key, colour in (("p50_ms", "#2ca02c"), ("p95_ms", "#ff7f0e"), ("p99_ms", "#d62728")):
        axes.axvline(
            float(summary[key]),
            color=colour,
            linestyle="--",
            linewidth=1.5,
            label=f"{key[:3]} = {summary[key]} ms",
        )
    axes.set_xlabel("Latency per image (ms)")
    axes.set_ylabel("Number of images")
    axes.set_title(f"Inference latency on {device} (batch = 1, n = {len(latencies)})")
    axes.legend()
    axes.grid(alpha=0.3, linestyle="--")
    figure.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination)
    plt.close(figure)
    LOGGER.info("Wrote %s", destination)
    return destination


# --- Ultralytics validator ---
def run_ultralytics_validation(
    model: Any,
    data_yaml: Path,
    split: str,
    imgsz: int,
    batch: int,
    device: str,
    figures_dir: Path,
) -> dict[str, Any]:
    """Run the reference Ultralytics validator for the headline metrics.

    The custom matcher in this module exists for the per-layout breakdown, which
    Ultralytics cannot produce. The headline numbers, however, should come from
    the reference implementation -- a thesis that quotes home-grown mAP invites
    the obvious question at the defence.

    Args:
        model: Loaded Ultralytics model.
        data_yaml: Dataset descriptor.
        split: Split to validate on.
        imgsz: Inference input size.
        batch: Validation batch size.
        device: Torch device string.
        figures_dir: Directory to copy generated plots into.

    Returns:
        Mapping of metric name to value; empty if validation failed.
    """
    try:
        results = model.val(
            data=str(data_yaml),
            split=split,
            imgsz=imgsz,
            batch=batch,
            device=device,
            plots=True,
            verbose=False,
            # Keep the validator's artefacts beside this report instead of in
            # the default runs/detect/val, which would collide across models.
            project=str(figures_dir),
            name="ultralytics_val",
            exist_ok=True,
        )
    except Exception as error:  # noqa: BLE001 - report and continue with our own metrics
        LOGGER.error(
            "Ultralytics validation failed (%s); falling back to the built-in "
            "matcher for all metrics",
            error,
        )
        return {}

    box = getattr(results, "box", None)
    metrics: dict[str, Any] = {}
    if box is not None:
        precision = float(getattr(box, "mp", 0.0))
        recall = float(getattr(box, "mr", 0.0))
        metrics = {
            "mAP@0.5": round(float(getattr(box, "map50", 0.0)), 5),
            "mAP@0.5:0.95": round(float(getattr(box, "map", 0.0)), 5),
            "precision": round(precision, 5),
            "recall": round(recall, 5),
            "f1": round(
                2 * precision * recall / (precision + recall) if precision + recall else 0.0,
                5,
            ),
        }

    save_dir = Path(str(getattr(results, "save_dir", "")))
    if save_dir.is_dir():
        figures_dir.mkdir(parents=True, exist_ok=True)
        for png in save_dir.glob("*.png"):
            try:
                shutil.copy2(png, figures_dir / f"ultralytics_{png.name}")
            except OSError as error:
                LOGGER.warning("Could not copy %s: %s", png, error)
        LOGGER.info("Copied Ultralytics plots from %s to %s", save_dir, figures_dir)
    return metrics


# --- CLI ---
def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line parser.

    Returns:
        The configured :class:`argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(
        prog="python -m ai.evaluation.evaluate",
        description=(
            "Evaluate a YOLO11 plate detector: mAP/precision/recall/F1, PR curve, "
            "confusion matrix, CPU latency percentiles, and a SEPARATE breakdown "
            "for single-line vs two-line plates (NFR-A8)."
        ),
        epilog=(
            "Examples:\n"
            "  python -m ai.evaluation.evaluate --weights models/best.pt\n"
            "  python -m ai.evaluation.evaluate --weights models/best.pt "
            "--split test --device cpu --speed-samples 200\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--weights",
        default=str(DEFAULT_MODELS_DIR / "best.pt"),
        help="Model to evaluate: .pt, .onnx, or an OpenVINO directory.",
    )
    parser.add_argument(
        "--data",
        default=str(DEFAULT_DATA_YAML),
        help="Ultralytics dataset descriptor (data.yaml).",
    )
    parser.add_argument(
        "--split",
        default="test",
        choices=("train", "val", "test"),
        help="Split to evaluate (default: test -- do not report val as final).",
    )
    parser.add_argument("--imgsz", type=int, default=640, help="Inference image size.")
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Confidence threshold for the operating-point metrics (default: 0.25).",
    )
    parser.add_argument(
        "--iou", type=float, default=0.45, help="NMS IoU threshold (default: 0.45)."
    )
    parser.add_argument(
        "--batch", type=int, default=8, help="Batch size for Ultralytics validation."
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help=(
            "Torch device. Defaults to cpu because the deployment target has no "
            "GPU and the reported latency must reflect that."
        ),
    )
    parser.add_argument(
        "--ar-threshold",
        type=float,
        default=DEFAULT_AR_THRESHOLD,
        help=(
            "Width/height ratio below which a plate counts as two-line, used "
            f"only when the labels do not say (default: {DEFAULT_AR_THRESHOLD}; "
            "QCVN 08:2024/BCA gives 4.727 for single-line and 2.000/1.357 for "
            "two-line)."
        ),
    )
    parser.add_argument(
        "--speed-samples",
        type=int,
        default=200,
        help=(
            "Number of images used for the latency percentiles (default: 200). "
            "0 uses every image in the split."
        ),
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=0,
        help="Cap the number of images evaluated (0 = all). Useful for a smoke test.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Where the JSON report and PNGs go (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Report basename (default: derived from the weights file and split).",
    )
    parser.add_argument("--no-plots", action="store_true", help="Skip PNG generation.")
    parser.add_argument(
        "--skip-ultralytics-val",
        action="store_true",
        help=(
            "Skip the reference Ultralytics validation pass and report only the "
            "built-in matcher's numbers (faster, but less authoritative)."
        ),
    )
    return parser


def _resolve(path: str | Path) -> Path:
    """Resolve a path against the repository root when relative.

    Args:
        path: Absolute or relative path.

    Returns:
        An absolute path.
    """
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate


def _log_table(metrics_by_group: dict[str, GroupMetrics], overall: GroupMetrics) -> None:
    """Print the per-layout metrics table to the log.

    Args:
        metrics_by_group: Per-group metrics.
        overall: Metrics over all plates.
    """
    header = f"{'GROUP':<14}{'N_GT':>7}{'TP':>7}{'FP':>7}{'FN':>7}{'P':>9}{'R':>9}{'F1':>9}{'mAP50':>9}{'mAP50-95':>10}"
    LOGGER.info("=" * len(header))
    LOGGER.info(header)
    LOGGER.info("-" * len(header))
    for metrics in [
        metrics_by_group.get(SINGLE_LINE),
        metrics_by_group.get(TWO_LINE),
        overall,
    ]:
        if metrics is None:
            continue
        LOGGER.info(
            "%-14s%7d%7d%7d%7d%9.4f%9.4f%9.4f%9.4f%10.4f",
            metrics.group,
            metrics.num_ground_truth,
            metrics.true_positives,
            metrics.false_positives,
            metrics.false_negatives,
            metrics.precision,
            metrics.recall,
            metrics.f1,
            metrics.ap50,
            metrics.ap50_95,
        )
    LOGGER.info("=" * len(header))

    single = metrics_by_group.get(SINGLE_LINE)
    two = metrics_by_group.get(TWO_LINE)
    if single and two and single.num_ground_truth and two.num_ground_truth:
        gap = single.ap50 - two.ap50
        LOGGER.info("NFR-A8 gap (single-line AP@0.5 minus two-line AP@0.5): %+.4f", gap)
        if gap > 0.10:
            LOGGER.warning(
                "Two-line plates lag single-line by more than 10 AP points. This "
                "is risk R-04 materialising. Prefer rebalancing the dataset over "
                "escalating to a larger model."
            )


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point.

    Args:
        argv: Argument list; defaults to :data:`sys.argv`.

    Returns:
        ``0`` on success, ``1`` on a handled error.
    """
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )

    weights = _resolve(args.weights)
    data_yaml = _resolve(args.data)
    output_dir = _resolve(args.output_dir)
    figures_dir = output_dir / "figures"

    if not weights.exists():
        LOGGER.error(
            "Model not found: %s\nTrain one first: "
            "python -m ai.training.train --config yolo11n_finetune.yaml",
            weights,
        )
        return 1

    try:
        descriptor = load_dataset_descriptor(data_yaml)
        images = resolve_split_images(data_yaml, descriptor, args.split)
    except (FileNotFoundError, ValueError) as error:
        LOGGER.error("%s", error)
        return 1

    if args.max_images > 0:
        images = images[: args.max_images]
    LOGGER.info("Evaluating %s on %d image(s) of split %r", weights.name, len(images), args.split)

    raw_names = descriptor.get("names", {})
    if isinstance(raw_names, dict):
        class_names = {int(k): str(v) for k, v in raw_names.items()}
    else:
        class_names = {index: str(name) for index, name in enumerate(raw_names)}
    LOGGER.info("Classes: %s", class_names)

    try:
        from ultralytics import YOLO
    except ImportError:
        LOGGER.error("ultralytics is not installed. Run: pip install -r ai/requirements.txt")
        return 1

    try:
        model = YOLO(str(weights))
    except Exception as error:  # noqa: BLE001
        LOGGER.error("Cannot load model %s: %s", weights, error)
        return 1

    try:
        ground_truth, gt_stats = read_ground_truth(images, class_names, args.ar_threshold)
    except RuntimeError as error:
        LOGGER.error("%s", error)
        return 1

    if not ground_truth:
        LOGGER.error(
            "No ground-truth boxes found for split %r. Expected label files "
            "alongside the images (images/ -> labels/, .txt). Nothing to evaluate.",
            args.split,
        )
        return 1
    LOGGER.info(
        "Ground truth: %d box(es) | grouping source: label=%d class=%d aspect_ratio=%d",
        len(ground_truth),
        gt_stats["grouped_by_label"],
        gt_stats["grouped_by_class"],
        gt_stats["grouped_by_aspect_ratio"],
    )
    if gt_stats["grouped_by_aspect_ratio"] == len(ground_truth):
        LOGGER.warning(
            "Every box was grouped by the aspect-ratio heuristic (no line_count "
            "labels and no layout-bearing class names). The single-line / "
            "two-line split is therefore an estimate -- say so in the report."
        )

    LOGGER.info("Running inference (batch = 1, device = %s)...", args.device)
    predictions, latencies = run_predictions(
        model, images, args.imgsz, args.conf, args.iou, args.device, args.ar_threshold
    )
    LOGGER.info("Produced %d detection(s)", len(predictions))
    assign_predictions_to_groups(ground_truth, predictions)

    metrics_by_group: dict[str, GroupMetrics] = {}
    for group in (SINGLE_LINE, TWO_LINE):
        metrics_by_group[group] = evaluate_group(
            group,
            [box for box in ground_truth if box.group == group],
            [box for box in predictions if box.group == group],
        )
    overall = evaluate_group("ALL", ground_truth, predictions)
    _log_table(metrics_by_group, overall)

    speed_samples = latencies
    if args.speed_samples > 0:
        speed_samples = latencies[: args.speed_samples]
    latency_summary = summarise_latency(speed_samples)
    LOGGER.info("Latency on %s: %s", args.device, latency_summary)

    reference_metrics: dict[str, Any] = {}
    if not args.skip_ultralytics_val:
        LOGGER.info("Running the reference Ultralytics validator...")
        reference_metrics = run_ultralytics_validation(
            model, data_yaml, args.split, args.imgsz, args.batch, args.device, figures_dir
        )
        if reference_metrics:
            LOGGER.info("Ultralytics reference metrics: %s", reference_metrics)

    plots: dict[str, str | None] = {}
    if not args.no_plots:
        basename = args.name or f"{weights.stem}_{args.split}"
        plots["pr_curve_by_line_count"] = str(
            plot_pr_curves(
                {**metrics_by_group, "ALL": overall},
                figures_dir / f"{basename}_pr_curve.png",
                f"PR curve by plate layout -- {weights.name} ({args.split})",
            )
            or ""
        )
        plots["confusion_matrix"] = str(
            plot_confusion_matrix(
                ground_truth, predictions, figures_dir / f"{basename}_confusion_matrix.png"
            )
            or ""
        )
        plots["latency_histogram"] = str(
            plot_latency(speed_samples, figures_dir / f"{basename}_latency.png", args.device) or ""
        )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": {
            "weights": str(weights),
            "size_mb": round(
                (
                    sum(f.stat().st_size for f in weights.rglob("*") if f.is_file())
                    if weights.is_dir()
                    else weights.stat().st_size
                )
                / (1024 * 1024),
                2,
            ),
        },
        "dataset": {
            "data_yaml": str(data_yaml),
            "split": args.split,
            "num_images": len(images),
            "num_ground_truth_boxes": len(ground_truth),
            "classes": class_names,
            "label_stats": gt_stats,
        },
        "settings": {
            "imgsz": args.imgsz,
            "conf": args.conf,
            "iou": args.iou,
            "device": args.device,
            "aspect_ratio_threshold": args.ar_threshold,
        },
        "environment": {
            "python": sys.version.split()[0],
            "platform": f"{platform.system()} {platform.release()}",
            "processor": platform.processor() or "unknown",
        },
        "metrics_reference_ultralytics": reference_metrics,
        "metrics_overall": overall.to_dict(),
        "metrics_by_line_count": {
            group: metrics.to_dict() for group, metrics in metrics_by_group.items()
        },
        "nfr_a8_gap_ap50": round(
            metrics_by_group[SINGLE_LINE].ap50 - metrics_by_group[TWO_LINE].ap50, 5
        ),
        "inference_latency": latency_summary,
        "plots": {key: value for key, value in plots.items() if value},
    }

    basename = args.name or f"{weights.stem}_{args.split}"
    report_path = output_dir / f"03-evaluation-{basename}.json"
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
        )
    except OSError as error:
        LOGGER.error("Cannot write report to %s: %s", report_path, error)
        return 1

    LOGGER.info("Report written to %s", report_path)
    if not args.no_plots:
        LOGGER.info("Figures written to %s", figures_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
