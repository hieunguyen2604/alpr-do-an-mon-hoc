"""HTTP layer: routers and the dependencies they are wired from.

The outermost layer, and deliberately the thinnest. A router's whole job is to
translate -- an HTTP request into service arguments, a service result into a
response model, a raised :class:`~backend.core.exceptions.APIError` into a
status code. No business rule and no query lives here, which is what makes the
same logic reachable from a background task and from a test that never starts a
server.

======================================= ====================================
Module                                  Contents
======================================= ====================================
:mod:`backend.api.deps`                 Shared FastAPI dependencies
:mod:`backend.api.routes.health`        ``GET /health``
:mod:`backend.api.routes.detection`     ``POST /api/detect/*``, job status
:mod:`backend.api.routes.history`       ``GET/DELETE /api/history*``
:mod:`backend.api.routes.statistics`    ``GET /api/statistics``
======================================= ====================================

Routers are declared without a prefix of their own and mounted by
``backend.main`` under :attr:`~backend.core.config.Settings.api_prefix`, so the
public prefix is configuration rather than something repeated in four files.
``/health`` is the exception: monitoring tools expect it at the root, and a
health check that moves when the API prefix changes is not much of a health
check.
"""

from __future__ import annotations

__all__: list[str] = []
