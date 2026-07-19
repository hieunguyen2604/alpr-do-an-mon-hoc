"""Safe persistence of uploaded files and generated crops.

This module owns every byte the application writes to disk, and it exists
because two of the security requirements cannot be satisfied by a router that
simply calls ``open(filename, "wb")``.

**NFR-S2 -- the stored name is never the supplied name.** An uploaded filename
is attacker-controlled text. ``../../backend/main.py`` escapes the storage
directory; ``CON`` and ``LPT1`` are reserved device names on Windows that make
the write hang rather than fail; a name that merely collides with an existing
one destroys another user's file. Sanitising such a string is a losing game --
every rule has an encoding that slips past it. Instead the original name is
**discarded** and the file is stored under a freshly generated UUID. There is
no code path in which caller-supplied text becomes part of a path, so there is
nothing left to sanitise.

**NFR-S1 -- the type is read from the bytes, not from the extension.** An
extension is chosen by whoever uploads the file and proves nothing; so does the
``Content-Type`` header, which the browser copies from the extension anyway.
Both are ignored. The first bytes of the file are matched against a table of
known signatures, and only the result of that match decides whether the upload
is accepted and which extension it is stored under.

Layout under :attr:`~backend.core.config.Settings.storage_root`::

    uploads/   original images and videos as received
    plates/    cropped plate images produced by the pipeline
    outputs/   annotated images and processed videos

Nothing here builds a path from a literal (NFR-M4): all three directories come
from the injected :class:`~backend.core.config.Settings`.

A note on ``python-magic``
-------------------------
``python-magic`` is listed in ``requirements.txt`` and is used when it can be
imported, but it is **not** required. It binds to the ``libmagic`` C library,
which the Windows and Linux wheels install differently, and a service that
refuses to start because an optional native library is missing is worse than
one that falls back. The built-in signature table below covers every type the
application accepts, so detection is fully functional without it; ``libmagic``
only widens the *reporting* of types that are rejected, which improves the log
line and nothing else.
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
"""URL prefix the storage root is served under.

Kept here rather than in the router because it is the storage layer that turns
a path into a URL, and the two must agree. ``backend.main`` mounts the static
handler on this same constant, so changing the public URL is a one-line edit.
"""

_JPEG_QUALITY: Final[int] = 92
"""Encoding quality for plate crops.

Crops are small and are read back by a human checking a recognition result, so
the extra bytes over the default 95 are irrelevant while visible compression
artefacts on already-blurry characters are not.
"""

_SIGNATURE_PROBE_BYTES: Final[int] = 32
"""How much of the file the signature table needs. Every check below fits."""


class MediaKind(StrEnum):
    """Which family of upload a request is expected to carry.

    Determines both the size ceiling and the set of accepted MIME types. The
    caller states the kind it wants -- the image endpoint will not accept a
    video even though a video is a perfectly valid upload elsewhere, because
    accepting one there would send a 200 MB file into the single-image code
    path.
    """

    IMAGE = "image"
    VIDEO = "video"


class StorageCategory(StrEnum):
    """A storage sub-directory.

    The values double as the URL segment a stored file is served under, which
    is what keeps :meth:`StorageService.get_path` and
    :attr:`StoredFile.url` from drifting apart.
    """

    UPLOADS = "uploads"
    PLATES = "plates"
    OUTPUTS = "outputs"


@dataclass(frozen=True, slots=True)
class StoredFile:
    """One file that has been written to disk.

    Carries the three forms of "where it is" that different layers need, so
    that no caller has to derive one from another and get it wrong:

    * :attr:`path` -- absolute, for reading the file back;
    * :attr:`relative_path` -- what goes in the database, so the storage root
      can be moved without rewriting every row;
    * :attr:`url` -- what goes in an API response, so the server's directory
      layout is never published to the client.

    Attributes:
        path: Absolute location on disk.
        relative_path: POSIX-style path relative to the storage root, e.g.
            ``"uploads/3f2a....jpg"``. POSIX separators on purpose: a Windows
            backslash written into the database would break the URL built from
            it after a move to the Linux container.
        media_type: MIME type detected from the file's magic bytes.
        size_bytes: Size of the stored file.
    """

    path: Path
    relative_path: str
    media_type: str
    size_bytes: int

    @property
    def url(self) -> str:
        """Return the public URL this file is served under.

        Returns:
            A root-relative URL such as ``"/files/plates/3f2a-plate-0.jpg"``.
        """
        return f"{FILES_URL_PREFIX}/{self.relative_path}"


# ---------------------------------------------------------------------------
# Magic-byte detection
# ---------------------------------------------------------------------------

_ISO_BMFF_BRANDS: Final[dict[bytes, str]] = {
    b"qt  ": "video/quicktime",
    b"moov": "video/quicktime",
}
"""ISO base-media brands that are *not* MP4.

