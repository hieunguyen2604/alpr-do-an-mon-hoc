"""Shared fixtures for the API integration tests."""

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
    """A pipeline whose output the test decides."""

    def __init__(self) -> None:
        """Start with a single readable plate."""
        self.plates: list[tuple[str | None, str | None, float, float | None, bool]] = [
            ("51F-12345", "51FI2345", 0.94, 0.87, True)
        ]
        self.calls = 0
        self.raises: Exception | None = None
        #: What the last call asked for, so a test can assert the flag reached
        #: the pipeline rather than being swallowed by the route or service.
        self.last_read_text: bool = True

    @property
    def name(self) -> str:
        """Return the engine identifier."""
        return "fake"

    @property
    def is_ready(self) -> bool:
        """Return ``True``; the fake is always able to answer."""
        return True

    def process(self, image: np.ndarray, *, read_text: bool = True) -> PipelineResult:
        """Return the configured plates, positioned inside the given image."""
        self.calls += 1
        self.last_read_text = read_text
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
                if text is not None and read_text
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
    """Encode a small but genuinely decodable JPEG."""
    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[:, ::4] = 200
    image[::4, :] = 120
    success, buffer = cv2.imencode(".jpg", image)
    assert success, "failed to encode the test JPEG"
    return bytes(buffer.tobytes())


def encode_png(width: int = 64, height: int = 48) -> bytes:
    """Encode a small decodable PNG."""
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
    """Configuration pointing at a throwaway database and storage root."""
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
    """A session factory bound to the throwaway database, schema created."""
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
    """A session the *test* uses to inspect and seed the database directly."""
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
    """The real application, wired to the throwaway database and the fake."""
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
    """An HTTP client against the configured application."""
    return TestClient(app)
