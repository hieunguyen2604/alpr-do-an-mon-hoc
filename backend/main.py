"""FastAPI application factory: start-up, middleware, error handling, and routing.

Configures logging, storage folders, database schema, and AI pipeline (NFR-S4).
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend import __version__
from backend.api.routes import (
    detection as detection_routes,
)
from backend.api.routes import (
    health as health_routes,
)
from backend.api.routes import (
    history as history_routes,
)
from backend.api.routes import (
    statistics as statistics_routes,
)
from backend.core.config import Settings, get_settings
from backend.core.exceptions import (
    APIError,
    NotFoundError,
    ProcessingError,
)
from backend.core.exceptions import (
    ValidationError as APIValidationError,
)
from backend.core.logging import (
    get_logger,
    new_request_id,
    request_context,
    safe_extra,
    setup_logging,
)
from backend.models.database import engine, init_database
from backend.services.detection_service import (
    DetectionService,
    PlatePipeline,
    StubPipeline,
    UnavailablePipeline,
)
from backend.services.storage_service import FILES_URL_PREFIX, StorageService

__all__ = ["app", "build_pipeline", "create_app", "lifespan"]

logger = get_logger(__name__)

_REQUEST_ID_HEADER = "X-Request-ID"
_PROCESS_TIME_HEADER = "X-Process-Time"

_API_DESCRIPTION = """
REST API for the Vietnamese Automatic License Plate Recognition system.
Provides plate detection, character recognition, and history management.
"""

_TAGS_METADATA = [
    {
        "name": "Health",
        "description": "Service readiness. Reports whether the database and the model are usable.",
    },
    {
        "name": "Detection",
        "description": "Recognition over images, videos and webcam frames; job progress polling.",
    },
    {
        "name": "History",
        "description": "Browse, search, filter, export and delete stored detection records.",
    },
    {
        "name": "Statistics",
        "description": "Aggregate figures for the dashboard.",
    },
]


def build_pipeline(settings: Settings) -> PlatePipeline:
    """Construct the recognition pipeline for this process (NFR-M5)."""
    if settings.use_stub:
        logger.warning(
            "ALPR_USE_STUB is set: installing the fabricating placeholder pipeline.",
            extra={"engine": "stub"},
        )
        return StubPipeline()

    if not settings.model_path.exists():
        reason = f"detector weights not found at {settings.model_path}"
        logger.warning(
            "detector weights not found; starting with recognition disabled",
            extra={"model_path": str(settings.model_path)},
        )
        return UnavailablePipeline(reason)

    try:
        from ai.inference.config import InferenceConfig  # noqa: PLC0415
        from ai.inference.detector import YoloPlateDetector  # noqa: PLC0415
        from ai.inference.normalizer import VietnamesePlateNormalizer  # noqa: PLC0415
        from ai.inference.pipeline import ALPRPipeline  # noqa: PLC0415
        from ai.inference.recognizer import PaddleOcrRecognizer  # noqa: PLC0415

        config = InferenceConfig(
            model_path=settings.model_path,
            device=settings.device,
            conf_threshold=settings.conf_threshold,
            iou_threshold=settings.iou_threshold,
            imgsz=settings.imgsz,
            ocr_rec_model_dir=settings.ocr_rec_model_dir,
        )

        pipeline: PlatePipeline = ALPRPipeline(
            detector=YoloPlateDetector(config),
            recognizer=PaddleOcrRecognizer(config),
            normalizer=VietnamesePlateNormalizer(),
            config=config,
        )
    except Exception as error:  # noqa: BLE001
        logger.exception(
            "recognition pipeline could not be constructed; starting in degraded mode",
            extra={
                "error_type": type(error).__name__,
                "model_path": str(settings.model_path),
            },
        )
        return UnavailablePipeline(f"{type(error).__name__}: {error}")

    logger.info(
        "recognition pipeline loaded",
        extra={
            "engine": pipeline.name,
            "device": settings.device,
            "model_path": str(settings.model_path),
        },
    )
    return pipeline


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Prepare process resources on startup and clean up on shutdown."""
    settings = get_settings()
    setup_logging(settings.log_level)

    app.state.started_at = time.monotonic()
    logger.info(
        "starting up",
        extra={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "debug": settings.debug,
            "device": settings.device,
        },
    )

    settings.ensure_directories()

    import os
    try:
        import cv2
        cv2.setUseOptimized(True)
        cv2.setNumThreads(min(8, os.cpu_count() or 4))
    except Exception:
        pass
    try:
        import torch
        torch.set_num_threads(min(8, os.cpu_count() or 4))
        torch.set_num_interop_threads(min(4, os.cpu_count() or 2))
    except Exception:
        pass

    try:
        init_database()
    except Exception as error:  # noqa: BLE001
        logger.exception(
            "database initialisation failed; the service will report degraded",
            extra={"error_type": type(error).__name__},
        )

    try:
        app.state.pipeline = build_pipeline(settings)
    except Exception as error:  # noqa: BLE001
        logger.exception(
            "pipeline construction failed; recognition will be disabled",
            extra={"error_type": type(error).__name__},
        )
        app.state.pipeline = UnavailablePipeline(f"{type(error).__name__}: {error}")

    try:
        DetectionService(
            pipeline=app.state.pipeline,
            storage=StorageService(settings),
            settings=settings,
        ).warmup()
    except Exception as error:  # noqa: BLE001
        logger.warning(
            "pipeline warm-up failed; the first request will be slower",
            extra={"error_type": type(error).__name__, "reason": str(error)},
        )

    logger.info(
        "startup complete",
        extra={
            "engine": getattr(app.state.pipeline, "name", "unknown"),
            "model_ready": getattr(app.state.pipeline, "is_ready", False),
            "cors_origins": settings.cors_origins,
        },
    )

    yield

    logger.info("shutting down")
    engine.dispose()


