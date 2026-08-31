"""Exception hierarchy for the ALPR inference package (NFR-S4)."""

from __future__ import annotations

__all__ = [
    "ALPRError",
    "ModelLoadError",
    "DetectionError",
    "RecognitionError",
    "InvalidImageError",
]


class ALPRError(Exception):
    """Base class for every error raised by the ALPR inference package."""


class ModelLoadError(ALPRError):
    """Raised when a model cannot be loaded."""


class DetectionError(ALPRError):
    """Raised when the plate-detection stage fails."""


class RecognitionError(ALPRError):
    """Raised when the OCR stage fails."""


class InvalidImageError(ALPRError):
    """Raised when the supplied image cannot be processed."""
