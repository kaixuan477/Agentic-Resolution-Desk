"""Unit tests for the billing worker — fully offline via the sandboxed tool."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from src.agents.billing import billing_node, extract_amount
from src.state import ResolutionState


def _state(text: str, user_id: str | None) -> ResolutionState:
    return ResolutionState(
        messages=[HumanMessage(content=text)],
        intent="billing",
        extracted_user_id=user_id,
    )


def test_extract_amount_variants() -> None:
    assert extract_amount("refund me $40") == 40.0
    assert extract_amount("please refund 12.50 dollars") == 12.50
    assert extract_amount("no numbers here") is None


def test_low_value_refund_succeeds() -> None:
    result = billing_node(_state("refund $40 please", "VIP-01"))
    assert result["current_assignee"] == "billing"
    assert result.get("requires_approval") is not True  # not escalated
    assert isinstance(result["messages"][0], AIMessage)
    assert "refunded" in result["messages"][0].content.lower()


def test_high_value_refund_escalates() -> None:
    result = billing_node(_state("I want a refund of $500", "VIP-01"))
    assert result["requires_approval"] is True
    assert result["current_assignee"] == "auditor"
    assert result["proposed_action"].tool == "execute_refund"
    assert result["proposed_action"].arguments["amount"] == 500.0


def test_missing_user_id_asks_for_it() -> None:
    result = billing_node(_state("refund $10", None))
    assert result["current_assignee"] == "billing"
    assert "account id" in result["messages"][0].content.lower()


def test_missing_amount_asks_for_it() -> None:
    result = billing_node(_state("I want a refund", "VIP-01"))
    assert result["current_assignee"] == "billing"
    assert "how much" in result["messages"][0].content.lower()


def test_unknown_user_returns_error_message() -> None:
    result = billing_node(_state("refund $10", "GHOST-99"))
    assert result["current_assignee"] == "billing"
    assert "couldn't" in result["messages"][0].content.lower()
