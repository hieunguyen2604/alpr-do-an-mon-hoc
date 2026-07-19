"""Load and soak tests for the recognition pipeline (NFR-SC1, NFR-R4).

Two questions, two sections
---------------------------
1. **Concurrency (NFR-SC1, target >= 5 simultaneous requests).** Fire N requests
   at once for N in {1, 2, 5, 10} and record throughput and error rate. On a
   CPU-bound pipeline the interesting result is usually *not* the error rate --
   it is that throughput stops rising once N exceeds the available cores,
   because the work was never I/O-bound to begin with.
2. **Soak (NFR-R4, target >= 99% success).** Run continuously for a set duration
   and report the success rate, sampling resident memory at both ends so a leak
   shows up as a number rather than a suspicion. Short benchmarks miss gradual
   degradation; the soak is what catches a pipeline that works for a minute and
   dies after ten.

Where the database benchmark went
---------------------------------
NFR-P6 (history query at 10,000 rows) is measured by
``scripts/benchmark_history_query.py``, **not** here. Timing the real query
requires importing ``backend.repositories``, and NFR-M1 forbids the ``ai``
package from depending on the service tier. ``scripts/`` may depend on both, so
that is where it lives; ``tests/test_architecture.py`` enforces the boundary.

Example:
    python -m ai.evaluation.stress_test --soak-seconds 300
"""

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
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger("stress_test")

IMAGE_SUFFIXES: frozenset[str] = frozenset({".jpg", ".jpeg", ".png", ".bmp", ".webp"})

#: Concurrency levels probed for NFR-SC1.
DEFAULT_CONCURRENCY: tuple[int, ...] = (1, 2, 5, 10)

#: NFR-R4 target success rate during the soak.
R4_TARGET_RATE: float = 0.99


@dataclass
class RequestOutcome:
    """One pipeline invocation: how long it took and whether it worked."""

    latency_ms: float
    ok: bool
    error: str | None = None
    plates: int = 0


@dataclass
class ConcurrencyResult:
    """Aggregate for one concurrency level."""

    concurrency: int
    requests: int
    successes: int
    failures: int
    wall_seconds: float
    throughput_rps: float
    latency: dict[str, float] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def error_rate(self) -> float:
        return self.failures / self.requests if self.requests else 0.0


def describe_hardware() -> dict[str, Any]:
    """Hardware header. Reported before any throughput figure, without exception."""
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
        except Exception:  # noqa: BLE001
            pass

    competing: list[str] = []
    procs = []
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            proc.cpu_percent(None)
            procs.append(proc)
        except Exception:  # noqa: BLE001
            continue
    time.sleep(2.0)
    for proc in procs:
        try:
            usage = proc.cpu_percent(None)
            if usage >= 25.0 and proc.pid != os.getpid() and proc.info.get("name") != "System Idle Process":
                cmd = " ".join(proc.info.get("cmdline") or [])[:120]
                competing.append(f"pid={proc.pid} cpu={usage:.0f}% {cmd or proc.info.get('name')}")
        except Exception:  # noqa: BLE001
            continue

    return {
        "cpu_name": cpu_name,
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "ram_total_gb": round(psutil.virtual_memory().total / 1024**3, 2),
        "platform": f"{platform.system()} {platform.release()}",
        "python_version": platform.python_version(),
        "competing_processes": competing,
    }


def percentiles(values: Sequence[float]) -> dict[str, float]:
    """p50/p95/p99 plus mean/min/max."""
    if not values:
        return {}
    ordered = sorted(values)

    def pick(fraction: float) -> float:
        if len(ordered) == 1:
            return ordered[0]
        index = min(len(ordered) - 1, max(0, int(round(fraction * (len(ordered) - 1)))))
        return ordered[index]

    return {
        "samples": len(ordered),
        "mean_ms": round(statistics.fmean(ordered), 2),
        "p50_ms": round(pick(0.50), 2),
        "p95_ms": round(pick(0.95), 2),
        "p99_ms": round(pick(0.99), 2),
        "min_ms": round(ordered[0], 2),
        "max_ms": round(ordered[-1], 2),
    }


def discover_images(root: Path, limit: int) -> list[Path]:
    """Return up to ``limit`` images from ``root``."""
    found = [
        path
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    ]
    if not found:
        raise FileNotFoundError(f"No images under {root}")
    return found[:limit] if limit > 0 else found


def build_pipeline(weights: Path, device: str) -> Any:
    """Construct and warm up the pipeline used by every load section."""
    from ai.inference.config import InferenceConfig
    from ai.inference.pipeline import build_default_pipeline

    pipeline = build_default_pipeline(InferenceConfig(model_path=weights, device=device))
    pipeline.warmup()
    return pipeline


