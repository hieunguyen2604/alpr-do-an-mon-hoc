"""Integration tests for the readiness endpoint.

``/health`` reports *readiness*, not liveness, and the distinction is the whole
point of the endpoint. A process that is answering HTTP but whose detector
weights failed to load cannot serve a single detection request; an endpoint that
says ``ok`` in that state turns a configuration mistake into a mystery that only
surfaces when a user uploads something.

Two design decisions are pinned down here because both look like bugs to someone
who has not read the module:

* the response is **always HTTP 200**, even when degraded -- the endpoint
  answering at all is itself information, and an orchestrator distinguishing
  "down" from "degraded" reads the body;
* a pipeline that is not ready reports ``model_loaded = false`` and drags the
  overall status to ``degraded``, so a deployment running on fabricated or
  absent results cannot look healthy.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.deps import get_pipeline
from backend.services.detection_service import StubPipeline, UnavailablePipeline

from .conftest import FakePipeline

pytestmark = pytest.mark.integration

HEALTH_URL = "/health"


class TestHealthyService:
    """Both dependencies usable."""

    def test_reports_ok(self, client: TestClient) -> None:
        response = client.get(HEALTH_URL)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_reports_both_dependencies_separately(self, client: TestClient) -> None:
        """One flag each, because they fail independently."""
        body = client.get(HEALTH_URL).json()
        assert body["database_connected"] is True
        assert body["model_loaded"] is True

    def test_carries_the_service_identity_and_uptime(self, client: TestClient) -> None:
        body = client.get(HEALTH_URL).json()
        assert body["app_name"] == "ALPR test"
        assert body["version"] == "test"
        assert body["uptime_seconds"] >= 0.0
        assert body["timestamp"]

    def test_sits_at_the_root_not_behind_the_api_prefix(self, client: TestClient) -> None:
        """A health check that moves when the API prefix changes is not much of
        a health check."""
        assert client.get(HEALTH_URL).status_code == 200
        assert client.get("/api/health").status_code == 404


class TestDegradedService:
    """A dependency that cannot serve requests must be visible from outside."""

    def test_an_unavailable_pipeline_reports_degraded(self, app: FastAPI) -> None:
        app.dependency_overrides[get_pipeline] = lambda: UnavailablePipeline("weights not found")
        body = TestClient(app).get(HEALTH_URL).json()

        assert body["status"] == "degraded"
        assert body["model_loaded"] is False
        assert body["database_connected"] is True

    def test_the_stub_pipeline_also_reports_degraded(self, app: FastAPI) -> None:
        """The stub fabricates plate numbers, so a deployment running on it must
        never be able to look healthy."""
        app.dependency_overrides[get_pipeline] = lambda: StubPipeline()
        body = TestClient(app).get(HEALTH_URL).json()

        assert body["status"] == "degraded"
        assert body["model_loaded"] is False

    def test_the_status_is_still_http_200_when_degraded(self, app: FastAPI) -> None:
        """The endpoint answering at all is information; the body says what is
        wrong. Failing the status line would make "degraded" indistinguishable
        from "unreachable"."""
        app.dependency_overrides[get_pipeline] = lambda: UnavailablePipeline("x")
        assert TestClient(app).get(HEALTH_URL).status_code == 200

    def test_a_pipeline_that_raises_while_being_probed_counts_as_not_ready(
        self, app: FastAPI
    ) -> None:
        """The safe reading: a health check must report, never raise."""

        class ExplodingPipeline(FakePipeline):
            @property
            def is_ready(self) -> bool:
                raise RuntimeError("readiness check blew up")

        app.dependency_overrides[get_pipeline] = ExplodingPipeline
        response = TestClient(app).get(HEALTH_URL)

        assert response.status_code == 200
        body = response.json()
        assert body["model_loaded"] is False
        assert body["status"] == "degraded"

    def test_the_reason_a_pipeline_is_unavailable_is_not_published(self, app: FastAPI) -> None:
        """NFR-S4: the health body says *that* the model is unavailable, not
        which path on the server it failed to load from."""
        app.dependency_overrides[get_pipeline] = lambda: UnavailablePipeline(
            "no weights at /srv/models/best.pt"
        )
        raw = TestClient(app).get(HEALTH_URL).text

        assert "/srv/models" not in raw
        assert "no weights" not in raw
