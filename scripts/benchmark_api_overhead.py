"""Measure the HTTP layer's cost on top of the pipeline (NFR-P5, P4, P7).

Three numbers that can only be measured against a real server
-------------------------------------------------------------
=========== ============================================================ ========
Requirement Quantity                                                     Target
=========== ============================================================ ========
NFR-P5      API overhead = wall-clock request time - pipeline time       <= 50 ms
NFR-P4      Process start until ``/health`` answers ready                <= 15 s
NFR-P7      Resident memory of the server process under load             <= 2 GB
=========== ============================================================ ========

Why a real server and not ``TestClient``
----------------------------------------
``TestClient`` calls the ASGI app in-process, which skips the socket, the HTTP
parser and the uvicorn event loop -- exactly the layers NFR-P5 is about. This
script therefore launches uvicorn as a subprocess and talks to it over real
HTTP, so the measured overhead includes everything a browser would pay for
except the network itself.

The overhead subtraction relies on the response's ``processing_time`` field,
which the service reports for the pipeline portion. Overhead is the difference
between what the client waited and what the pipeline spent. A negative value
would mean the two clocks disagree and is reported rather than clamped.

Example:
    python scripts/benchmark_api_overhead.py --requests 30
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ai.evaluation.stress_test import describe_hardware, percentiles  # noqa: E402

LOGGER = logging.getLogger("benchmark_api_overhead")

P5_TARGET_MS: float = 50.0
P4_TARGET_S: float = 15.0
P7_TARGET_GB: float = 2.0

IMAGE_SUFFIXES: frozenset[str] = frozenset({".jpg", ".jpeg", ".png", ".bmp", ".webp"})


def start_server(port: int, weights: Path, log_path: Path) -> subprocess.Popen[bytes]:
    """Launch uvicorn in a subprocess, pointed at the given detector weights."""
    environment = dict(os.environ)
    environment["ALPR_MODEL_PATH"] = str(weights)
    environment["PYTHONPATH"] = str(_PROJECT_ROOT)

    handle = log_path.open("wb")
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=str(_PROJECT_ROOT),
        env=environment,
        stdout=handle,
        stderr=subprocess.STDOUT,
    )


def wait_for_ready(base_url: str, timeout_s: float) -> tuple[float | None, dict[str, Any]]:
    """Poll ``/health`` until it answers, returning the elapsed seconds (NFR-P4)."""
    import httpx

    started = time.perf_counter()
    deadline = started + timeout_s
    last: dict[str, Any] = {}
    while time.perf_counter() < deadline:
        try:
            response = httpx.get(f"{base_url}/health", timeout=5.0)
            if response.status_code == 200:
                last = response.json()
                return time.perf_counter() - started, last
        except Exception:  # noqa: BLE001 - the server is simply not up yet
            pass
        time.sleep(0.15)
    return None, last


def discover_images(root: Path, limit: int) -> list[Path]:
    found = [
        path
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    ]
    if not found:
        raise FileNotFoundError(f"No images under {root}")
    return found[:limit] if limit > 0 else found


def measure_overhead(
    base_url: str, api_prefix: str, images: list[Path], warmup: int
) -> dict[str, Any]:
    """POST each image and split the wall time into pipeline time and overhead."""
    import httpx

    endpoint = f"{base_url}{api_prefix}/detect/image"
    wall_ms: list[float] = []
    pipeline_ms: list[float] = []
    overhead_ms: list[float] = []
    failures: list[str] = []

    with httpx.Client(timeout=120.0) as client:
        for index, path in enumerate(images):
            payload = path.read_bytes()
            started = time.perf_counter()
            try:
                response = client.post(endpoint, files={"file": (path.name, payload, "image/jpeg")})
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{type(exc).__name__}: {exc}")
                continue
            elapsed = (time.perf_counter() - started) * 1000.0

            if response.status_code != 200:
                failures.append(f"HTTP {response.status_code}: {response.text[:160]}")
                continue
            if index < warmup:
                continue

            body = response.json()
            processing_s = body.get("processing_time")
            if processing_s is None:
                failures.append("response has no processing_time field")
                continue

            wall_ms.append(elapsed)
            pipeline_ms.append(processing_s * 1000.0)
            overhead_ms.append(elapsed - processing_s * 1000.0)

    return {
        "requests_measured": len(wall_ms),
        "wall_clock": percentiles(wall_ms),
        "pipeline_reported": percentiles(pipeline_ms),
        "overhead": percentiles(overhead_ms),
        "failures": failures[:5],
        "failure_count": len(failures),
    }


def server_rss_gb(pid: int) -> float | None:
    """Resident memory of the server process and its children, in GB (NFR-P7)."""
    try:
        import psutil

        process = psutil.Process(pid)
        total = process.memory_info().rss
        for child in process.children(recursive=True):
            try:
                total += child.memory_info().rss
            except Exception:  # noqa: BLE001
                continue
        return round(total / 1024**3, 3)
    except Exception:  # noqa: BLE001
        return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python scripts/benchmark_api_overhead.py",
        description="Measure API overhead, startup time and server memory.",
    )
    parser.add_argument("--weights", default="models/checkpoints/best-cpu-epoch7.pt")
    parser.add_argument("--images", default="datasets/processed/yolo/images/test")
    parser.add_argument("--requests", type=int, default=30)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--port", type=int, default=8931)
    parser.add_argument("--api-prefix", default="/api")
    parser.add_argument("--startup-timeout", type=float, default=120.0)
    parser.add_argument("--output", default="docs/reports/07-api-overhead.json")
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
    LOGGER.info(
        "CPU: %s | %s physical / %s logical cores | %.2f GB RAM",
        hardware["cpu_name"],
        hardware["physical_cores"],
        hardware["logical_cores"],
        hardware["ram_total_gb"],
    )
    if hardware["competing_processes"]:
        LOGGER.warning("Competing CPU load present -- timings below are PESSIMISTIC:")
        for entry in hardware["competing_processes"]:
            LOGGER.warning("    %s", entry)
    LOGGER.info("=" * 72)

    weights = Path(args.weights).expanduser().resolve()
    images = discover_images(Path(args.images).expanduser().resolve(), args.requests)
    base_url = f"http://127.0.0.1:{args.port}"
    log_path = Path(args.output).expanduser().resolve().with_suffix(".server.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Starting uvicorn on port %d ...", args.port)
    server = start_server(args.port, weights, log_path)
    report: dict[str, Any] = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "hardware": hardware,
        "weights": str(weights),
        "server_log": str(log_path),
    }

    try:
        ready_s, health = wait_for_ready(base_url, args.startup_timeout)
        if ready_s is None:
            LOGGER.error(
                "Server did not become ready within %.0f s. See %s",
                args.startup_timeout,
                log_path,
            )
            report["error"] = "server did not become ready"
            report["nfr_p4_startup"] = {"measured_s": None, "status": "NOT_MEASURED"}
        else:
            LOGGER.info(
                "/health ready after %.2f s (model_loaded=%s)", ready_s, health.get("model_loaded")
            )
            report["nfr_p4_startup"] = {
                "measured_s": round(ready_s, 2),
                "target_s": P4_TARGET_S,
                "status": "PASS" if ready_s <= P4_TARGET_S else "FAIL",
                "health": health,
            }

            if not health.get("model_loaded", False):
                LOGGER.warning(
                    "model_loaded is false -- the server is running a degraded "
                    "pipeline, so the overhead below is NOT measured against real "
                    "inference. Treat it as invalid."
                )
                report["warning"] = (
                    "model_loaded=false; overhead not measured against real inference"
                )

            LOGGER.info("Sending %d request(s) to /detect/image ...", len(images))
            overhead = measure_overhead(base_url, args.api_prefix, images, args.warmup)
            report["nfr_p5_api_overhead"] = overhead

            rss = server_rss_gb(server.pid)
            report["nfr_p7_server_rss"] = {
                "measured_gb": rss,
                "target_gb": P7_TARGET_GB,
                "status": ("PASS" if rss is not None and rss <= P7_TARGET_GB else "FAIL"),
                "note": "uvicorn process plus children, sampled after the load.",
            }

            p95 = overhead.get("overhead", {}).get("p95_ms")
            if p95 is not None:
                overhead["target_ms"] = P5_TARGET_MS
                overhead["status"] = "PASS" if p95 <= P5_TARGET_MS else "FAIL"
                LOGGER.info(
                    "Overhead p50=%.2f ms p95=%.2f ms (target %.0f ms) -- %s",
                    overhead["overhead"]["p50_ms"],
                    p95,
                    P5_TARGET_MS,
                    overhead["status"],
                )
                LOGGER.info(
                    "  wall p50=%.1f ms | pipeline p50=%.1f ms",
                    overhead["wall_clock"]["p50_ms"],
                    overhead["pipeline_reported"]["p50_ms"],
                )
            LOGGER.info("Server RSS: %s GB", rss)
    finally:
        LOGGER.info("Stopping server ...")
        server.terminate()
        try:
            server.wait(timeout=20)
        except subprocess.TimeoutExpired:
            server.kill()

    destination = Path(args.output).expanduser().resolve()
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    LOGGER.info("Report written to %s", destination)
    return 0


if __name__ == "__main__":
    sys.exit(main())
