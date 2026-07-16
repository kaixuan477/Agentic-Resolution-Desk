"""Unit tests for the auditor node — offline, via injected refund executor."""

from __future__ import annotations

from langchain_core.messages import AIMessage

from src.agents.auditor import auditor_node
from src.mcp_server.models import RefundResult
from src.state import ProposedAction, ResolutionState


class _RecordingExecutor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, float]] = []

    def __call__(self, user_id: str, amount: float) -> RefundResult:
        self.calls.append((user_id, amount))
        return RefundResult(
            status="success", user_id=user_id, amount=amount, transaction_id="txn_test"
        )


def _state(decision: str | None) -> ResolutionState:
    return ResolutionState(
        intent="billing",
        requires_approval=True,
        approval_decision=decision,  # type: ignore[arg-type]
        proposed_action=ProposedAction(
            tool="execute_refund",
            arguments={"user_id": "VIP-01", "amount": 500.0},
            requires_approval=True,
        ),
    )


def test_approved_executes_refund() -> None:
    executor = _RecordingExecutor()
    result = auditor_node(_state("approved"), refund_executor=executor)
    assert executor.calls == [("VIP-01", 500.0)]
    assert result["requires_approval"] is False
    assert isinstance(result["messages"][0], AIMessage)
    assert "processed" in result["messages"][0].content.lower()


def test_denied_moves_no_money() -> None:
    executor = _RecordingExecutor()
    result = auditor_node(_state("denied"), refund_executor=executor)
    assert executor.calls == []
    assert result["requires_approval"] is False
    assert "declined" in result["messages"][0].content.lower()


def test_no_decision_is_noop() -> None:
    executor = _RecordingExecutor()
    result = auditor_node(_state(None), refund_executor=executor)
    assert executor.calls == []
    assert result == {"current_assignee": "auditor"}