def _request_id_of(request: Request) -> str:
    """Return the request identifier assigned by middleware."""
    return getattr(request.state, "request_id", "-")


def _error_response(error: APIError, request: Request) -> JSONResponse:
    """Render a structured JSON error response."""
    request_id = _request_id_of(request)
    return JSONResponse(
        status_code=error.status_code,
        content=error.to_response_dict(request_id),
        headers={_REQUEST_ID_HEADER: request_id},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register application exception handlers."""

    @app.exception_handler(APIError)
    async def handle_api_error(request: Request, exc: APIError) -> JSONResponse:
        fields = exc.log_fields()
        fields["path"] = request.url.path
        if exc.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            logger.error(exc.internal_detail, extra=safe_extra(fields), exc_info=exc)
        else:
            logger.warning(exc.internal_detail, extra=safe_extra(fields))
        return _error_response(exc, request)

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        error = APIValidationError(
            f"Request validation failed: {exc.errors()}",
            context={"path": request.url.path},
        )
        fields = error.log_fields()
        fields["status_code"] = status.HTTP_422_UNPROCESSABLE_ENTITY
        logger.warning(error.internal_detail, extra=safe_extra(fields))
        request_id = _request_id_of(request)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error.to_response_dict(request_id),
            headers={_REQUEST_ID_HEADER: request_id},
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            error: APIError = NotFoundError(f"No route matches {request.method} {request.url.path}")
        else:
            error = APIError(
                f"HTTP {exc.status_code} for {request.method} {request.url.path}: {exc.detail}",
                user_message="Yêu cầu không hợp lệ hoặc không được hỗ trợ.",
            )
            error.status_code = exc.status_code
            error.error_code = f"HTTP_{exc.status_code}"
        logger.warning(error.internal_detail, extra=safe_extra(error.log_fields()))
        return _error_response(error, request)

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        error = ProcessingError(
            f"Unhandled {type(exc).__name__}: {exc}",
            context={"path": request.url.path, "method": request.method},
        )
        logger.error(error.internal_detail, extra=safe_extra(error.log_fields()), exc_info=exc)
        return _error_response(error, request)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure the FastAPI application instance."""
    config = settings or get_settings()
    setup_logging(config.log_level)

    app = FastAPI(
        title=config.app_name,
        version=config.app_version or __version__,
        description=_API_DESCRIPTION,
        openapi_tags=_TAGS_METADATA,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        swagger_ui_parameters={"defaultModelsExpandDepth": 1, "displayRequestDuration": True},
    )

    @app.middleware("http")
    async def request_context_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[object]],
    ) -> object:
        incoming = request.headers.get(_REQUEST_ID_HEADER)
        with request_context(incoming or new_request_id()) as request_id:
            request.state.request_id = request_id
            started = time.perf_counter()
            response = await call_next(request)
            elapsed = time.perf_counter() - started

            response.headers[_REQUEST_ID_HEADER] = request_id  # type: ignore[attr-defined]
            response.headers[_PROCESS_TIME_HEADER] = f"{elapsed:.4f}"  # type: ignore[attr-defined]

            logger.info(
                "request handled",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": getattr(response, "status_code", 0),
                    "duration_seconds": round(elapsed, 4),
                },
            )
            return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=[_REQUEST_ID_HEADER, _PROCESS_TIME_HEADER],
    )

    register_exception_handlers(app)

    app.include_router(health_routes.router)
    app.include_router(detection_routes.router, prefix=config.api_prefix)
    app.include_router(history_routes.router, prefix=config.api_prefix)
    app.include_router(statistics_routes.router, prefix=config.api_prefix)

    config.ensure_directories()
    app.mount(
        FILES_URL_PREFIX,
        StaticFiles(directory=config.storage_root),
        name="files",
    )

    return app


app = create_app()
