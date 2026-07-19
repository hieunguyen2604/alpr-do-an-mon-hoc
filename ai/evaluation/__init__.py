"""Offline evaluation layer for the Vietnamese ALPR detector.

Modules:

* :mod:`ai.evaluation.evaluate` -- detection metrics (mAP@0.5, mAP@0.5:0.95,
  precision, recall, F1), confusion matrix, PR curves, a **separate breakdown
  for single-line vs two-line plates** (requirement NFR-A8, the project's
  highest-risk area R-04) and CPU latency percentiles.
* :mod:`ai.evaluation.benchmark_cpu` -- PyTorch vs ONNX vs OpenVINO latency
  comparison measured on *this* machine, so the thesis never quotes someone
  else's CPU numbers.
* :mod:`ai.evaluation.benchmark_ocr` -- accuracy and CPU latency of the OCR
  stage on hand-labelled plate crops. Reports full-string accuracy **before and
  after** normalisation as two separate figures (NFR-A5 vs NFR-A6, whose
  difference is what the post-processing rules contribute), breaks the result
  down by one-line vs two-line plates (NFR-A8, risk R-04) and emits a measured
  36x36 character confusion matrix.
* :mod:`ai.evaluation.error_analysis` -- groups the failures of a benchmark run
  by error class and exports the failing crops for visual review.

Architectural constraint (NFR-M1): no web/persistence framework imports.
"""

from __future__ import annotations

__all__: list[str] = []
