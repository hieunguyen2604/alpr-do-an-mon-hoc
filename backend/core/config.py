"""Centralised application settings and environment validation for ALPR backend (NFR-M4)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any, Final

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

__all__ = ["PROJECT_ROOT", "Settings", "get_settings"]

StringList = Annotated[list[str], NoDecode]
"""A list field that pydantic-settings must not JSON-decode on its own."""

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
"""Repository root, derived from ``<root>/backend/core/config.py``."""

_MEGABYTE: Final[int] = 1024 * 1024

_SQLITE_SCHEME: Final[str] = "sqlite:///"
"""URL prefix that marks a file-backed SQLite database."""


class Settings(BaseSettings):
    """Runtime configuration for the backend, read from the environment."""

    model_config = SettingsConfigDict(
        env_prefix="ALPR_",
        env_file=(PROJECT_ROOT / ".env", PROJECT_ROOT / "backend" / ".env"),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        case_sensitive=False,
        extra="ignore",
        # ``model_path`` collides with Pydantic's reserved ``model_`` namespace.
        # The field name is fixed by the environment contract shared with the
        # ``ai`` package, so the namespace guard is what gives way, not the name.
        protected_namespaces=(),
    )

    # -- Application ------------------------------------------------------
    app_name: str = Field(
        default="Vietnamese ALPR API",
        description="Service name shown in Swagger and the health endpoint.",
    )
    app_version: str = Field(
        default="0.1.0",
        description="Version string reported by the health endpoint.",
    )
    debug: bool = Field(
        default=False,
        description="Enable SQL echo and verbose server-side logging.",
    )
    api_prefix: str = Field(
        default="/api",
        description="Path prefix mounted in front of every API router.",
    )

    # -- Persistence ------------------------------------------------------
    database_url: str = Field(
        default="sqlite:///./data/alpr.db",
        description="SQLAlchemy database connection URL.",
    )

    # -- Storage ----------------------------------------------------------
    storage_root: Path = Field(
        default=Path("data"),
        description="Base directory for all files written to disk.",
    )
    upload_dir: Path = Field(
        default=Path("uploads"),
        description="Directory holding original uploaded images and videos.",
    )
    plate_dir: Path = Field(
        default=Path("plates"),
        description="Directory holding cropped license plate images.",
    )
    output_dir: Path = Field(
        default=Path("outputs"),
        description="Directory holding annotated images and processed videos.",
    )

    # -- Upload limits ----------------------------------------------------
    max_image_size_mb: int = Field(
        default=10,
        gt=0,
        description="Maximum accepted image upload size, in megabytes.",
    )
    max_video_size_mb: int = Field(
        default=200,
        gt=0,
        description="Maximum accepted video upload size, in megabytes.",
    )
    allowed_image_types: StringList = Field(
        default=["image/jpeg", "image/png", "image/webp", "image/bmp"],
        description="Image MIME types accepted on upload.",
    )
    allowed_video_types: StringList = Field(
        default=[
            "video/mp4",
            "video/x-msvideo",
            "video/quicktime",
            "video/x-matroska",
        ],
        description="Video MIME types accepted on upload.",
    )

    # -- Security ---------------------------------------------------------
    cors_origins: StringList = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        description="Browser origins permitted by CORS. Wildcards are rejected.",
    )

    # -- Inference (environment contract shared with the ``ai`` package) ---
    model_path: Path = Field(
        default=Path("models") / "best.pt",
        description="Path to the trained YOLO detector weights.",
    )
    conf_threshold: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Minimum detector confidence for a box to be kept.",
    )
    iou_threshold: float = Field(
        default=0.45,
        ge=0.0,
        le=1.0,
        description="IoU threshold used by non-maximum suppression.",
    )
    imgsz: int = Field(
        default=640,
        gt=0,
        description="Square detector input size in pixels; multiple of 32.",
    )
    device: str = Field(
        default="cpu",
        min_length=1,
        description="Torch device string, 'cpu' or 'cuda'.",
    )
    frame_stride: int = Field(
        default=5,
        gt=0,
        description="Process every Nth frame when handling a video.",
    )
    use_stub: bool = Field(
        default=False,
        description=(
            "Install the fabricating placeholder pipeline instead of the real "
            "one. Opt-in only: it invents plate numbers, so it must never be "
            "reached by accident. Intended for API tests and for demonstrating "
            "the frontend without model weights."
        ),
    )
    ocr_rec_model_dir: Path | None = Field(
        default=None,
        description="Path to optional fine-tuned recognition model directory.",
    )


    # -- Observability ----------------------------------------------------
    log_level: str = Field(
        default="INFO",
        description="Root logging level name, e.g. DEBUG, INFO, WARNING.",
    )

    # -- Validators -------------------------------------------------------

    @field_validator("cors_origins", "allowed_image_types", "allowed_video_types", mode="before")
    @classmethod
    def _split_list(cls, value: Any) -> Any:
        """Accept a comma-separated string wherever a list is expected."""
        if not isinstance(value, str):
            return value
        text = value.strip()
        if not text:
            return []
        if text.startswith("["):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return value
        return [item.strip() for item in text.split(",") if item.strip()]

    @field_validator("cors_origins")
    @classmethod
    def _reject_wildcard_origin(cls, value: list[str]) -> list[str]:
        """Refuse a wildcard CORS origin."""
        if not value:
            raise ValueError(
                "cors_origins must list at least one explicit origin; "
                "an empty allow-list blocks the frontend entirely"
            )
        if any(origin.strip() == "*" for origin in value):
            raise ValueError(
                "cors_origins must not contain '*' -- NFR-S4 requires an "
                "explicit origin allow-list"
            )
        return value

    @field_validator("imgsz")
    @classmethod
    def _validate_imgsz(cls, value: int) -> int:
        """Ensure the detector input size is a multiple of 32."""
        if value % 32 != 0:
            raise ValueError(f"imgsz must be a multiple of 32, got {value}")
        return value

    @field_validator("log_level")
    @classmethod
    def _normalize_log_level(cls, value: str) -> str:
        """Upper-case and validate the log level name."""
        level = value.strip().upper()
        valid = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}
        if level not in valid:
            raise ValueError(f"log_level must be one of {sorted(valid)}, got {value!r}")
        return level

    @model_validator(mode="after")
    def _resolve_paths(self) -> Settings:
        """Anchor every relative path and the SQLite database file."""
        self.storage_root = self._anchor(self.storage_root, PROJECT_ROOT)
        self.upload_dir = self._anchor(self.upload_dir, self.storage_root)
        self.plate_dir = self._anchor(self.plate_dir, self.storage_root)
        self.output_dir = self._anchor(self.output_dir, self.storage_root)
        self.model_path = self._anchor(self.model_path, PROJECT_ROOT)
        self.database_url = self._anchor_sqlite_url(self.database_url)
        return self

    @staticmethod
    def _anchor(path: Path, base: Path) -> Path:
        """Make a path absolute by resolving it against a base directory."""
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = base / candidate
        return candidate

    @staticmethod
    def _anchor_sqlite_url(url: str) -> str:
        """Rewrite a relative SQLite URL into an absolute one."""
        if not url.startswith(_SQLITE_SCHEME):
            return url
        raw_path = url[len(_SQLITE_SCHEME) :]
        if not raw_path or raw_path.startswith(":memory:") or raw_path.startswith("/"):
            return url
        absolute = Path(raw_path).expanduser()
        if not absolute.is_absolute():
            absolute = PROJECT_ROOT / absolute
        return f"{_SQLITE_SCHEME}{absolute.resolve().as_posix()}"

    # -- Derived values ---------------------------------------------------

    @property
    def max_image_size_bytes(self) -> int:
        """Return the image upload ceiling in bytes."""
        return self.max_image_size_mb * _MEGABYTE

    @property
    def max_video_size_bytes(self) -> int:
        """Return the video upload ceiling in bytes."""
        return self.max_video_size_mb * _MEGABYTE

    @property
    def is_sqlite(self) -> bool:
        """Return ``True`` when the configured database is SQLite."""
        return self.database_url.startswith("sqlite")

    @property
    def sqlite_file(self) -> Path | None:
        """Return the SQLite database file path, if there is one."""
        if not self.database_url.startswith(_SQLITE_SCHEME):
            return None
        raw_path = self.database_url[len(_SQLITE_SCHEME) :]
        if not raw_path or raw_path.startswith(":memory:"):
            return None
        return Path(raw_path)

    # -- Side effects -----------------------------------------------------

    def ensure_directories(self) -> None:
        """Create every directory the application writes to."""
        for directory in (
            self.storage_root,
            self.upload_dir,
            self.plate_dir,
            self.output_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

        database_file = self.sqlite_file
        if database_file is not None:
            database_file.parent.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
