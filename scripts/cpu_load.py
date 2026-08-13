"""Spin N CPU-burning child processes for a fixed number of seconds.

Used as the *control* arm of the NFR-P2 re-measurement: the original 2,379 FPS
figure was recorded while Explorer, VS Code, Visual Studio and Claude were
together consuming roughly 560% CPU, and the benchmark harness stamped every
timing from that run as PESSIMISTIC. Re-running on a quiet machine gives 5,2
FPS. This script reproduces the competing load so the difference can be
attributed rather than assumed.
"""

from __future__ import annotations

import multiprocessing as mp
import sys
import time


def burn(seconds: float) -> None:
    """Occupy one core with integer work until ``seconds`` have elapsed."""
    end = time.perf_counter() + seconds
    x = 0
    while time.perf_counter() < end:
        for _ in range(200_000):
            x = (x * 1103515245 + 12345) & 0x7FFFFFFF


if __name__ == "__main__":
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    duration = float(sys.argv[2]) if len(sys.argv) > 2 else 120.0
    procs = [mp.Process(target=burn, args=(duration,)) for _ in range(workers)]
    for p in procs:
        p.start()
    print(f"[load] {workers} worker dang chay trong {duration:.0f}s", flush=True)
    for p in procs:
        p.join()
    print("[load] xong", flush=True)