def invoke_once(pipeline: Any, image: Any) -> RequestOutcome:
    """Run one image through the pipeline, converting a failure into a datum.

    Exceptions are captured rather than raised: a stress test whose purpose is
    to measure an error rate cannot itself abort on the first error.
    """
    started = time.perf_counter()
    try:
        result = pipeline.process(image)
        elapsed = (time.perf_counter() - started) * 1000.0
        return RequestOutcome(latency_ms=elapsed, ok=True, plates=len(result.results))
    except Exception as exc:  # noqa: BLE001
        elapsed = (time.perf_counter() - started) * 1000.0
        return RequestOutcome(
            latency_ms=elapsed, ok=False, error=f"{type(exc).__name__}: {exc}"
        )


def run_concurrency_level(
    pipeline: Any, images: Sequence[Any], concurrency: int, requests: int
) -> ConcurrencyResult:
    """Send ``requests`` invocations with ``concurrency`` of them in flight."""
    outcomes: list[RequestOutcome] = []
    started = time.perf_counter()

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [
            pool.submit(invoke_once, pipeline, images[index % len(images)])
            for index in range(requests)
        ]
        for future in as_completed(futures):
            outcomes.append(future.result())

    wall = time.perf_counter() - started
    successes = sum(1 for outcome in outcomes if outcome.ok)
    failures = len(outcomes) - successes
    errors = sorted({outcome.error for outcome in outcomes if outcome.error})[:5]

    return ConcurrencyResult(
        concurrency=concurrency,
        requests=len(outcomes),
        successes=successes,
        failures=failures,
        wall_seconds=round(wall, 3),
        throughput_rps=round(len(outcomes) / wall, 3) if wall else 0.0,
        latency=percentiles([outcome.latency_ms for outcome in outcomes]),
        errors=[error for error in errors if error],
    )


def run_soak(
    pipeline: Any, images: Sequence[Any], duration_seconds: float, concurrency: int
) -> dict[str, Any]:
    """Drive the pipeline continuously, reporting the success rate (NFR-R4).

    Memory is sampled at start and end so that a leak shows up as a number
    rather than as a vague suspicion.
    """
    import psutil

    process = psutil.Process(os.getpid())
    rss_start = process.memory_info().rss / 1024**3

    outcomes: list[RequestOutcome] = []
    deadline = time.perf_counter() + duration_seconds
    index = 0
    last_log = time.perf_counter()

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        pending: set[Any] = set()
        while time.perf_counter() < deadline:
            while len(pending) < concurrency:
                pending.add(pool.submit(invoke_once, pipeline, images[index % len(images)]))
                index += 1
            done = {future for future in pending if future.done()}
            for future in done:
                outcomes.append(future.result())
            pending -= done
            if time.perf_counter() - last_log > 30.0:
                remaining = deadline - time.perf_counter()
                LOGGER.info(
                    "  soak: %d request(s) done, %.0f s remaining", len(outcomes), remaining
                )
                last_log = time.perf_counter()
            time.sleep(0.01)
        for future in pending:
            outcomes.append(future.result())

    rss_end = process.memory_info().rss / 1024**3
    successes = sum(1 for outcome in outcomes if outcome.ok)
    rate = successes / len(outcomes) if outcomes else 0.0

    return {
        "duration_seconds": round(duration_seconds, 1),
        "concurrency": concurrency,
        "requests": len(outcomes),
        "successes": successes,
        "failures": len(outcomes) - successes,
        "success_rate": round(rate, 5),
        "target_rate": R4_TARGET_RATE,
        "meets_target": rate >= R4_TARGET_RATE,
        "throughput_rps": round(len(outcomes) / duration_seconds, 3) if duration_seconds else 0.0,
        "latency": percentiles([outcome.latency_ms for outcome in outcomes]),
        "rss_start_gb": round(rss_start, 3),
        "rss_end_gb": round(rss_end, 3),
        "rss_growth_gb": round(rss_end - rss_start, 3),
        "errors": sorted({outcome.error for outcome in outcomes if outcome.error})[:5],
    }


