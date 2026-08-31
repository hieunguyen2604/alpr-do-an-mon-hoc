"""Group and export OCR failure cases by error taxonomy for visual inspection."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Sequence

from ai.evaluation.benchmark_ocr import DEFAULT_OUTPUT_DIR, align
from ai.inference.config import PROJECT_ROOT

__all__ = [
    "ERROR_CLASSES",
    "ErrorCase",
    "classify_error",
    "load_samples",
    "analyse",
    "export_cases",
    "main",
]

LOGGER = logging.getLogger("ai.evaluation.error_analysis")

DEFAULT_REPORT_PATH: Final[Path] = DEFAULT_OUTPUT_DIR / "ocr_benchmark.json"
"""Default location of the JSON produced by :mod:`ai.evaluation.benchmark_ocr`."""

DEFAULT_ERROR_DIR: Final[Path] = DEFAULT_OUTPUT_DIR / "errors"
"""Default directory receiving the exported failing crops."""

ERROR_CLASSES: Final[tuple[str, ...]] = (
    "correct",
    "empty_read",
    "substitution",
    "missing_chars",
    "extra_chars",
    "transposition",
    "mixed",
)
"""Every class :func:`classify_error` can return, in report order."""

_ANNOTATION_WIDTH: Final[int] = 480
_ANNOTATION_BAR_HEIGHT: Final[int] = 68
_FILENAME_SAFE: Final[frozenset[str]] = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
)


@dataclass(frozen=True, slots=True)
class ErrorCase:
    """One misread crop, classified."""

    image_path: str
    ground_truth: str
    prediction: str
    error_class: str
    line_count: int
    substitutions: tuple[tuple[str, str], ...]
    deleted: tuple[str, ...]
    inserted: tuple[str, ...]
    error_positions: tuple[int, ...]
    confidence: float

    @property
    def is_error(self) -> bool:
        """Return ``True`` when this case is not a correct read."""
        return self.error_class != "correct"


def classify_error(ground_truth: str, prediction: str) -> tuple[str, dict[str, Any]]:
    """Assign one error class to a prediction and describe the edit operations."""
    operations = align(ground_truth, prediction)
    substitutions: list[tuple[str, str]] = []
    deleted: list[str] = []
    inserted: list[str] = []
    error_positions: list[int] = []

    reference_index = 0
    for operation, ref_char, hyp_char in operations:
        if operation == "equal":
            reference_index += 1
        elif operation == "substitute":
            substitutions.append((ref_char, hyp_char))
            error_positions.append(reference_index)
            reference_index += 1
        elif operation == "delete":
            deleted.append(ref_char)
            error_positions.append(reference_index)
            reference_index += 1
        else:
            inserted.append(hyp_char)

    detail: dict[str, Any] = {
        "substitutions": tuple(substitutions),
        "deleted": tuple(deleted),
        "inserted": tuple(inserted),
        "error_positions": tuple(error_positions),
    }

    if prediction == ground_truth:
        return "correct", detail
    if not prediction:
        return "empty_read", detail
    if sorted(prediction) == sorted(ground_truth):
        return "transposition", detail

    kinds = {
        bool(substitutions) and "substitution",
        bool(deleted) and "missing_chars",
        bool(inserted) and "extra_chars",
    } - {False}
    if len(kinds) == 1:
        return next(iter(kinds)), detail
    return "mixed", detail


def load_samples(report_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read the per-crop records out of a benchmark JSON report."""
    if not report_path.is_file():
        raise FileNotFoundError(
            f"Benchmark report not found: {report_path}\n"
            "Produce it first:\n"
            "  python -m ai.evaluation.benchmark_ocr"
        )
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{report_path} is not valid JSON: {error}") from error

    samples = payload.get("samples")
    if not samples:
        raise ValueError(
            f"{report_path} carries no per-crop samples; it may have been "
            "written by an older version of the benchmark."
        )
    metadata = {
        "engine": payload.get("engine", "unknown"),
        "generated_at": payload.get("generated_at", "unknown"),
        "settings": payload.get("settings", {}),
        "summary": payload.get("summary", {}),
    }
    return samples, metadata


def analyse(samples: Sequence[dict[str, Any]], stage: str) -> list[ErrorCase]:
    """Classify every sample of a benchmark run."""
    if stage not in ("normalized", "raw"):
        raise ValueError(f"stage must be 'normalized' or 'raw', got {stage!r}")
    key = "post_norm_text" if stage == "normalized" else "pre_norm_text"

    cases: list[ErrorCase] = []
    for sample in samples:
        truth = sample.get("ground_truth", "")
        prediction = sample.get(key, "")
        error_class, detail = classify_error(truth, prediction)
        cases.append(
            ErrorCase(
                image_path=sample.get("image_path", ""),
                ground_truth=truth,
                prediction=prediction,
                error_class=error_class,
                line_count=int(sample.get("line_count", 0) or 0),
                substitutions=detail["substitutions"],
                deleted=detail["deleted"],
                inserted=detail["inserted"],
                error_positions=detail["error_positions"],
                confidence=float(sample.get("confidence", 0.0) or 0.0),
            )
        )
    return cases


