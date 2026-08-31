"""Service readiness endpoint reporting database connection and AI model state."""

from __future__ import annotations

import time

from fastapi import APIRouter, Request, status
from sqlalchemy import text

from backend.api.deps import DbSession, PipelineDep, SettingsDep
from backend.core.logging import get_logger
from backend.models.detection import utcnow
from backend.schemas.detection import HealthResponse

__all__ = ["router"]

logger = get_logger(__name__)

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Check service readiness",
    description="Reports service readiness including database and AI model availability.",
    responses={
        200: {
            "description": "The service answered. Read `status` for its state.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "app_name": "Vietnamese ALPR API",
                        "version": "0.1.0",
                        "database_connected": True,
                        "model_loaded": True,
                        "uptime_seconds": 1287.4,
                        "timestamp": "2026-07-19T09:31:22.145Z",
                    }
                }
            },
        }
    },
)
def health(
    request: Request,
    db: DbSession,
    settings: SettingsDep,
    pipeline: PipelineDep,
) -> HealthResponse:
    """Report the service's readiness.

    Args:
        request: Used to read the start time recorded by the lifespan handler.
        db: Session used for a trivial round trip that proves the database is
            reachable.
        settings: Supplies the reported service name and version.
        pipeline: The installed recognition pipeline, asked whether it is ready.

    Returns:
        The health response. Never raises: a health check that fails with a 500
        tells a monitor that the check is broken, not that the service is.
    """
    database_connected = _probe_database(db)
    model_loaded = _probe_pipeline(pipeline)

    started_at: float = getattr(request.app.state, "started_at", time.monotonic())
    uptime = max(0.0, time.monotonic() - started_at)

    return HealthResponse(
        status="ok" if database_connected and model_loaded else "degraded",
        app_name=settings.app_name,
        version=settings.app_version,
        database_connected=database_connected,
        model_loaded=model_loaded,
        uptime_seconds=uptime,
        timestamp=utcnow(),
    )


def _probe_database(db: DbSession) -> bool:
    """Check that the database answers a query.

    ``SELECT 1`` rather than an inspection of the connection object: a pooled
    connection can look alive while the file behind it has been removed or the
    disk has gone read-only. Only a round trip proves anything.

    Args:
        db: The session to probe.

    Returns:
        ``True`` if the query succeeded.
    """
    try:
        db.execute(text("SELECT 1"))
    except Exception as error:  # noqa: BLE001 -- the health check reports, never raises
        logger.warning(
            "health check: database unreachable",
            extra={"reason": str(error), "error_type": type(error).__name__},
        )
        return False
    return True


def _probe_pipeline(pipeline: PipelineDep) -> bool:
    """Check whether the recognition pipeline can produce genuine results.

    Args:
        pipeline: The installed pipeline.

    Returns:
        ``True`` when the pipeline reports itself ready. A pipeline that raises
        while being asked is treated as not ready, which is the safe reading.
    """
    try:
        return bool(pipeline.is_ready)
    except Exception as error:  # noqa: BLE001
        logger.warning(
            "health check: pipeline could not report readiness",
            extra={"reason": str(error), "error_type": type(error).__name__},
        )
        return False
