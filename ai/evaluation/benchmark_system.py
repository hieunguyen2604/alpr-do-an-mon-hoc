"""Measure end-to-end system performance and latency breakdown against NFR-P targets."""

from __future__ import annotations

import argparse
import json
import logging
import os
import platform
import statistics
import sys
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

import numpy as np

from ai.evaluation.stress_test import percentiles

LOGGER = logging.getLogger("benchmark_system")

IMAGE_SUFFIXES: frozenset[str] = frozenset(
    {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
)

#: NFR-P targets, as (target, minimum_acceptable). ``None`` means no floor.
NFR_TARGETS: dict[str, dict[str, Any]] = {
    "NFR-P1": {"name": "E2E latency p95 (ms)", "target": 800.0, "floor": 1500.0},
    "NFR-P4": {"name": "Model load time (s)", "target": 15.0, "floor": None},
    "NFR-P7": {"name": "Backend RSS (GB)", "target": 2.0, "floor": None},
}


@dataclass
class StageTimings:
    """Wall-clock milliseconds for one image, split by pipeline stage."""

    decode_ms: float = 0.0
    detect_ms: float = 0.0
    crop_ms: float = 0.0
    ocr_ms: float = 0.0
    normalize_ms: float = 0.0
    total_ms: float = 0.0
    plates_found: int = 0


@dataclass
class HardwareInfo:
    """The machine the numbers below were measured on."""

    cpu_name: str
    physical_cores: int | None
    logical_cores: int | None
    ram_total_gb: float
    platform: str
    python_version: str
    torch_version: str = "n/a"
    torch_threads: int | None = None
    baseline_cpu_percent: float = 0.0
    competing_processes: list[str] = field(default_factory=list)


def describe_hardware(sample_seconds: float = 3.0) -> HardwareInfo:
    """Collect the hardware header, including any competing CPU load.

    The competing-process scan matters: this project's benchmark may well be run
    while a training job is still going, and a latency measured against a
    saturated CPU has to be labelled as such rather than published bare.
    """
    import psutil

    cpu_name = platform.processor() or "unknown"
    if platform.system() == "Windows":
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
            )
            cpu_name = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        except Exception:  # noqa: BLE001 - registry access is best-effort
            pass

    torch_version = "n/a"
    torch_threads: int | None = None
    try:
        import torch

        torch_version = torch.__version__
        torch_threads = torch.get_num_threads()
    except Exception:  # noqa: BLE001
        pass

    # Prime per-process CPU counters, wait, then read the deltas.
    procs = []
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            proc.cpu_percent(None)
            procs.append(proc)
        except Exception:  # noqa: BLE001
            continue
    psutil.cpu_percent(interval=None)
    time.sleep(sample_seconds)
    baseline = psutil.cpu_percent(interval=None)

    self_pid = os.getpid()
    competing: list[str] = []
    for proc in procs:
        try:
            usage = proc.cpu_percent(None)
            if usage < 25.0 or proc.pid == self_pid:
                continue
            cmd = " ".join(proc.info.get("cmdline") or [])[:140]
            competing.append(f"pid={proc.pid} cpu={usage:.0f}% {cmd or proc.info.get('name')}")
        except Exception:  # noqa: BLE001
            continue

    return HardwareInfo(
        cpu_name=cpu_name,
        physical_cores=psutil.cpu_count(logical=False),
        logical_cores=psutil.cpu_count(logical=True),
        ram_total_gb=round(psutil.virtual_memory().total / 1024**3, 2),
        platform=f"{platform.system()} {platform.release()}",
        python_version=platform.python_version(),
        torch_version=torch_version,
        torch_threads=torch_threads,
        baseline_cpu_percent=baseline,
        competing_processes=competing,
    )


def log_hardware(info: HardwareInfo) -> None:
    """Print the hardware header. Always called before any timing is reported."""
    LOGGER.info("=" * 72)
    LOGGER.info("MEASUREMENT ENVIRONMENT (every number below is relative to this)")
    LOGGER.info("=" * 72)
    LOGGER.info("CPU              : %s", info.cpu_name)
    LOGGER.info(
        "Cores            : %s physical / %s logical", info.physical_cores, info.logical_cores
    )
    LOGGER.info("RAM              : %.2f GB", info.ram_total_gb)
    LOGGER.info("OS / Python      : %s / %s", info.platform, info.python_version)
    LOGGER.info("torch            : %s (threads=%s)", info.torch_version, info.torch_threads)
    LOGGER.info("System CPU load  : %.1f%% during sampling", info.baseline_cpu_percent)
    if info.competing_processes:
        LOGGER.warning(
            "%d competing process(es) using >25%% CPU. Latencies below are "
            "PESSIMISTIC -- the CPU was shared:",
            len(info.competing_processes),
        )
        for entry in info.competing_processes:
            LOGGER.warning("    %s", entry)
    else:
        LOGGER.info("Competing load   : none detected (>25%% CPU)")
    LOGGER.info("=" * 72)