def _safe_stem(text: str, fallback: str = "empty") -> str:
    """Reduce a plate string to characters that are safe in a filename."""
    cleaned = "".join(char if char in _FILENAME_SAFE else "-" for char in text)
    return cleaned[:24] or fallback


def _annotate(image: Any, case: ErrorCase) -> Any:
    """Draw the true and predicted strings underneath a crop."""
    import cv2
    import numpy as np

    height, width = image.shape[0], image.shape[1]
    scale = _ANNOTATION_WIDTH / max(width, 1)
    resized = cv2.resize(
        image,
        (_ANNOTATION_WIDTH, max(1, int(height * scale))),
        interpolation=cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA,
    )
    if resized.ndim == 2:
        resized = cv2.cvtColor(resized, cv2.COLOR_GRAY2BGR)

    bar = np.full((_ANNOTATION_BAR_HEIGHT, _ANNOTATION_WIDTH, 3), 255, dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(bar, f"GT  : {case.ground_truth}", (8, 22), font, 0.55, (0, 120, 0), 1, cv2.LINE_AA)
    cv2.putText(
        bar,
        f"PRED: {case.prediction or '(empty)'}",
        (8, 44),
        font,
        0.55,
        (0, 0, 200),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        bar,
        f"{case.error_class} | {case.line_count} line(s) | conf {case.confidence:.2f}",
        (8, 62),
        font,
        0.42,
        (90, 90, 90),
        1,
        cv2.LINE_AA,
    )
    return np.vstack((resized, bar))


def export_cases(
    cases: Sequence[ErrorCase], output_dir: Path, annotate: bool, limit_per_class: int
) -> dict[str, int]:
    """Copy the failing crops into one directory per error class."""
    exported: Counter[str] = Counter()
    grouped: dict[str, list[ErrorCase]] = defaultdict(list)
    for case in cases:
        if case.is_error:
            grouped[case.error_class].append(case)

    cv2: Any = None
    if annotate:
        try:
            import cv2 as _cv2

            cv2 = _cv2
        except ImportError as error:
            LOGGER.warning("OpenCV unavailable, exporting plain copies: %s", error)

    for error_class, class_cases in grouped.items():
        class_dir = output_dir / error_class
        if class_dir.exists():
            shutil.rmtree(class_dir, ignore_errors=True)
        class_dir.mkdir(parents=True, exist_ok=True)

        selected = class_cases[:limit_per_class] if limit_per_class > 0 else class_cases
        for index, case in enumerate(selected, start=1):
            source = Path(case.image_path)
            if not source.is_file():
                LOGGER.warning("Crop no longer on disk, not exported: %s", source)
                continue
            stem = (
                f"{index:04d}_gt-{_safe_stem(case.ground_truth)}"
                f"_pred-{_safe_stem(case.prediction)}"
            )
            try:
                if cv2 is not None:
                    image = cv2.imread(str(source))
                    if image is None:
                        raise OSError("cannot decode")
                    destination = class_dir / f"{stem}.png"
                    if not cv2.imwrite(str(destination), _annotate(image, case)):
                        raise OSError("cannot write")
                else:
                    destination = class_dir / f"{stem}{source.suffix}"
                    shutil.copy2(source, destination)
            except (OSError, ValueError) as error:
                LOGGER.warning("Could not export %s: %s", source, error)
                continue
            exported[error_class] += 1

    return dict(exported)


def _class_counts(cases: Sequence[ErrorCase]) -> dict[str, int]:
    """Count cases per error class, including the classes that never occurred."""
    counter = Counter(case.error_class for case in cases)
    return {name: counter.get(name, 0) for name in ERROR_CLASSES}


def _summary_payload(
    cases: Sequence[ErrorCase], metadata: dict[str, Any], stage: str
) -> dict[str, Any]:
    """Assemble the analysis summary."""
    errors = [case for case in cases if case.is_error]
    substitutions: Counter[tuple[str, str]] = Counter()
    positions: Counter[int] = Counter()
    lengths: Counter[int] = Counter()
    for case in errors:
        substitutions.update(case.substitutions)
        positions.update(case.error_positions)
        lengths[len(case.ground_truth)] += 1

    by_line_count: dict[str, dict[str, int]] = {}
    for line_count in (1, 2):
        subset = [case for case in cases if case.line_count == line_count]
        by_line_count[f"{line_count}_line"] = {
            "total": len(subset),
            **_class_counts(subset),
        }

    return {
        "source_report": metadata,
        "stage": stage,
        "total_cases": len(cases),
        "total_errors": len(errors),
        "error_rate": round(len(errors) / len(cases), 4) if cases else 0.0,
        "by_class": _class_counts(cases),
        "by_line_count": by_line_count,
        "top_substitutions": [
            {"true": true, "predicted": predicted, "count": count}
            for (true, predicted), count in substitutions.most_common(30)
        ],
        "error_positions": {str(k): v for k, v in sorted(positions.items())},
        "ground_truth_lengths_of_failures": {str(k): v for k, v in sorted(lengths.items())},
        "confident_but_wrong": [
            {
                "image_path": case.image_path,
                "ground_truth": case.ground_truth,
                "prediction": case.prediction,
                "confidence": round(case.confidence, 4),
                "error_class": case.error_class,
            }
            for case in sorted(errors, key=lambda c: c.confidence, reverse=True)[:20]
        ],
    }


def _write_csv(cases: Sequence[ErrorCase], destination: Path) -> None:
    """Write every failing case to a CSV for manual review in a spreadsheet."""
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "error_class",
                "line_count",
                "ground_truth",
                "prediction",
                "substitutions",
                "deleted",
                "inserted",
                "error_positions",
                "confidence",
                "image_path",
            ]
        )
        for case in cases:
            if not case.is_error:
                continue
            writer.writerow(
                [
                    case.error_class,
                    case.line_count,
                    case.ground_truth,
                    case.prediction,
                    " ".join(f"{a}>{b}" for a, b in case.substitutions),
                    "".join(case.deleted),
                    "".join(case.inserted),
                    " ".join(str(p) for p in case.error_positions),
                    f"{case.confidence:.4f}",
                    case.image_path,
                ]
            )


