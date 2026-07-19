"""Centralised application settings for the ALPR backend.

This module is the single source of truth for configuration. No other module in
``backend`` may read ``os.environ`` or build a filesystem path from a literal:
that is the whole content of NFR-M4, and it is what lets the identical code run
on a Windows development machine and inside the Linux Docker image without an
edit.

Relationship with the ``ai`` package
------------------------------------
``ai.inference.config.InferenceConfig`` is a plain dataclass reading the same
``ALPR_`` environment prefix, because the ``ai`` package must not import
Pydantic (NFR-M1). The two configuration objects are therefore *separate types*
that deliberately share an environment contract: ``ALPR_MODEL_PATH``,
``ALPR_DEVICE``, ``ALPR_CONF_THRESHOLD``, ``ALPR_IOU_THRESHOLD`` and
``ALPR_IMGSZ`` mean the same thing to both. One ``.env`` file configures both
layers, and no value has to be stated twice.

Path resolution
---------------
Every path is anchored, never trusted as given:

* an **absolute** value is used unchanged;
* a **relative** storage directory is resolved against :attr:`Settings.storage_root`;
* a **relative** ``storage_root`` or ``model_path`` is resolved against
  :data:`PROJECT_ROOT`, which is derived from this file's own location.

The consequence that matters: the process behaves identically no matter which
working directory it was started from. ``uvicorn`` launched from ``backend/``
and Alembic launched from the repository root see exactly the same paths.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any, Final

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

__all__ = ["PROJECT_ROOT", "Settings", "get_settings"]

StringList = Annotated[list[str], NoDecode]
"""A list field that pydantic-settings must not JSON-decode on its own.

Without ``NoDecode``, a list-typed setting read from the environment or a
``.env`` file is passed through ``json.loads`` *before* any validator runs, so
the natural line::

    ALPR_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

raises ``JSONDecodeError`` at start-up and the ``mode="before"`` validator below
never sees it. Suppressing the built-in decoding hands the raw string to
:meth:`Settings._split_list`, which accepts both the comma-separated form and
JSON.

The failure this prevents is a nasty one: the same value supplied as a keyword
argument works fine, because the init source does not decode. A unit test
constructing ``Settings(cors_origins="a,b")`` would therefore pass while the
deployed service refused to boot.
"""

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
"""Repository root, derived from ``<root>/backend/core/config.py``.

