"""FastAPI application factory: start-up, middleware, error handling, routing.

This module is the composition root. It is the one place that decides which
concrete pipeline the service runs with, which origins may call it, and what a
failure looks like from the outside. Everything below it receives its
collaborators rather than choosing them, which is why the choice can live here
in full.

Start-up order, and why it is that order
----------------------------------------
1. **Logging** -- first, so that every later line is structured JSON. Anything
   logged before this goes out through the standard library's default handler
   and is not machine-readable.
2. **Directories** -- before anything can write. A missing folder becomes a
   start-up failure instead of a failure halfway through a user's first upload,
   when part of a file has already been consumed.
3. **Database schema** -- before the first request can query it.
4. **Pipeline** -- last and slowest. Loading weights takes seconds; doing it
   here means the process is either ready or not, rather than becoming ready
   partway through serving.

Failures of the last two are logged and tolerated: the service starts, and
``/health`` reports ``degraded``. That is the more useful behaviour, because a
process that refuses to start tells an operator nothing about *why*, while one
that starts and reports which dependency is missing tells them exactly.

The three middleware, outermost first
-------------------------------------
``CORSMiddleware`` -> ``request context`` -> the application. CORS is outermost
so that a pre-flight ``OPTIONS`` is answered without allocating a request
identifier for a request that carries no work.

What a client never receives
----------------------------
No stack trace, no exception class name, no SQL, no filesystem path (NFR-S4).
Every error leaves through one of the handlers below, each of which builds the
body from :meth:`~backend.core.exceptions.APIError.to_response_dict` -- a method
that constructs its output from an explicit list of safe keys, so a field added
to an exception cannot leak by default. The technical half goes to the log under
the same ``request_id`` the client is given, which is what makes a user's bug
report resolvable without ever having shown them a traceback.
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
from backend.api.routes import detection as detection_routes
from backend.api.routes import health as health_routes
from backend.api.routes import history as history_routes
from backend.api.routes import statistics as statistics_routes
from backend.core.config import Settings, get_settings
from backend.core.exceptions import APIError, NotFoundError, ProcessingError
from backend.core.exceptions import ValidationError as APIValidationError
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

__all__ = ["app", "create_app", "build_pipeline"]

logger = get_logger(__name__)

_REQUEST_ID_HEADER = "X-Request-ID"
_PROCESS_TIME_HEADER = "X-Process-Time"

_API_DESCRIPTION = """
REST API for the Vietnamese Automatic License Plate Recognition system.

## What it does

Locates license plates in an image, a video or a webcam stream with a YOLO11
detector, reads the characters with OCR, corrects them against Vietnamese plate
patterns, and stores the result.

## Counting: jobs versus detections

One upload is one **job**. Each license plate found in it is one **detection**.
An image containing three vehicles is one job and three detections. Usage
figures count jobs; recognition figures count detections. The distinction runs
through the whole API and is the single easiest thing to get wrong.

## Two confidences, never merged

`detection_confidence` is how sure the detector was that it was looking at a
plate. `ocr_confidence` is how sure the OCR was of the characters. They are
reported separately because a low value in each means something entirely
different, and one number could not express either.

## Errors

Every failure returns the same body shape: a stable `error` code, a
user-facing `message` in Vietnamese, and the `request_id` of the request.
Branch on `error`; the message text may be reworded. Responses never contain a
stack trace or any server-side detail — that material is written to the server
log under the same `request_id`.

## Uploads

