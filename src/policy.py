"""Deterministic business-governance policy.

Single source of truth for governance decisions that must **not** be delegated to
the LLM. Both the MCP tool layer and (from M5) the auditor node reference these
functions so the approval rule can never drift between components.
"""

from __future__ import annotations

from src.config import get_settings


def refund_requires_approval(amount: float) -> bool:
    """Return True if a refund amount must be escalated to a human.

    Amounts strictly greater than the configured auto-approve limit require
    approval. The boundary (``amount == limit``) is auto-approved.
    """
    limit = get_settings().refund_auto_approve_limit
    return amount > limit


def auto_approve_limit() -> float:
    """Expose the current auto-approve limit (for messaging and tests)."""
    return get_settings().refund_auto_approve_limit