def discover_images(root: Path, limit: int) -> list[Path]:
    """Return up to ``limit`` images from ``root``, sorted for reproducibility."""
    if not root.is_dir():
        raise FileNotFoundError(f"Image directory not found: {root}")
    found = [
        path
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    ]
    if not found:
        raise FileNotFoundError(f"No images under {root}")
    return found[:limit] if limit > 0 else found


def measure_model_load(model_path: Path, device: str) -> tuple[Any, float]:
    """Build the pipeline, timing construction end to end (NFR-P4).

    Returns the pipeline and the elapsed seconds. Warmup is timed separately by
    the caller, because "load" and "first inference" are different costs and
    conflating them would misattribute several hundred milliseconds.
    """
    from ai.inference.config import InferenceConfig
    from ai.inference.pipeline import build_default_pipeline

    # from_env() truoc, chi ghi de truong benchmark nay so huu: dung
    # InferenceConfig() tran se ghim ALPR_RECTIFY/SR_RETRY vao mac dinh va phep
    # boc tach khong do duoc gi (loi da xay ra, sua 28/07).
    config = replace(
        InferenceConfig.from_env(),
        model_path=model_path,
        device=device,
    )
    started = time.perf_counter()
    pipeline = build_default_pipeline(config)
    elapsed = time.perf_counter() - started
    return pipeline, elapsed


def measure_stages(pipeline: Any, image_path: Path) -> StageTimings:
    """Time one image stage by stage, driving the components directly.

    The pipeline's own ``process`` returns a single total, which cannot answer
    "where does the time go". Calling detector / recogniser / normalizer in turn
    reproduces the same sequence while letting each boundary be timed. The
    resulting ``total_ms`` is therefore the sum of measured stages and will
    differ slightly from ``ALPRPipeline.process`` overhead, which is measured
    separately by :func:`measure_end_to_end`.
    """
    import cv2

    timings = StageTimings()

    started = time.perf_counter()
    image = cv2.imread(str(image_path))
    timings.decode_ms = (time.perf_counter() - started) * 1000.0
    if image is None:
        return timings

    started = time.perf_counter()
    detections = pipeline.detector.detect(image)
    timings.detect_ms = (time.perf_counter() - started) * 1000.0
    timings.plates_found = len(detections)

    for detection in detections:
        started = time.perf_counter()
        box = detection.bbox
        crop = image[box.y : box.y + box.height, box.x : box.x + box.width]
        timings.crop_ms += (time.perf_counter() - started) * 1000.0

        if crop.size == 0:
            continue

        started = time.perf_counter()
        try:
            recognition = pipeline.recognizer.recognize(crop)
        except Exception:  # noqa: BLE001 - a failed read is still a timed read
            recognition = None
        timings.ocr_ms += (time.perf_counter() - started) * 1000.0

        if recognition is None:
            continue

        started = time.perf_counter()
        try:
            pipeline.normalizer.normalize(recognition.raw_text or recognition.text)
        except Exception:  # noqa: BLE001
            pass
        timings.normalize_ms += (time.perf_counter() - started) * 1000.0

    timings.total_ms = (
        timings.decode_ms
        + timings.detect_ms
        + timings.crop_ms
        + timings.ocr_ms
        + timings.normalize_ms
    )
    return timings


def measure_end_to_end(pipeline: Any, images: Sequence[Path]) -> tuple[list[float], list[int]]:
    """Time ``ALPRPipeline.process`` per image -- the number NFR-P1 governs."""
    import cv2

    latencies: list[float] = []
    plate_counts: list[int] = []
    for index, path in enumerate(images):
        image = cv2.imread(str(path))
        if image is None:
            continue
        started = time.perf_counter()
        try:
            result = pipeline.process(image)
            plate_counts.append(len(result.results))
        except Exception as exc:  # noqa: BLE001
            LOGGER.debug("process() failed on %s: %s", path.name, exc)
            plate_counts.append(0)
        latencies.append((time.perf_counter() - started) * 1000.0)
        if index and index % 25 == 0:
            LOGGER.info("  ... %d/%d images", index, len(images))
    return latencies, plate_counts


