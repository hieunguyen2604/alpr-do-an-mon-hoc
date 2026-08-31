"""Alembic environment: DB URL from Settings (NFR-M4), batch mode for SQLite."""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import Connection, create_engine, pool

# Derive project root from __file__ so `alembic -c` works from any folder.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import the package to register all model classes on Base.metadata.
import backend.models  # noqa: E402, F401
from backend.core.config import Settings, get_settings  # noqa: E402
from backend.models.detection import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata



def get_database_url() -> str:
    """Return DB URL from CLI override or Settings."""
    overrides = context.get_x_argument(as_dictionary=True)
    override_url = overrides.get("db_url")
    if override_url:
        return override_url
    settings: Settings = get_settings()
    return settings.database_url


def _configure(connection: Connection | None, url: str) -> None:
    """Apply shared Alembic context configuration for offline/online modes."""
    is_sqlite = url.startswith("sqlite")
    context.configure(
        connection=connection,
        url=url if connection is None else None,
        target_metadata=target_metadata,
        literal_binds=connection is None,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_as_batch=is_sqlite,
        transaction_per_migration=True,
    )


def run_migrations_offline() -> None:
    """Emit migration SQL to stdout without a live database connection."""
    url = get_database_url()
    _configure(None, url)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations against a live database with NullPool."""
    url = get_database_url()
    connectable = create_engine(url, poolclass=pool.NullPool, future=True)

    with connectable.connect() as connection:
        _configure(connection, url)
        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
