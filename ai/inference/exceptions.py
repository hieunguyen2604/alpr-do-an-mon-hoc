"""Exception hierarchy for the ALPR inference package.

Every error raised on purpose by this package derives from :class:`ALPRError`.
That single root lets the API layer catch the whole family with one ``except``
clause, translate it into an HTTP response and log the technical detail
server-side without ever leaking a stack trace to the end user (NFR-S4).

Hierarchy::

    ALPRError
    ├── ModelLoadError     -- weights missing / unreadable / incompatible
    ├── DetectionError     -- the detection stage failed
    ├── RecognitionError   -- the OCR stage failed
    └── InvalidImageError  -- the input image is unusable

Note that these exceptions carry *developer-facing* messages in English. The
API layer is responsible for mapping them to user-facing messages.
"""

from __future__ import annotations

__all__ = [
    "ALPRError",
    "ModelLoadError",
    "DetectionError",
    "RecognitionError",
    "InvalidImageError",
]


class ALPRError(Exception):
    """Base class for every error raised by the ALPR inference package.

    Catching this class catches all errors that this package raises
    deliberately. Anything else escaping the package is a genuine bug.
    """


class ModelLoadError(ALPRError):
    """Raised when a model cannot be loaded.

    Typical causes: the weights file does not exist at the configured path,
    the file is corrupted, or it was produced by an incompatible framework
    version.
    """


class DetectionError(ALPRError):
    """Raised when the plate-detection stage fails.

    This signals a failure of the detector itself (inference crashed,
    unexpected output shape). Finding no plate in an image is *not* an error:
    that is reported as an empty result list.
    """


class RecognitionError(ALPRError):
    """Raised when the OCR stage fails.

    As with :class:`DetectionError`, reading no text from a plate crop is a
    normal outcome and is reported as ``None``/empty text, not an exception.
    """


class InvalidImageError(ALPRError):
    """Raised when the supplied image cannot be processed.

    Typical causes: the array is ``None`` or empty, has the wrong number of
    dimensions, has zero width or height, or the uploaded file could not be
    decoded into an image at all.
    """
