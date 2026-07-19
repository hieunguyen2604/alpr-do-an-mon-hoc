"""FastAPI backend for the Vietnamese ALPR system.

This package owns everything that is *not* computer vision: HTTP routing,
persistence, validation and configuration. The recognition pipeline lives in
the separate top-level ``ai`` package and is consumed here strictly through the
abstract interfaces it publishes.

The dependency arrow points one way only::

    backend  ---->  ai
    backend  <--/-  ai      (never; enforced by NFR-M1)

``ai`` must never import FastAPI or Pydantic. Keeping the arrow one-directional
is what allows the pipeline to be reused from training and benchmarking scripts
that have no web server, and what allows the OCR engine to be swapped without
touching a single router (NFR-M5).

Layers, outermost first::

    api/          HTTP routers -- request/response only, no business rules
    services/     business logic -- orchestrates pipeline + persistence
    repositories/ data access -- SQLAlchemy queries
    models/       SQLAlchemy ORM models (the approved schema)
    schemas/      Pydantic v2 wire contracts (Swagger documentation)
    core/         configuration, structured logging, exception hierarchy

This module intentionally performs no imports of its own. Importing
``backend`` must stay free of side effects so that tooling -- Alembic, test
collection, the ``ai`` benchmark scripts -- can touch the package without
building a database engine or reading the environment.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"
"""Backend version, surfaced by the ``/health`` endpoint."""
