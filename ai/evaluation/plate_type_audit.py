"""Audit distribution of license plate types and colors across datasets (TT 79/2024)."""

from __future__ import annotations

import argparse
import collections
import csv
import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import cv2
import numpy as np

from ai.inference.plate_color import MIN_DOMINANT_FRACTION, PlateColor, classify_plate_color

LOGGER = logging.getLogger("plate_type_audit")

__all__ = ["AuditRecord", "AuditSummary", "audit_images", "build_parser", "main", "read_image"]

IMAGE_SUFFIXES = frozenset({".jpg", ".jpeg", ".png", ".bmp", ".webp"})

#: Colours that the project has essentially no data for. Listed explicitly so a
#: zero count is reported as a zero rather than silently omitted -- an absent row
#: reads as "not measured", which is a different claim from "measured as none".
EXPECTED_COLORS: tuple[str, ...] = ("white", "yellow", "blue", "red", "unknown")


@dataclass(slots=True)
class AuditRecord:
    """One image's perceived type."""

    image_path: str
    color: str
    color_confidence: float
    kind: str = ""
    plate_text: str = ""


@dataclass(slots=True)
class AuditSummary:
    """Aggregate counts across an audited set."""

    total: int = 0
    unreadable: int = 0
    by_color: dict[str, int] = field(default_factory=dict)
    by_kind: dict[str, int] = field(default_factory=dict)
    by_color_and_kind: dict[str, int] = field(default_factory=dict)
    low_confidence: int = 0


def read_image(path: str):
    """Read an image, tolerating paths OpenCV cannot open directly."""
    image = cv2.imread(path)
    if image is not None:
        return image
    try:
        return cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    except Exception:  # noqa: BLE001 - a truly unreadable file is a normal outcome
        return None


def _iter_labelled(labels_path: Path) -> list[tuple[str, str, int]]:
    """Read ``(image_path, plate_text, line_count)`` triples from a label CSV."""
    with labels_path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return []
    key = "﻿image_path" if "﻿image_path" in rows[0] else "image_path"
    return [(row[key], row.get("plate_text", ""), int(row.get("line_count") or 1)) for row in rows]


def _iter_directory(images_dir: Path) -> list[tuple[str, str, int]]:
    """List images under a directory, with no label information."""
    return [
        (str(path), "", 1)
        for path in sorted(images_dir.rglob("*"))
        if path.suffix.lower() in IMAGE_SUFFIXES
    ]


def audit_images(
    entries: list[tuple[str, str, int]],
    classify_kind: bool = True,
) -> tuple[list[AuditRecord], AuditSummary]:
    """Classify every image and aggregate the distribution."""
    normalizer = None
    if classify_kind:
        try:
            from ai.inference.normalizer import VietnamesePlateNormalizer

            normalizer = VietnamesePlateNormalizer()
        except Exception:  # noqa: BLE001 - the colour half of the audit still works
            LOGGER.warning("normalizer unavailable; auditing colour only")

    records: list[AuditRecord] = []
    summary = AuditSummary(by_color=dict.fromkeys(EXPECTED_COLORS, 0))
    colors: collections.Counter[str] = collections.Counter()
    kinds: collections.Counter[str] = collections.Counter()
    joint: collections.Counter[str] = collections.Counter()

    for index, (path, text, line_count) in enumerate(entries, start=1):
        if index % 500 == 0:
            LOGGER.info("  %d/%d", index, len(entries))

        image = read_image(path)
        if image is None:
            summary.unreadable += 1
            continue

        estimate = classify_plate_color(image)
        kind = ""
        if normalizer is not None and text:
            kind = normalizer.detect_plate_kind(text, line_count=line_count).kind.value

        records.append(
            AuditRecord(
                image_path=path,
                color=estimate.color.value,
                color_confidence=round(estimate.confidence, 4),
                kind=kind,
                plate_text=text,
            )
        )
        summary.total += 1
        colors[estimate.color.value] += 1
        if estimate.color is PlateColor.UNKNOWN or estimate.confidence < MIN_DOMINANT_FRACTION:
            summary.low_confidence += 1
        if kind:
            kinds[kind] += 1
            joint[f"{estimate.color.value}/{kind}"] += 1

    summary.by_color.update(colors)
    summary.by_kind = dict(kinds.most_common())
    summary.by_color_and_kind = dict(joint.most_common())
    return records, summary


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--labels", help="CSV of labelled plates.")
    source.add_argument("--images-dir", help="Directory of plate crops, recursively.")
    parser.add_argument("--output", required=True, help="Where to write the JSON report.")
    parser.add_argument(
        "--sample-for-review",
        type=int,
        default=0,
        help=(
            "Copy this many low-confidence crops into <output>-review/ for "
            "checking by eye. Auditing by machine tells you a class is absent; "
            "only a human can confirm the ones it did name."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the audit."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = build_parser().parse_args(argv)

    if args.labels:
        entries = _iter_labelled(Path(args.labels))
        source_label = args.labels
    else:
        entries = _iter_directory(Path(args.images_dir))
        source_label = args.images_dir

    if not entries:
        LOGGER.error("no images found in %s", source_label)
        return 1

    LOGGER.info("auditing %d images from %s", len(entries), source_label)
    records, summary = audit_images(entries, classify_kind=bool(args.labels))

    if summary.total == 0:
        LOGGER.error("none of the %d entries could be decoded", len(entries))
        return 1

    shares = {
        color: round(100.0 * count / summary.total, 2) for color, count in summary.by_color.items()
    }
    report = {
        "source": source_label,
        "summary": asdict(summary),
        "color_share_percent": shares,
        "missing_colors": [color for color, count in summary.by_color.items() if count == 0],
        "records": [asdict(record) for record in records],
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    LOGGER.info("")
    LOGGER.info("total readable: %d (unreadable: %d)", summary.total, summary.unreadable)
    for color in EXPECTED_COLORS:
        LOGGER.info(
            "  %-8s %6d  %5.1f%%", color, summary.by_color.get(color, 0), shares.get(color, 0.0)
        )
    if report["missing_colors"]:
        LOGGER.info("")
        LOGGER.info("ABSENT ENTIRELY: %s", ", ".join(report["missing_colors"]))
    LOGGER.info("wrote %s", output)

    if args.sample_for_review:
        review_dir = output.with_name(output.stem + "-review")
        review_dir.mkdir(parents=True, exist_ok=True)
        low = [r for r in records if r.color_confidence < MIN_DOMINANT_FRACTION]
        for record in low[: args.sample_for_review]:
            image = read_image(record.image_path)
            if image is None:
                continue
            name = f"{record.color}_{record.color_confidence:.2f}_{Path(record.image_path).name}"
            cv2.imwrite(str(review_dir / name), image)
        LOGGER.info(
            "copied %d low-confidence crops to %s",
            min(len(low), args.sample_for_review),
            review_dir,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
