"""Check dataset annotation quality before any of it reaches the trainer.

Usage examples::

    python scripts/dataset/verify_annotations.py --input-dir datasets/raw/vnlp
    python scripts/dataset/verify_annotations.py --input-dir datasets/processed --strict
    python scripts/dataset/verify_annotations.py --input-dir datasets/raw --min-box-area 0.001

What gets checked
-----------------
=========================  ========  ====================================
Check                      Severity  Rationale
=========================  ========  ====================================
Label file exists          error     A missing label silently becomes a
                                     background image and teaches the model
                                     that plates are not plates.
Label file parses          error     Malformed rows abort training later.
Coordinates in ``[0, 1]``  error     Pixel coordinates left in a YOLO file
                                     are the single most common conversion
                                     bug.
Positive box area          error     Zero-area boxes produce NaN losses.
Box inside the frame       error     Clipped boxes shift the target.
Image decodes in OpenCV    error     Ultralytics loads via OpenCV, so a
                                     file Pillow reads and OpenCV does not
                                     will fail mid-epoch.
Image dimensions > 0       error     Same.
Box area >= threshold      warning   Plates below ~0.5% of the frame are
                                     near-unlearnable at 640px input.
Duplicate boxes            warning   Usually a double-annotation mistake.
=========================  ========  ====================================

Why OpenCV specifically
-----------------------
Dimensions could be read far more cheaply from the file header with Pillow, and
the rest of the pipeline does exactly that. This script decodes fully, with
OpenCV, on purpose: a truncated JPEG has a perfectly valid header, and Pillow
will happily report its size. The failure then surfaces during training instead
of here, which is the worst possible moment to discover it.

The aspect-ratio section
------------------------
The one-line / two-line breakdown in the report is a **heuristic** derived from
box aspect ratio (threshold 2.5, from the plate dimensions in QCVN 08:2024/BCA).
It is not ground truth: perspective, loose boxes and bent motorcycle plates all
push a plate across the threshold. Use it to check that a dataset contains a
plausible mix of both types, not to label anything.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Iterable, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    add_common_arguments,
    bootstrap_project_path,
    configure_logging,
    format_count,
    iter_image_files,
    resolve_dataset_paths,
    summarise_distribution,
    write_csv,
    write_json,
)

bootstrap_project_path()

from ai.data.schema import (  # noqa: E402
    AR_ONE_LINE_MIN,
    BoxRecord,
    LabelParseError,
    estimate_line_count,
    image_path_to_label_path,
    parse_yolo_label_file,
)

LOGGER = logging.getLogger("dataset.verify")

DEFAULT_MIN_BOX_AREA: Final[float] = 0.005
"""0.5% of image area. Below this a plate is a handful of pixels at 640px input."""

SEVERITY_ERROR: Final[str] = "error"
SEVERITY_WARNING: Final[str] = "warning"


@dataclass(slots=True)
class Issue:
    """One problem found with one image.

    Attributes:
        image: Path to the image the problem concerns.
        severity: :data:`SEVERITY_ERROR` or :data:`SEVERITY_WARNING`.
        code: Short machine-readable category, e.g. ``"missing_label"``.
        detail: Human-readable explanation.
        box_index: Which box is at fault, or ``None`` for image-level problems.
    """

    image: Path
    severity: str
    code: str
    detail: str
    box_index: int | None = None

    def as_row(self) -> dict[str, Any]:
        """Return a CSV-ready view of the issue."""
        return {
            "image": self.image,
            "severity": self.severity,
            "code": self.code,
            "box_index": self.box_index,
            "detail": self.detail,
        }


@dataclass(slots=True)
class VerificationReport:
    """Accumulated results of a verification run.

    Attributes:
        issues: Every problem found, in discovery order.
        images_checked: Number of image files examined.
        images_ok: Number with no error-severity issue.
        boxes_checked: Total boxes parsed.
        aspect_ratios: Every usable box aspect ratio, for the distribution.
        boxes_per_image: Box count per image, for the distribution.
        box_areas: Box areas as a fraction of image area.
        per_dataset: Per-source-directory counters.
    """

    issues: list[Issue] = field(default_factory=list)
    images_checked: int = 0
    images_ok: int = 0
    boxes_checked: int = 0
    aspect_ratios: list[float] = field(default_factory=list)
    boxes_per_image: list[int] = field(default_factory=list)
    box_areas: list[float] = field(default_factory=list)
    per_dataset: dict[str, Counter[str]] = field(
        default_factory=lambda: defaultdict(Counter)
    )

    @property
    def error_count(self) -> int:
        """Return the number of error-severity issues."""
        return sum(1 for issue in self.issues if issue.severity == SEVERITY_ERROR)

    @property
    def warning_count(self) -> int:
        """Return the number of warning-severity issues."""
        return sum(1 for issue in self.issues if issue.severity == SEVERITY_WARNING)

    @property
    def images_with_errors(self) -> int:
        """Return how many distinct images carry at least one error."""
        return len(
            {issue.image for issue in self.issues if issue.severity == SEVERITY_ERROR}
        )


def load_image_dimensions(image_path: Path) -> tuple[int, int] | None:
    """Decode an image with OpenCV and return its dimensions.

    A full decode, not a header read -- see the module docstring for why.

    Args:
        image_path: The image to open.

    Returns:
        ``(width, height)``, or ``None`` if OpenCV cannot decode the file or
        the result has a non-positive dimension.
    """
    try:
        import cv2
        import numpy as np

        # cv2.imread cannot handle non-ASCII paths on Windows; reading the bytes
        # ourselves and decoding from memory works regardless of the locale.
        buffer = np.fromfile(str(image_path), dtype=np.uint8)
        if buffer.size == 0:
            return None
        image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    except Exception as exc:  # noqa: BLE001 - any decoder failure means unusable
        LOGGER.debug("OpenCV failed on %s: %s", image_path, exc)
        return None

    if image is None or image.ndim < 2:
        return None
    height, width = image.shape[:2]
    if width <= 0 or height <= 0:
        return None
    return int(width), int(height)


def find_duplicate_boxes(boxes: Sequence[BoxRecord], *, tolerance: float = 1e-4) -> list[int]:
    """Return the indices of boxes that repeat an earlier box.

    Args:
        boxes: The boxes from one label file.
        tolerance: Coordinates closer than this on all four axes count as the
            same box. Loose enough to catch a re-export that re-rounded the
            numbers, tight enough not to merge two genuinely adjacent plates.

    Returns:
        Indices of the later copies. The first occurrence is not reported.
    """
    duplicates: list[int] = []
    for index, box in enumerate(boxes):
        for earlier in boxes[:index]:
            if (
                abs(box.x_center - earlier.x_center) < tolerance
                and abs(box.y_center - earlier.y_center) < tolerance
                and abs(box.width - earlier.width) < tolerance
                and abs(box.height - earlier.height) < tolerance
            ):
                duplicates.append(index)
                break
    return duplicates


def verify_image(
    image_path: Path,
    *,
    dataset: str,
    min_box_area: float,
    allow_missing_labels: bool,
    report: VerificationReport,
) -> None:
    """Run every check against one image and record what it finds.

    Args:
        image_path: The image to check.
        dataset: Slug used to group the per-dataset counters.
        min_box_area: Small-box warning threshold, as a fraction of image area.
        allow_missing_labels: Treat an absent label file as a deliberate
            background image rather than an error. Off by default: an
            accidentally missing label is far more common than an intentional
            background image, and the two are indistinguishable on disk.
        report: The report to append to. Mutated in place.
    """
    report.images_checked += 1
    counters = report.per_dataset[dataset]
    counters["images"] += 1
    had_error = False

    def _record(severity: str, code: str, detail: str, box_index: int | None = None) -> None:
        nonlocal had_error
        report.issues.append(
            Issue(
                image=image_path,
                severity=severity,
                code=code,
                detail=detail,
                box_index=box_index,
            )
        )
        counters[code] += 1
        if severity == SEVERITY_ERROR:
            had_error = True

    dimensions = load_image_dimensions(image_path)
    if dimensions is None:
        _record(
            SEVERITY_ERROR,
            "unreadable_image",
            "OpenCV cannot decode this file, or it decodes to a zero-sized image. "
            "It will fail during training; delete it or re-download the dataset.",
        )
        return

    width, height = dimensions

    label_path = image_path_to_label_path(image_path)
    if not label_path.is_file():
        if allow_missing_labels:
            _record(
                SEVERITY_WARNING,
                "missing_label",
                f"No label file at {label_path}; treated as a background image "
                "because --allow-missing-labels was given.",
            )
            report.boxes_per_image.append(0)
        else:
            _record(
                SEVERITY_ERROR,
                "missing_label",
                f"No label file at {label_path}. YOLO would silently treat this "
                "image as containing no plates. If that is intended, pass "
                "--allow-missing-labels; otherwise the annotation is lost.",
            )
        return

    try:
        boxes = parse_yolo_label_file(label_path)
    except LabelParseError as exc:
        _record(SEVERITY_ERROR, "unparseable_label", str(exc))
        return
    except OSError as exc:
        _record(SEVERITY_ERROR, "unreadable_label", f"Cannot read {label_path}: {exc}")
        return

    report.boxes_per_image.append(len(boxes))
    if not boxes:
        _record(
            SEVERITY_WARNING,
            "empty_label",
            "Label file is empty, so this is a background image with no plates. "
            "That is valid, but a whole dataset of these means a conversion failed.",
        )

    for box_index, box in enumerate(boxes):
        report.boxes_checked += 1
        counters["boxes"] += 1

        for message in box.validate(min_area=min_box_area):
            if message.startswith("warning:"):
                _record(
                    SEVERITY_WARNING,
                    "small_box",
                    message.removeprefix("warning:").strip(),
                    box_index,
                )
            else:
                _record(SEVERITY_ERROR, "invalid_box", message, box_index)

        # Geometry-derived statistics are only meaningful for valid boxes.
        if box.width > 0 and box.height > 0:
            report.box_areas.append(box.area)
            try:
                ratio = box.aspect_ratio_for(width, height)
            except ValueError:
                continue
            report.aspect_ratios.append(ratio)
            counters[f"line_estimate_{estimate_line_count(ratio)}"] += 1

    for duplicate_index in find_duplicate_boxes(boxes):
        _record(
            SEVERITY_WARNING,
            "duplicate_box",
            f"Box {duplicate_index} repeats an earlier box in the same file; "
            "this is usually a double annotation.",
            duplicate_index,
        )

    if not had_error:
        report.images_ok += 1


def summarise_aspect_ratios(ratios: Sequence[float]) -> dict[str, Any]:
    """Summarise the box aspect-ratio distribution and the line-count guess.

    Args:
        ratios: Every usable box aspect ratio.

    Returns:
        A JSON-serialisable summary, explicitly flagged as heuristic.
    """
    if not ratios:
        return {
            "count": 0,
            "note": "No usable boxes, so no aspect ratio distribution.",
        }

    one_line = sum(1 for ratio in ratios if ratio >= AR_ONE_LINE_MIN)
    two_line = len(ratios) - one_line

    summary = dict(summarise_distribution(ratios, "box_aspect_ratio"))
    summary.pop("name", None)
    summary |= {
        "threshold": AR_ONE_LINE_MIN,
        "estimated_one_line": one_line,
        "estimated_two_line": two_line,
        "estimated_two_line_ratio": round(two_line / len(ratios), 4),
        "method": "HEURISTIC",
        "method_note": (
            "Line count is inferred from box aspect ratio against the 2.5 "
            "threshold, derived from QCVN 08:2024/BCA nominal plate sizes "
            "(1-line car 520x110mm = 4.727; 2-line car 330x165mm = 2.000; "
            "motorcycle 190x140mm = 1.357). Perspective, loose boxes and bent "
            "plates all move a plate across the threshold, so these counts are "
            "an approximate distribution and NOT ground truth."
        ),
    }
    return summary


def build_summary(report: VerificationReport, min_box_area: float) -> dict[str, Any]:
    """Assemble the JSON report from an accumulated run.

    Args:
        report: The accumulated results.
        min_box_area: The small-box threshold that was in force.

    Returns:
        A JSON-serialisable summary.
    """
    by_code: Counter[str] = Counter()
    for issue in report.issues:
        by_code[f"{issue.severity}:{issue.code}"] += 1

    return {
        "images_checked": report.images_checked,
        "images_ok": report.images_ok,
        "images_with_errors": report.images_with_errors,
        "boxes_checked": report.boxes_checked,
        "errors": report.error_count,
        "warnings": report.warning_count,
        "issues_by_code": dict(sorted(by_code.items())),
        "min_box_area_threshold": min_box_area,
        "aspect_ratio": summarise_aspect_ratios(report.aspect_ratios),
        "box_area": summarise_distribution(report.box_areas, "box_area_fraction"),
        "boxes_per_image": summarise_distribution(
            [float(count) for count in report.boxes_per_image], "boxes_per_image"
        ),
        "per_dataset": {
            dataset: dict(sorted(counters.items()))
            for dataset, counters in sorted(report.per_dataset.items())
        },
    }


def dataset_name_for(image_path: Path, root: Path) -> str:
    """Attribute an image to a dataset by its first path component below ``root``.

    Args:
        image_path: The image.
        root: Scan root.

    Returns:
        The dataset slug, or ``root.name`` when the image sits directly in the
        root (the case when the root *is* one dataset's directory).
    """
    try:
        relative = image_path.relative_to(root)
    except ValueError:
        return "unknown"
    return relative.parts[0] if len(relative.parts) > 1 else root.name


def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line parser.

    Returns:
        The configured parser.
    """
    parser = argparse.ArgumentParser(
        prog="verify_annotations.py",
        description=(
            "Verify YOLO annotation quality: label presence, coordinate ranges, "
            "box geometry, image decodability, and the aspect-ratio distribution."
        ),
        epilog=(
            "Examples:\n"
            "  python verify_annotations.py --input-dir datasets/raw/vnlp\n"
            "  python verify_annotations.py --input-dir datasets/processed --strict\n\n"
            "Exit code is 0 unless --strict is given and errors were found."
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
        "--min-box-area",
        type=float,
        default=DEFAULT_MIN_BOX_AREA,
        metavar="FRACTION",
        help=(
            "Warn about boxes smaller than this fraction of the image area "
            "(default: %(default)s, i.e. 0.5%%). Pass 0 to disable."
        ),
    )
    parser.add_argument(
        "--allow-missing-labels",
        action="store_true",
        help=(
            "Treat an image with no label file as an intentional background "
            "image (warning) rather than a lost annotation (error)."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 when any error-severity issue is found.",
    )
    parser.add_argument(
        "--max-issues",
        type=int,
        default=0,
        metavar="N",
        help=(
            "Stop after recording this many issues, to keep a badly broken "
            "dataset from producing a gigantic report. 0 means no limit "
            "(default: %(default)s)."
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
        ``0`` on success, or ``1`` if the input directory is missing, contains
        no images, or (with ``--strict``) any error was found.
    """
    args = build_parser().parse_args(argv)
    configure_logging(args.log_level)

    paths = resolve_dataset_paths(args.datasets_dir)
    input_dir = (args.input_dir or paths.raw).expanduser().resolve()
    output_dir = (args.output_dir or paths.reports).expanduser().resolve()

    if not input_dir.is_dir():
        LOGGER.error("Input directory does not exist: %s", input_dir)
        LOGGER.error("Run download.py first, or pass --input-dir.")
        return 1

    image_paths = list(iter_image_files(input_dir))
    if not image_paths:
        LOGGER.error("No images found under %s", input_dir)
        return 1

    LOGGER.info("Verifying %d images under %s", len(image_paths), input_dir)
    report = VerificationReport()

    iterator: Iterable[Path] = image_paths
    if len(image_paths) >= 200:
        try:
            from tqdm import tqdm

            iterator = tqdm(image_paths, desc="Verifying", unit="img")
        except ImportError:
            pass

    truncated = False
    for image_path in iterator:
        verify_image(
            image_path,
            dataset=dataset_name_for(image_path, input_dir),
            min_box_area=args.min_box_area,
            allow_missing_labels=args.allow_missing_labels,
            report=report,
        )
        if args.max_issues and len(report.issues) >= args.max_issues:
            truncated = True
            LOGGER.warning(
                "Reached --max-issues=%d; stopping early. The report covers only "
                "the first %d images.",
                args.max_issues,
                report.images_checked,
            )
            break

    summary = build_summary(report, args.min_box_area)
    summary["input_dir"] = str(input_dir)
    summary["truncated"] = truncated

    write_json(output_dir / "annotation_verification.json", summary)
    write_csv(
        output_dir / "annotation_issues.csv",
        [issue.as_row() for issue in report.issues],
        fieldnames=["image", "severity", "code", "box_index", "detail"],
    )

    LOGGER.info("=" * 70)
    LOGGER.info(
        "Images clean : %s", format_count(report.images_ok, report.images_checked)
    )
    LOGGER.info("Boxes checked: %d", report.boxes_checked)
    LOGGER.info("Errors       : %d", report.error_count)
    LOGGER.info("Warnings     : %d", report.warning_count)
    for code, count in sorted(summary["issues_by_code"].items()):
        LOGGER.info("    %-32s %d", code, count)

    aspect = summary["aspect_ratio"]
    if aspect.get("count"):
        LOGGER.info(
            "Aspect ratio : median %.2f | HEURISTIC split: %d one-line, %d two-line",
            aspect["median"],
            aspect["estimated_one_line"],
            aspect["estimated_two_line"],
        )
        if aspect["estimated_two_line_ratio"] < 0.1:
            LOGGER.warning(
                "Only %.1f%% of boxes look like two-line plates. Two-line "
                "motorcycle plates are the known weak point (OpenALPR: 94.3%% on "
                "one-line cars vs 45.7%% on two-line motorcycles), so a dataset "
                "this skewed will not fix it.",
                100 * aspect["estimated_two_line_ratio"],
            )
    LOGGER.info("=" * 70)
    LOGGER.info("Reports written to %s", output_dir)

    if args.strict and report.error_count:
        LOGGER.error("--strict: %d error(s) found.", report.error_count)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
