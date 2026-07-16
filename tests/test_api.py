"""API tests using an in-memory-saver service injected via dependency override.

``TestClient`` is instantiated without the context-manager form so the Postgres
``lifespan`` startup is not triggered — the service is supplied entirely through
``dependency_overrides``, keeping these tests fully offline.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.api.main import app, get_service
from src.workflow_service import WorkflowService
from tests._offline import build_offline_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    service = WorkflowService(build_offline_app())
    app.dependency_overrides[get_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_support_ticket(client: TestClient) -> None:
    response = client.post("/tickets", json={"message": "how do I reset my password?",
                                             "thread_id": "api-support"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "resolved"
    assert body["requires_approval"] is False


def test_high_value_flow(client: TestClient) -> None:
    submit = client.post("/tickets", json={"message": "refund $500 for VIP-01",
                                           "thread_id": "api-high"})
    assert submit.json()["status"] == "awaiting_approval"

    pending = client.get("/pending")
    assert "api-high" in pending.json()["pending"]

    approve = client.post("/approve", json={"thread_id": "api-high", "decision": "approved"})
    assert approve.status_code == 200
    assert approve.json()["status"] == "resolved"

    assert client.get("/pending").json()["pending"] == []


def test_invalid_decision_rejected(client: TestClient) -> None:
    response = client.post("/approve", json={"thread_id": "x", "decision": "maybe"})
    assert response.status_code == 422


def test_service_unavailable_returns_503() -> None:
    # No dependency override -> the un-initialized service yields a 503.
    unconfigured = TestClient(app)
    response = unconfigured.post("/tickets", json={"message": "hello"})
    assert response.status_code == 503
