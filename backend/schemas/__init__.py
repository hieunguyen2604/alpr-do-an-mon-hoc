"""Pydantic v2 schemas defining the API's request and response contract.

These are the types FastAPI validates against and the ones Swagger documents.
They are kept separate from the SQLAlchemy models in :mod:`backend.models` so
that the storage schema and the public contract can evolve independently -- and
so that a column added for an internal purpose is not published by default.

Re-exported here so callers can write ``from backend.schemas import
HistoryListResponse`` without knowing which module it lives in.
"""

from __future__ import annotations

from backend.schemas.detection import (
    BoundingBoxSchema,
    DailyCountSchema,
    DetectionHistoryResponse,
    DetectionJobResponse,
    DetectionResponse,
    DetectionResultSchema,
    ErrorResponse,
    HealthResponse,
    HistoryListResponse,
    InputTypeCountSchema,
    StatisticsResponse,
)

__all__ = [
    "BoundingBoxSchema",
    "DetectionResultSchema",
    "DetectionResponse",
    "DetectionHistoryResponse",
    "DetectionJobResponse",
    "HistoryListResponse",
    "InputTypeCountSchema",
    "DailyCountSchema",
    "StatisticsResponse",
    "HealthResponse",
    "ErrorResponse",
]
