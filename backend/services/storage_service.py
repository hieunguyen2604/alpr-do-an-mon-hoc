"""Safe persistence of uploaded files and generated crops.

- NFR-S2: Stored filenames are random UUIDs, discarding client-provided names.
- NFR-S1: Media MIME types are verified directly from magic bytes.
- NFR-M4: Storage directory paths are injected from configuration.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

import cv2
import numpy as np

from backend.core.config import Settings
from backend.core.exceptions import (
    FileTooLargeError,
    ProcessingError,
    UnsupportedMediaTypeError,
    ValidationError,
)
from backend.core.logging import get_logger

__all__ = [
    "FILES_URL_PREFIX",
    "MediaKind",
    "StorageCategory",
    "StoredFile",
    "StorageService",
    "detect_media_type",
]

logger = get_logger(__name__)

FILES_URL_PREFIX: Final[str] = "/files"
"""URL prefix the storage root is served under."""

_JPEG_QUALITY: Final[int] = 92
"""Encoding quality for plate crops and output images."""

_SIGNATURE_PROBE_BYTES: Final[int] = 32
"""Bytes needed to probe file magic signature."""


class MediaKind(StrEnum):
    """Upload media family (image or video)."""

    IMAGE = "image"
    VIDEO = "video"


class StorageCategory(StrEnum):
    """Storage sub-directory categories."""

    UPLOADS = "uploads"
    PLATES = "plates"
    OUTPUTS = "outputs"


@dataclass(frozen=True, slots=True)
class StoredFile:
    """Represents a file written to disk."""

    path: Path
    relative_path: str
    media_type: str
    size_bytes: int

    @property
    def url(self) -> str:
        """Return public URL path for the stored file."""
        return f"{FILES_URL_PREFIX}/{self.relative_path}"


_ISO_BMFF_BRANDS: Final[dict[bytes, str]] = {
    b"qt  ": "video/quicktime",
    b"moov": "video/quicktime",
}
"""ISO base-media brands for QuickTime video."""

_MIME_EXTENSIONS: Final[dict[str, str]] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "video/x-msvideo": ".avi",
    "video/x-matroska": ".mkv",
}
"""Extension mapped for each recognized MIME type."""

_UNKNOWN_MEDIA_TYPE: Final[str] = "application/octet-stream"


def _sniff_signature(data: bytes) -> str | None:
    """Identify media type from leading magic bytes."""
    if len(data) < 12:
        return None

    # Images
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"BM"):
        return "image/bmp"

    # RIFF family: WebP and AVI
    if data.startswith(b"RIFF"):
        riff_type = data[8:12]
        if riff_type == b"WEBP":
            return "image/webp"
        if riff_type == b"AVI ":
            return "video/x-msvideo"
        return None

    # Matroska / WebM
    if data.startswith(b"\x1a\x45\xdf\xa3"):
        return "video/x-matroska"

    # ISO base media: MP4 and MOV
    if data[4:8] == b"ftyp":
        brand = data[8:12]
        return _ISO_BMFF_BRANDS.get(brand, "video/mp4")

    return None


def _sniff_with_libmagic(data: bytes) -> str | None:
    """Identify MIME type using optional libmagic for logging context."""
    try:
        import magic  # noqa: PLC0415
    except ImportError:
        return None
    try:
        detected = magic.from_buffer(data[:2048], mime=True)
    except Exception:
        logger.warning("libmagic failed to identify an upload", exc_info=True)
        return None
    return str(detected) if detected else None


def detect_media_type(data: bytes) -> str:
    """Determine file MIME type from its content (NFR-S1)."""
    detected = _sniff_signature(data[:_SIGNATURE_PROBE_BYTES])
    if detected is not None:
        return detected
    return _sniff_with_libmagic(data) or _UNKNOWN_MEDIA_TYPE


class StorageService:
    """Writes, locates and deletes files in application storage."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _directory_for(self, category: StorageCategory) -> Path:
        """Return configured directory for a storage category."""
        mapping: dict[StorageCategory, Path] = {
            StorageCategory.UPLOADS: self._settings.upload_dir,
            StorageCategory.PLATES: self._settings.plate_dir,
            StorageCategory.OUTPUTS: self._settings.output_dir,
        }
        return mapping[category]

    def get_path(self, relative_path: str) -> Path:
        """Resolve and verify absolute path for a stored relative path."""
        root = self._settings.storage_root.resolve()
        candidate = (root / relative_path).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as error:
            raise ValidationError(
                f"Path traversal attempt rejected: {relative_path!r} "
                f"resolves outside the storage root",
                context={"relative_path": relative_path},
            ) from error
        return candidate

    def _relative_to_root(self, path: Path) -> str:
        """Return POSIX-style path relative to storage root."""
        root = self._settings.storage_root.resolve()
        try:
            rel = path.resolve().relative_to(root)
            return rel.as_posix()
        except ValueError as error:
            raise ProcessingError(
                f"Stored file {path} is outside the storage root {root}",
                context={"path": str(path)},
            ) from error

    def _limits_for(self, kind: MediaKind) -> tuple[int, list[str]]:
        """Return max size and allowed MIME types for a media kind."""
        if kind is MediaKind.IMAGE:
            return self._settings.max_image_size_bytes, self._settings.allowed_image_types
        return self._settings.max_video_size_bytes, self._settings.allowed_video_types

    def validate_upload(
        self,
        data: bytes,
        *,
        kind: MediaKind,
        original_filename: str | None = None,
    ) -> str:
        """Validate upload size and MIME type before persistence."""
        if not data:
            raise ValidationError(
                "Upload contained no data",
                user_message="Tệp tải lên rỗng. Vui lòng chọn một tệp khác.",
                context={"filename": original_filename},
            )

        max_bytes, allowed_types = self._limits_for(kind)
        if len(data) > max_bytes:
            raise FileTooLargeError.with_limit(
                actual_bytes=len(data),
                limit_bytes=max_bytes,
                filename=original_filename,
            )

        media_type = detect_media_type(data)
        if media_type not in allowed_types:
            raise UnsupportedMediaTypeError.with_detected_type(
                detected_type=media_type,
                allowed_types=list(allowed_types),
                filename=original_filename,
            )
        return media_type

    def _write(self, directory: Path, filename: str, payload: bytes) -> Path:
        """Write bytes to target directory."""
        try:
            directory.mkdir(parents=True, exist_ok=True)
            target = directory / filename
            target.write_bytes(payload)
            return target
        except OSError as error:
            raise ProcessingError(
                f"Failed to write stored file {filename}",
                context={"directory": str(directory), "filename": filename},
            ) from error

    def save_upload(
        self,
        data: bytes,
        *,
        kind: MediaKind,
        original_filename: str | None = None,
    ) -> StoredFile:
        """Validate and write uploaded payload under a new UUID filename (NFR-S2)."""
        media_type = self.validate_upload(data, kind=kind, original_filename=original_filename)

        extension = _MIME_EXTENSIONS.get(media_type, ".bin")
        filename = f"{uuid.uuid4().hex}{extension}"
        directory = self._directory_for(StorageCategory.UPLOADS)
        path = self._write(directory, filename, data)

        stored = StoredFile(
            path=path,
            relative_path=self._relative_to_root(path),
            media_type=media_type,
            size_bytes=len(data),
        )
        logger.info(
            "upload stored",
            extra={
                "stored_as": stored.relative_path,
                "media_type": media_type,
                "size_bytes": stored.size_bytes,
                "original_filename": original_filename,
            },
        )
        return stored

    def save_plate_crop(
        self,
        image: np.ndarray,
        *,
        job_id: str,
        index: int,
    ) -> StoredFile:
        """Encode and save a cropped license plate image."""
        if image is None or image.size == 0:
            raise ValidationError(
                "Refusing to store an empty plate crop",
                context={"job_id": job_id, "index": index},
            )

        success, buffer = cv2.imencode(
            ".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), _JPEG_QUALITY]
        )
        if not success:
            raise ProcessingError(
                "cv2.imencode failed to encode a plate crop",
                context={"job_id": job_id, "index": index},
            )

        payload = buffer.tobytes()
        filename = f"{job_id}-plate-{index}.jpg"
        directory = self._directory_for(StorageCategory.PLATES)
        path = self._write(directory, filename, payload)

        return StoredFile(
            path=path,
            relative_path=self._relative_to_root(path),
            media_type="image/jpeg",
            size_bytes=len(payload),
        )

    def save_output_image(
        self,
        image: np.ndarray,
        *,
        job_id: str,
    ) -> StoredFile:
        """Encode and save an annotated result image."""
        if image is None or image.size == 0:
            raise ValidationError(
                "Refusing to store an empty output image",
                context={"job_id": job_id},
            )

        success, buffer = cv2.imencode(
            ".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), _JPEG_QUALITY]
        )
        if not success:
            raise ProcessingError(
                "cv2.imencode failed to encode an output image",
                context={"job_id": job_id},
            )

        payload = buffer.tobytes()
        directory = self._directory_for(StorageCategory.OUTPUTS)
        path = self._write(directory, f"{job_id}-result.jpg", payload)

        return StoredFile(
            path=path,
            relative_path=self._relative_to_root(path),
            media_type="image/jpeg",
            size_bytes=len(payload),
        )

    def delete_file(self, relative_path: str | None) -> bool:
        """Delete a stored file safely."""
        if not relative_path:
            return False

        path = self.get_path(relative_path)
        try:
            path.unlink()
        except FileNotFoundError:
            logger.debug(
                "file already absent at delete time",
                extra={"relative_path": relative_path},
            )
            return False
        except OSError as error:
            logger.warning(
                "could not delete stored file",
                extra={"relative_path": relative_path, "reason": str(error)},
            )
            return False

        logger.info("stored file deleted", extra={"relative_path": relative_path})
        return True

    def to_url(self, relative_path: str | None) -> str | None:
        """Convert a stored relative path into a public URL string."""
        if not relative_path:
            return None
        return f"{FILES_URL_PREFIX}/{relative_path}"
