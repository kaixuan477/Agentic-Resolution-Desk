"""Sandboxed MCP tool server (mocked enterprise backends).

This is the security boundary between the LLM and real business systems. The
agents never receive API keys or database handles directly — they can only act
through the tools exposed here. In M1 these return deterministic mock data; the
governance rule (refunds over the configured limit escalate to a human) is
already enforced so later milestones can rely on it.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastmcp import FastMCP

from src.config import get_settings

mcp = FastMCP("Billing_and_CRM_Tools")
_settings = get_settings()


@mcp.tool()
def lookup_user(user_id: str) -> dict[str, Any]:
    """Return mock CRM profile for a user."""
    return {
        "user_id": user_id,
        "tier": "VIP" if user_id.upper().startswith("VIP") else "standard",
        "email": f"{user_id.lower()}@example.com",
    }


@mcp.tool()
def check_account_balance(user_id: str) -> dict[str, Any]:
    """Return a mock account balance."""
    return {"user_id": user_id, "balance": 250.00, "currency": "USD"}


@mcp.tool()
def lookup_user_policy(user_id: str) -> str:
    """Return the refund policy applicable to a user."""
    limit = _settings.refund_auto_approve_limit
    tier = "VIP" if user_id.upper().startswith("VIP") else "standard"
    return (
        f"User {user_id} is {tier}. Automated refunds are permitted up to "
        f"${limit:.2f}; anything above requires human approval."
    )


@mcp.tool()
def execute_refund(user_id: str, amount: float) -> dict[str, Any]:
    """Execute a refund.

    Deterministic governance: amounts strictly greater than the configured
    auto-approve limit are NOT executed here; they return a flag that routes the
    workflow to the human-in-the-loop auditor.
    """
    if amount > _settings.refund_auto_approve_limit:
        return {
            "status": "requires_human_auditor",
            "user_id": user_id,
            "amount": amount,
            "limit": _settings.refund_auto_approve_limit,
        }
    return {
        "status": "success",
        "user_id": user_id,
        "amount": amount,
        "transaction_id": f"txn_{datetime.now(UTC).timestamp()}",
    }


if __name__ == "__main__":
    mcp.run()
