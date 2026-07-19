"""Business logic: everything the API does, minus the HTTP.

This layer is where a request stops being a request and becomes work. It
orchestrates the pipeline, the filesystem and the database; the routers above
it only translate HTTP, and the layers below it know nothing about either.

============================================== =============================
Service                                        Responsibility
============================================== =============================
:class:`~backend.services.storage_service.StorageService`      Safe file writes, reads and deletes
:class:`~backend.services.detection_service.DetectionService`  Runs the pipeline and records results
:class:`~backend.services.history_service.HistoryService`      Queries, exports and deletes records
:class:`~backend.services.statistics_service.StatisticsService` Dashboard aggregates
============================================== =============================

Two rules hold throughout this package, and both are what let the same code be
driven from a test, a script or a router:

**No FastAPI.** Nothing here imports the web framework. Services receive a
:class:`~sqlalchemy.orm.Session` and plain arguments, and raise
:class:`~backend.core.exceptions.APIError` subclasses that the router layer
turns into responses. A service can therefore be called from a background task
or a benchmark with no HTTP involved.

**No construction of collaborators.** Every dependency arrives through
``__init__``. In particular :class:`~backend.services.detection_service.DetectionService`
never builds a pipeline -- that is the whole of NFR-M5, and it is why the API
runs today against
:class:`~backend.services.detection_service.StubPipeline` and will run against
the trained model after a one-line change in ``backend.main``.
"""

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
