"""Dataset-side data structures and YOLO label I/O (NFR-M1: pure Python only)."""

from __future__ import annotations

from ai.data.schema import (
    AR_ONE_LINE_MIN,
    EXCLUDED_LETTERS,
    OCR_SAFE_CHARSET,
    PLATE_CLASS_ID,
    PLATE_CLASS_NAME,
    SERIAL_FIRST_LETTERS,
    BoxRecord,
    ImageRecord,
    LineCount,
    estimate_line_count,
    parse_yolo_label_file,
    write_yolo_label_file,
)

__all__ = [
    "AR_ONE_LINE_MIN",
    "EXCLUDED_LETTERS",
    "OCR_SAFE_CHARSET",
    "PLATE_CLASS_ID",
    "PLATE_CLASS_NAME",
    "SERIAL_FIRST_LETTERS",
    "BoxRecord",
    "ImageRecord",
    "LineCount",
    "estimate_line_count",
    "parse_yolo_label_file",
    "write_yolo_label_file",
]
