"""Pure tool implementations (no MCP decoration).

Separating the implementations from MCP registration lets internal callers —
notably the Billing worker and unit tests — invoke tools directly with explicit,
least-privilege imports, while ``server.py`` exposes the same functions over the
Model Context Protocol. Governance and audit logging live here so every path
(agent or MCP) is covered identically.
"""

from __future__ import annotations

from datetime import UTC, datetime

from src.audit.logger import audit_log
from src.mcp_server.mock_crm import UserNotFoundError, get_user
from src.mcp_server.models import (
    AccountBalance,
    PolicyResult,
    RefundResult,
    ToolError,
    UserProfile,
)
from src.policy import auto_approve_limit, refund_requires_approval


def lookup_user(user_id: str) -> UserProfile | ToolError:
    """Return the CRM profile for a user, or a structured error if unknown."""
    try:
        user = get_user(user_id)
    except UserNotFoundError as exc:
        audit_log.record(
            tool="lookup_user", arguments={"user_id": user_id},
            result_status="not_found", user_id=user_id,
        )
        return ToolError(error="user_not_found", detail=str(exc), user_id=user_id)

    audit_log.record(
        tool="lookup_user", arguments={"user_id": user_id},
        result_status="success", user_id=user_id,
    )
    return UserProfile(user_id=user.user_id, tier=user.tier, email=user.email)


def check_account_balance(user_id: str) -> AccountBalance | ToolError:
    """Return a user's account balance, or a structured error if unknown."""
    try:
        user = get_user(user_id)
    except UserNotFoundError as exc:
        audit_log.record(
            tool="check_account_balance", arguments={"user_id": user_id},
            result_status="not_found", user_id=user_id,
        )
        return ToolError(error="user_not_found", detail=str(exc), user_id=user_id)

    audit_log.record(
        tool="check_account_balance", arguments={"user_id": user_id},
        result_status="success", user_id=user_id,
    )
    return AccountBalance(user_id=user.user_id, balance=user.balance, currency=user.currency)


def lookup_user_policy(user_id: str) -> PolicyResult | ToolError:
    """Return the refund policy applicable to a user."""
    try:
        user = get_user(user_id)
    except UserNotFoundError as exc:
        audit_log.record(
            tool="lookup_user_policy", arguments={"user_id": user_id},
            result_status="not_found", user_id=user_id,
        )
        return ToolError(error="user_not_found", detail=str(exc), user_id=user_id)

    limit = auto_approve_limit()
    summary = (
        f"User {user.user_id} is {user.tier}. Automated refunds are permitted up "
        f"to ${limit:.2f}; anything above requires human approval."
    )
    audit_log.record(
        tool="lookup_user_policy", arguments={"user_id": user_id},
        result_status="success", user_id=user_id,
    )
    return PolicyResult(user_id=user.user_id, summary=summary, auto_approve_limit=limit)


def execute_refund(
    user_id: str, amount: float, idempotency_key: str | None = None
) -> RefundResult | ToolError:
    """Execute a refund under deterministic governance.

    - Unknown user or non-positive amount -> structured ``ToolError``.
    - Amount over the auto-approve limit -> ``requires_human_auditor`` (routed to
      the human-in-the-loop auditor in M5; not executed here).
    - Otherwise -> ``success`` with a transaction id.

    ``idempotency_key`` is accepted as a dedupe seam; full dedupe enforcement
    lands with the durable approval flow in M5.
    """
    args = {"user_id": user_id, "amount": amount, "idempotency_key": idempotency_key}

    if amount <= 0:
        audit_log.record(
            tool="execute_refund", arguments=args, result_status="rejected", user_id=user_id
        )
        return ToolError(
            error="invalid_amount", detail="Refund amount must be positive.", user_id=user_id
        )

    try:
        get_user(user_id)
    except UserNotFoundError as exc:
        audit_log.record(
            tool="execute_refund", arguments=args, result_status="not_found", user_id=user_id
        )
        return ToolError(error="user_not_found", detail=str(exc), user_id=user_id)

    if refund_requires_approval(amount):
        audit_log.record(
            tool="execute_refund", arguments=args,
            result_status="requires_human_auditor", user_id=user_id,
        )
        return RefundResult(
            status="requires_human_auditor",
            user_id=user_id,
            amount=amount,
            limit=auto_approve_limit(),
            reason="Amount exceeds auto-approve limit; human approval required.",
        )

    txn_id = f"txn_{datetime.now(UTC).timestamp()}"
    audit_log.record(
        tool="execute_refund", arguments=args, result_status="success", user_id=user_id
    )
    return RefundResult(status="success", user_id=user_id, amount=amount, transaction_id=txn_id)
