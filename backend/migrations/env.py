"""Alembic environment: connects the migration tool to the application's config.

Two things happen here that are not in Alembic's generated template, and both
are required by the project's constraints.

**The database URL comes from :class:`~backend.core.config.Settings`, not from
``alembic.ini``.** NFR-M4 forbids a path or URL written down twice. If
``alembic.ini`` carried its own ``sqlalchemy.url``, then setting
``ALPR_DATABASE_URL`` would move the server's database and leave Alembic
pointing at the old one -- migrations would report success against a file
nothing reads. Reading the same settings object removes the possibility.

**``sys.path`` is extended before ``backend`` is imported.** Alembic runs as its
own entry point with the working directory wherever the developer happened to
be, so ``import backend`` is not guaranteed to resolve. The repository root is
derived from this file's location, never from ``os.getcwd()``.

Batch mode
----------
``render_as_batch=True`` is set for SQLite. SQLite cannot ``ALTER TABLE`` to
drop a column, change a type or add a constraint; batch mode emulates those by
creating a new table, copying the rows and swapping it in. Without it the first
migration that alters an existing column fails outright, which -- given the
schema is expected to keep moving during development -- would be soon.
"""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import Connection, create_engine, pool

# --- Import path ------------------------------------------------------------
# <root>/backend/migrations/env.py -> parents[2] is the repository root.
# Derived from __file__ rather than the working directory so that `alembic -c
# backend/alembic.ini` behaves identically from any folder (NFR-M4).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.config import Settings, get_settings  # noqa: E402

# Importing the package -- not just Base -- is what registers every model class
# on Base.metadata. A model that has not been imported is invisible to
# autogenerate, which reads its absence as an instruction to DROP the table.
import backend.models  # noqa: E402, F401
from backend.models.detection import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
"""Schema Alembic diffs the database against during ``--autogenerate``."""


def get_database_url() -> str:
    """Return the database URL the migrations should run against.

    Resolution order:

    1. ``-x db_url=...`` passed on the Alembic command line, which lets a
       one-off migration be run against a copy of the database without editing
       any file or exporting anything;
    2. :attr:`Settings.database_url`, i.e. the same value the server uses.

    Note what is missing: ``alembic.ini``'s ``sqlalchemy.url``. It is left
    unset on purpose so that it cannot disagree with the application.

    Returns:
        A SQLAlchemy connection URL. Relative SQLite paths have already been
        anchored to the project root by the settings model, so the file opened
        here is the same one the server opens.
    """
    overrides = context.get_x_argument(as_dictionary=True)
    override_url = overrides.get("db_url")
    if override_url:
        return override_url
    settings: Settings = get_settings()
    return settings.database_url


def _configure(connection: Connection | None, url: str) -> None:
    """Apply the shared context configuration for both migration modes.

    Kept in one function so offline and online runs cannot be configured
    differently -- a difference there produces SQL that works when applied
    directly and fails when generated as a script, or the reverse.

    Args:
        connection: An open connection for online mode, ``None`` for offline.
        url: The database URL, used by offline mode to pick a dialect.
    """
    is_sqlite = url.startswith("sqlite")
    context.configure(
        connection=connection,
        url=url if connection is None else None,
        target_metadata=target_metadata,
        # Emit the literal values instead of bind parameters when generating a
        # script, so the .sql file can be handed to a DBA and run as-is.
        literal_binds=connection is None,
        dialect_opts={"paramstyle": "named"},
        # Detect column type changes, which Alembic ignores by default.
        compare_type=True,
        compare_server_default=True,
        # Required for SQLite: see the module docstring.
        render_as_batch=is_sqlite,
        # Record the migration version inside a transaction with the migration
        # itself, so a failure cannot leave the version table claiming a
        # migration succeeded when it did not.
        transaction_per_migration=True,
    )


def run_migrations_offline() -> None:
    """Emit the migration SQL to stdout without connecting to a database.

    Used with ``alembic upgrade head --sql`` to review exactly what a migration
    would do, or to hand the statements to someone who applies them manually.
    """
    url = get_database_url()
    _configure(None, url)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply the migrations against a live database.

    The engine is built with :func:`sqlalchemy.create_engine` and the URL
    passed directly, rather than through ``engine_from_config``. That avoids a
    real trap: ``alembic.ini`` is parsed by ``configparser``, which treats
    ``%`` as interpolation syntax, so a URL containing a percent-encoded
    password (``p%40ss``) raises an ``InterpolationSyntaxError`` that names the
    config file and not the password. Bypassing the config entirely means the
    URL is never re-parsed.

    A NullPool is used because a migration opens one connection, does its work
    and exits; pooling would only keep a connection alive after the process is
    finished with it.
    """
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
