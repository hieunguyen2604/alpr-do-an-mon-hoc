"""Structured JSON logging with per-request correlation identifiers (NFR-S4, NFR-S5)."""

from __future__ import annotations

import datetime as dt
import json
import logging
import sys
import uuid
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Any, Final, TextIO

__all__ = [
    "NO_REQUEST_ID",
    "JsonFormatter",
    "RequestIdFilter",
    "setup_logging",
    "get_logger",
    "new_request_id",
    "get_request_id",
    "set_request_id",
    "reset_request_id",
    "request_context",
    "safe_extra",
]

NO_REQUEST_ID: Final[str] = "-"
"""Placeholder used for log records emitted outside any request.

Start-up, shutdown and background maintenance produce real log lines that
belong to no HTTP request. They still get the ``request_id`` key so that every
record has an identical shape -- a log consumer never has to handle a missing
field.
"""

_request_id: ContextVar[str] = ContextVar("alpr_request_id", default=NO_REQUEST_ID)
"""Holds the identifier of the request being served by the current context."""

_LOG_RECORD_BUILTINS: Final[frozenset[str]] = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "taskName",
        "thread",
        "threadName",
        "request_id",
    }
)
"""Attributes the standard library puts on every record.

Anything on a record that is *not* in this set was supplied by the caller
through ``logger.info(..., extra={...})``, and is copied into the JSON output
verbatim. This is what makes structured logging usable::

    logger.info("upload accepted", extra={"job_id": job.id, "size_bytes": n})
"""

_UVICORN_LOGGERS: Final[tuple[str, ...]] = (
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
    "fastapi",
)
"""Third-party loggers re-pointed at our handler.

Uvicorn installs its own colourised handlers at start-up. Left alone, the
server's own lines would be plain text in the middle of a JSON stream, which
defeats machine parsing. Their handlers are removed and propagation is turned
on so they flow through the same formatter as everything else.
"""

_CONFIGURED: bool = False
"""Guards against installing duplicate handlers.

``setup_logging`` is reachable from the app factory, from Alembic and from test
fixtures. Without this flag a test suite that builds the app repeatedly would
add one handler per call and print every line N times.
"""


# --- Request identifier ---


def new_request_id() -> str:
    """Generate a fresh request identifier."""
    return uuid.uuid4().hex


def get_request_id() -> str:
    """Return the identifier of the request being handled in this context."""
    return _request_id.get()


def set_request_id(request_id: str) -> Token[str]:
    """Bind a request identifier to the current context."""
    return _request_id.set(request_id)


def reset_request_id(token: Token[str]) -> None:
    """Restore the request identifier that was bound before :func:`set_request_id`."""
    _request_id.reset(token)


@contextmanager
def request_context(request_id: str | None = None) -> Iterator[str]:
    """Bind a request identifier for the duration of a ``with`` block."""
    token = set_request_id(request_id or new_request_id())
    try:
        yield get_request_id()
    finally:
        reset_request_id(token)


# --- Structured fields ---

_RESERVED_LOG_KEYS: Final[frozenset[str]] = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "taskName",
        "thread",
        "threadName",
    }
)
"""Keys ``logging`` refuses to accept in ``extra=``.

The standard library owns these attribute names on every ``LogRecord`` and
raises ``KeyError: "Attempt to overwrite 'filename' in LogRecord"`` rather than
letting a caller shadow one. The failure has an unpleasant shape: it is raised
*by the logging call*, so it replaces the diagnostic that was being written
with an unrelated exception -- and it usually happens on an error path, which
is the moment the log mattered most. ``filename`` and ``module`` are the ones
that bite in practice, because they are the natural names for exactly the
things worth logging about an upload.
"""

_SAFE_KEY_PREFIX: Final[str] = "ctx_"
"""Prefix applied to a field whose name the standard library has reserved."""


def safe_extra(fields: Mapping[str, Any]) -> dict[str, Any]:
    """Make a mapping safe to pass as ``logger.*(..., extra=...)``."""
    return {
        (f"{_SAFE_KEY_PREFIX}{key}" if key in _RESERVED_LOG_KEYS else key): value
        for key, value in fields.items()
    }


# --- Formatting ---


class RequestIdFilter(logging.Filter):
    """Attaches the current request identifier to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add a ``request_id`` attribute to the record."""
        if not hasattr(record, "request_id"):
            record.request_id = get_request_id()
        return True


class JsonFormatter(logging.Formatter):
    """Renders a log record as a single-line JSON object."""

    def __init__(self, *, ensure_ascii: bool = False) -> None:
        """Initialise the formatter."""
        super().__init__()
        self._ensure_ascii = ensure_ascii

    def format(self, record: logging.LogRecord) -> str:
        """Serialise one log record to a JSON string."""
        timestamp = dt.datetime.fromtimestamp(record.created, tz=dt.timezone.utc)
        payload: dict[str, Any] = {
            "timestamp": timestamp.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", NO_REQUEST_ID),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)

        for key, value in record.__dict__.items():
            if key not in _LOG_RECORD_BUILTINS and not key.startswith("_"):
                payload[key] = self._coerce(value)

        return json.dumps(payload, ensure_ascii=self._ensure_ascii, default=str)

    @staticmethod
    def _coerce(value: Any) -> Any:
        """Make a value safe to hand to :func:`json.dumps`."""
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        if isinstance(value, (list, tuple, set)):
            return [JsonFormatter._coerce(item) for item in value]
        if isinstance(value, dict):
            return {str(k): JsonFormatter._coerce(v) for k, v in value.items()}
        return str(value)


# --- Set-up ---


def _utf8_stdout() -> TextIO:
    """Return ``sys.stdout``, switched to UTF-8 if it is not already."""
    stream = sys.stdout
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is not None:
        try:
            reconfigure(encoding="utf-8", errors="backslashreplace")
        except (ValueError, OSError):
            # A stream replaced by a test harness may not support this; the
            # handler still works, so this is not worth failing start-up over.
            pass
    return stream


def setup_logging(level: str = "INFO", *, force: bool = False) -> None:
    """Install the JSON handler on the root logger."""
    global _CONFIGURED

    if _CONFIGURED and not force:
        return

    numeric_level = logging.getLevelName(level.strip().upper())
    if not isinstance(numeric_level, int):
        raise ValueError(f"Unknown log level: {level!r}")

    handler = logging.StreamHandler(stream=_utf8_stdout())
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RequestIdFilter())

    root = logging.getLogger()
    for existing in list(root.handlers):
        root.removeHandler(existing)
        existing.close()
    root.addHandler(handler)
    root.setLevel(numeric_level)

    # Let uvicorn's records reach our handler instead of its own coloured one,
    # so the stream stays uniformly parseable.
    for name in _UVICORN_LOGGERS:
        third_party = logging.getLogger(name)
        third_party.handlers.clear()
        third_party.propagate = True

    # These two are chatty at DEBUG and would bury our own records. SQLAlchemy
    # in particular echoes every statement, which is only wanted when debug
    # mode explicitly asks for it via ``echo=True`` on the engine.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.LoggerAdapter[logging.Logger] | logging.Logger:
    """Return the logger for a module."""
    return logging.getLogger(name)
