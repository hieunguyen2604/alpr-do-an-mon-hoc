"""Dataset-side data structures for the Vietnamese ALPR project.

This package is the single source of truth for how a *training sample* is
represented in memory. It sits next to :mod:`ai.inference` (which models what
comes out of the pipeline at runtime) and is deliberately kept free of any web
framework: nothing here may import FastAPI or Pydantic (NFR-M1). The names are
written capitalised on purpose, so that the grep enforcing the rule does not
match this sentence describing it.

The only public module today is :mod:`ai.data.schema`, which defines
:class:`~ai.data.schema.ImageRecord` / :class:`~ai.data.schema.BoxRecord` and
the conversions to and from the YOLO ``.txt`` label format used by every script
under ``scripts/dataset/``.
"""

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
