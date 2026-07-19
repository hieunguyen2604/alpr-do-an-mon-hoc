"""Vietnamese ALPR artificial-intelligence layer.

This package holds every piece of machine-learning code in the project:
model training (:mod:`ai.training`), offline evaluation (:mod:`ai.evaluation`)
and runtime inference (:mod:`ai.inference`).

Architectural constraint (NFR-M1): nothing under ``ai/`` may import FastAPI,
Pydantic, SQLAlchemy or any other web/persistence framework. This package is
plain Python plus scientific libraries, so it can be unit-tested in isolation
and reused from training scripts, notebooks and the API layer alike.
"""

__all__: list[str] = []
