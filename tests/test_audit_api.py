"""Offline tests for the audit-trail read endpoint and its dashboard view."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.audit.logger import audit_log


@pytest.fixture
def client() -> Iterator[TestClient]:
    audit_log.clear()
    yield TestClient(app)
    audit_log.clear()


def _seed() -> None:
    audit_log.record(tool="lookup_user", arguments={"user_id": "VIP-01"},
                     result_status="success", user_id="VIP-01")
    audit_log.record(tool="execute_refund", arguments={"user_id": "VIP-01", "amount": 40.0},
                     result_status="success", user_id="VIP-01")
    audit_log.record(tool="execute_refund", arguments={"user_id": "VIP-02", "amount": 500.0},
                     result_status="requires_human_auditor", user_id="VIP-02")


def test_audit_returns_all_records(client: TestClient) -> None:
    _seed()
    records = client.get("/audit").json()
    assert len(records) == 3
    assert {r["tool"] for r in records} == {"lookup_user", "execute_refund"}


def test_audit_filters_by_user(client: TestClient) -> None:
    _seed()
    records = client.get("/audit", params={"user_id": "VIP-02"}).json()
    assert len(records) == 1
    assert records[0]["result_status"] == "requires_human_auditor"


def test_audit_filters_by_tool(client: TestClient) -> None:
    _seed()
    records = client.get("/audit", params={"tool": "execute_refund"}).json()
    assert len(records) == 2


def test_audit_respects_limit(client: TestClient) -> None:
    _seed()
    records = client.get("/audit", params={"limit": 1}).json()
    assert len(records) == 1
    # Limit returns the most recent record.
    assert records[0]["user_id"] == "VIP-02"


def test_audit_redacts_email_at_write(client: TestClient) -> None:
    audit_log.record(tool="lookup_user", arguments={"email": "jane.doe@example.com"},
                     result_status="success", user_id="VIP-01")
    records = client.get("/audit").json()
    assert records[0]["arguments"]["email"] == "***"


def test_audit_dashboard_served() -> None:
    response = TestClient(app).get("/dashboard/audit.html")
    assert response.status_code == 200
    assert "Audit Trail" in response.text
