"""Runtime inference package for Vietnamese license plate recognition (NFR-M1)."""

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
