"""Sandboxed MCP tool server (mocked enterprise backends).

This is the security boundary between the LLM and real business systems. Agents
never receive API keys or database handles directly — they act only through the
tools exposed here. The tool logic lives in ``tools_impl`` (so internal callers
can use it with least-privilege imports); this module registers those pure
implementations over the Model Context Protocol.
"""

from __future__ import annotations

from fastmcp import FastMCP

from src.mcp_server import tools_impl
from src.mcp_server.models import (
    AccountBalance,
    PolicyResult,
    RefundResult,
    ToolError,
    UserProfile,
)

mcp = FastMCP("Billing_and_CRM_Tools")


@mcp.tool()
def lookup_user(user_id: str) -> UserProfile | ToolError:
    """Return the CRM profile for a user, or a structured error if unknown."""
    return tools_impl.lookup_user(user_id)


@mcp.tool()
def check_account_balance(user_id: str) -> AccountBalance | ToolError:
    """Return a user's account balance, or a structured error if unknown."""
    return tools_impl.check_account_balance(user_id)


@mcp.tool()
def lookup_user_policy(user_id: str) -> PolicyResult | ToolError:
    """Return the refund policy applicable to a user."""
    return tools_impl.lookup_user_policy(user_id)


@mcp.tool()
def execute_refund(
    user_id: str, amount: float, idempotency_key: str | None = None
) -> RefundResult | ToolError:
    """Execute a refund under deterministic governance (see ``tools_impl``)."""
    return tools_impl.execute_refund(user_id, amount, idempotency_key)


if __name__ == "__main__":
    mcp.run()
