"""Database engine configuration, session lifecycle, and SQLite connection pragmas."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Final

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.models.detection import Base

__all__ = [
    "engine",
    "SessionLocal",
    "create_database_engine",
    "get_db",
    "session_scope",
    "init_database",
]

logger = get_logger(__name__)

_SQLITE_BUSY_TIMEOUT_MS: Final[int] = 5_000


def _register_sqlite_pragmas(target: Engine) -> None:
    """Apply the required pragmas to every new SQLite connection."""

    @event.listens_for(target, "connect")
    def _set_pragmas(dbapi_connection: Any, connection_record: Any) -> None:
        """Configure one freshly opened SQLite connection."""
        cursor = dbapi_connection.cursor()
        try:
            # Without this, every ForeignKey and ON DELETE CASCADE is decorative.
            cursor.execute("PRAGMA foreign_keys=ON")
            # Concurrent reads during long-running video jobs.
            cursor.execute("PRAGMA journal_mode=WAL")
            # Durability traded for speed: with WAL, NORMAL risks losing only
            # the most recent transactions on an OS crash, never corruption.
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute(f"PRAGMA busy_timeout={_SQLITE_BUSY_TIMEOUT_MS}")
        finally:
            cursor.close()


def create_database_engine(settings: Settings | None = None) -> Engine:
    """Build a configured SQLAlchemy engine."""
    config = settings or get_settings()
    connect_args: dict[str, Any] = {}

    if config.is_sqlite:
        # FastAPI runs synchronous endpoints in a thread pool, so a connection
        # created on one thread is used on another. SQLite's default same-thread
        # check would reject that; SQLAlchemy's pool already serialises access.
        connect_args["check_same_thread"] = False

    new_engine = create_engine(
        config.database_url,
        connect_args=connect_args,
        # Detects a connection dropped while idle and replaces it, instead of
        # surfacing the failure inside a user's request.
        pool_pre_ping=True,
        echo=config.debug,
        future=True,
    )

    if config.is_sqlite:
        _register_sqlite_pragmas(new_engine)

    return new_engine


engine: Engine = create_database_engine()
"""The process-wide engine, and with it the connection pool."""

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    # Keeps ORM objects usable after commit(); otherwise serialising a
    # just-created detection re-queries on a session about to close.
    expire_on_commit=False,
)
"""Factory producing sessions bound to :data:`engine`."""


def get_db() -> Iterator[Session]:
    """Yield a database session for the lifetime of one request."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional session for work outside a request."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database(target: Engine | None = None) -> None:
    """Create any missing tables."""
    Base.metadata.create_all(bind=target or engine)
    logger.info(
        "database schema ensured",
        extra={"tables": sorted(Base.metadata.tables)},
    )
