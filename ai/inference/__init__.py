"""Runtime inference package for Vietnamese license plate recognition.

This package is the contract layer of the AI tier. It defines *what* the
pipeline exchanges (:mod:`~ai.inference.types`), *how* its stages can be
replaced (:mod:`~ai.inference.interfaces`), *how* it is configured
(:mod:`~ai.inference.config`) and *how* it fails
(:mod:`~ai.inference.exceptions`).

Architectural constraint (NFR-M1): this package must never import the web
framework or its schema library. It depends on NumPy and the standard library
alone, plus the ML runtimes used by concrete engine implementations. The
constraint is verified mechanically by a grep over ``ai/``; the exact command
is given in ``docs/architecture/system-architecture.md`` and is deliberately
not repeated here, since spelling the forbidden names in this file would make
the check match its own documentation.

Typical use from the API layer::

    from ai.inference import InferenceConfig

    config = InferenceConfig.from_env()

See ``README.md`` in this directory for the design rationale (in Vietnamese).
"""

from ai.inference.config import PROJECT_ROOT, InferenceConfig
from ai.inference.exceptions import (
    ALPRError,
    DetectionError,
    InvalidImageError,
    ModelLoadError,
    RecognitionError,
)
from ai.inference.interfaces import BaseDetector, BaseNormalizer, BaseRecognizer
from ai.inference.normalizer import (
    KindDecision,
    NormalizationOutcome,
    VietnamesePlateNormalizer,
)
from ai.inference.pipeline import ALPRPipeline, build_default_pipeline
from ai.inference.plate_rules import PlateKind
from ai.inference.types import (
    BoundingBox,
    DetectionResult,
    ImageArray,
    PipelineResult,
    PlateDetection,
    PlateRecognition,
)

__all__ = [
    # Configuration
    "InferenceConfig",
    "PROJECT_ROOT",
    # Abstractions (NFR-M5)
    "BaseDetector",
    "BaseRecognizer",
    "BaseNormalizer",
    # Composition root
    "ALPRPipeline",
    "build_default_pipeline",
    # Post-processing (the project's own contribution)
    "VietnamesePlateNormalizer",
    "NormalizationOutcome",
    "KindDecision",
    "PlateKind",
    # Data structures
    "ImageArray",
    "BoundingBox",
    "PlateDetection",
    "PlateRecognition",
    "DetectionResult",
    "PipelineResult",
    # Exceptions
    "ALPRError",
    "ModelLoadError",
    "DetectionError",
    "RecognitionError",
    "InvalidImageError",
]
