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
    """Return the process-wide settings."""
    return get_settings()


def get_db_session() -> Iterator[Session]:
    """Yield a database session scoped to one request."""
    yield from get_db()


def get_pipeline(request: Request) -> PlatePipeline:
    """Return the recognition pipeline created at start-up."""
    pipeline: PlatePipeline | None = getattr(request.app.state, "pipeline", None)
    if pipeline is None:
        raise ProcessingError(
            "No pipeline is installed on app.state; the lifespan handler did not run",
        )
    return pipeline


def get_storage_service(
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> StorageService:
    """Build the storage service for this request."""
    return StorageService(settings)


def get_detection_service(
    pipeline: Annotated[PlatePipeline, Depends(get_pipeline)],
    storage: Annotated[StorageService, Depends(get_storage_service)],
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> DetectionService:
    """Build the detection service for this request."""
    return DetectionService(pipeline=pipeline, storage=storage, settings=settings)


def get_history_service(
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> HistoryService:
    """Build the history service for this request."""
    return HistoryService(storage)


def get_statistics_service() -> StatisticsService:
    """Build the statistics service for this request."""
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
