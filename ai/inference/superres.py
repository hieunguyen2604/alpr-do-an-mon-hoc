"""Super-resolution for small plate crops via FSRCNN, used by the failure-retry ladder."""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING, Final

import cv2

from ai.inference.config import PROJECT_ROOT

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ai.inference.types import ImageArray

__all__ = ["SR_SCALES", "superres_available", "superres_upscale"]

_LOGGER = logging.getLogger(__name__)

SR_SCALES: Final[tuple[int, ...]] = (3, 4)
"""Upscale factors shipped with the project, tried in this order.

Both earned their place by measurement, on different crop sizes: x3 fixed the
32x23 px case, x4 the 171x120 px one. The corresponding graphs live in
``models/sr/FSRCNN_x<scale>.pb``.
"""

_MODEL_DIR: Final = PROJECT_ROOT / "models" / "sr"

_lock = threading.Lock()
_engines: dict[int, object] = {}
_unavailable_logged = False


def _load_engine(scale: int) -> object | None:
    """Build (or fetch the cached) FSRCNN engine for one scale.

    Returns:
        The engine, or ``None`` when the contrib module or the model file is
        missing -- both are survivable configurations, not errors.
    """
    global _unavailable_logged

    with _lock:
        if scale in _engines:
            return _engines[scale]

        factory = getattr(getattr(cv2, "dnn_superres", None), "DnnSuperResImpl_create", None)
        model_path = _MODEL_DIR / f"FSRCNN_x{scale}.pb"
        if factory is None or not model_path.exists():
            if not _unavailable_logged:
                _LOGGER.info(
                    "Super-resolution unavailable, retry ladder runs without it",
                    extra={
                        "has_dnn_superres": factory is not None,
                        "model_path": str(model_path),
                        "model_exists": model_path.exists(),
                    },
                )
                _unavailable_logged = True
            _engines[scale] = None
            return None

        try:
            engine = factory()
            engine.readModel(str(model_path))
            engine.setModel("fsrcnn", scale)
        except Exception as error:  # noqa: BLE001 - degrade, never break a read
            _LOGGER.warning(
                "Failed to load the super-resolution model",
                extra={"scale": scale, "error": f"{type(error).__name__}: {error}"},
            )
            engine = None
        _engines[scale] = engine
        return engine


def superres_available() -> bool:
    """Return whether at least one SR engine can be used in this environment."""
    return any(_load_engine(scale) is not None for scale in SR_SCALES)


def superres_upscale(image: ImageArray, scale: int) -> ImageArray | None:
    """Upscale a crop with the FSRCNN model for ``scale``.

    Args:
        image: The plate crop, BGR ``uint8``.
        scale: One of :data:`SR_SCALES`.

    Returns:
        The upscaled image, or ``None`` when SR is unavailable or fails --
        the caller simply skips the variant.
    """
    engine = _load_engine(scale)
    if engine is None:
        return None
    try:
        with _lock:
            # DnnSuperResImpl carries internal state; one inference at a time
            # is cheap insurance for a step that only runs on failed reads.
            result: ImageArray = engine.upsample(image)
        return result
    except Exception as error:  # noqa: BLE001 - degrade, never break a read
        _LOGGER.warning(
            "Super-resolution upsample failed",
            extra={"scale": scale, "error": f"{type(error).__name__}: {error}"},
        )
        return None
