"""Business logic layer: orchestrates pipeline, storage and persistence (NFR-M5)."""

from __future__ import annotations

from backend.services.detection_service import (
    DetectionService,
    PlatePipeline,
    StubPipeline,
    to_job_response,
)
from backend.services.history_service import (
    HistoryFilter,
    HistoryService,
    SortField,
    SortOrder,
)
from backend.services.statistics_service import StatisticsService
from backend.services.storage_service import (
    FILES_URL_PREFIX,
    MediaKind,
    StorageCategory,
    StorageService,
    StoredFile,
    detect_media_type,
)

__all__ = [
    # Storage
    "StorageService",
    "StoredFile",
    "MediaKind",
    "StorageCategory",
    "FILES_URL_PREFIX",
    "detect_media_type",
    # Detection
    "DetectionService",
    "PlatePipeline",
    "StubPipeline",
    "to_job_response",
    # History
    "HistoryService",
    "HistoryFilter",
    "SortField",
    "SortOrder",
    # Statistics
    "StatisticsService",
]