def measure_detector_backend(
    weights: Path, images: Sequence[Path], device: str, imgsz: int
) -> dict[str, Any]:
    """Time the detector alone for one weights file (``.pt`` or ``.onnx``).

    Isolating the detector is what makes the PyTorch/ONNX comparison meaningful:
    OCR dominates the end-to-end budget, so a large relative speedup in the
    detector would be almost invisible if measured through the full pipeline.
    """
    import cv2
    from ultralytics import YOLO

    started = time.perf_counter()
    model = YOLO(str(weights), task="detect")
    load_s = time.perf_counter() - started

    decoded = [img for img in (cv2.imread(str(p)) for p in images) if img is not None]
    if not decoded:
        return {"error": "no decodable images"}

    # Warm up: the first call allocates buffers and, for ONNX, builds the graph.
    for _ in range(3):
        model.predict(decoded[0], imgsz=imgsz, device=device, verbose=False)

    latencies: list[float] = []
    for image in decoded:
        started = time.perf_counter()
        model.predict(image, imgsz=imgsz, device=device, verbose=False)
        latencies.append((time.perf_counter() - started) * 1000.0)

    return {
        "weights": str(weights),
        "load_seconds": round(load_s, 3),
        "latency": percentiles(latencies),
    }


def export_onnx(weights: Path, imgsz: int) -> Path | None:
    """Export the detector to ONNX, returning the path or ``None`` on failure."""
    try:
        from ultralytics import YOLO

        model = YOLO(str(weights))
        exported = model.export(format="onnx", imgsz=imgsz, dynamic=False, simplify=False)
        return Path(exported)
    except Exception as exc:  # noqa: BLE001 - export is optional
        LOGGER.warning("ONNX export failed (%s: %s)", type(exc).__name__, exc)
        return None


def process_rss_gb() -> float:
    """Resident set size of this process, in GB (NFR-P7)."""
    import psutil

    return round(psutil.Process(os.getpid()).memory_info().rss / 1024**3, 3)


def summarise_stage_budget(stage_rows: Sequence[StageTimings]) -> dict[str, Any]:
    """Aggregate per-stage timings into medians and percentage shares.

    Medians rather than means: one pathological image with a dozen plates would
    drag a mean and misrepresent the typical request the budget describes.
    """
    if not stage_rows:
        return {}

    fields = ["decode_ms", "detect_ms", "crop_ms", "ocr_ms", "normalize_ms"]
    medians = {
        field_name: round(statistics.median(getattr(row, field_name) for row in stage_rows), 2)
        for field_name in fields
    }
    total = sum(medians.values()) or 1.0
    shares = {field_name: round(100.0 * value / total, 1) for field_name, value in medians.items()}
    return {
        "median_ms": medians,
        "share_percent": shares,
        "median_total_ms": round(total, 2),
        "mean_plates_per_image": round(statistics.fmean(row.plates_found for row in stage_rows), 2),
        "samples": len(stage_rows),
    }


