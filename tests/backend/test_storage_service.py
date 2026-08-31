"""Unit tests for :mod:`backend.services.storage_service`."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from backend.core.config import Settings
from backend.core.exceptions import (
    FileTooLargeError,
    UnsupportedMediaTypeError,
    ValidationError,
)
from backend.services.storage_service import (
    FILES_URL_PREFIX,
    MediaKind,
    StorageCategory,
    StorageService,
    StoredFile,
    _sniff_signature,
    detect_media_type,
)

_ALL_ACCEPTED_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/bmp",
        "video/mp4",
        "video/quicktime",
        "video/x-msvideo",
        "video/x-matroska",
    }
)
"""Every MIME type any endpoint accepts."""

# -- Minimal byte sequences carrying a recognisable signature ---------------
#
# Padded past the 12-byte minimum the sniffer requires. Real files are not
# needed: the function under test reads only the leading bytes.

_PAD = b"\x00" * 24

JPEG_BYTES = b"\xff\xd8\xff\xe0" + _PAD
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + _PAD
BMP_BYTES = b"BM" + _PAD
WEBP_BYTES = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + _PAD
AVI_BYTES = b"RIFF" + b"\x00\x00\x00\x00" + b"AVI " + _PAD
MKV_BYTES = b"\x1a\x45\xdf\xa3" + _PAD
MP4_BYTES = b"\x00\x00\x00\x18" + b"ftyp" + b"isom" + _PAD
MOV_BYTES = b"\x00\x00\x00\x18" + b"ftyp" + b"qt  " + _PAD

EXE_BYTES = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff" + _PAD
"""A Windows PE executable header -- the classic ``.exe`` renamed ``.jpg``."""

PDF_BYTES = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n" + _PAD
ZIP_BYTES = b"PK\x03\x04\x14\x00\x00\x00\x08\x00\x00\x00" + _PAD


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    """Build settings pointing entirely at a throwaway directory."""
    root = tmp_path / "storage"
    config = Settings(
        storage_root=root,
        upload_dir=root / "uploads",
        plate_dir=root / "plates",
        output_dir=root / "outputs",
        database_url="sqlite:///:memory:",
        max_image_size_mb=1,
        max_video_size_mb=2,
        cors_origins=["http://localhost:5173"],
    )
    config.ensure_directories()
    return config


@pytest.fixture()
def storage(settings: Settings) -> StorageService:
    """A storage service bound to the throwaway directory."""
    return StorageService(settings)


class TestMagicByteDetection:
    """NFR-S1: the MIME type is read from the file's contents."""

    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (JPEG_BYTES, "image/jpeg"),
            (PNG_BYTES, "image/png"),
            (BMP_BYTES, "image/bmp"),
            (WEBP_BYTES, "image/webp"),
            (AVI_BYTES, "video/x-msvideo"),
            (MKV_BYTES, "video/x-matroska"),
            (MP4_BYTES, "video/mp4"),
            (MOV_BYTES, "video/quicktime"),
        ],
    )
    def test_recognises_every_accepted_format(self, data: bytes, expected: str) -> None:
        assert detect_media_type(data) == expected

    def test_mov_and_mp4_are_distinguished_by_their_brand(self) -> None:
        """Both carry ``ftyp`` at offset 4 and differ only in the brand."""
        assert detect_media_type(MP4_BYTES) == "video/mp4"
        assert detect_media_type(MOV_BYTES) == "video/quicktime"

    def test_webp_and_avi_are_distinguished_despite_a_shared_riff_header(self) -> None:
        assert WEBP_BYTES[:4] == AVI_BYTES[:4] == b"RIFF"
        assert detect_media_type(WEBP_BYTES) == "image/webp"
        assert detect_media_type(AVI_BYTES) == "video/x-msvideo"

    def test_an_unknown_riff_subtype_is_not_accepted(self) -> None:
        """A WAV file is RIFF too; the allow-list must not let it through."""
        wave = b"RIFF" + b"\x00\x00\x00\x00" + b"WAVE" + _PAD
        assert detect_media_type(wave) not in _ALL_ACCEPTED_TYPES

    @pytest.mark.parametrize("data", [EXE_BYTES, PDF_BYTES, ZIP_BYTES])
    def test_an_unrecognised_format_never_reports_an_accepted_type(self, data: bytes) -> None:
        """What matters is that the answer is outside the allow-list."""
        assert detect_media_type(data) not in _ALL_ACCEPTED_TYPES

    @pytest.mark.parametrize("data", [b"", b"short"])
    def test_a_file_too_short_to_identify_is_not_accepted(self, data: bytes) -> None:
        """Fewer than 12 bytes cannot match a signature, so nothing is assumed."""
        assert detect_media_type(data) not in _ALL_ACCEPTED_TYPES

    def test_the_builtin_table_alone_refuses_a_truncated_signature(self) -> None:
        """The fallback path, exercised without ``libmagic`` in the way."""
        assert _sniff_signature(b"\xff\xd8\xff") is None
        assert _sniff_signature(b"") is None

    def test_only_the_leading_bytes_are_consulted(self) -> None:
        """A JPEG header followed by arbitrary payload is still a JPEG here."""
        assert detect_media_type(JPEG_BYTES + b"whatever" * 100) == "image/jpeg"