A file's type is determined from its **magic bytes**, never from its extension
or its `Content-Type` header. Uploads are stored under generated names; the
name supplied by the client is never used as a path.
"""

_TAGS_METADATA = [
    {
        "name": "Health",
        "description": "Service readiness. Reports whether the database and the model are usable.",
    },
    {
        "name": "Detection",
        "description": (
            "Run recognition over an image, a video or a webcam frame, and "
            "poll the progress of a queued job."
        ),
    },
    {
        "name": "History",
        "description": (
            "Browse, search, filter, export and delete stored detection records."
        ),
    },
    {
        "name": "Statistics",
        "description": "Aggregate figures for the dashboard.",
    },
]


# ---------------------------------------------------------------------------
# Pipeline selection
# ---------------------------------------------------------------------------


def build_pipeline(settings: Settings) -> PlatePipeline:
    """Construct the recognition pipeline for this process.

    **This function is the composition root of the recognition stack.** It is
    the only place in the backend that names a concrete detector, recogniser or
    normalizer; the service layer, the routers and the schemas receive whatever
    it returns and are indifferent to which it was (NFR-M5).

    Three outcomes, and the difference between them is deliberate
    ------------------------------------------------------------
    * **The real pipeline.** The normal case: the weights exist and the ``ai``
      package's runtime dependencies are installed. ``/health`` reports
      ``model_loaded = true``.
    * **:class:`~backend.services.detection_service.UnavailablePipeline`.** The
      weights are missing, or constructing a stage raised. The process still
      starts -- an operator learns far more from a service that answers
      "degraded" and says why than from a crash loop -- but every detection
      request fails cleanly. It never invents a plate number.
    * **:class:`~backend.services.detection_service.StubPipeline`.** Only when
      ``ALPR_USE_STUB`` is set explicitly. The stub fabricates results, which is
      useful for exercising the API without model weights and dangerous
      anywhere else, so it is never reached by accident.

    The middle case is the one that matters. Falling back to the stub on a load
    failure would mean a misconfigured deployment answering every upload with a
    convincing, entirely fictional plate -- a failure mode that looks like
    success. An explicit opt-in is what separates "I want fake data" from "my
    model did not load".

    Args:
        settings: Supplies the weights path, the inference parameters and the
            stub opt-in.

    Returns:
        The pipeline this process will serve requests with.
    """
    if settings.use_stub:
        logger.warning(
            "ALPR_USE_STUB is set: installing the fabricating placeholder pipeline. "
            "Every result this process returns is invented.",
            extra={"engine": "stub"},
        )
        return StubPipeline()

    # ``exists()`` rather than ``is_file()``: a PyTorch checkpoint and an ONNX
    # graph are single files, but an OpenVINO export is a *directory* holding
    # the ``.xml`` and ``.bin`` pair. Requiring a file made the fastest CPU
    # backend impossible to configure -- the service would start degraded and
    # only say "weights not found", which is not what has gone wrong.
    if not settings.model_path.exists():
        reason = f"detector weights not found at {settings.model_path}"
        logger.warning(
            "detector weights not found; the service will start with recognition "
            "disabled and /health will report model_loaded=false",
            extra={"model_path": str(settings.model_path)},
        )
        return UnavailablePipeline(reason)

    try:
        # Imported here, not at module level: the ``ai`` package pulls in
        # Ultralytics, Torch and PaddleOCR, and a backend-only deployment that
        # never runs recognition should not pay that import cost -- nor fail to
        # start because those wheels are absent.
        from ai.inference.config import InferenceConfig  # noqa: PLC0415
        from ai.inference.detector import YoloPlateDetector  # noqa: PLC0415
        from ai.inference.normalizer import VietnamesePlateNormalizer  # noqa: PLC0415
        from ai.inference.pipeline import ALPRPipeline  # noqa: PLC0415
        from ai.inference.recognizer import PaddleOcrRecognizer  # noqa: PLC0415

        # Built from ``settings`` rather than from ``InferenceConfig.from_env``:
        # both read the same ``ALPR_`` variables, but ``settings`` has already
        # applied the ``.env`` files and the validators, so going through it is
        # what keeps the two halves of the process agreeing on one value each.
        config = InferenceConfig(
            model_path=settings.model_path,
            device=settings.device,
            conf_threshold=settings.conf_threshold,
            iou_threshold=settings.iou_threshold,
            imgsz=settings.imgsz,
        )

        # Explicit assembly rather than ``build_default_pipeline``: swapping the
        # OCR engine is then a one-line change here, visible at the composition
        # root, instead of a change hidden inside a factory in another package.
        pipeline: PlatePipeline = ALPRPipeline(
            detector=YoloPlateDetector(config),
            recognizer=PaddleOcrRecognizer(config),
            normalizer=VietnamesePlateNormalizer(),
            config=config,
        )
    except Exception as error:  # noqa: BLE001 -- reported by /health, not fatal
        logger.exception(
            "recognition pipeline could not be constructed; the service will "
            "start with recognition disabled and /health will report "
            "model_loaded=false. NOTE: results are NOT being faked -- every "
            "detection request will return an error until this is fixed.",
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


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Prepare the process before it serves, and wind it down afterwards.

    Args:
        app: The application being started. Long-lived objects are attached to
            ``app.state``, which is where the dependencies read them from.

    Yields:
        Control to the server for the lifetime of the process.
    """
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

    try:
        init_database()
    except Exception as error:  # noqa: BLE001 -- reported by /health, not fatal
        logger.exception(
            "database initialisation failed; the service will report degraded",
            extra={"error_type": type(error).__name__},
        )

    try:
        app.state.pipeline = build_pipeline(settings)
    except Exception as error:  # noqa: BLE001
        # A pipeline that fails to construct must not take the process down: a
        # running service that answers "degraded" is diagnosable from outside,
        # a crash loop is not. It must equally not fall back to the fabricating
        # stub -- see ``build_pipeline`` for why that would be worse than the
        # failure it hides.
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
    except Exception as error:  # noqa: BLE001 -- warm-up is an optimisation
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


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def _request_id_of(request: Request) -> str:
    """Return the identifier assigned to a request.

    Args:
        request: The request being handled.

    Returns:
        The identifier stored by the middleware, or a placeholder if the
        failure happened before the middleware ran.
    """
    return getattr(request.state, "request_id", "-")


