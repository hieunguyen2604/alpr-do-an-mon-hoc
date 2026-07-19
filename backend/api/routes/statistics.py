"""The dashboard statistics endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, status

from backend.api.deps import DbSession, StatisticsDep
from backend.api.routes import ERROR_400, ERROR_500, errors
from backend.schemas.detection import StatisticsResponse
from backend.services.statistics_service import DEFAULT_TREND_DAYS, MAX_TREND_DAYS

__all__ = ["router"]

router = APIRouter(tags=["Statistics"])


@router.get(
    "/statistics",
    response_model=StatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get aggregate statistics for the dashboard",
    description=(
        "Returns every figure the dashboard displays, in one call.\n\n"
        "**Two families of counter, which must not be mixed up.** `*_jobs` "
        "counts uploads and capture sessions — how much the system was used. "
        "`*_detections` counts license plates — how much was recognized. An "
        "image containing three plates is **one** job and **three** "
        "detections.\n\n"
        "A tile labelled 'images processed' must therefore read `total_jobs`. "
        "Filling it from `total_detections` inflates the figure by the average "
        "number of plates per image, and the result is plausible enough to "
        "survive review.\n\n"
        "`valid_format_count`, `invalid_format_count` and `unreadable_count` "
        "are mutually exclusive and sum to `total_detections`: text read and "
        "matching a Vietnamese pattern, text read but matching none, and no "
        "text read at all.\n\n"
        "Averages are `null` rather than `0` when there is nothing to average — "
        "an average confidence of zero would read as 'the model is certain of "
        "nothing', which is a different statement from 'no data yet'."
    ),
    responses={
        200: {
            "description": "The aggregate figures.",
            "content": {
                "application/json": {
                    "example": {
                        "total_jobs": 412,
                        "total_detections": 689,
                        "unique_plates": 574,
                        "valid_format_count": 601,
                        "invalid_format_count": 52,
                        "unreadable_count": 36,
                        "average_confidence": 0.912,
                        "average_ocr_confidence": 0.864,
                        "average_processing_time": 0.437,
                        "jobs_today": 12,
                        "detections_today": 19,
                        "by_input_type": [
                            {
                                "input_type": "image",
                                "job_count": 318,
                                "detection_count": 502,
                            },
                            {
                                "input_type": "video",
                                "job_count": 47,
                                "detection_count": 143,
                            },
                            {
                                "input_type": "webcam",
                                "job_count": 47,
                                "detection_count": 44,
                            },
                        ],
                        "daily_counts": [
                            {
                                "date": "2026-07-18",
                                "job_count": 23,
                                "detection_count": 41,
                            },
                            {
                                "date": "2026-07-19",
                                "job_count": 12,
                                "detection_count": 19,
                            },
                        ],
                    }
                }
            },
        },
        **errors(ERROR_400, ERROR_500),
    },
)
def get_statistics(
    db: DbSession,
    statistics: StatisticsDep,
    days: Annotated[
        int,
        Query(
            ge=1,
            le=MAX_TREND_DAYS,
            description=(
                "Length of the daily trend window, ending today (UTC). Days "
                "with no activity are returned with zero counts rather than "
                "omitted, so a chart drawn from the series does not silently "
                "close the gaps."
            ),
            examples=[7],
        ),
    ] = DEFAULT_TREND_DAYS,
) -> StatisticsResponse:
    """Return the dashboard's aggregate figures.

    Args:
        db: Session for this request.
        statistics: The statistics service.
        days: Length of the daily trend window.

    Returns:
        Every figure the dashboard needs.

    Raises:
        ValidationError: If ``days`` is out of range.
    """
    return statistics.get_statistics(db, days=days)