class TestUploadValidation:
    """Size and type checks, in the order they are applied."""

    def test_accepts_a_valid_image(self, storage: StorageService) -> None:
        assert storage.validate_upload(JPEG_BYTES, kind=MediaKind.IMAGE) == "image/jpeg"

    def test_accepts_a_valid_video(self, storage: StorageService) -> None:
        assert storage.validate_upload(MP4_BYTES, kind=MediaKind.VIDEO) == "video/mp4"

    def test_rejects_an_empty_upload(self, storage: StorageService) -> None:
        with pytest.raises(ValidationError):
            storage.validate_upload(b"", kind=MediaKind.IMAGE)

    def test_rejects_an_oversized_image(self, storage: StorageService, settings: Settings) -> None:
        oversized = JPEG_BYTES + b"\x00" * settings.max_image_size_bytes
        with pytest.raises(FileTooLargeError):
            storage.validate_upload(oversized, kind=MediaKind.IMAGE)

    def test_accepts_a_file_exactly_at_the_ceiling(
        self, storage: StorageService, settings: Settings
    ) -> None:
        """The limit is inclusive; only *exceeding* it is refused."""
        exact = JPEG_BYTES + b"\x00" * (settings.max_image_size_bytes - len(JPEG_BYTES))
        assert len(exact) == settings.max_image_size_bytes
        assert storage.validate_upload(exact, kind=MediaKind.IMAGE) == "image/jpeg"

    def test_size_is_checked_before_the_signature(
        self, storage: StorageService, settings: Settings
    ) -> None:
        """A 500 MB file must be refused without the type check touching it."""
        oversized_garbage = EXE_BYTES + b"\x00" * settings.max_image_size_bytes
        with pytest.raises(FileTooLargeError):
            storage.validate_upload(oversized_garbage, kind=MediaKind.IMAGE)

    def test_rejects_an_executable_renamed_as_an_image(self, storage: StorageService) -> None:
        """NFR-S1, stated as the attack it prevents."""
        with pytest.raises(UnsupportedMediaTypeError):
            storage.validate_upload(EXE_BYTES, kind=MediaKind.IMAGE, original_filename="photo.jpg")

    @pytest.mark.parametrize("data", [PDF_BYTES, ZIP_BYTES])
    def test_rejects_any_unlisted_format(self, storage: StorageService, data: bytes) -> None:
        with pytest.raises(UnsupportedMediaTypeError):
            storage.validate_upload(data, kind=MediaKind.IMAGE)

    def test_a_video_is_not_accepted_by_the_image_endpoint(self, storage: StorageService) -> None:
        """Accepting one would send a 200 MB file into the single-image path."""
        with pytest.raises(UnsupportedMediaTypeError):
            storage.validate_upload(MP4_BYTES, kind=MediaKind.IMAGE)

    def test_an_image_is_not_accepted_by_the_video_endpoint(self, storage: StorageService) -> None:
        with pytest.raises(UnsupportedMediaTypeError):
            storage.validate_upload(JPEG_BYTES, kind=MediaKind.VIDEO)

    def test_the_two_kinds_have_different_ceilings(
        self, storage: StorageService, settings: Settings
    ) -> None:
        """A file too large as an image can still be a legal video."""
        between = MP4_BYTES + b"\x00" * settings.max_image_size_bytes
        assert len(between) > settings.max_image_size_bytes
        assert len(between) <= settings.max_video_size_bytes
        assert storage.validate_upload(between, kind=MediaKind.VIDEO) == "video/mp4"