def plot_concurrency(results: Sequence[ConcurrencyResult], destination: Path) -> str | None:
    """Throughput and latency against concurrency."""
    if not results:
        return None
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    destination.parent.mkdir(parents=True, exist_ok=True)
    levels = [entry.concurrency for entry in results]
    throughput = [entry.throughput_rps for entry in results]
    p95 = [entry.latency.get("p95_ms", 0.0) for entry in results]

    figure, axis = plt.subplots(figsize=(9, 4.5))
    axis.plot(levels, throughput, marker="o", color="#2563EB", label="Throughput (req/s)")
    axis.set_xlabel("Concurrent requests")
    axis.set_ylabel("Throughput (req/s)", color="#2563EB")
    axis.set_xticks(levels)

    twin = axis.twinx()
    twin.plot(levels, p95, marker="s", color="#DC2626", label="p95 latency (ms)")
    twin.set_ylabel("p95 latency (ms)", color="#DC2626")

    axis.set_title("Throughput and latency versus concurrency (NFR-SC1)")
    figure.tight_layout()
    figure.savefig(destination, dpi=150)
    plt.close(figure)
    return str(destination)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m ai.evaluation.stress_test",
        description="Concurrency, soak and history-query-at-scale tests.",
    )
    parser.add_argument("--weights", default="models/checkpoints/best-cpu-epoch7.pt")
    parser.add_argument("--images", default="datasets/processed/yolo/images/test")
    parser.add_argument("--image-pool", type=int, default=20)
    parser.add_argument(
        "--concurrency", type=int, nargs="+", default=list(DEFAULT_CONCURRENCY)
    )
    parser.add_argument(
        "--requests-per-level",
        type=int,
        default=20,
        help="Requests sent at each concurrency level (default: %(default)s).",
    )
    parser.add_argument(
        "--soak-seconds", type=float, default=300.0, help="Soak duration (default: 300)."
    )
    parser.add_argument("--soak-concurrency", type=int, default=2)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output", default="docs/reports/07-stress-test.json")
    parser.add_argument("--figures-dir", default="docs/reports/figures")
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    args = build_parser().parse_args(argv)

    hardware = describe_hardware()
    LOGGER.info("=" * 72)
    LOGGER.info("CPU: %s | %s physical / %s logical cores | %.2f GB RAM",
                hardware["cpu_name"], hardware["physical_cores"],
                hardware["logical_cores"], hardware["ram_total_gb"])
    if hardware["competing_processes"]:
        LOGGER.warning("Competing CPU load present -- throughput below is PESSIMISTIC:")
        for entry in hardware["competing_processes"]:
            LOGGER.warning("    %s", entry)
    LOGGER.info("=" * 72)

    report: dict[str, Any] = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "hardware": hardware,
    }

    import cv2

    weights = Path(args.weights).expanduser().resolve()
    image_paths = discover_images(
        Path(args.images).expanduser().resolve(), args.image_pool
    )
    images = [img for img in (cv2.imread(str(p)) for p in image_paths) if img is not None]
    LOGGER.info("Loaded %d image(s) into memory", len(images))

    LOGGER.info("Building pipeline...")
    pipeline = build_pipeline(weights, args.device)

    LOGGER.info("--- Concurrency sweep (NFR-SC1) ---")
    concurrency_results: list[ConcurrencyResult] = []
    for level in args.concurrency:
        LOGGER.info("Concurrency %d: sending %d request(s)...", level, args.requests_per_level)
        result = run_concurrency_level(pipeline, images, level, args.requests_per_level)
        concurrency_results.append(result)
        LOGGER.info(
            "  throughput=%.3f req/s  p95=%.0f ms  errors=%d/%d",
            result.throughput_rps,
            result.latency.get("p95_ms", 0.0),
            result.failures,
            result.requests,
        )

    best = max(concurrency_results, key=lambda entry: entry.throughput_rps)
    stable = [entry for entry in concurrency_results if entry.error_rate == 0.0]
    report["concurrency"] = {
        "levels": [
            {
                "concurrency": entry.concurrency,
                "requests": entry.requests,
                "successes": entry.successes,
                "failures": entry.failures,
                "error_rate": round(entry.error_rate, 5),
                "wall_seconds": entry.wall_seconds,
                "throughput_rps": entry.throughput_rps,
                "latency": entry.latency,
                "errors": entry.errors,
            }
            for entry in concurrency_results
        ],
        "peak_throughput_rps": best.throughput_rps,
        "peak_throughput_at_concurrency": best.concurrency,
        "max_error_free_concurrency": max((e.concurrency for e in stable), default=0),
        "nfr_sc1_target_concurrency": 5,
        "meets_nfr_sc1": max((e.concurrency for e in stable), default=0) >= 5,
    }

    figure = plot_concurrency(
        concurrency_results,
        Path(args.figures_dir).expanduser().resolve() / "07-concurrency.png",
    )
    if figure:
        report["concurrency"]["figure"] = figure

    if args.soak_seconds > 0:
        LOGGER.info("--- Soak for %.0f s (NFR-R4) ---", args.soak_seconds)
        report["soak"] = run_soak(
            pipeline, images, args.soak_seconds, args.soak_concurrency
        )
        LOGGER.info(
            "Soak: %d request(s), success rate %.4f (%s), RSS %+.3f GB",
            report["soak"]["requests"],
            report["soak"]["success_rate"],
            "PASS" if report["soak"]["meets_target"] else "FAIL",
            report["soak"]["rss_growth_gb"],
        )

    destination = Path(args.output).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    LOGGER.info("=" * 72)
    if "concurrency" in report:
        LOGGER.info(
            "NFR-SC1 %s  (error-free up to concurrency %d, target 5)",
            "PASS" if report["concurrency"]["meets_nfr_sc1"] else "FAIL",
            report["concurrency"]["max_error_free_concurrency"],
        )
    if "soak" in report:
        LOGGER.info(
            "NFR-R4  %s  (success rate %.4f, target %.2f)",
            "PASS" if report["soak"]["meets_target"] else "FAIL",
            report["soak"]["success_rate"],
            R4_TARGET_RATE,
        )
    LOGGER.info("Report written to %s", destination)
    LOGGER.info("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
