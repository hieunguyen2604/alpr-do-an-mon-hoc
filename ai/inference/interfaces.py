"""Abstract base classes for swappable detector, recognizer, and normalizer stages (NFR-M5)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai.inference.types import ImageArray, PlateDetection, PlateRecognition

__all__ = ["BaseDetector", "BaseRecognizer", "BaseNormalizer"]


class BaseDetector(ABC):
    """Contract for anything that locates license plates in an image."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return a short human-readable engine identifier."""

    @abstractmethod
    def detect(self, image: ImageArray) -> list[PlateDetection]:
        """Locate every license plate in an image."""

    def warmup(self) -> None:
        """Run a throwaway inference pass to prime the model."""
        return None


class BaseRecognizer(ABC):
    """Contract for anything that reads characters from a cropped plate."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return a short human-readable engine identifier, e.g. ``"paddleocr"``."""

    @abstractmethod
    def recognize(self, plate_image: ImageArray) -> PlateRecognition:
        """Read the plate text from a cropped plate image."""

    def warmup(self) -> None:
        """Run a throwaway OCR pass to prime the engine."""
        return None


class BaseNormalizer(ABC):
    """Contract for correcting and validating raw OCR output."""

    @abstractmethod
    def normalize(self, raw_text: str) -> tuple[str, bool]:
        """Correct a raw OCR string and check it against the plate format."""
