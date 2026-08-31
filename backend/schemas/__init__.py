"""Pydantic v2 schemas defining the API's request/response contract."""

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