class TestGeneratedFilenames:
    """NFR-S2: the client's filename is discarded, never reused."""

    def test_the_stored_name_is_a_uuid_hex_string(self, storage: StorageService) -> None:
        stored = storage.save_upload(
            JPEG_BYTES, kind=MediaKind.IMAGE, original_filename="holiday.jpg"
        )
        stem = stored.path.stem
        assert len(stem) == 32
        assert all(character in "0123456789abcdef" for character in stem)

    def test_the_original_name_appears_nowhere_in_the_stored_path(
        self, storage: StorageService
    ) -> None:
        stored = storage.save_upload(
            JPEG_BYTES, kind=MediaKind.IMAGE, original_filename="holiday.jpg"
        )
        assert "holiday" not in str(stored.path)
        assert "holiday" not in stored.relative_path

    @pytest.mark.parametrize(
        "hostile",
        [
            "../../backend/main.py",
            "..\\..\\windows\\system32\\evil.jpg",
            "/etc/passwd",
            "CON",
            "LPT1",
            "a" * 400 + ".jpg",
            "name\x00.jpg",
            "%2e%2e%2fescape.jpg",
        ],
    )
    def test_a_hostile_filename_cannot_influence_the_stored_path(
        self, storage: StorageService, settings: Settings, hostile: str
    ) -> None:
        """The decisive property: the name is not sanitised, it is *dropped*."""
        stored = storage.save_upload(JPEG_BYTES, kind=MediaKind.IMAGE, original_filename=hostile)
        assert stored.path.parent == settings.upload_dir
        assert stored.path.is_file()
        assert settings.storage_root.resolve() in stored.path.resolve().parents

    def test_two_uploads_of_identical_bytes_do_not_collide(self, storage: StorageService) -> None:
        """A name that merely collides would destroy another user's file."""
        first = storage.save_upload(JPEG_BYTES, kind=MediaKind.IMAGE)
        second = storage.save_upload(JPEG_BYTES, kind=MediaKind.IMAGE)
        assert first.path != second.path
        assert first.path.is_file()
        assert second.path.is_file()

    @pytest.mark.parametrize(
        ("data", "suffix"),
        [
            (JPEG_BYTES, ".jpg"),
            (PNG_BYTES, ".png"),
            (WEBP_BYTES, ".webp"),
            (BMP_BYTES, ".bmp"),
        ],
    )
    def test_the_extension_comes_from_the_detected_type(
        self, storage: StorageService, data: bytes, suffix: str
    ) -> None:
        """Not from the upload -- a PNG sent as ``x.jpg`` is stored as ``.png``."""
        stored = storage.save_upload(data, kind=MediaKind.IMAGE, original_filename="misleading.jpg")
        assert stored.path.suffix == suffix


class TestStoredFileMetadata:
    """What ``save_upload`` reports back about the file it wrote."""

    def test_records_the_detected_type_and_the_real_size(self, storage: StorageService) -> None:
        stored = storage.save_upload(JPEG_BYTES, kind=MediaKind.IMAGE)
        assert stored.media_type == "image/jpeg"
        assert stored.size_bytes == len(JPEG_BYTES)
        assert stored.path.read_bytes() == JPEG_BYTES

    def test_the_relative_path_uses_posix_separators(self, storage: StorageService) -> None:
        """A Windows backslash in the database would break the URL after a move"""
        stored = storage.save_upload(JPEG_BYTES, kind=MediaKind.IMAGE)
        assert "\\" not in stored.relative_path
        assert stored.relative_path.startswith("uploads/")

    def test_the_url_is_the_prefix_plus_the_relative_path(self, storage: StorageService) -> None:
        stored = storage.save_upload(JPEG_BYTES, kind=MediaKind.IMAGE)
        assert stored.url == f"{FILES_URL_PREFIX}/{stored.relative_path}"
        assert stored.url.startswith("/files/uploads/")

    def test_the_absolute_path_is_not_published(
        self, storage: StorageService, settings: Settings
    ) -> None:
        stored = storage.save_upload(JPEG_BYTES, kind=MediaKind.IMAGE)
        assert str(settings.storage_root) not in stored.url


class TestPathTraversalOnRead:
    """``get_path`` is one HTTP parameter away from being an attack target."""

    def test_resolves_a_legitimate_relative_path(
        self, storage: StorageService, settings: Settings
    ) -> None:
        stored = storage.save_upload(JPEG_BYTES, kind=MediaKind.IMAGE)
        assert storage.get_path(stored.relative_path) == stored.path.resolve()

    @pytest.mark.parametrize(
        "hostile",
        [
            "../../../etc/passwd",
            "uploads/../../../etc/passwd",
            "..",
            "../secret.txt",
            "uploads/../../outside.txt",
            "./../../escape.bin",
        ],
    )
    def test_rejects_a_path_escaping_the_storage_root(
        self, storage: StorageService, hostile: str
    ) -> None:
        with pytest.raises(ValidationError, match="traversal"):
            storage.get_path(hostile)

    def test_containment_is_checked_after_resolution_not_before(
        self, storage: StorageService
    ) -> None:
        """``uploads/../../etc/passwd`` looks contained until ``..`` collapses."""
        candidate = "uploads/../../etc/passwd"
        assert candidate.startswith("uploads/")
        with pytest.raises(ValidationError):
            storage.get_path(candidate)

    def test_a_path_inside_a_sibling_category_is_allowed(
        self, storage: StorageService, settings: Settings
    ) -> None:
        """Containment, not a category allow-list, is what is enforced."""
        resolved = storage.get_path("plates/anything.jpg")
        assert settings.storage_root.resolve() in resolved.parents


