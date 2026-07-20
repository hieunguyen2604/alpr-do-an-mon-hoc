"""Measure the plate-colour classifier against human-assigned labels.

Why this evaluation exists
--------------------------
:mod:`ai.inference.plate_color` decides a plate's background colour from pixels,
and until now nothing measured whether it was right. Its thresholds were tuned
against five real crops -- enough to show the idea works, nowhere near enough to
publish a number. The project's own corpus could not help: it is 97.4% white
plates with one red and no ground-truth colour labels at all
(``docs/reports/17-plate-type-audit.json``).

The ``nguyenluanai/license-plate-color`` dataset (CC BY 4.0) closes that gap. Its
2,107 crops carry a **human-assigned colour class**, including 694 yellow and 63
blue -- two orders of magnitude more yellow than this project had.

What this dataset can and cannot support
----------------------------------------
Every image in it is 640x640. Not resized to fit: **stretched**, by the
contributor before upload -- the filenames end in ``_640`` and even the
"original" served by Roboflow is already square. The true aspect ratio is
unrecoverable.

That rules the dataset out for OCR evaluation here, because
:func:`~ai.inference.two_line.estimate_line_count` decides one-line versus
two-line from the aspect ratio: every crop would come back square, hence
"two-line", and the measurement would be of the distortion rather than of the
system. Recording that plainly matters more than the lost sample size -- a
tempting dataset used for the wrong question produces a number that looks
publishable and means nothing.

Colour survives stretching, so the colour question is exactly the one this data
can answer.

The ``bien_unknown`` class
--------------------------
542 of the 2,107 images (25.7%) are labelled ``bien_unknown``: night and
infrared captures whose white balance failed, leaving a purple cast under which
a human annotator could not name the colour either. They are reported
separately, never folded into the accuracy figure. Averaging them in would
measure the camera, not the classifier; excluding them silently would hide that
a quarter of a real-world corpus is unreadable by colour at all.

Usage
-----
::

    python -m ai.evaluation.color_accuracy \\
        --dataset datasets/raw/roboflow_plate_color \\
        --output docs/reports/19-color-accuracy.json
"""

from __future__ import annotations

import argparse
import collections
import json
import logging
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np

from ai.inference.plate_color import PlateColor, classify_plate_color

LOGGER = logging.getLogger("color_accuracy")

__all__ = ["ColorSample", "evaluate_dataset", "build_parser", "main"]

#: Maps the dataset's Vietnamese class names onto this project's enum. The
#: dataset names its classes in unaccented Vietnamese, which is itself part of
#: the evidence that it is a Vietnamese corpus rather than a relabelled foreign
#: one -- a distinction this project has had to make before.
CLASS_TO_COLOR: dict[str, PlateColor] = {
    "bien_trang": PlateColor.WHITE,
    "bien_vang": PlateColor.YELLOW,
    "bien_xanh": PlateColor.BLUE,
    "bien_do": PlateColor.RED,
    "bien_unknown": PlateColor.UNKNOWN,
}

#: Classes excluded from the headline accuracy, with the reason. Kept as data so
#: the report can state the exclusion instead of the reader having to infer it.
EXCLUDED_CLASSES: dict[str, str] = {
    "bien_unknown": (
        "anh chup dem/hong ngoai bi loi can bang trang, am mau tim; chinh nguoi "
        "gan nhan cung khong doc duoc mau nen"
    ),
}


@dataclass(slots=True)
class ColorSample:
    """One evaluated crop.

    Attributes:
        image_path: Where the crop came from.
        truth: Human-assigned colour class from the dataset.
        predicted: Colour this project's classifier named.
        confidence: Fraction of sampled pixels behind the prediction.
        correct: Whether the two agree.
        excluded: Whether this sample sits outside the headline figure.
    """

    image_path: str
    truth: str
    predicted: str
    confidence: float
    correct: bool
    excluded: bool


def _read_image(path: Path) -> np.ndarray | None:
    """Read an image, tolerating paths OpenCV cannot open directly.

    Args:
        path: Filesystem path to an image.

    Returns:
        The decoded BGR array, or ``None`` when the file cannot be read.
    """
    image = cv2.imread(str(path))
    if image is not None:
        return image
    try:
        return cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    except Exception:  # noqa: BLE001 - an unreadable file is a normal outcome
        return None


def _load_class_names(dataset: Path) -> list[str]:
    """Read the class-index-to-name list from the dataset descriptor.

    Args:
        dataset: Root of the exported dataset, containing ``data.yaml``.

    Returns:
        Class names in index order.

    Raises:
        ValueError: If the descriptor carries no ``names`` list. Guessing the
            order would silently mislabel every sample.
    """
    text = (dataset / "data.yaml").read_text(encoding="utf-8")
    for line in text.splitlines():
        if not line.startswith("names:"):
            continue
        raw = line.split(":", 1)[1].strip()
        return [n.strip().strip("'\"") for n in raw.strip("[]").split(",") if n.strip()]
    raise ValueError(f"{dataset / 'data.yaml'} has no 'names:' list")


