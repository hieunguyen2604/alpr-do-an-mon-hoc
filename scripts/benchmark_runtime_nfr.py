"""Measure the runtime NFRs that require a live server (P2, P3, R4, R5).

Four quantities that cannot be measured in-process
--------------------------------------------------
=========== ============================================================ =============
Requirement Quantity                                                     Target
=========== ============================================================ =============
NFR-P2      Effective webcam frame rate over 60 s                        >= 5 FPS
NFR-P3      Video processing speed relative to real time                 >= 0.3x
NFR-R4      Success rate under continuous load                           >= 99%
NFR-R5      Database contents survive a restart                          100%
=========== ============================================================ =============

Why a real uvicorn subprocess
-----------------------------
``TestClient`` calls the ASGI app in-process. That removes the socket, the HTTP
parser and the event loop -- and for NFR-R5 it removes the very thing under
test, since an in-process client shares the interpreter whose death is the
event we want to survive. Every phase here therefore talks to a real server
over real HTTP on the loopback interface.

What the webcam number does and does not include
------------------------------------------------
There is no camera in this environment, so NFR-P2 is measured by replaying
stored test images through ``POST /api/detect/frame`` under the *same*
single-slot queue discipline the frontend uses: at most one request is in
flight, and a frame produced by the camera while a request is outstanding is
dropped rather than queued. The reported figure is therefore the frame rate the
*server* can sustain over localhost HTTP. It excludes camera capture, JPEG
encoding in the browser and canvas draw time, all of which a real deployment
would additionally pay. Treat it as an upper bound.

Example:
    python scripts/benchmark_runtime_nfr.py --soak-minutes 15
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
from typing import Any, Final

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ai.evaluation.stress_test import describe_hardware, percentiles  # noqa: E402

LOGGER = logging.getLogger("benchmark_runtime_nfr")

P2_TARGET_FPS: Final[float] = 5.0
P2_FLOOR_FPS: Final[float] = 3.0
P3_TARGET_RATIO: Final[float] = 0.3
P3_FLOOR_RATIO: Final[float] = 0.15
R4_TARGET_SUCCESS: Final[float] = 99.0
R4_SPECIFIED_MINUTES: Final[float] = 60.0

IMAGE_SUFFIXES: Final[frozenset[str]] = frozenset({".jpg", ".jpeg", ".png", ".bmp", ".webp"})


# --- Server lifecycle ---
def start_server(
    port: int, log_path: Path, model_path: str | None = None
) -> subprocess.Popen[bytes]:
    """Launch uvicorn in a subprocess.

    With no ``model_path`` the server resolves its own weights from the ``.env``
    files, which is what a real deployment does and therefore what should be
    measured by default. Passing one sets ``ALPR_MODEL_PATH`` in the child's
    environment; a real environment variable outranks both ``.env`` files in
    pydantic-settings, so this reliably wins.

    Args:
        port: Loopback port to bind.
        log_path: File the server's stdout and stderr are appended to.
        model_path: Detector weights to force, or None to use the configuration.

    Returns:
        The running process handle.
    """
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(_PROJECT_ROOT)
    if model_path:
        environment["ALPR_MODEL_PATH"] = model_path

    handle = log_path.open("ab")
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


def stop_server(server: subprocess.Popen[bytes], timeout_s: float = 30.0) -> None:
    """Terminate the server and wait for the process to actually be gone.

    On Windows ``terminate()`` is ``TerminateProcess``, which gives the server
    no chance to run shutdown handlers or close its database connections. For
    NFR-R5 that is a feature rather than a limitation: the restart it tests is
    an abrupt one, closer to a crash or a pulled plug than to a polite stop, so
    surviving it is the stronger claim.
    """
    server.terminate()
    try:
        server.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        LOGGER.warning("Server ignored terminate; killing.")
        server.kill()
        server.wait(timeout=timeout_s)


def wait_for_ready(base_url: str, timeout_s: float) -> tuple[float | None, dict[str, Any]]:
    """Poll ``/health`` until it answers, returning elapsed seconds and body."""
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
    """Return up to ``limit`` image files under ``root``, sorted for repeatability."""
    found = [
        path
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    ]
    if not found:
        raise FileNotFoundError(f"No images under {root}")
    return found[:limit] if limit > 0 else found


# --- NFR-P2 -- webcam frame rate ---
def measure_webcam_fps(
    base_url: str,
    api_prefix: str,
    images: list[Path],
    duration_s: float,
    capture_fps: float,
) -> dict[str, Any]:
    """Replay frames under the frontend's single-slot queue discipline.

    A virtual camera produces a frame every ``1 / capture_fps`` seconds. If a
    request is still in flight when a frame arrives, that frame is *dropped* --
    it is never queued. This is what the frontend does, and it is why the
    effective frame rate is bounded by the server's per-frame latency rather
    than by the capture rate.

    Because only one request is ever outstanding, the loop can be written
    synchronously: send, wait, then discard whatever the virtual camera
    produced meanwhile.

    Args:
        base_url: Server root, e.g. ``http://127.0.0.1:8931``.
        api_prefix: Router prefix, normally ``/api``.
        images: Frames to cycle through, standing in for camera output.
        duration_s: Length of the measurement window.
        capture_fps: Rate at which the virtual camera produces frames.

    Returns:
        Frame counts, latency percentiles and the effective frame rate.
    """
    import httpx

    endpoint = f"{base_url}{api_prefix}/detect/frame"
    payloads = [(path.name, path.read_bytes()) for path in images]
    capture_interval = 1.0 / capture_fps

    latencies_ms: list[float] = []
    failures: list[str] = []
    job_id: str | None = None
    frames_sent = 0
    frames_ok = 0
    plates_found = 0

    with httpx.Client(timeout=120.0) as client:
        # One warm-up frame outside the window: the first call pays for lazy
        # model warm-up and would otherwise be charged to the 60 s budget.
        name, blob = payloads[0]
        try:
            warm = client.post(endpoint, files={"file": (name, blob, "image/jpeg")})
            if warm.status_code == 200:
                job_id = warm.json().get("job_id")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"warmup {type(exc).__name__}: {exc}")

        window_start = time.perf_counter()
        deadline = window_start + duration_s
        next_capture = window_start

        while True:
            now = time.perf_counter()
            if now >= deadline:
                break
            # Wait for the virtual camera's next frame if we got here early.
            if now < next_capture:
                time.sleep(min(next_capture - now, deadline - now))
                continue

            name, blob = payloads[frames_sent % len(payloads)]
            form = {"job_id": job_id} if job_id else None
            started = time.perf_counter()
            try:
                response = client.post(
                    endpoint,
                    files={"file": (name, blob, "image/jpeg")},
                    data=form,
                )
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{type(exc).__name__}: {exc}")
                frames_sent += 1
                next_capture = time.perf_counter()
                continue
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            frames_sent += 1

            if response.status_code == 200:
                body = response.json()
                job_id = body.get("job_id") or job_id
                frames_ok += 1
                plates_found += len(body.get("results") or [])
                latencies_ms.append(elapsed_ms)
            else:
                failures.append(f"HTTP {response.status_code}: {response.text[:160]}")

            # Frames the camera produced while the request was in flight are
            # dropped; the next capture slot is the first one at or after now.
            now = time.perf_counter()
            missed = int((now - next_capture) / capture_interval)
            next_capture += capture_interval * (missed + 1)

        window_s = time.perf_counter() - window_start

    effective_fps = frames_ok / window_s if window_s > 0 else 0.0
    frames_offered = int(window_s * capture_fps)

    if effective_fps >= P2_TARGET_FPS:
        status_text = "PASS"
    elif effective_fps >= P2_FLOOR_FPS:
        status_text = "MARGINAL"
    else:
        status_text = "FAIL"

    return {
        "window_seconds": round(window_s, 2),
        "virtual_capture_fps": capture_fps,
        "frames_offered_by_camera": frames_offered,
        "frames_sent": frames_sent,
        "frames_succeeded": frames_ok,
        "frames_dropped_by_single_slot_queue": max(0, frames_offered - frames_sent),
        "failure_count": len(failures),
        "failures": failures[:5],
        "plates_returned_total": plates_found,
        "per_frame_latency_ms": percentiles(latencies_ms),
        "effective_fps": round(effective_fps, 3),
        "target_fps": P2_TARGET_FPS,
        "floor_fps": P2_FLOOR_FPS,
        "status": status_text,
        "measurement_note": (
            "Measured over HTTP on the loopback interface. Excludes real camera "
            "capture, browser-side JPEG encoding and canvas draw time; a real "
            "webcam session would be slower. Upper bound, not a field figure."
        ),
    }


# --- NFR-P3 -- video throughput ---
def probe_video(path: Path) -> dict[str, Any]:
    """Read frame count, frame rate and resolution from a video file."""
    import cv2

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise FileNotFoundError(f"Cannot open video {path}")
    frames = float(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    capture.release()
    return {
        "path": str(path),
        "frame_count": int(frames),
        "fps": round(fps, 3),
        "duration_s": round(frames / fps, 3) if fps > 0 else None,
        "width": width,
        "height": height,
    }


def measure_video_throughput(
    base_url: str,
    api_prefix: str,
    video: Path,
    frame_stride: int,
    poll_interval_s: float,
    timeout_s: float,
) -> dict[str, Any]:
    """Upload a video, poll its job to completion and time the whole thing.

    The stopwatch starts before the upload and stops when the job first reports
    a terminal status. That includes the upload, the queueing delay and the
    polling granularity -- all of which a user waits through, so none of them
    is subtracted.

    Args:
        base_url: Server root.
        api_prefix: Router prefix.
        video: File to upload.
        frame_stride: The server's configured stride, recorded for the report.
        poll_interval_s: Gap between status polls.
        timeout_s: Give up after this long.

    Returns:
        Timings, the ratio against real time and the verdict.
    """
    import httpx

    info = probe_video(video)
    payload = video.read_bytes()

    with httpx.Client(timeout=300.0) as client:
        started = time.perf_counter()
        response = client.post(
            f"{base_url}{api_prefix}/detect/video",
            files={"file": (video.name, payload, "video/mp4")},
        )
        if response.status_code not in (200, 202):
            return {
                "video": info,
                "error": f"HTTP {response.status_code}: {response.text[:300]}",
                "status": "NOT_MEASURED",
            }
        accepted_s = time.perf_counter() - started
        job = response.json()
        job_id = job["id"]
        LOGGER.info("Video accepted as job %s after %.2f s", job_id, accepted_s)

        final: dict[str, Any] = job
        deadline = started + timeout_s
        while time.perf_counter() < deadline:
            time.sleep(poll_interval_s)
            poll = client.get(f"{base_url}{api_prefix}/jobs/{job_id}")
            if poll.status_code != 200:
                continue
            final = poll.json()
            if final.get("status") in ("completed", "failed", "cancelled"):
                break
        total_s = time.perf_counter() - started

    if final.get("status") != "completed":
        return {
            "video": info,
            "job": final,
            "elapsed_s": round(total_s, 3),
            "error": f"job ended in state {final.get('status')!r}",
            "status": "NOT_MEASURED",
        }

    duration_s = info["duration_s"] or 0.0
    ratio = duration_s / total_s if total_s > 0 else 0.0
    processed = final.get("processed_frames") or 0

    if ratio >= P3_TARGET_RATIO:
        status_text = "PASS"
    elif ratio >= P3_FLOOR_RATIO:
        status_text = "MARGINAL"
    else:
        status_text = "FAIL"

    return {
        "video": info,
        "frame_stride": frame_stride,
        "accepted_after_s": round(accepted_s, 3),
        "total_wall_s": round(total_s, 3),
        "poll_interval_s": poll_interval_s,
        "total_frames_reported": final.get("total_frames"),
        "processed_frames": processed,
        "detection_count": final.get("detection_count"),
        "seconds_per_processed_frame": (round(total_s / processed, 4) if processed else None),
        "realtime_ratio": round(ratio, 4),
        "target_ratio": P3_TARGET_RATIO,
        "floor_ratio": P3_FLOOR_RATIO,
        "status": status_text,
        "measurement_note": (
            f"Stopwatch spans upload -> terminal job state, including a "
            f"{poll_interval_s} s polling granularity that is not subtracted. "
            f"Only every {frame_stride}th frame is analysed (ALPR_FRAME_STRIDE)."
        ),
    }


# --- NFR-R4 -- soak ---
def run_soak(
    base_url: str,
    api_prefix: str,
    images: list[Path],
    minutes: float,
    server_pid: int,
) -> dict[str, Any]:
    """Drive the image endpoint continuously and record the success rate.

    Args:
        base_url: Server root.
        api_prefix: Router prefix.
        images: Cycled as request bodies.
        minutes: Length of the run.
        server_pid: Sampled for resident memory, to catch a leak.

    Returns:
        Counts, latency percentiles, an RSS trace and the verdict.
    """
    import httpx

    endpoint = f"{base_url}{api_prefix}/detect/image"
    payloads = [(path.name, path.read_bytes()) for path in images]

    latencies_ms: list[float] = []
    errors: list[str] = []
    rss_trace: list[dict[str, float]] = []
    sent = 0
    succeeded = 0

    duration_s = minutes * 60.0
    started = time.perf_counter()
    deadline = started + duration_s
    next_sample = started

    with httpx.Client(timeout=180.0) as client:
        while time.perf_counter() < deadline:
            name, blob = payloads[sent % len(payloads)]
            request_start = time.perf_counter()
            try:
                response = client.post(endpoint, files={"file": (name, blob, "image/jpeg")})
                elapsed_ms = (time.perf_counter() - request_start) * 1000.0
                sent += 1
                if response.status_code == 200:
                    succeeded += 1
                    latencies_ms.append(elapsed_ms)
                else:
                    errors.append(f"HTTP {response.status_code}: {response.text[:120]}")
            except Exception as exc:  # noqa: BLE001
                sent += 1
                errors.append(f"{type(exc).__name__}: {exc}")

            now = time.perf_counter()
            if now >= next_sample:
                rss = server_rss_gb(server_pid)
                if rss is not None:
                    rss_trace.append({"elapsed_s": round(now - started, 1), "rss_gb": rss})
                next_sample = now + 30.0
                LOGGER.info(
                    "  soak %.1f/%.1f min | %d requests | %.2f%% ok | RSS %s GB",
                    (now - started) / 60.0,
                    minutes,
                    sent,
                    100.0 * succeeded / sent if sent else 0.0,
                    rss,
                )

    elapsed_s = time.perf_counter() - started
    success_rate = 100.0 * succeeded / sent if sent else 0.0

    rss_growth = None
    if len(rss_trace) >= 2:
        rss_growth = round(rss_trace[-1]["rss_gb"] - rss_trace[0]["rss_gb"], 3)

    return {
        "duration_minutes_run": round(elapsed_s / 60.0, 2),
        "duration_minutes_specified": R4_SPECIFIED_MINUTES,
        "requests_sent": sent,
        "requests_succeeded": succeeded,
        "requests_failed": sent - succeeded,
        "success_rate_percent": round(success_rate, 3),
        "target_success_percent": R4_TARGET_SUCCESS,
        "latency_ms": percentiles(latencies_ms),
        "throughput_rps": round(sent / elapsed_s, 3) if elapsed_s else None,
        "error_samples": errors[:5],
        "rss_trace_gb": rss_trace,
        "rss_growth_gb": rss_growth,
        "status": "PASS" if success_rate >= R4_TARGET_SUCCESS else "FAIL",
        "coverage_caveat": (
            f"Run for {elapsed_s / 60.0:.1f} minutes, NOT the "
            f"{R4_SPECIFIED_MINUTES:.0f} minutes the requirement specifies. "
            "The success rate below is therefore evidence over a shorter window "
            "than NFR-R4 asks for, and does not by itself close the requirement."
        ),
    }


def server_rss_gb(pid: int) -> float | None:
    """Resident memory of the server process and its children, in GB."""
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


# --- NFR-R5 -- durability across a restart ---
def snapshot_database(base_url: str, api_prefix: str, sample_size: int) -> dict[str, Any]:
    """Read a fingerprint of the stored data through the public API.

    Reading through the API rather than the file keeps the check honest: it
    proves the data is still *reachable by the application*, not merely that
    bytes remain on disk.

    Args:
        base_url: Server root.
        api_prefix: Router prefix.
        sample_size: How many newest records to fingerprint individually.

    Returns:
        Total record count, statistics body and the sampled records.
    """
    import httpx

    with httpx.Client(timeout=60.0) as client:
        listing = client.get(
            f"{base_url}{api_prefix}/history",
            params={
                "page": 1,
                "page_size": sample_size,
                "sort_by": "detected_time",
                "order": "desc",
            },
        )
        listing.raise_for_status()
        body = listing.json()

        stats = client.get(f"{base_url}{api_prefix}/statistics")
        stats_body = stats.json() if stats.status_code == 200 else None

    items = body.get("items") or body.get("data") or []
    sample = [
        {
            "id": str(item.get("id")),
            "plate_number": item.get("plate_number"),
            "detected_time": item.get("detected_time"),
        }
        for item in items
    ]
    return {
        "total_records": body.get("total"),
        "sample": sample,
        "statistics": stats_body,
    }


def compare_snapshots(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Decide whether a restart lost anything.

    Args:
        before: Snapshot taken while the first server was alive.
        after: Snapshot taken from the freshly started server.

    Returns:
        The comparison and the verdict.
    """
    total_before = before.get("total_records")
    total_after = after.get("total_records")
    sample_identical = before.get("sample") == after.get("sample")
    counts_identical = total_before == total_after

    lost = None
    if isinstance(total_before, int) and isinstance(total_after, int):
        lost = total_before - total_after

    return {
        "total_records_before": total_before,
        "total_records_after": total_after,
        "records_lost": lost,
        "counts_identical": counts_identical,
        "sample_records_identical": sample_identical,
        "sample_size": len(before.get("sample") or []),
        "sample_before": before.get("sample"),
        "sample_after": after.get("sample"),
        "status": "PASS" if (counts_identical and sample_identical) else "FAIL",
        "measurement_note": (
            "Both snapshots were read through GET /api/history and "
            "GET /api/statistics, so the check proves the rows are still "
            "reachable by the application after the process was terminated and "
            "started again -- not merely that a file survived."
        ),
        "shutdown_kind": (
            "Abrupt: TerminateProcess on Windows, so no graceful shutdown hook "
            "and no orderly connection close. Closer to a crash than to a "
            "clean stop, which makes survival the stronger result."
        ),
    }


