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
    """Apply the required pragmas to every new SQLite connection.

    Registered as a ``connect`` listener because SQLite scopes these settings
    to a connection: running them once at start-up would configure a single
    pooled connection and leave the rest of the pool with foreign keys silently
    switched off.

    Args:
        target: The engine whose connections should be configured.
    """

    @event.listens_for(target, "connect")
    def _set_pragmas(dbapi_connection: Any, connection_record: Any) -> None:
        """Configure one freshly opened SQLite connection.

        Args:
            dbapi_connection: The raw DB-API connection just established.
            connection_record: SQLAlchemy's pool bookkeeping entry; unused.
        """
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
    """Build a configured SQLAlchemy engine.

    Exposed as a function, rather than only as the module-level
    :data:`engine`, so tests can point a second engine at a throwaway database
    without touching global state.

    Args:
        settings: Configuration to use. Defaults to the process-wide settings.

    Returns:
        An engine ready for use. For SQLite it carries the pragma listener and
        the connection arguments a threaded server needs.
    """
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
    """Yield a database session for the lifetime of one request.

    Written for use as a FastAPI dependency::

        @router.get("/history")
        def list_history(db: Session = Depends(get_db)) -> HistoryListResponse:
            ...

    The session is always closed, including when the endpoint raises, because
    the ``finally`` clause runs when FastAPI closes the generator. Note what
    this function does *not* do: it never commits. Committing here would make
    every request that raised halfway through persist its partial writes, since
    the exception arrives after the endpoint has already made some of them.
    The service layer commits explicitly, at the point where it knows the unit
    of work is complete.

    Yields:
        A session bound to the process-wide engine.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional session for work outside a request.

    Background video jobs and start-up tasks have no FastAPI dependency
    injection to lean on, but still need a session with correct commit and
    rollback behaviour. This context manager commits on success and rolls back
    on any exception::

        with session_scope() as db:
            db.add(job)

    A background task must not reuse the request's session: the request that
    started it returns ``202 Accepted`` immediately and closes its session,
    while the job keeps running for minutes afterwards.

    Yields:
        A session that is committed on clean exit and rolled back on error.

    Raises:
        Exception: Re-raises whatever the caller raised, after rolling back.
    """
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
    """Create any missing tables.

    Intended for development and for the test suite. In deployment, schema
    changes go through Alembic: ``create_all`` only ever *adds* missing tables,
    so it silently does nothing when a table exists but its columns have
    changed -- which is the situation a migration exists to handle.

    Args:
        target: Engine to create the tables on. Defaults to the process-wide
            engine.
    """
    Base.metadata.create_all(bind=target or engine)
    logger.info(
        "database schema ensured",
        extra={"tables": sorted(Base.metadata.tables)},
    )
