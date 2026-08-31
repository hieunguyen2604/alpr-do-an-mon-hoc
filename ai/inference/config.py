"""Centralised configuration dataclass for the ALPR inference package (NFR-M4)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["PROJECT_ROOT", "DEFAULT_ENV_PREFIX", "InferenceConfig"]

PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
"""Repository root, resolved from this file (``<root>/ai/inference/config.py``)."""

DEFAULT_ENV_PREFIX: str = "ALPR_"
"""Prefix for all environment variables read by :meth:`InferenceConfig.from_env`."""

_DEFAULT_MODEL_RELATIVE_PATH = Path("models") / "best.pt"
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off"})


def _read_str(prefix: str, key: str, default: str) -> str:
    """Read a string environment variable."""
    raw = os.environ.get(f"{prefix}{key}", "").strip()
    return raw if raw else default


def _read_float(prefix: str, key: str, default: float) -> float:
    """Read a floating-point environment variable."""
    raw = os.environ.get(f"{prefix}{key}", "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError as error:
        raise ValueError(
            f"Environment variable {prefix}{key}={raw!r} is not a valid number"
        ) from error


def _read_int(prefix: str, key: str, default: int) -> int:
    """Read an integer environment variable."""
    raw = os.environ.get(f"{prefix}{key}", "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as error:
        raise ValueError(
            f"Environment variable {prefix}{key}={raw!r} is not a valid integer"
        ) from error


def _read_bool(prefix: str, key: str, default: bool) -> bool:
    """Read a boolean environment variable."""
    raw = os.environ.get(f"{prefix}{key}", "").strip().lower()
    if not raw:
        return default
    if raw in _TRUE_VALUES:
        return True
    if raw in _FALSE_VALUES:
        return False
    raise ValueError(
        f"Environment variable {prefix}{key}={raw!r} is not a valid boolean; "
        "use one of 1/0, true/false, yes/no, on/off"
    )


def _read_path(prefix: str, key: str, default: Path) -> Path:
    """Read a filesystem path from an environment variable."""
    raw = os.environ.get(f"{prefix}{key}", "").strip()
    if not raw:
        return default
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate


def _read_optional_path(prefix: str, key: str) -> Path | None:
    """Read a path that has no default: unset or empty simply means ``None``."""
    raw = os.environ.get(f"{prefix}{key}", "").strip()
    if not raw:
        return None
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate


@dataclass(slots=True)
class InferenceConfig:
    """Runtime settings for the detection and recognition stages."""

    model_path: Path = field(default_factory=lambda: PROJECT_ROOT / _DEFAULT_MODEL_RELATIVE_PATH)
    device: str = "cpu"
    conf_threshold: float = 0.25
    iou_threshold: float = 0.45
    imgsz: int = 640
    ocr_lang: str = "en"
    ocr_use_gpu: bool = False
    ocr_rec_model_dir: Path | None = None
    ocr_skip_detection: bool = False
    two_line_aspect_ratio_threshold: float = 2.5
    rectify_enabled: bool = True
    sr_retry_enabled: bool = False

    def __post_init__(self) -> None:
        """Normalise the model path and validate every field."""
        self.model_path = Path(self.model_path).expanduser()
        if not self.model_path.is_absolute():
            self.model_path = PROJECT_ROOT / self.model_path

        if not 0.0 <= self.conf_threshold <= 1.0:
            raise ValueError(f"conf_threshold must be within [0.0, 1.0], got {self.conf_threshold}")
        if not 0.0 <= self.iou_threshold <= 1.0:
            raise ValueError(f"iou_threshold must be within [0.0, 1.0], got {self.iou_threshold}")
        if self.imgsz <= 0 or self.imgsz % 32 != 0:
            raise ValueError(f"imgsz must be a positive multiple of 32, got {self.imgsz}")
        if self.two_line_aspect_ratio_threshold <= 0.0:
            raise ValueError(
                "two_line_aspect_ratio_threshold must be positive, got "
                f"{self.two_line_aspect_ratio_threshold}"
            )
        if not self.device:
            raise ValueError("device must be a non-empty string, e.g. 'cpu' or 'cuda'")
        if not self.ocr_lang:
            raise ValueError("ocr_lang must be a non-empty string, e.g. 'en'")

        if self.ocr_rec_model_dir is not None:
            self.ocr_rec_model_dir = Path(self.ocr_rec_model_dir).expanduser()
            if not self.ocr_rec_model_dir.is_absolute():
                self.ocr_rec_model_dir = PROJECT_ROOT / self.ocr_rec_model_dir
            if not self.ocr_rec_model_dir.is_dir():
                raise ValueError(
                    "ocr_rec_model_dir does not exist or is not a directory: "
                    f"{self.ocr_rec_model_dir}"
                )

    @classmethod
    def from_env(cls, prefix: str = DEFAULT_ENV_PREFIX) -> InferenceConfig:
        """Build a configuration from environment variables."""
        defaults = cls()
        return cls(
            model_path=_read_path(prefix, "MODEL_PATH", defaults.model_path),
            device=_read_str(prefix, "DEVICE", defaults.device),
            conf_threshold=_read_float(prefix, "CONF_THRESHOLD", defaults.conf_threshold),
            iou_threshold=_read_float(prefix, "IOU_THRESHOLD", defaults.iou_threshold),
            imgsz=_read_int(prefix, "IMGSZ", defaults.imgsz),
            ocr_lang=_read_str(prefix, "OCR_LANG", defaults.ocr_lang),
            ocr_use_gpu=_read_bool(prefix, "OCR_USE_GPU", defaults.ocr_use_gpu),
            ocr_rec_model_dir=_read_optional_path(prefix, "OCR_REC_MODEL_DIR"),
            ocr_skip_detection=_read_bool(
                prefix, "OCR_SKIP_DETECTION", defaults.ocr_skip_detection
            ),
            two_line_aspect_ratio_threshold=_read_float(
                prefix,
                "TWO_LINE_ASPECT_RATIO",
                defaults.two_line_aspect_ratio_threshold,
            ),
            rectify_enabled=_read_bool(prefix, "RECTIFY_ENABLED", defaults.rectify_enabled),
            sr_retry_enabled=_read_bool(prefix, "SR_RETRY_ENABLED", defaults.sr_retry_enabled),
        )