# --- Driver ---
def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface."""
    parser = argparse.ArgumentParser(
        prog="python scripts/benchmark_runtime_nfr.py",
        description="Measure NFR-P2, NFR-P3, NFR-R4 and NFR-R5 against a live server.",
    )
    parser.add_argument("--images", default="datasets/processed/yolo/images/test")
    parser.add_argument("--video", default="demo/demo-video.mp4")
    parser.add_argument(
        "--frame-images",
        type=int,
        default=40,
        help="How many distinct images stand in for camera frames.",
    )
    parser.add_argument("--soak-images", type=int, default=40)
    parser.add_argument("--webcam-seconds", type=float, default=60.0)
    parser.add_argument("--capture-fps", type=float, default=30.0)
    parser.add_argument("--soak-minutes", type=float, default=15.0)
    parser.add_argument("--poll-interval", type=float, default=0.25)
    parser.add_argument("--video-timeout", type=float, default=900.0)
    parser.add_argument("--sample-size", type=int, default=10)
    parser.add_argument("--port", type=int, default=8934)
    parser.add_argument("--api-prefix", default="/api")
    parser.add_argument("--startup-timeout", type=float, default=180.0)
    parser.add_argument("--output", default="docs/reports/07-benchmark-data-v2.json")
    parser.add_argument("--skip-soak", action="store_true")
    parser.add_argument(
        "--skip-restart",
        action="store_true",
        help="Skip NFR-R5. Useful for a second run that only re-measures speed.",
    )
    parser.add_argument(
        "--model-path",
        default=None,
        help=(
            "Override ALPR_MODEL_PATH for the server. Omit to measure the "
            "configuration the project actually ships."
        ),
    )
    return parser


def _log_hardware(hardware: dict[str, Any]) -> None:
    """Print the CPU configuration every published figure must be read against."""
    LOGGER.info("=" * 78)
    LOGGER.info(
        "CPU: %s | %s physical / %s logical cores | %.2f GB RAM | %s",
        hardware["cpu_name"],
        hardware["physical_cores"],
        hardware["logical_cores"],
        hardware["ram_total_gb"],
        hardware["platform"],
    )
    if hardware.get("competing_processes"):
        LOGGER.warning("Competing CPU load present -- every timing below is PESSIMISTIC:")
        for entry in hardware["competing_processes"]:
            LOGGER.warning("    %s", entry)
    LOGGER.info("=" * 78)


def main(argv: list[str] | None = None) -> int:
    """Run every phase and write the combined report."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    # httpx logs a line per request; a 15-minute soak would bury the report.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    args = build_parser().parse_args(argv)

    from backend.core.config import get_settings

    settings = get_settings()
    hardware = describe_hardware()
    _log_hardware(hardware)

    images_root = Path(args.images).expanduser().resolve()
    frame_images = discover_images(images_root, args.frame_images)
    soak_images = discover_images(images_root, args.soak_images)
    video = Path(args.video).expanduser().resolve()

    base_url = f"http://127.0.0.1:{args.port}"
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    log_path = output_path.with_suffix(".server.log")

    report: dict[str, Any] = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "hardware": hardware,
        "configuration": {
            "model_path_effective": args.model_path or str(settings.model_path),
            "model_path_override": args.model_path,
            "model_path_from_env_files": str(settings.model_path),
            "imgsz": settings.imgsz,
            "device": settings.device,
            "conf_threshold": settings.conf_threshold,
            "frame_stride": settings.frame_stride,
            "database_url": str(settings.database_url),
            "use_stub": settings.use_stub,
        },
        "images_root": str(images_root),
        "server_log": str(log_path),
    }

    LOGGER.info("Starting server (run 1) on port %d ...", args.port)
    server = start_server(args.port, log_path, args.model_path)
    try:
        ready_s, health = wait_for_ready(base_url, args.startup_timeout)
        if ready_s is None:
            LOGGER.error("Server never became ready. See %s", log_path)
            report["error"] = "server did not become ready"
            output_path.write_text(
                json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            return 1
        LOGGER.info("Ready after %.2f s | health=%s", ready_s, health)
        report["server_run_1"] = {"ready_after_s": round(ready_s, 2), "health": health}

        if not health.get("model_loaded", False):
            LOGGER.error(
                "model_loaded=false -- the server is NOT running real inference. "
                "Every figure below would be meaningless. Aborting."
            )
            report["error"] = "model_loaded=false; refusing to publish fake timings"
            output_path.write_text(
                json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            return 1

        # -- NFR-P2 ------------------------------------------------------
        LOGGER.info("NFR-P2: webcam frame rate over %.0f s ...", args.webcam_seconds)
        report["nfr_p2_webcam_fps"] = measure_webcam_fps(
            base_url,
            args.api_prefix,
            frame_images,
            args.webcam_seconds,
            args.capture_fps,
        )
        p2 = report["nfr_p2_webcam_fps"]
        LOGGER.info(
            "NFR-P2: %.2f FPS effective (%d ok / %.1f s) -- %s",
            p2["effective_fps"],
            p2["frames_succeeded"],
            p2["window_seconds"],
            p2["status"],
        )

        # -- NFR-P3 ------------------------------------------------------
        LOGGER.info("NFR-P3: processing %s ...", video.name)
        report["nfr_p3_video_throughput"] = measure_video_throughput(
            base_url,
            args.api_prefix,
            video,
            settings.frame_stride,
            args.poll_interval,
            args.video_timeout,
        )
        p3 = report["nfr_p3_video_throughput"]
        LOGGER.info(
            "NFR-P3: %.3fx real time (%.1f s of video in %.1f s) -- %s",
            p3.get("realtime_ratio", 0.0),
            (p3.get("video") or {}).get("duration_s", 0.0),
            p3.get("total_wall_s", 0.0),
            p3["status"],
        )

        # -- NFR-R4 ------------------------------------------------------
        if args.skip_soak:
            LOGGER.warning("Soak skipped by flag; NFR-R4 left unmeasured.")
            report["nfr_r4_soak"] = {"status": "NOT_MEASURED", "reason": "--skip-soak"}
        else:
            LOGGER.info("NFR-R4: soaking for %.0f minutes ...", args.soak_minutes)
            report["nfr_r4_soak"] = run_soak(
                base_url,
                args.api_prefix,
                soak_images,
                args.soak_minutes,
                server.pid,
            )
            r4 = report["nfr_r4_soak"]
            LOGGER.info(
                "NFR-R4: %.3f%% success over %d requests in %.1f min -- %s",
                r4["success_rate_percent"],
                r4["requests_sent"],
                r4["duration_minutes_run"],
                r4["status"],
            )

        # -- NFR-R5, first half ------------------------------------------
        LOGGER.info("NFR-R5: snapshotting the database before restart ...")
        before = snapshot_database(base_url, args.api_prefix, args.sample_size)
        LOGGER.info("  %s records before restart", before["total_records"])
    finally:
        LOGGER.info("Stopping server (run 1) ...")
        stop_server(server)

    # -- NFR-R5, second half ---------------------------------------------
    if args.skip_restart:
        LOGGER.warning("Restart check skipped by flag; NFR-R5 left unmeasured.")
        report["nfr_r5_restart_durability"] = {
            "status": "NOT_MEASURED",
            "reason": "--skip-restart",
        }
        report["summary"] = _summarise(report)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        LOGGER.info("Report written to %s", output_path)
        for line in report["summary"]["verdicts"]:
            LOGGER.info("  %s", line)
        return 0

    time.sleep(3.0)
    LOGGER.info("Starting server (run 2) on port %d ...", args.port)
    server2 = start_server(args.port, log_path, args.model_path)
    try:
        ready2_s, health2 = wait_for_ready(base_url, args.startup_timeout)
        if ready2_s is None:
            report["nfr_r5_restart_durability"] = {
                "status": "NOT_MEASURED",
                "reason": "server did not come back up",
            }
        else:
            LOGGER.info("Ready again after %.2f s", ready2_s)
            after = snapshot_database(base_url, args.api_prefix, args.sample_size)
            comparison = compare_snapshots(before, after)
            comparison["restart_ready_after_s"] = round(ready2_s, 2)
            comparison["health_after_restart"] = health2
            report["nfr_r5_restart_durability"] = comparison
            LOGGER.info(
                "NFR-R5: %s before / %s after -- %s",
                comparison["total_records_before"],
                comparison["total_records_after"],
                comparison["status"],
            )
    finally:
        LOGGER.info("Stopping server (run 2) ...")
        stop_server(server2)

    report["summary"] = _summarise(report)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    LOGGER.info("Report written to %s", output_path)
    for line in report["summary"]["verdicts"]:
        LOGGER.info("  %s", line)
    return 0


def _summarise(report: dict[str, Any]) -> dict[str, Any]:
    """Collapse the phases into a one-line verdict each."""
    entries = [
        ("NFR-P2", "nfr_p2_webcam_fps", "effective_fps", "FPS webcam hiệu dụng"),
        ("NFR-P3", "nfr_p3_video_throughput", "realtime_ratio", "Tỉ lệ so với thời gian thực"),
        ("NFR-R4", "nfr_r4_soak", "success_rate_percent", "Tỉ lệ thành công khi chạy liên tục"),
        ("NFR-R5", "nfr_r5_restart_durability", "records_lost", "Bản ghi mất sau khởi động lại"),
    ]
    verdicts: list[str] = []
    passed = 0
    failed: list[str] = []
    for code, key, value_key, label in entries:
        block = report.get(key) or {}
        state = block.get("status", "NOT_MEASURED")
        verdicts.append(f"{code} {label}: {block.get(value_key)} -- {state}")
        if state == "PASS":
            passed += 1
        else:
            failed.append(code)
    return {
        "requirements_checked": len(entries),
        "passed": passed,
        "not_passed": failed,
        "verdicts": verdicts,
    }


if __name__ == "__main__":
    sys.exit(main())
