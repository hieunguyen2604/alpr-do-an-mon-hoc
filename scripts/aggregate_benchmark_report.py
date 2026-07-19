"""Consolidate the Phase 7 measurements into one report and its figures.

This script does no measuring of its own. It reads the JSON written by the
individual benchmarks, assembles a single NFR verdict table, and emits
``docs/reports/07-benchmark-data.json`` plus the data-leakage figure.

Inputs (each optional -- a missing file becomes a recorded gap, not a crash):
    docs/reports/07-benchmark-system.json          ai.evaluation.benchmark_system
    docs/reports/07-stress-load.json               ai.evaluation.stress_test
    docs/reports/07-stress-db.json                 scripts/benchmark_history_query.py
    docs/reports/07-leak-check.json                ai.evaluation.leak_check (t=5)
    docs/reports/07-leak-check-t10.json            ai.evaluation.leak_check (t=10)
    docs/reports/03-evaluation-07-detection-test.json   ai.evaluation.evaluate

The verdict table records, for every requirement, the measured value, the
target, and the shortfall when the target was missed. A missed target is
reported as a number, never softened into a phrase.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

LOGGER = logging.getLogger("aggregate_benchmark")


def load_json(path: Path) -> dict[str, Any] | None:
    """Read a JSON report, returning ``None`` when it has not been produced."""
    if not path.is_file():
        LOGGER.warning("Missing input: %s", path)
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Could not parse %s (%s)", path, exc)
        return None


def verdict(
    requirement: str,
    description: str,
    measured: float | None,
    target: float,
    unit: str,
    lower_is_better: bool = True,
    floor: float | None = None,
) -> dict[str, Any]:
    """Build one verdict row, including the signed shortfall when it fails."""
    if measured is None:
        return {
            "requirement": requirement,
            "description": description,
            "measured": None,
            "target": target,
            "unit": unit,
            "status": "NOT_MEASURED",
        }

    passed = measured <= target if lower_is_better else measured >= target
    row: dict[str, Any] = {
        "requirement": requirement,
        "description": description,
        "measured": round(measured, 4),
        "target": target,
        "unit": unit,
        "status": "PASS" if passed else "FAIL",
    }
    if not passed:
        shortfall = measured - target if lower_is_better else target - measured
        row["shortfall"] = round(shortfall, 4)
        row["times_over_target"] = (
            round(measured / target, 2) if lower_is_better and target else None
        )
    if floor is not None:
        row["minimum_acceptable"] = floor
        row["meets_minimum"] = measured <= floor if lower_is_better else measured >= floor
    return row


def plot_leak_distribution(dataset_root: Path, destination: Path) -> str | None:
    """Plot, for each test image, the Hamming distance to its nearest train image.

    This is the figure that settles the "is the split contaminated" question. The
    dedup threshold used when the dataset was built is drawn on it, because the
    absence of pairs below that line is a consequence of the build process and
    not independent evidence of anything.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from ai.evaluation.leak_check import discover_images, hamming_matrix, hash_split
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Cannot plot leak distribution (%s)", exc)
        return None

    images_root = dataset_root / "images"
    if not (images_root / "train").is_dir() or not (images_root / "test").is_dir():
        LOGGER.warning("Train/test directories not found under %s", images_root)
        return None

    LOGGER.info("Hashing train and test splits for the leakage figure...")
    train = hash_split("train", discover_images(images_root / "train"))
    test = hash_split("test", discover_images(images_root / "test"))
    distances = hamming_matrix(test.bits, train.bits)
    nearest = distances.min(axis=1)

    destination.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(9, 4.5))
    axis.hist(nearest, bins=range(0, int(nearest.max()) + 2), color="#2563EB", edgecolor="white")
    axis.axvline(
        5.5, color="#DC2626", linestyle="--", linewidth=2,
        label="dedup threshold used when building the split (5)",
    )
    axis.set_xlabel("Hamming distance from a test image to its nearest train image (64-bit phash)")
    axis.set_ylabel("Test images")
    axis.set_title("Train/test proximity: nothing below 5 by construction, not by luck")
    axis.legend()
    figure.tight_layout()
    figure.savefig(destination, dpi=150)
    plt.close(figure)

    return str(destination)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python scripts/aggregate_benchmark_report.py",
        description="Consolidate the Phase 7 benchmark JSON into one report.",
    )
    parser.add_argument("--reports-dir", default="docs/reports")
    parser.add_argument("--dataset", default="datasets/processed/yolo")
    parser.add_argument("--output", default="docs/reports/07-benchmark-data.json")
    parser.add_argument("--no-plots", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    args = build_parser().parse_args(argv)
    reports = Path(args.reports_dir).expanduser().resolve()

    system = load_json(reports / "07-benchmark-system.json")
    load = load_json(reports / "07-stress-load.json")
    database = load_json(reports / "07-stress-db.json")
    leak5 = load_json(reports / "07-leak-check.json")
    leak10 = load_json(reports / "07-leak-check-t10.json")
    detection = load_json(reports / "03-evaluation-07-detection-test.json")
    api = load_json(reports / "07-api-overhead.json")

    hardware = (system or {}).get("hardware") or (load or {}).get("hardware") or {}

    rows: list[dict[str, Any]] = []

    if system:
        e2e = system.get("nfr_p1_e2e_latency", {})
        rows.append(
            verdict("NFR-P1", "End-to-end latency for one image, p95",
                    e2e.get("p95_ms"), 800.0, "ms", floor=1500.0)
        )
        p4 = system.get("nfr_verdicts", {}).get("NFR-P4", {})
        rows.append(
            verdict("NFR-P4", "Model load to pipeline ready",
                    p4.get("measured_ready_s"), 15.0, "s")
        )
        p7 = system.get("nfr_verdicts", {}).get("NFR-P7", {})
        rows.append(
            verdict("NFR-P7a", "Resident memory of the in-process pipeline",
                    p7.get("rss_peak_gb"), 2.0, "GB")
        )

    if api:
        overhead = api.get("nfr_p5_api_overhead", {}).get("overhead", {})
        rows.append(
            verdict("NFR-P5", "API overhead above pipeline time, p95",
                    overhead.get("p95_ms"), 50.0, "ms", floor=100.0)
        )
        startup = api.get("nfr_p4_startup", {})
        rows.append(
            verdict("NFR-P4b", "Server start until /health reports ready",
                    startup.get("measured_s"), 15.0, "s")
        )
        rows.append(
            verdict("NFR-P7b", "Resident memory of the uvicorn server under load",
                    api.get("nfr_p7_server_rss", {}).get("measured_gb"), 2.0, "GB")
        )

    if load and "concurrency" in load:
        concurrency = load["concurrency"]
        rows.append(
            verdict("NFR-SC1", "Highest error-free concurrency",
                    float(concurrency.get("max_error_free_concurrency", 0)), 5.0,
                    "concurrent requests", lower_is_better=False)
        )
    if load and "soak" in load:
        rows.append(
            verdict("NFR-R4", "Success rate during the soak",
                    load["soak"].get("success_rate"), 0.99, "fraction",
                    lower_is_better=False)
        )

    if database:
        payload = database.get("nfr_p6_history_query", {})
        rows.append(
            verdict("NFR-P6", "History query over 10,000 rows, worst p95",
                    payload.get("worst_p95_ms"), 500.0, "ms")
        )

    if detection:
        reference = detection.get("metrics_reference_ultralytics", {})
        rows.append(verdict("NFR-A1", "Detection mAP@0.5",
                            reference.get("mAP@0.5"), 0.90, "", lower_is_better=False))
        rows.append(verdict("NFR-A2", "Detection mAP@0.5:0.95",
                            reference.get("mAP@0.5:0.95"), 0.65, "", lower_is_better=False))
        rows.append(verdict("NFR-A3a", "Detection precision",
                            reference.get("precision"), 0.92, "", lower_is_better=False))
        rows.append(verdict("NFR-A3b", "Detection recall",
                            reference.get("recall"), 0.90, "", lower_is_better=False))

    passes = sum(1 for row in rows if row["status"] == "PASS")
    failures = [row["requirement"] for row in rows if row["status"] == "FAIL"]

    leakage: dict[str, Any] = {}
    if leak5:
        leakage["at_threshold_5"] = {
            "cross_split_near_duplicate_pairs": leak5.get(
                "total_cross_split_near_duplicate_pairs"
            ),
            "verdict": leak5.get("verdict"),
            "comparisons": leak5.get("cross_split_comparisons"),
            "within_split": leak5.get("within_split"),
            "circularity_warning": (
                "The dataset build pipeline (scripts/dataset/deduplicate.py) groups "
                "images with imagehash.phash at DEFAULT_THRESHOLD = 5 and "
                "scripts/dataset/split.py keeps each duplicate group whole inside one "
                "split. This check uses the same hash and the same threshold, so a "
                "result of zero pairs is guaranteed by construction. It confirms the "
                "splitter did its job; it is NOT independent evidence that the task "
                "is hard or that the split is free of contamination."
            ),
        }
    if leak10:
        leakage["at_threshold_10"] = {
            "cross_split_near_duplicate_pairs": leak10.get(
                "total_cross_split_near_duplicate_pairs"
            ),
            "verdict": leak10.get("verdict"),
            "note": (
                "Distances 6-10 are the band the splitter did NOT protect. Visual "
                "inspection of the closest pairs found the same vehicle and the same "
                "plate string present in both train and test."
            ),
        }

    report: dict[str, Any] = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "hardware": hardware,
        "nfr_verdicts": rows,
        "summary": {
            "requirements_checked": len(rows),
            "passed": passes,
            "failed": len(failures),
            "failed_requirements": failures,
        },
        "detection_accuracy": detection,
        "system_performance": system,
        "load_and_soak": load,
        "database_performance": database,
        "api_overhead": api,
        "data_leakage": leakage,
    }

    if not args.no_plots:
        figure = plot_leak_distribution(
            Path(args.dataset).expanduser().resolve(),
            reports / "figures" / "07-leak-distance-distribution.png",
        )
        if figure:
            report["data_leakage"]["figure"] = figure

    destination = Path(args.output).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    LOGGER.info("=" * 72)
    for row in rows:
        LOGGER.info(
            "%-9s %-12s %-42s measured=%s target=%s",
            row["requirement"], row["status"], row["description"],
            row["measured"], row["target"],
        )
    LOGGER.info("-" * 72)
    LOGGER.info("%d/%d requirements met. Failing: %s",
                passes, len(rows), ", ".join(failures) or "none")
    LOGGER.info("Report written to %s", destination)
    LOGGER.info("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