def _write_markdown(payload: dict[str, Any], destination: Path) -> None:
    """Render the analysis as a Markdown summary."""
    total = payload["total_cases"]
    lines: list[str] = [
        "# Phan tich loi OCR",
        "",
        f"- Bao cao nguon sinh luc: `{payload['source_report']['generated_at']}`",
        f"- Engine: `{payload['source_report']['engine']}`",
        f"- Chuoi duoc phan tich: `{payload['stage']}`",
        f"- Tong so mau: **{total}**, so mau sai: **{payload['total_errors']}** "
        f"({payload['error_rate'] * 100:.1f}%)",
        "",
        "## 1. Phan bo theo loai loi",
        "",
        "| Loai loi | So mau | Ty le |",
        "|---|---|---|",
    ]
    for name, count in payload["by_class"].items():
        share = f"{count / total * 100:.1f}%" if total else "-"
        lines.append(f"| `{name}` | {count} | {share} |")

    lines.extend(
        [
            "",
            "## 2. Phan bo theo so dong",
            "",
            "| Loai loi | Bien 1 dong | Bien 2 dong |",
            "|---|---|---|",
        ]
    )
    one = payload["by_line_count"]["1_line"]
    two = payload["by_line_count"]["2_line"]
    lines.append(f"| **Tong so mau** | {one['total']} | {two['total']} |")
    for name in ERROR_CLASSES:
        lines.append(f"| `{name}` | {one.get(name, 0)} | {two.get(name, 0)} |")

    lines.extend(
        [
            "",
            "## 3. Cac cap ky tu bi nham nhieu nhat",
            "",
            "| That | Doc thanh | So lan |",
            "|---|---|---|",
        ]
    )
    if payload["top_substitutions"]:
        lines.extend(
            f"| `{item['true']}` | `{item['predicted']}` | {item['count']} |"
            for item in payload["top_substitutions"][:20]
        )
    else:
        lines.append("| _khong co_ | - | - |")

    lines.extend(
        [
            "",
            "## 4. Vi tri ky tu hay sai",
            "",
            "| Vi tri (0-based) | So lan sai |",
            "|---|---|",
        ]
    )
    if payload["error_positions"]:
        lines.extend(
            f"| {position} | {count} |" for position, count in payload["error_positions"].items()
        )
    else:
        lines.append("| _khong co_ | - |")

    lines.extend(
        [
            "",
            "## 5. Sai nhung do tin cay cao",
            "",
            "Day la kieu loi nguy hiem nhat: he thong sai ma van tu tin, nen khong",
            "the dung nguong do tin cay de loc bo.",
            "",
            "| Do tin cay | That | Doc thanh | Loai loi |",
            "|---|---|---|---|",
        ]
    )
    if payload["confident_but_wrong"]:
        lines.extend(
            f"| {item['confidence']:.3f} | `{item['ground_truth']}` "
            f"| `{item['prediction'] or '(rong)'}` | `{item['error_class']}` |"
            for item in payload["confident_but_wrong"]
        )
    else:
        lines.append("| _khong co_ | - | - | - |")

    lines.append("")
    destination.write_text("\n".join(lines), encoding="utf-8")


