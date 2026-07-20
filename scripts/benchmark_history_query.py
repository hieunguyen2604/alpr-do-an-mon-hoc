"""Measure the detection-history query at scale (NFR-P6, target <= 500 ms).

Why this lives in ``scripts/`` and not in ``ai/evaluation/``
-----------------------------------------------------------
NFR-M1 forbids the ``ai`` package from importing the service tier: no FastAPI,
no Pydantic, no SQLAlchemy, nothing from ``backend``. This benchmark has to
import ``backend.repositories`` in order to time the *real* query rather than a
reimplementation of it, so it cannot live under ``ai/``. ``scripts/`` may depend
on both tiers, which makes it the correct home. ``tests/test_architecture.py``
enforces the rule, and it caught an earlier draft of this file sitting in the
wrong package.

What it measures
----------------
A throwaway SQLite database is seeded with 10,000 synthetic detections, then the
repository's ``list_paginated`` is timed under eight filter shapes. Several
shapes rather than one, because they stress different machinery: an unfiltered
first page tests sort plus count, a deep page tests OFFSET cost, and a plate
substring search is the one query that cannot use an index and is therefore the
realistic worst case.

The seeded database is a temporary file, deleted afterwards. This script never
touches the project's real database.

Example:
    python scripts/benchmark_history_query.py --rows 10000 --repeats 10
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import random
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ai.evaluation.stress_test import describe_hardware, percentiles  # noqa: E402

LOGGER = logging.getLogger("benchmark_history_query")

#: NFR-P6 target: a filtered, paginated history page over 10,000 rows.
P6_TARGET_MS: float = 500.0


def seed_history_database(row_count: int, batch_size: int = 1000) -> tuple[Any, Path]:
    """Create a temporary SQLite database holding ``row_count`` detections.

    Rows get spread-out timestamps, a mixture of input types and realistic plate
    strings, so the filtered queries below exercise the indexes instead of
    matching everything or nothing.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from backend.models.detection import Base, DetectionHistory, DetectionJob

    handle, raw_path = tempfile.mkstemp(suffix=".sqlite", prefix="nfr_p6_")
    os.close(handle)
    db_path = Path(raw_path)

    engine = create_engine(f"sqlite:///{db_path}", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, future=True)

    rng = random.Random(20260719)
    provinces = ["51", "29", "43", "60", "72", "92", "30", "77"]
    letters = "ABCDEFGHKLMNPSTUVXYZ"
    input_types = ["image", "video", "webcam"]
    base_time = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)

    # ``detection_history.source_job_id`` is a non-null foreign key, so the
    # parent jobs must exist first. A pool of jobs rather than a single one
    # keeps the ``source_job_id`` filter selective instead of matching all rows.
    job_count = max(1, row_count // 50)
    job_ids = [f"job-{index:06d}" for index in range(job_count)]
    LOGGER.info("Seeding %d parent job(s) ...", job_count)
    with factory() as session:
        session.add_all(
            [
                DetectionJob(
                    id=job_id,
                    input_type=rng.choice(input_types),
                    status="completed",
                    progress=1.0,
                    created_at=base_time + dt.timedelta(minutes=index),
                )
                for index, job_id in enumerate(job_ids)
            ]
        )
        session.commit()

    LOGGER.info("Seeding %d history rows into %s ...", row_count, db_path.name)
    with factory() as session:
        for start in range(0, row_count, batch_size):
            rows = []
            for offset in range(start, min(start + batch_size, row_count)):
                plate = (
                    f"{rng.choice(provinces)}{rng.choice(letters)}-"
                    f"{rng.randint(100, 999)}.{rng.randint(10, 99)}"
                )
                rows.append(
                    DetectionHistory(
                        plate_number=plate,
                        raw_ocr_text=plate.replace("-", "").replace(".", ""),
                        confidence=round(rng.uniform(0.30, 0.99), 4),
                        ocr_confidence=round(rng.uniform(0.30, 0.99), 4),
                        input_type=rng.choice(input_types),
                        bbox_x=rng.randint(0, 500),
                        bbox_y=rng.randint(0, 500),
                        bbox_w=rng.randint(40, 300),
                        bbox_h=rng.randint(20, 150),
                        is_valid_format=rng.random() > 0.2,
                        plate_line_count=rng.choice([1, 2]),
                        processing_time=round(rng.uniform(0.1, 3.0), 4),
                        detected_time=base_time + dt.timedelta(minutes=offset),
                        source_job_id=job_ids[offset % len(job_ids)],
                    )
                )
            session.add_all(rows)
            session.commit()

    return factory, db_path


def benchmark_history_queries(factory: Any, row_count: int, repeats: int) -> dict[str, Any]:
    """Time the real repository query under several filter shapes."""
    from backend.repositories.detection_repository import (
        DetectionRepository,
        HistoryFilter,
    )

    base_time = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)

    scenarios: dict[str, dict[str, Any]] = {
        "page_1_no_filter": {"page": 1, "page_size": 20, "filters": None},
        "page_50_no_filter": {"page": 50, "page_size": 20, "filters": None},
        "deep_page_400": {"page": 400, "page_size": 20, "filters": None},
        "filter_input_type": {
            "page": 1,
            "page_size": 20,
            "filters": HistoryFilter(input_type="image"),
        },
        "filter_time_range": {
            "page": 1,
            "page_size": 20,
            "filters": HistoryFilter(
                start_time=base_time + dt.timedelta(days=1),
                end_time=base_time + dt.timedelta(days=4),
            ),
        },
        "filter_confidence": {
            "page": 1,
            "page_size": 20,
            "filters": HistoryFilter(min_confidence=0.8),
        },
        "filter_plate_substring": {
            "page": 1,
            "page_size": 20,
            "filters": HistoryFilter(plate_number="51A"),
        },
        "combined_filters": {
            "page": 1,
            "page_size": 20,
            "filters": HistoryFilter(input_type="image", min_confidence=0.7, is_valid_format=True),
        },
    }

    results: dict[str, Any] = {}
    with factory() as session:
        repository = DetectionRepository(session)
        LOGGER.info("Database holds %d row(s)", repository.count())

        for name, kwargs in scenarios.items():
            timings: list[float] = []
            matched = 0
            records: list[Any] = []
            for _ in range(repeats):
                started = time.perf_counter()
                records, matched = repository.list_paginated(**kwargs)
                timings.append((time.perf_counter() - started) * 1000.0)
            stats = percentiles(timings)
            passed = stats["p95_ms"] <= P6_TARGET_MS
            results[name] = {
                **stats,
                "matched_rows": matched,
                "returned_rows": len(records),
                "meets_target": passed,
            }
            LOGGER.info(
                "  %-24s p50=%7.2f ms  p95=%7.2f ms  matched=%6d  %s",
                name,
                stats["p50_ms"],
                stats["p95_ms"],
                matched,
                "PASS" if passed else "FAIL",
            )

    worst = max((entry["p95_ms"] for entry in results.values()), default=0.0)
    return {
        "row_count": row_count,
        "repeats": repeats,
        "target_ms": P6_TARGET_MS,
        "scenarios": results,
        "worst_p95_ms": worst,
        "meets_target": worst <= P6_TARGET_MS,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python scripts/benchmark_history_query.py",
        description="Time the detection-history query at scale (NFR-P6).",
    )
    parser.add_argument("--rows", type=int, default=10000)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--output", default="docs/reports/07-stress-db.json")
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

    factory, db_path = seed_history_database(args.rows)
    try:
        payload = benchmark_history_queries(factory, args.rows, args.repeats)
    finally:
        try:
            db_path.unlink(missing_ok=True)
        except Exception:  # noqa: BLE001
            LOGGER.debug("Could not remove %s", db_path)

    report = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "hardware": hardware,
        "nfr_p6_history_query": payload,
    }

    destination = Path(args.output).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    LOGGER.info("=" * 72)
    LOGGER.info(
        "NFR-P6  %s  (worst p95 %.2f ms, target %.0f ms)",
        "PASS" if payload["meets_target"] else "FAIL",
        payload["worst_p95_ms"],
        P6_TARGET_MS,
    )
    LOGGER.info("Report written to %s", destination)
    LOGGER.info("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