def evaluate_dataset(dataset: Path, limit: int = 0) -> tuple[list[ColorSample], dict]:
    """Classify every crop and compare against the dataset's labels.

    Args:
        dataset: Root of the exported YOLO dataset.
        limit: Stop after this many images; ``0`` evaluates all of them.

    Returns:
        A ``(samples, summary)`` pair. The summary carries the headline accuracy
        over the scored classes, a per-class breakdown, and the confusion matrix.
    """
    names = _load_class_names(dataset)
    LOGGER.info("classes: %s", ", ".join(names))

    samples: list[ColorSample] = []
    confusion: collections.Counter[tuple[str, str]] = collections.Counter()

    label_files = sorted(dataset.rglob("labels/*.txt"))
    if limit:
        label_files = label_files[:limit]

    for index, label_file in enumerate(label_files, start=1):
        if index % 250 == 0:
            LOGGER.info("  %d/%d", index, len(label_files))

        rows = [r for r in label_file.read_text().splitlines() if r.strip()]
        if len(rows) != 1:
            # Every crop in this dataset holds exactly one plate. More than one
            # box means the file is not what the evaluation assumes, so skipping
            # is safer than picking one arbitrarily.
            continue
        truth = names[int(rows[0].split()[0])]

        image_path = label_file.parent.parent / "images" / (label_file.stem + ".jpg")
        image = _read_image(image_path)
        if image is None:
            continue

        estimate = classify_plate_color(image)
        predicted = estimate.color.value
        expected = CLASS_TO_COLOR.get(truth, PlateColor.UNKNOWN).value
        excluded = truth in EXCLUDED_CLASSES

        samples.append(
            ColorSample(
                image_path=str(image_path),
                truth=truth,
                predicted=predicted,
                confidence=round(estimate.confidence, 4),
                correct=predicted == expected,
                excluded=excluded,
            )
        )
        confusion[(truth, predicted)] += 1

    scored = [s for s in samples if not s.excluded]
    correct = sum(1 for s in scored if s.correct)

    per_class: dict[str, dict] = {}
    for name in names:
        group = [s for s in samples if s.truth == name]
        if not group:
            continue
        hits = sum(1 for s in group if s.correct)
        per_class[name] = {
            "n": len(group),
            "correct": hits,
            "accuracy": round(hits / len(group), 4),
            "excluded_from_headline": name in EXCLUDED_CLASSES,
        }

    summary = {
        "total_images": len(samples),
        "scored_images": len(scored),
        "excluded_images": len(samples) - len(scored),
        "excluded_reason": EXCLUDED_CLASSES,
        "accuracy": round(correct / len(scored), 4) if scored else 0.0,
        "correct": correct,
        "per_class": per_class,
        "confusion": {f"{t}->{p}": n for (t, p), n in confusion.most_common()},
    }
    return samples, summary


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--dataset", default="datasets/raw/roboflow_plate_color")
    parser.add_argument("--output", default="docs/reports/19-color-accuracy.json")
    parser.add_argument("--limit", type=int, default=0)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the evaluation and write the report.

    Args:
        argv: Command-line arguments; ``sys.argv[1:]`` when omitted.

    Returns:
        ``0`` on success, ``1`` when no sample could be evaluated.
    """
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = build_parser().parse_args(argv)

    dataset = Path(args.dataset)
    if not dataset.is_dir():
        LOGGER.error("dataset not found: %s", dataset)
        return 1

    samples, summary = evaluate_dataset(dataset, args.limit)
    if not samples:
        LOGGER.error("no sample could be evaluated")
        return 1

    report = {
        "dataset": str(dataset),
        "source": "nguyenluanai/license-plate-color v4 (Roboflow Universe)",
        "license": "CC BY 4.0",
        "caveat_aspect_ratio": (
            "Moi anh trong bo deu la 640x640 do nguoi dong gop KEO MEO truoc khi "
            "tai len. Bo nay vi vay KHONG dung duoc de danh gia OCR, vi buoc uoc "
            "luong so dong dua tren ty le khung hinh. Mau nen khong bi anh huong "
            "boi phep keo, nen cau hoi ve mau la cau hoi bo nay tra loi duoc."
        ),
        "summary": summary,
        "samples": [asdict(s) for s in samples],
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    LOGGER.info("")
    LOGGER.info(
        "Do chinh xac nhan mau: %.2f%%  (%d/%d anh duoc cham)",
        summary["accuracy"] * 100,
        summary["correct"],
        summary["scored_images"],
    )
    LOGGER.info("Loai khoi diem: %d anh", summary["excluded_images"])
    LOGGER.info("")
    for name, stats in summary["per_class"].items():
        mark = "  (khong tinh diem)" if stats["excluded_from_headline"] else ""
        LOGGER.info(
            "  %-14s %4d anh  dung %4d  = %5.1f%%%s",
            name,
            stats["n"],
            stats["correct"],
            stats["accuracy"] * 100,
            mark,
        )
    LOGGER.info("")
    LOGGER.info("wrote %s", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
