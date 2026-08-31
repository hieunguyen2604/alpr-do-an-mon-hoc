"""Benchmark PyTorch vs ONNX vs OpenVINO inference latency on CPU."""

from __future__ import annotations

import argparse
import json
import logging
import os
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Sequence

from ai.training.config import DEFAULT_MODELS_DIR, PROJECT_ROOT

__all__ = ["collect_cpu_info", "benchmark_backend", "main"]

LOGGER = logging.getLogger("ai.evaluation.benchmark_cpu")

DEFAULT_OUTPUT_DIR: Final[Path] = PROJECT_ROOT / "docs" / "reports"

_IMAGE_SUFFIXES: Final[frozenset[str]] = frozenset({".jpg", ".jpeg", ".png", ".bmp", ".webp"})

# Backend name -> (file suffix produced by ai.training.export, human label).
_BACKENDS: Final[dict[str, tuple[str, str]]] = {
    "pytorch": (".pt", "PyTorch (eager, CPU)"),
    "onnx": (".onnx", "ONNX Runtime (CPU)"),
    "openvino": ("_openvino_model", "OpenVINO (Intel CPU)"),
    "torchscript": (".torchscript", "TorchScript (CPU)"),
}


def collect_cpu_info() -> dict[str, Any]:
    """Describe the CPU and thread configuration the benchmark ran on."""
    info: dict[str, Any] = {
        "system": f"{platform.system()} {platform.release()}",
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
        "processor_identifier": os.environ.get("PROCESSOR_IDENTIFIER", "unknown"),
        "python": platform.python_version(),
        "logical_cores": os.cpu_count() or 0,
        "physical_cores": "unknown",
        "max_frequency_mhz": "unknown",
        "total_ram_gb": "unknown",
    }
    try:
        import psutil

        info["physical_cores"] = psutil.cpu_count(logical=False) or "unknown"
        frequency = psutil.cpu_freq()
        if frequency is not None:
            info["max_frequency_mhz"] = round(frequency.max, 1)
        info["total_ram_gb"] = round(psutil.virtual_memory().total / (1024**3), 1)
    except ImportError:
        LOGGER.warning(
            "psutil is not installed; physical core count and RAM are unknown. "
            "Install it for a complete hardware record: pip install psutil"
        )
    except Exception as error:  # noqa: BLE001 - hardware probing is best-effort
        LOGGER.warning("Could not query hardware details: %s", error)

    try:
        import torch

        info["torch_version"] = torch.__version__
        info["torch_threads"] = torch.get_num_threads()
    except ImportError:
        info["torch_version"] = "not installed"
    return info


def discover_images(source: Path, limit: int) -> list[Path]:
    """Collect the images to benchmark on."""
    if not source.exists():
        raise FileNotFoundError(
            f"Benchmark image source not found: {source}\n"
            "Pass --images pointing at a directory of real photographs. "
            "Synthetic frames would understate decode cost and overstate speed."
        )
    if source.is_file():
        images = [source]
    else:
        images = sorted(p for p in source.rglob("*") if p.suffix.lower() in _IMAGE_SUFFIXES)
    if not images:
        raise FileNotFoundError(f"No images found under {source}")
    return images[:limit] if limit > 0 else images


def resolve_backend_path(weights: Path, backend: str) -> Path | None:
    """Locate the exported artefact for a backend, next to the .pt checkpoint."""
    suffix, _ = _BACKENDS[backend]
    if backend == "pytorch":
        return weights if weights.is_file() else None
    if backend == "openvino":
        candidate = weights.with_name(f"{weights.stem}{suffix}")
        return candidate if candidate.is_dir() else None
    candidate = weights.with_suffix(suffix)
    return candidate if candidate.is_file() else None