class TestPlateCropStorage:
    """Crops are named after the job that produced them."""

    @staticmethod
    def _crop() -> np.ndarray:
        """A small non-uniform BGR image that JPEG can encode."""
        image = np.zeros((32, 96, 3), dtype=np.uint8)
        image[:, ::2] = 255
        return image

    def test_stores_a_crop_under_the_plates_directory(
        self, storage: StorageService, settings: Settings
    ) -> None:
        stored = storage.save_plate_crop(self._crop(), job_id="job-1", index=0)
        assert stored.path.parent == settings.plate_dir
        assert stored.path.is_file()
        assert stored.media_type == "image/jpeg"

    def test_the_name_carries_the_job_and_the_plate_index(self, storage: StorageService) -> None:
        """So the crops of one upload sort together on disk."""
        stored = storage.save_plate_crop(self._crop(), job_id="job-1", index=2)
        assert stored.path.name == "job-1-plate-2.jpg"

    def test_several_plates_of_one_job_get_distinct_names(self, storage: StorageService) -> None:
        first = storage.save_plate_crop(self._crop(), job_id="job-1", index=0)
        second = storage.save_plate_crop(self._crop(), job_id="job-1", index=1)
        assert first.path != second.path

    def test_the_stored_crop_is_a_readable_jpeg(self, storage: StorageService) -> None:
        stored = storage.save_plate_crop(self._crop(), job_id="job-1", index=0)
        assert detect_media_type(stored.path.read_bytes()) == "image/jpeg"

    def test_refuses_an_empty_crop(self, storage: StorageService) -> None:
        empty = np.zeros((0, 0, 3), dtype=np.uint8)
        with pytest.raises(ValidationError):
            storage.save_plate_crop(empty, job_id="job-1", index=0)

    def test_stores_an_output_image(self, storage: StorageService, settings: Settings) -> None:
        stored = storage.save_output_image(self._crop(), job_id="job-1")
        assert stored.path.parent == settings.output_dir
        assert stored.path.name == "job-1-result.jpg"

    def test_refuses_an_empty_output_image(self, storage: StorageService) -> None:
        with pytest.raises(ValidationError):
            storage.save_output_image(np.zeros((0, 0, 3), dtype=np.uint8), job_id="job-1")


class TestDeletion:
    """Deleting must be idempotent from the caller's point of view."""

    def test_deletes_an_existing_file(self, storage: StorageService) -> None:
        stored = storage.save_upload(JPEG_BYTES, kind=MediaKind.IMAGE)
        assert storage.delete_file(stored.relative_path) is True
        assert not stored.path.exists()

    def test_a_missing_file_reports_false_rather_than_raising(
        self, storage: StorageService
    ) -> None:
        """Raising would leave a history row that can never be deleted."""
        assert storage.delete_file("uploads/never-existed.jpg") is False

    def test_deleting_twice_is_not_an_error(self, storage: StorageService) -> None:
        stored = storage.save_upload(JPEG_BYTES, kind=MediaKind.IMAGE)
        assert storage.delete_file(stored.relative_path) is True
        assert storage.delete_file(stored.relative_path) is False

    @pytest.mark.parametrize("value", [None, ""])
    def test_an_absent_path_is_a_no_op(self, storage: StorageService, value: str | None) -> None:
        assert storage.delete_file(value) is False

    def test_a_traversing_delete_is_refused(self, storage: StorageService) -> None:
        with pytest.raises(ValidationError):
            storage.delete_file("../../../etc/passwd")


class TestUrlConversion:
    """Turning a stored path into something safe to publish."""

    def test_builds_a_url_under_the_files_prefix(self, storage: StorageService) -> None:
        assert storage.to_url("plates/x.jpg") == "/files/plates/x.jpg"

    @pytest.mark.parametrize("value", [None, ""])
    def test_no_file_yields_none_not_an_empty_url(
        self, storage: StorageService, value: str | None
    ) -> None:
        """Keeps "no image" distinguishable from "an image at the empty URL"."""
        assert storage.to_url(value) is None


class TestStorageCategories:
    """The sub-directory names double as URL segments."""

    def test_the_three_categories_are_declared(self) -> None:
        assert {category.value for category in StorageCategory} == {
            "uploads",
            "plates",
            "outputs",
        }

    def test_a_stored_file_url_starts_with_its_category(self) -> None:
        stored = StoredFile(
            path=Path("/tmp/x/plates/a.jpg"),
            relative_path="plates/a.jpg",
            media_type="image/jpeg",
            size_bytes=10,
        )
        assert stored.url == "/files/plates/a.jpg"
