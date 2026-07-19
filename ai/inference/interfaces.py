"""Abstract base classes for the swappable stages of the ALPR pipeline.

This module is the concrete answer to NFR-M5: *"the OCR engine can be replaced
without touching the API layer"*. The pipeline depends on these abstractions
only; concrete engines (YOLO11, PaddleOCR, ...) are implementation details
injected at start-up. Swapping PaddleOCR for EasyOCR means writing one new
subclass of :class:`BaseRecognizer` -- no change to the pipeline, the services
or the routers.

Three stages are abstracted:

=================== ===================================== ======================
Stage               Contract                              Reference engine
=================== ===================================== ======================
Locate the plate    :class:`BaseDetector`                 YOLO11
Read the characters :class:`BaseRecognizer`               PaddleOCR
Correct + validate  :class:`BaseNormalizer`               regex rules
=================== ===================================== ======================

Implementations receive their settings through
:class:`~ai.inference.config.InferenceConfig` and must raise only the exception
types defined in :mod:`ai.inference.exceptions`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai.inference.types import ImageArray, PlateDetection, PlateRecognition

__all__ = ["BaseDetector", "BaseRecognizer", "BaseNormalizer"]


class BaseDetector(ABC):
    """Contract for anything that locates license plates in an image.

    A detector answers one question -- *where are the plates?* -- and nothing
    else. It never reads text and never touches the filesystem beyond loading
    its own weights.

    Implementations are expected to load their model once, at construction or
    on first use, and to be reusable across many calls.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return a short human-readable engine identifier.

        Used in structured logs and in benchmark reports so that a stored
        result can be traced back to the engine that produced it, for example
        ``"yolo11n"``. Being abstract, every engine must declare its identity.
        """

    @abstractmethod
    def detect(self, image: ImageArray) -> list[PlateDetection]:
        """Locate every license plate in an image.

        Args:
            image: Source image as a BGR ``uint8`` array of shape
                ``(height, width, 3)`` -- the format ``cv2.imread`` returns.

        Returns:
            One :class:`~ai.inference.types.PlateDetection` per plate found,
            already filtered by the configured confidence threshold and
            non-maximum suppression. An empty list means the image contains no
            plate, which is a normal outcome and never an error.

            Boxes must be clamped to the image bounds so that every returned
            box can be used directly to crop.

        Raises:
            InvalidImageError: If the array is empty or not a valid image.
            DetectionError: If inference itself fails.
        """

    def warmup(self) -> None:
        """Run a throwaway inference pass to prime the model.

        The first inference of a process is far slower than the rest: weights
        are paged in and lazy kernels are compiled. Calling this at start-up
        moves that cost off the first user request, which matters for the
        latency budget (NFR-P1).

        The default implementation does nothing, so engines with no warm-up
        cost need not override it.
        """
        return None


class BaseRecognizer(ABC):
    """Contract for anything that reads characters from a cropped plate.

    A recognizer receives a plate crop -- not a full scene -- and returns the
    characters it read together with a confidence score. Text correction and
    format validation are *not* its job: those belong to
    :class:`BaseNormalizer`, so that the raw engine output stays observable and
    the post-processing step remains independently measurable.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return a short human-readable engine identifier, e.g. ``"paddleocr"``."""

    @abstractmethod
    def recognize(self, plate_image: ImageArray) -> PlateRecognition:
        """Read the plate text from a cropped plate image.

        Args:
            plate_image: The cropped plate as a BGR ``uint8`` array. Callers
                pass the region delimited by a detected bounding box, not the
                whole scene.

        Returns:
            A :class:`~ai.inference.types.PlateRecognition` carrying both the
            raw engine output and the normalised string. When the crop is
            unreadable, implementations return a result with empty text and
            zero confidence rather than raising -- an unreadable plate is a
            normal outcome that must still be recorded.

        Raises:
            InvalidImageError: If the crop is empty or not a valid image.
            RecognitionError: If the OCR engine itself fails.
        """

    def warmup(self) -> None:
        """Run a throwaway OCR pass to prime the engine.

        See :meth:`BaseDetector.warmup`. The default implementation does
        nothing.
        """
        return None


class BaseNormalizer(ABC):
    """Contract for correcting and validating raw OCR output.

    OCR engines confuse characters that look alike -- ``0``/``O``, ``1``/``I``,
    ``8``/``B`` -- and the correct reading depends on position: Vietnamese
    plates put digits in some slots and a letter in others, so the very same
    glyph resolves differently depending on where it sits. A normalizer encodes
    those rules.

    It is kept separate from :class:`BaseRecognizer` on purpose: because the
    raw string is preserved alongside the corrected one, the contribution of
    this stage can be measured by comparing the two columns in
    ``detection_history``.
    """

    @abstractmethod
    def normalize(self, raw_text: str) -> tuple[str, bool]:
        """Correct a raw OCR string and check it against the plate format.

        Args:
            raw_text: The unmodified string returned by the OCR engine, which
                may contain separators, whitespace or misread characters.

        Returns:
            A ``(normalized_text, is_valid_format)`` pair, where
            ``normalized_text`` is the cleaned-up plate string and
            ``is_valid_format`` says whether it matches a known Vietnamese
            plate pattern.

            An invalid result is still returned rather than discarded: the
            caller stores it with ``is_valid_format`` set to ``False``, which
            keeps recognition failures visible in the statistics instead of
            silently dropping them.
        """
