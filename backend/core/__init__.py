"""Cross-cutting concerns shared by every other backend layer.

Three modules, deliberately kept free of any dependency on the layers above
them so that they can be imported from anywhere without creating a cycle:

============================ ==================================================
Module                       Responsibility
============================ ==================================================
:mod:`backend.core.config`     Every setting and **every path**, in one place
:mod:`backend.core.logging`    Structured JSON logs carrying a ``request_id``
:mod:`backend.core.exceptions` The API error hierarchy and its Vietnamese
                               user-facing messages
============================ ==================================================

Nothing here imports from ``backend.api``, ``backend.services`` or
``backend.models``.
"""

from __future__ import annotations

__all__: list[str] = []