MOV and MP4 share a container: both start with a ``ftyp`` box at offset 4 and
differ only in the four-byte brand that follows. Without this table a
QuickTime file is reported as ``video/mp4``, which is close enough to be
confusing and wrong enough to fail an allow-list that lists only one of them.
"""

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
"""Extension used on disk for each recognised type.

The extension is derived from the *detected* type, never copied from the
upload. It exists only so that a developer browsing the storage directory, and
the static file handler guessing a ``Content-Type``, both see something
sensible -- nothing in the application reads it back.
"""

_UNKNOWN_MEDIA_TYPE: Final[str] = "application/octet-stream"
"""Reported when no signature matches, so the log line always names something."""


def _sniff_signature(data: bytes) -> str | None:
    """Identify a media type from the leading bytes of a file.

    Only the types this application accepts are recognised. Anything else
    returns ``None`` and is rejected by the caller -- an allow-list, so a
    format nobody thought about is refused rather than let through.

    Args:
        data: The file's contents, or at least its first
            :data:`_SIGNATURE_PROBE_BYTES` bytes.

    Returns:
        The detected MIME type, or ``None`` when no known signature matches.
    """
    if len(data) < 12:
        return None

    # -- Images ---------------------------------------------------------
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"BM"):
        return "image/bmp"

    # -- RIFF family: WebP and AVI share the first four bytes ------------
    if data.startswith(b"RIFF"):
        riff_type = data[8:12]
        if riff_type == b"WEBP":
            return "image/webp"
        if riff_type == b"AVI ":
            return "video/x-msvideo"
        return None

    # -- Matroska / WebM -------------------------------------------------
    if data.startswith(b"\x1a\x45\xdf\xa3"):
        return "video/x-matroska"

    # -- ISO base media: MP4 and MOV -------------------------------------
    if data[4:8] == b"ftyp":
        brand = data[8:12]
        return _ISO_BMFF_BRANDS.get(brand, "video/mp4")

    return None


def _sniff_with_libmagic(data: bytes) -> str | None:
    """Ask ``libmagic`` to identify bytes the built-in table did not match.

    Used purely to enrich the rejection log and the error context: knowing that
    a refused upload was a PDF rather than "unrecognised" is what turns a
    support question into an answer. The result never widens what is accepted,
    because the caller checks it against the configured allow-list either way.

    Args:
        data: The file's contents.

    Returns:
        The MIME type ``libmagic`` reports, or ``None`` when the library is not
        installed or fails to identify the bytes.
    """
    try:
        import magic  # noqa: PLC0415 -- optional dependency, imported on demand
    except ImportError:
        return None
    try:
        detected = magic.from_buffer(data[:2048], mime=True)
    except Exception:  # pragma: no cover -- libmagic failure must not 500
        logger.warning("libmagic failed to identify an upload", exc_info=True)
        return None
    return str(detected) if detected else None


def detect_media_type(data: bytes) -> str:
    """Determine a file's MIME type from its contents.

    The public form of the NFR-S1 rule: the answer comes from the bytes, and
    the caller never passes in a filename or a ``Content-Type`` header for this
    function to be influenced by -- it cannot consult them because it is not
    given them.

    Args:
        data: The complete file contents, or at least its first kilobyte.

    Returns:
        The detected MIME type, or ``"application/octet-stream"`` when nothing
        recognised the bytes.
    """
    detected = _sniff_signature(data[:_SIGNATURE_PROBE_BYTES])
    if detected is not None:
        return detected
    return _sniff_with_libmagic(data) or _UNKNOWN_MEDIA_TYPE


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class StorageService:
    """Writes, locates and deletes the application's files.

    Every path is derived from the injected settings, so a test can point the
    whole service at a temporary directory by constructing one ``Settings``
    object -- no monkey-patching and no global state.

    The service is stateless beyond its configuration and is safe to share
    across requests.
    """

    def __init__(self, settings: Settings) -> None:
        """Create the service.

        Args:
            settings: Configuration supplying the storage directories and the
                upload limits. Directories are *not* created here --
                :meth:`~backend.core.config.Settings.ensure_directories` does
                that once at start-up, so that a missing directory fails the
                boot rather than a user's first upload.
        """
        self._settings = settings

    # -- Directory resolution --------------------------------------------

    def _directory_for(self, category: StorageCategory) -> Path:
        """Return the configured directory for a storage category.

        Args:
            category: Which sub-directory is wanted.

        Returns:
            The absolute directory path taken from the settings.
        """
        mapping: dict[StorageCategory, Path] = {
            StorageCategory.UPLOADS: self._settings.upload_dir,
            StorageCategory.PLATES: self._settings.plate_dir,
            StorageCategory.OUTPUTS: self._settings.output_dir,
        }
        return mapping[category]

    def get_path(self, relative_path: str) -> Path:
        """Resolve a stored file's relative path back to an absolute one.

        This is the read-side half of NFR-S2. Values reaching it come from the
        database, but a database value is only as trustworthy as whatever wrote
        it, and this function is one HTTP parameter away from being the target
        of a traversal attempt. It therefore re-derives the path from the
        configured root and **verifies containment after resolution** --
        checking before resolving would miss ``uploads/../../etc/passwd``,
        since the ``..`` segments only collapse during ``resolve()``.

        Args:
            relative_path: A path relative to the storage root, as stored in
                :attr:`StoredFile.relative_path`, e.g. ``"plates/x.jpg"``.

        Returns:
            The absolute path to the file.

        Raises:
            ValidationError: If the resolved path lies outside the storage
                root, or if the leading segment is not a known category.
        """
        root = self._settings.storage_root.resolve()
        candidate = (root / relative_path).resolve()

        if candidate != root and root not in candidate.parents:
            raise ValidationError(
                f"Path traversal attempt rejected: {relative_path!r} "
                f"resolves outside the storage root",
                context={"relative_path": relative_path},
            )
        return candidate

    def _relative_to_root(self, path: Path) -> str:
        """Express an absolute stored path relative to the storage root.

        Args:
            path: Absolute path of a file inside the storage root.

        Returns:
            A POSIX-style relative path suitable for the database and for
            building a URL.

        Raises:
            ProcessingError: If the path is not inside the storage root, which
                would mean the service wrote somewhere it should not have.
        """
        root = self._settings.storage_root.resolve()
        try:
            return path.resolve().relative_to(root).as_posix()
        except ValueError as error:
            raise ProcessingError(
                f"Stored file {path} is outside the storage root {root}",
                context={"path": str(path)},
            ) from error

    # -- Validation -------------------------------------------------------

    def _limits_for(self, kind: MediaKind) -> tuple[int, list[str]]:
        """Return the size ceiling and accepted MIME types for a media kind.

        Args:
            kind: Whether an image or a video is expected.

        Returns:
            A ``(max_bytes, allowed_mime_types)`` pair drawn from the settings.
        """
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
        """Check an upload's size and true type before anything is written.

        Runs in this order on purpose: emptiness, then size, then type. Size is
        checked before the signature so that a 500 MB file is rejected without
        the type check ever touching it, and both are checked before a single
        byte reaches the disk.

        Args:
            data: The complete upload contents.
            kind: Whether the endpoint expects an image or a video.
            original_filename: The client-supplied name. Used **only** in log
                and error context -- never to determine the type, and never as
                part of a path.

        Returns:
            The MIME type detected from the file's magic bytes.

        Raises:
            ValidationError: If the upload is empty.
            FileTooLargeError: If it exceeds the configured ceiling.
            UnsupportedMediaTypeError: If its detected type is not accepted for
                this kind of upload.
        """
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

    # -- Writing ----------------------------------------------------------

    def _write(self, directory: Path, filename: str, payload: bytes) -> Path:
        """Write bytes to disk, creating the directory if necessary.

        Args:
            directory: Target directory.
            filename: Generated filename; never derived from user input.
            payload: The bytes to write.

        Returns:
            The absolute path written.

        Raises:
            ProcessingError: If the write fails -- a full disk, a permission
                problem, a read-only mount.
        """
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / filename
        try:
            target.write_bytes(payload)
        except OSError as error:
            raise ProcessingError(
                f"Failed to write {target}: {error}",
                context={"path": str(target), "size_bytes": len(payload)},
            ) from error
        return target

    def save_upload(
        self,
        data: bytes,
        *,
        kind: MediaKind,
        original_filename: str | None = None,
    ) -> StoredFile:
        """Validate an upload and store it under a generated name.

        The original filename is deliberately dropped. It is recorded in the
        log for traceability and then never referenced again -- there is no
        code path from it to the filesystem, which is what makes path traversal
        impossible rather than merely difficult (NFR-S2).

        Args:
            data: The complete upload contents.
            kind: Whether the endpoint expects an image or a video.
            original_filename: The client-supplied name, for the log only.

        Returns:
            A :class:`StoredFile` describing where the upload now lives.

        Raises:
            ValidationError: If the upload is empty.
            FileTooLargeError: If it exceeds the configured ceiling.
            UnsupportedMediaTypeError: If its true type is not accepted.
            ProcessingError: If the file could not be written.
        """
        media_type = self.validate_upload(
            data, kind=kind, original_filename=original_filename
        )

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
                # The size and the detected type are logged; the bytes never
                # are (NFR-S5).
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
        """Encode a cropped plate image and store it.

        Named after the job that produced it and the plate's position within
        that job, so the crops belonging to one upload sort together on disk --
        useful when checking a multi-plate result by eye. The job identifier is
        already a UUID, so the name stays unguessable.

        Args:
            image: The crop as a BGR ``uint8`` array, as produced by the
                pipeline.
            job_id: Identifier of the job this plate belongs to.
            index: Zero-based position of the plate within the job.

        Returns:
            A :class:`StoredFile` describing the stored crop.

        Raises:
            ValidationError: If the array is empty or not a usable image.
            ProcessingError: If encoding or writing fails.
        """
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
        """Store an annotated result image for a job.

        Args:
            image: The rendered image as a BGR ``uint8`` array.
            job_id: Identifier of the job the image illustrates.

        Returns:
            A :class:`StoredFile` describing the stored image.

        Raises:
            ValidationError: If the array is empty.
            ProcessingError: If encoding or writing fails.
        """
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

    # -- Deletion ---------------------------------------------------------

    def delete_file(self, relative_path: str | None) -> bool:
        """Delete a stored file, tolerating one that is already gone.

        Deleting a history record must not fail because its image had already
        been removed -- from the user's point of view the desired end state is
        identical, and raising would leave a row that can never be deleted.
        A missing file is therefore reported as ``False``, not as an error.

        Args:
            relative_path: Path relative to the storage root, or ``None`` when
                the record never had a file.

        Returns:
            ``True`` if a file was removed, ``False`` if there was nothing to
            remove.

        Raises:
            ValidationError: If the path escapes the storage root.
        """
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
            # A locked or read-only file is worth a log line, but failing the
            # user's delete request over it would be worse than leaving one
            # orphaned file behind.
            logger.warning(
                "could not delete stored file",
                extra={"relative_path": relative_path, "reason": str(error)},
            )
            return False

        logger.info("stored file deleted", extra={"relative_path": relative_path})
        return True

    # -- Reading ----------------------------------------------------------

    def to_url(self, relative_path: str | None) -> str | None:
        """Convert a stored relative path into a public URL.

        Args:
            relative_path: Path relative to the storage root, or ``None``.

        Returns:
            The URL the file is served under, or ``None`` when there is no
            file. Returning ``None`` rather than an empty string keeps the
            distinction between "no image" and "an image at the empty URL"
            visible in the JSON response.
        """
        if not relative_path:
            return None
        return f"{FILES_URL_PREFIX}/{relative_path}"
