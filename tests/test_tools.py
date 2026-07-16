"""Unit tests for the sandboxed MCP tools (pure functions, no network)."""

from __future__ import annotations

from src.mcp_server.server import (
    check_account_balance,
    execute_refund,
    lookup_user,
    lookup_user_policy,
)


def _call(tool, /, **kwargs):
    """Invoke an MCP-wrapped tool's underlying function."""
    fn = getattr(tool, "fn", None) or getattr(tool, "__wrapped__", None) or tool
    return fn(**kwargs)


def test_lookup_user_vip_detection() -> None:
    assert _call(lookup_user, user_id="VIP-01")["tier"] == "VIP"
    assert _call(lookup_user, user_id="user-9")["tier"] == "standard"


def test_check_account_balance_shape() -> None:
    result = _call(check_account_balance, user_id="VIP-01")
    assert result["currency"] == "USD"
    assert "balance" in result


def test_policy_mentions_limit() -> None:
    assert "approval" in _call(lookup_user_policy, user_id="VIP-01").lower()


def test_refund_under_limit_succeeds() -> None:
    result = _call(execute_refund, user_id="VIP-01", amount=25.0)
    assert result["status"] == "success"
    assert "transaction_id" in result


def test_refund_over_limit_escalates() -> None:
    result = _call(execute_refund, user_id="VIP-01", amount=100.0)
    assert result["status"] == "requires_human_auditor"
    assert result["amount"] == 100.0
