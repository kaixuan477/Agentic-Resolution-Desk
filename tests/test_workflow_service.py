"""End-to-end workflow tests — full graph, in-memory saver, no network."""

from __future__ import annotations

from src.workflow_service import WorkflowService
from tests._offline import build_offline_app


def _service() -> WorkflowService:
    return WorkflowService(build_offline_app())


def test_support_ticket_resolves_immediately() -> None:
    service = _service()
    snap = service.submit("how do I reset my password?", thread_id="t-support")
    assert snap.status == "resolved"
    assert snap.requires_approval is False
    assert service.pending() == []


def test_low_value_refund_resolves_without_approval() -> None:
    service = _service()
    snap = service.submit("please refund $30 for VIP-01", thread_id="t-low")
    assert snap.status == "resolved"
    assert snap.requires_approval is False


def test_high_value_refund_suspends_then_approves() -> None:
    service = _service()
    snap = service.submit("I need a refund of $500 for VIP-01", thread_id="t-high")
    assert snap.status == "awaiting_approval"
    assert snap.requires_approval is True
    assert service.pending() == ["t-high"]

    resumed = service.resume("t-high", "approved")
    assert resumed.status == "resolved"
    assert resumed.requires_approval is False
    assert service.pending() == []
    assert any("processed" in m.lower() for m in resumed.messages)


def test_high_value_refund_can_be_denied() -> None:
    service = _service()
    service.submit("refund $750 for VIP-01", thread_id="t-deny")
    resumed = service.resume("t-deny", "denied")
    assert resumed.status == "resolved"
    assert any("declined" in m.lower() for m in resumed.messages)


def test_pending_tracks_multiple_threads() -> None:
    service = _service()
    service.submit("refund $500 for VIP-01", thread_id="a")
    service.submit("refund $900 for VIP-02", thread_id="b")
    assert service.pending() == ["a", "b"]
    service.resume("a", "approved")
    assert service.pending() == ["b"]
