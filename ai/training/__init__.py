"""Training layer for the Vietnamese ALPR detector.

This package owns everything needed to fit a YOLO11 plate detector and to ship
the resulting weights:

* :mod:`ai.training.config` -- the :class:`~ai.training.config.TrainingConfig`
  dataclass plus YAML (de)serialisation, the single source of truth for every
  hyper-parameter.
* :mod:`ai.training.train` -- the training entry point (checkpointing, resume,
  device auto-selection, logging).
* :mod:`ai.training.export` -- conversion of ``best.pt`` to ONNX / OpenVINO for
  CPU inference.

Architectural constraint (NFR-M1): no module here may import FastAPI, Pydantic
or any other web/persistence framework. The Colab notebook under ``notebooks/``
is a *runner* only -- it must call into this package rather than reimplement any
logic in a cell.
"""

from __future__ import annotations

__all__: list[str] = []
