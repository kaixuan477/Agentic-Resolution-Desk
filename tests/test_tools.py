"""Unit tests for the sandboxed MCP tools (pure functions, no network)."""

from __future__ import annotations

import pytest

from src.audit.logger import audit_log
from src.mcp_server.models import (
    AccountBalance,
    PolicyResult,
    RefundResult,
    ToolError,
    UserProfile,
)
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


@pytest.fixture(autouse=True)
def _clear_audit():
    audit_log.clear()
    yield
    audit_log.clear()


def test_lookup_user_known() -> None:
    result = _call(lookup_user, user_id="VIP-01")
    assert isinstance(result, UserProfile)
    assert result.tier == "VIP"


def test_lookup_user_unknown_returns_error() -> None:
    result = _call(lookup_user, user_id="does-not-exist")
    assert isinstance(result, ToolError)
    assert result.error == "user_not_found"


def test_check_account_balance_known() -> None:
    result = _call(check_account_balance, user_id="USER-100")
    assert isinstance(result, AccountBalance)
    assert result.currency == "USD"


def test_policy_known_mentions_approval() -> None:
    result = _call(lookup_user_policy, user_id="VIP-01")
    assert isinstance(result, PolicyResult)
    assert "approval" in result.summary.lower()


def test_refund_under_limit_succeeds() -> None:
    result = _call(execute_refund, user_id="VIP-01", amount=25.0)
    assert isinstance(result, RefundResult)
    assert result.status == "success"
    assert result.transaction_id is not None


def test_refund_at_limit_auto_approves() -> None:
    result = _call(execute_refund, user_id="VIP-01", amount=50.0)
    assert isinstance(result, RefundResult)
    assert result.status == "success"


def test_refund_over_limit_escalates() -> None:
    result = _call(execute_refund, user_id="VIP-01", amount=100.0)
    assert isinstance(result, RefundResult)
    assert result.status == "requires_human_auditor"
    assert result.limit == 50.0


def test_refund_non_positive_rejected() -> None:
    result = _call(execute_refund, user_id="VIP-01", amount=0.0)
    assert isinstance(result, ToolError)
    assert result.error == "invalid_amount"


def test_refund_unknown_user_error() -> None:
    result = _call(execute_refund, user_id="ghost", amount=10.0)
    assert isinstance(result, ToolError)
    assert result.error == "user_not_found"


def test_tools_write_audit_records() -> None:
    _call(lookup_user, user_id="VIP-01")
    _call(execute_refund, user_id="VIP-01", amount=100.0)
    statuses = [r["result_status"] for r in audit_log.records]
    assert "success" in statuses
    assert "requires_human_auditor" in statuses