def plot_results(report: dict[str, Any], figures_dir: Path) -> list[str]:
    """Write the latency-distribution and stage-budget PNGs."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figures_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    raw = report.get("e2e_raw_latencies_ms") or []
    if raw:
        figure, axis = plt.subplots(figsize=(9, 4.5))
        axis.hist(raw, bins=40, color="#2563EB", edgecolor="white")
        for label, key, colour in (
            ("p50", "p50_ms", "#16A34A"),
            ("p95", "p95_ms", "#F59E0B"),
            ("p99", "p99_ms", "#DC2626"),
        ):
            value = report["nfr_p1_e2e_latency"].get(key)
            if value:
                axis.axvline(value, color=colour, linestyle="--", label=f"{label} = {value:.0f} ms")
        target = NFR_TARGETS["NFR-P1"]["target"]
        axis.axvline(target, color="#111827", linewidth=2, label=f"NFR-P1 target = {target:.0f} ms")
        axis.set_xlabel("End-to-end latency per image (ms)")
        axis.set_ylabel("Images")
        axis.set_title(f"NFR-P1 end-to-end latency\n{report['hardware']['cpu_name']}")
        axis.legend()
        figure.tight_layout()
        destination = figures_dir / "07-latency-distribution.png"
        figure.savefig(destination, dpi=150)
        plt.close(figure)
        written.append(str(destination))

    budget = report.get("latency_budget", {}).get("median_ms")
    if budget:
        figure, axis = plt.subplots(figsize=(9, 4.5))
        labels = [key.replace("_ms", "") for key in budget]
        values = list(budget.values())
        bars = axis.barh(labels, values, color="#2563EB")
        for bar, value in zip(bars, values, strict=True):
            axis.text(
                bar.get_width(),
                bar.get_y() + bar.get_height() / 2,
                f" {value:.1f} ms",
                va="center",
                fontsize=9,
            )
        axis.set_xlabel("Median milliseconds per image")
        axis.set_title(f"Measured latency budget by stage\n{report['hardware']['cpu_name']}")
        figure.tight_layout()
        destination = figures_dir / "07-latency-budget.png"
        figure.savefig(destination, dpi=150)
        plt.close(figure)
        written.append(str(destination))

    backends = report.get("detector_backend_comparison", {})
    pt = backends.get("pytorch", {}).get("latency", {})
    onnx = backends.get("onnx", {}).get("latency", {})
    if pt and onnx:
        figure, axis = plt.subplots(figsize=(8, 4.5))
        keys = ["p50_ms", "p95_ms", "p99_ms"]
        x = np.arange(len(keys))
        axis.bar(x - 0.2, [pt.get(k, 0) for k in keys], 0.4, label="PyTorch (.pt)", color="#2563EB")
        axis.bar(
            x + 0.2, [onnx.get(k, 0) for k in keys], 0.4, label="ONNX Runtime", color="#16A34A"
        )
        axis.set_xticks(x)
        axis.set_xticklabels([k.replace("_ms", "") for k in keys])
        axis.set_ylabel("Detector latency (ms)")
        axis.set_title(f"Detector backend comparison\n{report['hardware']['cpu_name']}")
        axis.legend()
        figure.tight_layout()
        destination = figures_dir / "07-backend-comparison.png"
        figure.savefig(destination, dpi=150)
        plt.close(figure)
        written.append(str(destination))

    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m ai.evaluation.benchmark_system",
        description="Measure end-to-end system performance against the NFR-P targets.",
    )
    # Mac dinh PHAI la mo hinh ban giao hang — tro nham checkpoint la moi so do
    # mo ta mot he thong khong ai giao, va khong co canh bao nao.
    parser.add_argument("--weights", default="models/best.pt")
    parser.add_argument("--images", default="datasets/processed/yolo/images/test")
    parser.add_argument(
        "--limit", type=int, default=100, help="Images for the E2E run (default: %(default)s)."
    )
    parser.add_argument(
        "--stage-limit",
        type=int,
        default=40,
        help="Images for the per-stage breakdown (default: %(default)s).",
    )
    parser.add_argument(
        "--backend-limit",
        type=int,
        default=50,
        help="Images for the PyTorch/ONNX comparison (default: %(default)s).",
    )
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--skip-onnx", action="store_true", help="Skip the ONNX comparison.")
    parser.add_argument("--output", default="docs/reports/07-benchmark-system.json")
    parser.add_argument("--figures-dir", default="docs/reports/figures")
    parser.add_argument("--no-plots", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    args = build_parser().parse_args(argv)

    hardware = describe_hardware()
    log_hardware(hardware)

    weights = Path(args.weights).expanduser().resolve()
    images_root = Path(args.images).expanduser().resolve()
    images = discover_images(images_root, args.limit)
    LOGGER.info("Using %d image(s) from %s", len(images), images_root)

    rss_before = process_rss_gb()

    LOGGER.info("Loading pipeline (NFR-P4)...")
    pipeline, load_seconds = measure_model_load(weights, args.device)
    LOGGER.info("Pipeline constructed in %.2f s", load_seconds)

    started = time.perf_counter()
    try:
        pipeline.warmup()
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("warmup() raised: %s", exc)
    warmup_seconds = time.perf_counter() - started
    LOGGER.info(
        "Warmup took %.2f s (ready after %.2f s total)",
        warmup_seconds,
        load_seconds + warmup_seconds,
    )

    rss_loaded = process_rss_gb()

    for path in images[: max(0, args.warmup)]:
        import cv2

        image = cv2.imread(str(path))
        if image is not None:
            try:
                pipeline.process(image)
            except Exception:  # noqa: BLE001
                pass

    LOGGER.info("Measuring end-to-end latency (NFR-P1) over %d image(s)...", len(images))
    latencies, plate_counts = measure_end_to_end(pipeline, images)
    e2e = percentiles(latencies)
    LOGGER.info("E2E latency: %s", e2e)

    LOGGER.info("Measuring per-stage latency budget over %d image(s)...", args.stage_limit)
    stage_rows = [measure_stages(pipeline, path) for path in images[: args.stage_limit]]
    budget = summarise_stage_budget(stage_rows)
    for name, value in budget.get("median_ms", {}).items():
        LOGGER.info("  %-14s %8.2f ms  (%4.1f%%)", name, value, budget["share_percent"][name])

    rss_peak = process_rss_gb()

    backends: dict[str, Any] = {}
    if not args.skip_onnx:
        backend_images = images[: args.backend_limit]
        LOGGER.info("Timing PyTorch detector backend...")
        backends["pytorch"] = measure_detector_backend(
            weights, backend_images, args.device, args.imgsz
        )
        LOGGER.info("Exporting ONNX...")
        onnx_path = export_onnx(weights, args.imgsz)
        if onnx_path and onnx_path.is_file():
            LOGGER.info("Timing ONNX detector backend...")
            backends["onnx"] = measure_detector_backend(
                onnx_path, backend_images, args.device, args.imgsz
            )
            pt_p50 = backends["pytorch"]["latency"]["p50_ms"]
            onnx_p50 = backends["onnx"]["latency"]["p50_ms"]
            if onnx_p50:
                speedup = pt_p50 / onnx_p50
                backends["speedup_p50"] = round(speedup, 3)
                LOGGER.info(
                    "ONNX speedup at p50: %.2fx (%.1f ms -> %.1f ms)",
                    speedup,
                    pt_p50,
                    onnx_p50,
                )
        else:
            backends["onnx"] = {"error": "export failed or file missing"}

    verdicts: dict[str, Any] = {}
    p95 = e2e.get("p95_ms")
    if p95 is not None:
        verdicts["NFR-P1"] = {
            "measured_p95_ms": p95,
            "target_ms": 800.0,
            "floor_ms": 1500.0,
            "meets_target": p95 <= 800.0,
            "meets_floor": p95 <= 1500.0,
            "margin_to_target_ms": round(800.0 - p95, 2),
        }
    ready_s = load_seconds + warmup_seconds
    verdicts["NFR-P4"] = {
        "measured_load_s": round(load_seconds, 2),
        "measured_warmup_s": round(warmup_seconds, 2),
        "measured_ready_s": round(ready_s, 2),
        "target_s": 15.0,
        "meets_target": ready_s <= 15.0,
    }
    verdicts["NFR-P7"] = {
        "rss_before_load_gb": rss_before,
        "rss_after_load_gb": rss_loaded,
        "rss_peak_gb": rss_peak,
        "target_gb": 2.0,
        "meets_target": rss_peak <= 2.0,
        "note": "In-process pipeline RSS. The FastAPI server adds its own overhead.",
    }

    report: dict[str, Any] = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "hardware": asdict(hardware),
        "weights": str(weights),
        "images_root": str(images_root),
        "image_count": len(images),
        "device": args.device,
        # Self-describing numbers: without this, a latency table gives no way to
        # tell an ablation run from a full-system run, and the two are only ever
        # comparable when the reader knows which is which.
        "retry_ladder": {
            "rectify_enabled": getattr(pipeline.config, "rectify_enabled", None),
            "sr_retry_enabled": getattr(pipeline.config, "sr_retry_enabled", None),
        },
        "nfr_p1_e2e_latency": e2e,
        "mean_plates_per_image": (
            round(statistics.fmean(plate_counts), 2) if plate_counts else 0.0
        ),
        "latency_budget": budget,
        "detector_backend_comparison": backends,
        "nfr_verdicts": verdicts,
        "e2e_raw_latencies_ms": [round(value, 2) for value in latencies],
    }

    if not args.no_plots:
        report["figures"] = plot_results(report, Path(args.figures_dir).expanduser().resolve())

    destination = Path(args.output).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    LOGGER.info("=" * 72)
    for requirement, verdict in verdicts.items():
        status = "PASS" if verdict.get("meets_target") else "FAIL"
        LOGGER.info(
            "%-8s %s  %s", requirement, status, NFR_TARGETS.get(requirement, {}).get("name", "")
        )
    LOGGER.info("Report written to %s", destination)
    LOGGER.info("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
