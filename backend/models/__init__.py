"""SQLAlchemy ORM models and the database connection.

Re-exports the two tables of the approved schema, the declarative
:class:`~backend.models.detection.Base` and the session helpers, so that the
rest of the backend imports from ``backend.models`` rather than reaching into
individual modules.

Import order matters here: :mod:`backend.models.database` builds the engine at
import time, so it comes after :mod:`backend.models.detection`, whose
``Base.metadata`` it registers tables from.

.. warning::
   Alembic's ``env.py`` must import this package -- not just ``Base`` -- before
   calling ``autogenerate``. A model class that has not been imported is not
   attached to ``Base.metadata``, and autogenerate would read the missing table
   as an instruction to *drop* it.
"""

from __future__ import annotations

from backend.models.database import (
    SessionLocal,
    create_database_engine,
    engine,
    get_db,
    init_database,
    session_scope,
)
from backend.models.detection import (
    Base,
    DetectionHistory,
    DetectionJob,
    InputType,
    JobStatus,
    utcnow,
)

__all__ = [
    "Base",
    "DetectionHistory",
    "DetectionJob",
    "InputType",
    "JobStatus",
    "utcnow",
    "engine",
    "SessionLocal",
    "create_database_engine",
    "get_db",
    "session_scope",
    "init_database",
]