def _error_response(error: APIError, request: Request) -> JSONResponse:
    """Render an API error as a response, echoing the request identifier.

    Args:
        error: The error to report.
        request: The request that failed.

    Returns:
        A JSON response carrying only user-safe values.
    """
    request_id = _request_id_of(request)
    return JSONResponse(
        status_code=error.status_code,
        content=error.to_response_dict(request_id),
        headers={_REQUEST_ID_HEADER: request_id},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Install the handlers that turn every failure into a safe response.

    Four handlers, covering every way a request can fail. The last is the one
    that matters most: without a catch-all, an unanticipated exception is
    rendered by the server's default handler, which in a debug configuration
    includes the traceback (NFR-S4).

    Args:
        app: The application to install the handlers on.
    """

    @app.exception_handler(APIError)
    async def handle_api_error(request: Request, exc: APIError) -> JSONResponse:
        """Report a deliberate API error.

        Args:
            request: The failed request.
            exc: The raised error.

        Returns:
            The response built from the error's user-safe fields.
        """
        fields = exc.log_fields()
        fields["path"] = request.url.path
        if exc.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            # Server-side faults carry the traceback into the log, never into
            # the response.
            logger.error(exc.internal_detail, extra=safe_extra(fields), exc_info=exc)
        else:
            # Client mistakes are expected traffic; a traceback per bad request
            # would bury the ones that matter.
            logger.warning(exc.internal_detail, extra=safe_extra(fields))
        return _error_response(exc, request)

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Report a request FastAPI could not parse into the declared types.

        The framework's own body lists every failing field with its location
        and the offending value. That is excellent for a developer and wrong
        for an end user -- it names internal parameters and echoes back their
        input. The detail is logged; the user is told, in Vietnamese, that the
        request was invalid.

        Args:
            request: The failed request.
            exc: The validation error raised by FastAPI.

        Returns:
            A 422 in the API's standard error shape.
        """
        error = APIValidationError(
            f"Request validation failed: {exc.errors()}",
            context={"path": request.url.path},
        )
        # 422 rather than the 400 that ValidationError carries: it is what
        # FastAPI clients and generated SDKs expect from a schema violation,
        # and the stable `error` code is what callers actually branch on.
        fields = error.log_fields()
        # Overridden so the log records the status actually sent. Leaving the
        # class default would make every log-based check of "how many 422s did
        # we return" silently miss all of them.
        fields["status_code"] = status.HTTP_422_UNPROCESSABLE_ENTITY
        logger.warning(error.internal_detail, extra=safe_extra(fields))
        request_id = _request_id_of(request)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error.to_response_dict(request_id),
            headers={_REQUEST_ID_HEADER: request_id},
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Report an HTTP error raised by the framework itself.

        Chiefly the 404 for an unknown path and the 405 for a wrong method.
        Rewritten into the API's error shape so a client has exactly one body
        format to parse rather than two.

        Args:
            request: The failed request.
            exc: The framework's exception.

        Returns:
            The response in the API's standard error shape.
        """
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            error: APIError = NotFoundError(
                f"No route matches {request.method} {request.url.path}"
            )
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
        """Report anything that was not anticipated.

        The last line of defence for NFR-S4. Whatever escaped -- a driver
        error, a bug, a library raising something undocumented -- the client
        receives the same opaque Vietnamese message and the request identifier,
        while the full traceback goes to the log.

        Args:
            request: The failed request.
            exc: The escaped exception.

        Returns:
            A 500 in the API's standard error shape.
        """
        error = ProcessingError(
            f"Unhandled {type(exc).__name__}: {exc}",
            context={"path": request.url.path, "method": request.method},
        )
        logger.error(error.internal_detail, extra=safe_extra(error.log_fields()), exc_info=exc)
        return _error_response(error, request)


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the application.

    A factory rather than a module-level constant alone, so that a test can
    build a second application against a throwaway database and temporary
    storage without touching the process-wide one.

    Args:
        settings: Configuration to build against. Defaults to the process-wide
            settings.

    Returns:
        The configured application, ready to serve.
    """
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
        # Swagger's own "successful response" wording says nothing; every route
        # documents its 200 individually.
        swagger_ui_parameters={"defaultModelsExpandDepth": 1, "displayRequestDuration": True},
    )

    # -- Middleware -------------------------------------------------------
    # Added innermost-first: the last one added is the outermost, so CORS wraps
    # the request-context middleware and answers pre-flights without allocating
    # an identifier for them.

    @app.middleware("http")
    async def request_context_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[object]],
    ) -> object:
        """Attach a correlation identifier and measure the request.

        An inbound ``X-Request-ID`` is honoured so that a trace started by a
        reverse proxy or by the frontend continues through the backend instead
        of restarting here. One is generated when absent.

        The identifier is bound to a context variable, not passed as an
        argument: every ``logger`` call underneath -- in a service, in a
        repository, inside a worker thread -- picks it up automatically, and
        no function can break the trace by forgetting to forward it.

        Args:
            request: The inbound request.
            call_next: The rest of the application.

        Returns:
            The response, with the identifier and the elapsed time attached as
            headers.
        """
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
        # Explicit origins, never "*". The configuration object rejects the
        # wildcard at start-up (NFR-S4), so this cannot be widened by an
        # environment variable slipped in while debugging.
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        # Without this the browser hides both headers from the frontend, so the
        # identifier a user would quote in a bug report never reaches the UI.
        expose_headers=[_REQUEST_ID_HEADER, _PROCESS_TIME_HEADER],
    )

    register_exception_handlers(app)

    # -- Routes -----------------------------------------------------------
    # ``/health`` sits at the root: a health check that moves when the API
    # prefix changes is not much of a health check.
    app.include_router(health_routes.router)
    app.include_router(detection_routes.router, prefix=config.api_prefix)
    app.include_router(history_routes.router, prefix=config.api_prefix)
    app.include_router(statistics_routes.router, prefix=config.api_prefix)

    # -- Static files -----------------------------------------------------
    # Stored images are served by Starlette's handler, which resolves paths
    # against the mounted directory and refuses to escape it. The directory has
    # to exist before the mount, hence the call here as well as in the lifespan.
    config.ensure_directories()
    app.mount(
        FILES_URL_PREFIX,
        StaticFiles(directory=config.storage_root),
        name="files",
    )

    return app


app = create_app()
"""The application instance uvicorn serves: ``uvicorn backend.main:app``."""