def benchmark_backend(
    model_path: Path,
    images: Sequence[Path],
    imgsz: int,
    runs: int,
    warmup: int,
) -> dict[str, Any]:
    """Time one backend over a fixed set of images."""
    try:
        from ultralytics import YOLO
    except ImportError as error:  # pragma: no cover - environment problem
        return {"ok": False, "error": f"ultralytics unavailable: {error}"}

    result: dict[str, Any] = {"ok": False, "model_path": str(model_path)}
    try:
        model = YOLO(str(model_path), task="detect")
    except Exception as error:  # noqa: BLE001 - a missing runtime is expected here
        result["error"] = f"cannot load: {type(error).__name__}: {error}"
        return result

    def sample(index: int) -> Path:
        return images[index % len(images)]

    try:
        for index in range(max(0, warmup)):
            model.predict(str(sample(index)), imgsz=imgsz, device="cpu", verbose=False)
    except Exception as error:  # noqa: BLE001
        result["error"] = f"warm-up failed: {type(error).__name__}: {error}"
        return result

    latencies: list[float] = []
    try:
        for index in range(runs):
            started = time.perf_counter()
            model.predict(str(sample(index)), imgsz=imgsz, device="cpu", verbose=False)
            latencies.append((time.perf_counter() - started) * 1000.0)
    except Exception as error:  # noqa: BLE001
        result["error"] = f"inference failed: {type(error).__name__}: {error}"
        return result

    ordered = sorted(latencies)

    def percentile(fraction: float) -> float:
        rank = max(1, min(len(ordered), int(round(fraction * len(ordered)))))
        return ordered[rank - 1]

    mean = statistics.fmean(ordered)
    result.update(
        {
            "ok": True,
            "runs": len(ordered),
            "mean_ms": round(mean, 2),
            "median_ms": round(statistics.median(ordered), 2),
            "stdev_ms": round(statistics.stdev(ordered), 2) if len(ordered) > 1 else 0.0,
            "p50_ms": round(percentile(0.50), 2),
            "p95_ms": round(percentile(0.95), 2),
            "p99_ms": round(percentile(0.99), 2),
            "min_ms": round(ordered[0], 2),
            "max_ms": round(ordered[-1], 2),
            "fps_mean": round(1000.0 / mean, 2) if mean > 0 else 0.0,
        }
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="python -m ai.evaluation.benchmark_cpu",
        description=(
            "Measure detector inference latency on this machine's CPU across "
            "PyTorch / ONNX / OpenVINO / TorchScript. Numbers produced here are "
            "the only CPU figures that may be quoted in the thesis."
        ),
        epilog=(
            "Export the other formats first:\n"
            "  python -m ai.training.export --weights models/best.pt --format all\n"
            "\n"
            "Then benchmark:\n"
            "  python -m ai.evaluation.benchmark_cpu --weights models/best.pt "
            "--images datasets/processed/test/images\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--weights",
        default=str(DEFAULT_MODELS_DIR / "best.pt"),
        help=(
            "Base .pt checkpoint. Exported artefacts are looked up beside it "
            "(best.onnx, best_openvino_model/, best.torchscript)."
        ),
    )
    parser.add_argument(
        "--images",
        default=str(PROJECT_ROOT / "datasets" / "processed" / "test" / "images"),
        help="Directory (or single file) of REAL images to benchmark on.",
    )
    parser.add_argument(
        "--backends",
        nargs="+",
        default=["pytorch", "onnx", "openvino"],
        choices=sorted(_BACKENDS),
        help="Backends to compare (default: pytorch onnx openvino).",
    )
    parser.add_argument("--imgsz", type=int, default=640, help="Inference image size.")
    parser.add_argument(
        "--runs", type=int, default=50, help="Timed inferences per backend (default: 50)."
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=5,
        help="Discarded warm-up inferences per backend (default: 5).",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=50,
        help="Cap on images loaded from --images (0 = all; default: 50).",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=0,
        help=(
            "Pin the PyTorch intra-op thread count (0 = library default). Set it "
            "to compare single-thread against multi-thread behaviour."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Where the JSON result goes (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--no-save", action="store_true", help="Print results without writing JSON."
    )
    return parser


def _resolve(path: str | Path) -> Path:
    """Resolve a path against the repository root when relative."""
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

    if args.threads > 0:
        try:
            import torch

            torch.set_num_threads(args.threads)
            LOGGER.info("PyTorch intra-op threads pinned to %d", args.threads)
        except ImportError:
            LOGGER.error("torch is not installed; --threads ignored")

    cpu_info = collect_cpu_info()
    LOGGER.info("=" * 78)
    LOGGER.info("CPU inference benchmark -- measured on THIS machine")
    LOGGER.info("=" * 78)
    for key, value in cpu_info.items():
        LOGGER.info("  %-22s %s", key, value)

    weights = _resolve(args.weights)
    try:
        images = discover_images(_resolve(args.images), args.max_images)
    except FileNotFoundError as error:
        LOGGER.error("%s", error)
        return 1
    LOGGER.info("Images        : %d from %s", len(images), args.images)
    LOGGER.info("Runs/backend  : %d (plus %d warm-up)", args.runs, args.warmup)
    LOGGER.info("Image size    : %d", args.imgsz)

    results: dict[str, dict[str, Any]] = {}
    for backend in args.backends:
        model_path = resolve_backend_path(weights, backend)
        if model_path is None:
            LOGGER.warning(
                "Skipping %s: no artefact found. Export it first: "
                "python -m ai.training.export --weights %s --format %s",
                backend,
                weights,
                backend if backend != "pytorch" else "onnx",
            )
            results[backend] = {"ok": False, "error": "artefact not found"}
            continue
        LOGGER.info("Benchmarking %s (%s)...", backend, model_path.name)
        results[backend] = benchmark_backend(model_path, images, args.imgsz, args.runs, args.warmup)
        if not results[backend]["ok"]:
            LOGGER.error("  %s failed: %s", backend, results[backend].get("error"))

    successful = {name: data for name, data in results.items() if data.get("ok")}
    if not successful:
        LOGGER.error(
            "No backend could be benchmarked. Export the model first:\n"
            "  python -m ai.training.export --weights %s --format all",
            weights,
        )
        return 1

    baseline = successful.get("pytorch", {}).get("mean_ms")
    header = (
        f"{'BACKEND':<14}{'MEAN':>9}{'p50':>9}{'p95':>9}{'p99':>9}"
        f"{'MIN':>9}{'MAX':>9}{'FPS':>8}{'SPEEDUP':>10}"
    )
    LOGGER.info("=" * len(header))
    LOGGER.info(header)
    LOGGER.info("-" * len(header))
    for name, data in results.items():
        if not data.get("ok"):
            LOGGER.info("%-14s%s", name, "  (unavailable)")
            continue
        speedup = f"{baseline / data['mean_ms']:.2f}x" if baseline and data["mean_ms"] > 0 else "-"
        LOGGER.info(
            "%-14s%9.2f%9.2f%9.2f%9.2f%9.2f%9.2f%8.1f%10s",
            name,
            data["mean_ms"],
            data["p50_ms"],
            data["p95_ms"],
            data["p99_ms"],
            data["min_ms"],
            data["max_ms"],
            data["fps_mean"],
            speedup,
        )
    LOGGER.info("=" * len(header))
    LOGGER.info("All timings in milliseconds, batch = 1, speedup relative to PyTorch.")

    if args.no_save:
        return 0

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cpu": cpu_info,
        "settings": {
            "weights": str(weights),
            "images_source": str(_resolve(args.images)),
            "num_images": len(images),
            "imgsz": args.imgsz,
            "runs": args.runs,
            "warmup": args.warmup,
            "threads": args.threads or "library default",
        },
        "results": results,
    }
    output_dir = _resolve(args.output_dir)
    destination = output_dir / "03-cpu-benchmark.json"
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
    except OSError as error:
        LOGGER.error("Cannot write %s: %s", destination, error)
        return 1
    LOGGER.info("Results written to %s", destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
