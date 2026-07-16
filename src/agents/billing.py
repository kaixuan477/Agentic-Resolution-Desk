"""Billing worker.

A narrow specialist that resolves money-related requests. By design it has
access **only** to the billing tools (`execute_refund`, `lookup_user`) — it
cannot answer support questions or reach the policy corpus. This enforces the
least-privilege boundary described in ADR 0001.

The worker is deterministic and fully testable: it extracts the refund amount
from the request, calls the refund tool, and translates the typed result into
state updates. When the tool signals that human approval is required, the worker
records a ``proposed_action`` and hands off to the auditor node (M5 suspends
there via ``interrupt_before``).
"""

from __future__ import annotations

import re
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from src.mcp_server.models import RefundResult, ToolError
from src.mcp_server.tools_impl import execute_refund
from src.state import ProposedAction, ResolutionState

# Matches "$100", "100.50", "100 dollars".
_AMOUNT_RE = re.compile(r"\$?\s*(\d+(?:\.\d{1,2})?)")


def extract_amount(text: str) -> float | None:
    """Extract the first monetary amount mentioned in the text."""
    match = _AMOUNT_RE.search(text)
    return float(match.group(1)) if match else None


def _latest_user_text(state: ResolutionState) -> str:
    for message in reversed(state.messages):
        if isinstance(message, HumanMessage):
            return str(message.content)
    return ""


def billing_node(state: ResolutionState) -> dict[str, Any]:
    """Resolve a billing request through the sandboxed refund tool."""
    text = _latest_user_text(state)
    user_id = state.extracted_user_id
    amount = extract_amount(text)

    if user_id is None:
        return {
            "messages": [AIMessage(content="I could not identify your account id. "
                                           "Please provide it (e.g. VIP-01).")],
            "current_assignee": "billing",
        }
    if amount is None:
        return {
            "messages": [AIMessage(content="How much would you like refunded?")],
            "current_assignee": "billing",
        }

    result = execute_refund(user_id=user_id, amount=amount)

    if isinstance(result, ToolError):
        return {
            "messages": [AIMessage(content=f"I couldn't process that: {result.detail}")],
            "current_assignee": "billing",
        }

    assert isinstance(result, RefundResult)

    if result.status == "requires_human_auditor":
        return {
            "messages": [AIMessage(
                content=(
                    f"A refund of ${amount:.2f} exceeds the automated limit and "
                    "needs manager approval. I've escalated it."
                )
            )],
            "proposed_action": ProposedAction(
                tool="execute_refund",
                arguments={"user_id": user_id, "amount": amount},
                requires_approval=True,
            ),
            "requires_approval": True,
            "current_assignee": "auditor",
        }

    return {
        "messages": [AIMessage(
            content=(
                f"Done — I've refunded ${amount:.2f} to {user_id}. "
                f"Reference: {result.transaction_id}."
            )
        )],
        "current_assignee": "billing",
    }