def _write_chart(payload: dict[str, Any], destination: Path) -> bool:
    """Render the error-class distribution as a bar chart."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as error:
        LOGGER.warning("Chart skipped, Matplotlib unavailable: %s", error)
        return False

    try:
        classes = [name for name in ERROR_CLASSES if name != "correct"]
        one = [payload["by_line_count"]["1_line"].get(name, 0) for name in classes]
        two = [payload["by_line_count"]["2_line"].get(name, 0) for name in classes]
        positions = np.arange(len(classes))
        width = 0.38

        figure, axes = plt.subplots(figsize=(9, 5))
        axes.bar(positions - width / 2, one, width, label="Bien 1 dong")
        axes.bar(positions + width / 2, two, width, label="Bien 2 dong")
        axes.set_xticks(positions, classes, rotation=20, ha="right")
        axes.set_ylabel("So mau sai")
        axes.set_title("Phan bo loai loi OCR theo so dong bien so")
        axes.legend()
        axes.grid(axis="y", alpha=0.3)
        figure.tight_layout()
        figure.savefig(destination, dpi=150)
        plt.close(figure)
        return True
    except Exception as error:  # noqa: BLE001 - charts are best-effort
        LOGGER.warning("Could not render the error chart: %s", error)
        return False


def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="python -m ai.evaluation.error_analysis",
        description=(
            "Group the OCR failures of a benchmark run by error class and "
            "export the failing crops for visual review."
        ),
        epilog=(
            "Run the benchmark first:\n"
            "  python -m ai.evaluation.benchmark_ocr\n"
            "then analyse its report:\n"
            "  python -m ai.evaluation.error_analysis --annotate\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help=f"Benchmark JSON to analyse (default: {DEFAULT_REPORT_PATH}).",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_ERROR_DIR),
        help=f"Where the analysis is written (default: {DEFAULT_ERROR_DIR}).",
    )
    parser.add_argument(
        "--stage",
        default="normalized",
        choices=("normalized", "raw"),
        help=(
            "Which prediction to analyse: 'normalized' is what the system "
            "reports, 'raw' is what the engine read (default: normalized)."
        ),
    )
    parser.add_argument(
        "--annotate",
        action="store_true",
        help="Append a caption with the true and predicted strings to each crop.",
    )
    parser.add_argument(
        "--limit-per-class",
        type=int,
        default=100,
        help="Cap on crops exported per error class (0 = all; default: 100).",
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Compute the statistics without copying any image.",
    )
    return parser


def _resolve(path: str | Path) -> Path:
    """Resolve a path against the repository root when it is relative."""
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )

    report_path = _resolve(args.report)
    try:
        samples, metadata = load_samples(report_path)
    except (FileNotFoundError, ValueError) as error:
        LOGGER.error("%s", error)
        return 2
    except OSError as error:
        LOGGER.error("Cannot read %s: %s", report_path, error)
        return 2

    try:
        cases = analyse(samples, args.stage)
    except ValueError as error:
        LOGGER.error("%s", error)
        return 2

    payload = _summary_payload(cases, metadata, args.stage)

    LOGGER.info("=" * 78)
    LOGGER.info("OCR error analysis -- %s predictions", args.stage)
    LOGGER.info("=" * 78)
    LOGGER.info(
        "Cases: %d, errors: %d (%.1f%%)",
        payload["total_cases"],
        payload["total_errors"],
        payload["error_rate"] * 100,
    )
    for name, count in payload["by_class"].items():
        LOGGER.info("  %-14s %5d", name, count)

    output_dir = _resolve(args.output_dir)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "error_analysis.json"
        json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        _write_csv(cases, output_dir / "error_cases.csv")
        _write_markdown(payload, output_dir / "error_analysis.md")
    except OSError as error:
        LOGGER.error("Cannot write the analysis into %s: %s", output_dir, error)
        return 1

    _write_chart(payload, output_dir / "error_classes.png")

    if not args.no_export:
        exported = export_cases(cases, output_dir, args.annotate, args.limit_per_class)
        for error_class, count in sorted(exported.items()):
            LOGGER.info("Exported %d crop(s) into %s", count, output_dir / error_class)

    LOGGER.info("Analysis written to %s", output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
