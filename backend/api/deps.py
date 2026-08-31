"""Shared FastAPI dependencies and dependency injection aliases (NFR-M1, NFR-M5)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from backend.core.config import Settings, get_settings
from backend.core.exceptions import ProcessingError
from backend.models.database import get_db
from backend.services.detection_service import DetectionService, PlatePipeline
from backend.services.history_service import HistoryService
from backend.services.statistics_service import StatisticsService
from backend.services.storage_service import StorageService

__all__ = [
    "get_settings_dependency",
    "get_db_session",
    "get_pipeline",
    "get_storage_service",
    "get_detection_service",
    "get_history_service",
    "get_statistics_service",
    "SettingsDep",
    "DbSession",
    "PipelineDep",
    "StorageDep",
    "DetectionDep",
    "HistoryDep",
    "StatisticsDep",
]


def get_settings_dependency() -> Settings:
    """Return the process-wide settings.

    A thin wrapper around :func:`~backend.core.config.get_settings` rather than
    the function itself, so that a test overriding configuration does not have
    to override the cached accessor that half the application calls directly.

    Returns:
        The shared settings instance.
    """
    return get_settings()


def get_db_session() -> Iterator[Session]:
    """Yield a database session scoped to one request.

    Delegates to :func:`~backend.models.database.get_db`, which is a plain
    generator with no FastAPI import -- keeping the persistence layer usable
    from Alembic and from scripts. This wrapper exists purely to give the API
    layer its own overridable dependency name.

    Yields:
        A session that is closed when the request finishes, however it finishes.
    """
    yield from get_db()


def get_pipeline(request: Request) -> PlatePipeline:
    """Return the recognition pipeline created at start-up.

    Read from ``app.state`` rather than constructed here: loading model weights
    takes seconds and hundreds of megabytes, so doing it per request would make
    every upload pay a cost that belongs to the process.

    Args:
        request: The active request, used only to reach the application state.

    Returns:
        The single pipeline instance for this process.

    Raises:
        ProcessingError: If no pipeline was installed -- meaning the lifespan
            handler did not run. Better to fail the request with a clean 500
            than to build a second pipeline behind the operator's back and
            answer with results from an engine nobody configured.
    """
    pipeline: PlatePipeline | None = getattr(request.app.state, "pipeline", None)
    if pipeline is None:
        raise ProcessingError(
            "No pipeline is installed on app.state; the lifespan handler did not run",
        )
    return pipeline


def get_storage_service(
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> StorageService:
    """Build the storage service for this request.

    Args:
        settings: Supplies the storage directories and upload limits.

    Returns:
        A storage service bound to the configured directories.
    """
    return StorageService(settings)


def get_detection_service(
    pipeline: Annotated[PlatePipeline, Depends(get_pipeline)],
    storage: Annotated[StorageService, Depends(get_storage_service)],
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> DetectionService:
    """Build the detection service for this request.

    The composition root for NFR-M5: this is the only place in the request path
    where a pipeline is handed to something that uses it, and it receives one
    rather than choosing one.

    Args:
        pipeline: The recognition pipeline created at start-up.
        storage: Handles the files the detection reads and writes.
        settings: Supplies the video frame stride and upload limits.

    Returns:
        A detection service wired to this request's collaborators.
    """
    return DetectionService(pipeline=pipeline, storage=storage, settings=settings)


def get_history_service(
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> HistoryService:
    """Build the history service for this request.

    Args:
        storage: Used to build public URLs and to remove deleted files.

    Returns:
        A history service.
    """
    return HistoryService(storage)


def get_statistics_service() -> StatisticsService:
    """Build the statistics service for this request.

    Returns:
        A statistics service. It holds no state and needs no collaborators --
        every figure it reports comes from the session passed to its methods.
    """
    return StatisticsService()


SettingsDep = Annotated[Settings, Depends(get_settings_dependency)]
"""The process-wide configuration."""

DbSession = Annotated[Session, Depends(get_db_session)]
"""A database session scoped to the current request."""

PipelineDep = Annotated[PlatePipeline, Depends(get_pipeline)]
"""The recognition pipeline installed at start-up."""

StorageDep = Annotated[StorageService, Depends(get_storage_service)]
"""File storage, reading and writing under the configured storage root."""

DetectionDep = Annotated[DetectionService, Depends(get_detection_service)]
"""Detection orchestration: pipeline plus storage plus persistence."""

HistoryDep = Annotated[HistoryService, Depends(get_history_service)]
"""Access to stored detection records."""

StatisticsDep = Annotated[StatisticsService, Depends(get_statistics_service)]
"""Dashboard aggregate figures."""
