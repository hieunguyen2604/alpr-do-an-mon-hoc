"""Shared fixtures for the API integration tests.

These tests drive the real application through ``TestClient``: real routers,
real middleware, real exception handlers, real services, real SQL. Three things
are replaced, and only three:

* **the database** -- a throwaway SQLite file per test, so nothing touches the
  developer's ``data/alpr.db``;
* **the storage root** -- a temporary directory, so uploads are cleaned up;
* **the pipeline** -- a fake, so the suite runs in seconds and needs no model
  weights. This is the payoff of the dependency injection the service layer was
  built around: the substitution is a one-line dependency override rather than
  a monkey-patch.

Why the lifespan is not run
--------------------------
``TestClient`` executes the lifespan handler only when used as a context
manager. It is deliberately not used that way here: the handler builds the real
pipeline, initialises the process-wide database and loads model weights, all of
which the overrides below replace anyway. Everything the request path reads from
``app.state`` is set explicitly instead.

Why ``SessionLocal`` is monkey-patched as well as overridden
-----------------------------------------------------------
Two code paths deliberately open a session of their own rather than accept the
request's: the CSV export (whose generator outlives the request that returned
it) and the background video worker. Both import the module-level
``SessionLocal`` at call time, so a dependency override cannot reach them --
they have to be redirected at the module.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from ai.inference.types import (
    BoundingBox,
    DetectionResult,
    PipelineResult,
    PlateDetection,
    PlateRecognition,
)
from backend.api.deps import (
    get_db_session,
    get_pipeline,
    get_settings_dependency,
)
from backend.core.config import Settings
from backend.main import create_app
from backend.models.detection import Base


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class FakePipeline:
    """A pipeline whose output the test decides.

    Satisfies :class:`~backend.services.detection_service.PlatePipeline`
    structurally -- it inherits from nothing, which is the point of expressing
    that contract as a ``Protocol``: the fake does not import the service layer
    and the service layer does not know the fake exists.

    Attributes:
        plates: Descriptions of the plates every ``process`` call should
            report. Each entry is ``(text, raw_text, detection_confidence,
            ocr_confidence, is_valid_format)``; ``text`` of ``None`` produces a
            detection OCR could not read.
        calls: How many times ``process`` has been invoked.
    """

    def __init__(self) -> None:
        """Start with a single readable plate."""
        self.plates: list[tuple[str | None, str | None, float, float | None, bool]] = [
            ("51F-12345", "51FI2345", 0.94, 0.87, True)
        ]
        self.calls = 0
        self.raises: Exception | None = None

    @property
    def name(self) -> str:
        """Return the engine identifier."""
        return "fake"

    @property
    def is_ready(self) -> bool:
        """Return ``True``; the fake is always able to answer."""
        return True

    def process(self, image: np.ndarray) -> PipelineResult:
        """Return the configured plates, positioned inside the given image.

        Args:
            image: The decoded source image; only its shape is used.

        Returns:
            A result carrying one entry per configured plate.

        Raises:
            Exception: Whatever ``raises`` was set to, for failure-path tests.
        """
        self.calls += 1
        if self.raises is not None:
            raise self.raises

        height, width = int(image.shape[0]), int(image.shape[1])
        results: list[DetectionResult] = []
        for index, (text, raw, confidence, ocr, valid) in enumerate(self.plates):
            bbox = BoundingBox(
                x=min(index * 20, max(0, width - 40)),
                y=min(index * 10, max(0, height - 20)),
                width=min(40, width),
                height=min(20, height),
            )
            recognition = (
                PlateRecognition(
                    text=text,
                    raw_text=raw or "",
                    confidence=ocr if ocr is not None else 0.0,
                    line_count=1,
                    is_valid_format=valid,
                )
                if text is not None
                else None
            )
            crop = image[bbox.y : bbox.y2, bbox.x : bbox.x2]
            results.append(
                DetectionResult(
                    detection=PlateDetection(bbox=bbox, confidence=confidence),
                    recognition=recognition,
                    plate_image=crop if crop.size else None,
                    processing_time=0.05,
                )
            )

        return PipelineResult(
            results=results,
            total_time=0.1 * max(1, len(results)),
            image_width=width,
            image_height=height,
        )

    def warmup(self) -> None:
        """Do nothing; there is no model to prime."""
        return None


# ---------------------------------------------------------------------------
# Sample media
# ---------------------------------------------------------------------------


def encode_jpeg(width: int = 320, height: int = 240) -> bytes:
    """Encode a small but genuinely decodable JPEG.

    A real encode rather than a handcrafted header, because the upload path
    decodes the bytes after the signature check: a file with a valid JPEG
    header but no image data is rejected further along, which would make these
    fixtures fail for the wrong reason.

    Args:
        width: Image width in pixels.
        height: Image height in pixels.

    Returns:
        The encoded JPEG bytes.
    """
    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[:, ::4] = 200
    image[::4, :] = 120
    success, buffer = cv2.imencode(".jpg", image)
    assert success, "failed to encode the test JPEG"
    return bytes(buffer.tobytes())


def encode_png(width: int = 64, height: int = 48) -> bytes:
    """Encode a small decodable PNG.

    Returns:
        The encoded PNG bytes.
    """
    image = np.full((height, width, 3), 90, dtype=np.uint8)
    success, buffer = cv2.imencode(".png", image)
    assert success, "failed to encode the test PNG"
    return bytes(buffer.tobytes())


EXE_DISGUISED_AS_JPEG = (
    b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
    b"\xb8\x00\x00\x00This program cannot be run in DOS mode." + b"\x00" * 64
)
"""A Windows PE executable. Uploaded as ``photo.jpg``, it must be refused."""

PDF_BYTES = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\n" + b"\x00" * 64
"""A PDF, for the "wrong format entirely" case."""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    """Configuration pointing at a throwaway database and storage root.

    ``max_image_size_mb`` is set to 1 so that the oversized-upload test can
    build its payload in memory instead of writing 10 MB.
    """
    root = tmp_path / "storage"
    return Settings(
        app_name="ALPR test",
        app_version="test",
        storage_root=root,
        upload_dir=root / "uploads",
        plate_dir=root / "plates",
        output_dir=root / "outputs",
        database_url=f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        max_image_size_mb=1,
        max_video_size_mb=2,
        cors_origins=["http://localhost:5173"],
        log_level="WARNING",
        frame_stride=5,
    )


@pytest.fixture()
def session_factory(settings: Settings) -> Iterator[sessionmaker[Session]]:
    """A session factory bound to the throwaway database, schema created.

    Foreign keys are switched on for every connection, exactly as the real
    engine does. Without the pragma SQLite ignores ``ON DELETE CASCADE`` and a
    test of cascading deletion would pass against a database that never
    cascades.
    """
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        future=True,
    )

    @event.listens_for(engine, "connect")
    def _pragmas(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    try:
        yield factory
    finally:
        engine.dispose()


@pytest.fixture()
def db(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """A session the *test* uses to inspect and seed the database directly.

    Separate from the sessions the application opens per request, so that an
    assertion never accidentally reads uncommitted state from the request that
    produced it.
    """
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def pipeline() -> FakePipeline:
    """The fake pipeline installed for the test."""
    return FakePipeline()


@pytest.fixture()
def app(
    settings: Settings,
    session_factory: sessionmaker[Session],
    pipeline: FakePipeline,
    monkeypatch: pytest.MonkeyPatch,
) -> FastAPI:
    """The real application, wired to the throwaway database and the fake.

    Returns:
        A fully configured application with the three dependencies overridden.
    """
    # Redirect the two paths that open their own session -- the CSV export
    # generator and the background video worker -- at the module they import
    # it from. A dependency override cannot reach either of them.
    import backend.models.database as database_module

    monkeypatch.setattr(database_module, "SessionLocal", session_factory)

    application = create_app(settings)

    def _override_db() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    application.dependency_overrides[get_db_session] = _override_db
    application.dependency_overrides[get_settings_dependency] = lambda: settings
    application.dependency_overrides[get_pipeline] = lambda: pipeline

    # Normally set by the lifespan handler, which is not run here.
    application.state.pipeline = pipeline
    application.state.started_at = 0.0

    return application


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    """An HTTP client against the configured application.

    Constructed directly rather than entered as a context manager, which is
    what keeps the lifespan handler from running -- see the module docstring.
    Entering it would initialise the *process-wide* engine and create the
    developer's real ``data/alpr.db`` as a side effect of running the tests.
    """
    return TestClient(app)
