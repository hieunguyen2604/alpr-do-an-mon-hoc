"""Pytest bootstrap: make the repository root importable as a package root.

Tests import ``ai.inference...`` directly. Placing this file at the repository
root is what puts that root on ``sys.path`` regardless of the directory pytest
was started from, so the test suite behaves the same locally and in CI.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