Computed from ``__file__`` rather than the working directory so that moving or
renaming the checkout breaks nothing and no absolute path is ever written down.
"""

_MEGABYTE: Final[int] = 1024 * 1024

_SQLITE_SCHEME: Final[str] = "sqlite:///"
"""URL prefix that marks a file-backed SQLite database."""


class Settings(BaseSettings):
    """Runtime configuration for the backend, read from the environment.

    Values are resolved in this order, first match winning:

    1. an explicit keyword argument (used by tests),
    2. an environment variable named ``ALPR_<FIELD>`` in upper case,
    3. the same variable defined in a ``.env`` file,
    4. the field default declared here.

    Empty environment variables are treated as *unset* rather than as an empty
    string, so a stray ``ALPR_DEVICE=`` in a shell profile cannot silently
    blank out a setting.

    An instance is built once per process by :func:`get_settings` and injected
    wherever it is needed. Modules must not construct their own: two instances
    could disagree, and configuration that disagrees with itself is worse than
    configuration that is wrong.

    Attributes:
        app_name: Human-readable service name, shown in Swagger and ``/health``.
        app_version: Version string reported by ``/health``.
        debug: Enables verbose behaviour -- SQL echo and full tracebacks in the
            log. Never enable in production: it does *not* change what the user
            sees (errors stay opaque either way, NFR-S4), only how much detail
            is written server-side.
        api_prefix: Common prefix mounted in front of every router.
        database_url: SQLAlchemy connection URL.
        storage_root: Base directory for everything written to disk.
        upload_dir: Original uploaded images and videos.
        plate_dir: Cropped plate images.
        output_dir: Rendered result images and processed videos.
        max_image_size_mb: Upload ceiling for images, in megabytes.
        max_video_size_mb: Upload ceiling for videos, in megabytes.
        allowed_image_types: Accepted image MIME types, verified against the
            file's magic bytes rather than its extension (NFR-S1).
        allowed_video_types: Accepted video MIME types, verified the same way.
        cors_origins: Browser origins allowed to call the API.
        model_path: Detector weights. Shared with the ``ai`` package through
            ``ALPR_MODEL_PATH``.
        conf_threshold: Minimum detector confidence, in ``[0.0, 1.0]``.
        iou_threshold: Non-maximum-suppression IoU threshold, in ``[0.0, 1.0]``.
        imgsz: Square detector input size in pixels; a positive multiple of 32.
        device: Torch device string. Defaults to ``"cpu"`` -- the target machine
            has no CUDA GPU (decision AD-06).
        frame_stride: Process every Nth video frame. Raising this speeds video
            jobs up proportionally at the cost of possibly missing a plate that
            is only briefly visible.
        log_level: Root log level name, e.g. ``"INFO"``.
    """

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

    # -- Observability ----------------------------------------------------
    log_level: str = Field(
        default="INFO",
        description="Root logging level name, e.g. DEBUG, INFO, WARNING.",
    )

    # -- Validators -------------------------------------------------------

    @field_validator("cors_origins", "allowed_image_types", "allowed_video_types", mode="before")
    @classmethod
    def _split_list(cls, value: Any) -> Any:
        """Accept a comma-separated string wherever a list is expected.

        Pydantic-settings parses list-typed fields as JSON, which makes the
        obvious ``.env`` line ``ALPR_CORS_ORIGINS=http://a,http://b`` a hard
        error. Since ``.env`` files are hand-edited by people, the friendlier
        form is supported too; JSON is still accepted so generated deployment
        configuration keeps working.

        Args:
            value: Raw value straight from the environment or the field default.

        Returns:
            A list of strings when the input was a delimited string, otherwise
            the value unchanged for Pydantic to handle.
        """
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
        """Refuse a wildcard CORS origin.

        NFR-S4 requires an explicit origin allow-list. This is enforced at
        start-up rather than reviewed by eye, because ``"*"`` is exactly the
        value someone reaches for while debugging and then forgets to remove.

        Args:
            value: The configured origins.

        Returns:
            The origins unchanged when all of them are explicit.

        Raises:
            ValueError: If the list is empty or contains ``"*"``.
        """
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
        """Ensure the detector input size is a multiple of 32.

        The YOLO backbone downsamples by 32, so any other value is silently
        resized at inference time -- meaning the configured number would not be
        the number actually used.

        Args:
            value: Configured input size in pixels.

        Returns:
            The value unchanged when valid.

        Raises:
            ValueError: If the value is not a multiple of 32.
        """
        if value % 32 != 0:
            raise ValueError(f"imgsz must be a multiple of 32, got {value}")
        return value

    @field_validator("log_level")
    @classmethod
    def _normalize_log_level(cls, value: str) -> str:
        """Upper-case and validate the log level name.

        Args:
            value: Configured level name, in any case.

        Returns:
            The canonical upper-case level name.

        Raises:
            ValueError: If the name is not a standard logging level.
        """
        level = value.strip().upper()
        valid = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}
        if level not in valid:
            raise ValueError(
                f"log_level must be one of {sorted(valid)}, got {value!r}"
            )
        return level

    @model_validator(mode="after")
    def _resolve_paths(self) -> Settings:
        """Anchor every relative path and the SQLite database file.

        Runs after all fields are populated, which is what makes it possible to
        resolve the storage sub-directories against ``storage_root`` -- a
        field-level validator cannot see its siblings.

        Returns:
            The same instance, with all path fields absolute.
        """
        self.storage_root = self._anchor(self.storage_root, PROJECT_ROOT)
        self.upload_dir = self._anchor(self.upload_dir, self.storage_root)
        self.plate_dir = self._anchor(self.plate_dir, self.storage_root)
        self.output_dir = self._anchor(self.output_dir, self.storage_root)
        self.model_path = self._anchor(self.model_path, PROJECT_ROOT)
        self.database_url = self._anchor_sqlite_url(self.database_url)
        return self

    @staticmethod
    def _anchor(path: Path, base: Path) -> Path:
        """Make a path absolute by resolving it against a base directory.

        Args:
            path: Configured path, absolute or relative.
            base: Directory a relative path is interpreted against.

        Returns:
            An absolute path with ``~`` expanded.
        """
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = base / candidate
        return candidate

    @staticmethod
    def _anchor_sqlite_url(url: str) -> str:
        """Rewrite a relative SQLite URL into an absolute one.

        ``sqlite:///./data/alpr.db`` is relative to the *working directory*,
        so the server and Alembic would open two different database files when
        launched from different folders -- a failure that looks like vanished
        data rather than a configuration mistake. Anchoring the path to the
        project root removes the possibility.

        Non-SQLite URLs and URLs already carrying an absolute path are returned
        untouched, as is the in-memory database used by tests.

        Args:
            url: The configured SQLAlchemy URL.

        Returns:
            The URL with any relative SQLite file path made absolute.
        """
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
    def allowed_media_types(self) -> list[str]:
        """Return every accepted MIME type, images and videos together."""
        return [*self.allowed_image_types, *self.allowed_video_types]

    @property
    def is_sqlite(self) -> bool:
        """Return ``True`` when the configured database is SQLite.

        Used by the engine factory, which must apply SQLite-specific
        connection arguments and pragmas that other backends reject.
        """
        return self.database_url.startswith("sqlite")

    @property
    def sqlite_file(self) -> Path | None:
        """Return the SQLite database file path, if there is one.

        Returns:
            The absolute path to the database file, or ``None`` when the
            database is not a file-backed SQLite database (another engine, or
            SQLite in memory). Callers use it to create the parent directory
            before SQLAlchemy first connects -- SQLite will not create a
            missing folder and fails with an opaque "unable to open database
            file" instead.
        """
        if not self.database_url.startswith(_SQLITE_SCHEME):
            return None
        raw_path = self.database_url[len(_SQLITE_SCHEME) :]
        if not raw_path or raw_path.startswith(":memory:"):
            return None
        return Path(raw_path)

    # -- Side effects -----------------------------------------------------

    def ensure_directories(self) -> None:
        """Create every directory the application writes to.

        Called once during application start-up. Creating the folders up front
        turns a missing directory into a start-up failure instead of a failure
        halfway through a user's first upload, when a file has already been
        partially consumed.

        Idempotent: existing directories are left alone.
        """
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
    """Return the process-wide settings instance.

    Cached so that the environment and the ``.env`` file are read exactly once
    and every caller observes the same object. This function is what the API
    layer uses as a FastAPI dependency, which also makes it overridable in
    tests via ``app.dependency_overrides``.

    Returns:
        The shared, fully validated settings instance.

    Raises:
        pydantic.ValidationError: If any environment value is missing, of the
            wrong type, or out of range. Failing here means the process refuses
            to start rather than misbehaving later under a bad configuration.
    """
    return Settings()
