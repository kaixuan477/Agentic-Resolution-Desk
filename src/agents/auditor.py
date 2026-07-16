"""Auditor node — the human-in-the-loop approval gate.

The graph is compiled with ``interrupt_before=["auditor"]``, so execution
suspends *before* this node runs whenever the billing worker escalates a
high-value refund. A human then submits an ``approved`` / ``denied`` decision
(via the API), which is written into state, and the graph is resumed — at which
point this node runs and acts on the decision.

Governance is deterministic: this node never decides *whether* to refund; it only
executes the human's recorded decision. Approved refunds are finalized through
``execute_approved_refund`` (which bypasses the auto-approve limit precisely
because a human has approved), while denials move no money.
"""

from __future__ import annotations

from typing import Any, Protocol

from langchain_core.messages import AIMessage

from src.mcp_server.models import RefundResult
from src.mcp_server.tools_impl import execute_approved_refund
from src.state import ResolutionState


class RefundExecutor(Protocol):
    """Finalizes an already-approved refund."""

    def __call__(self, user_id: str, amount: float) -> RefundResult: ...


def auditor_node(
    state: ResolutionState,
    refund_executor: RefundExecutor | None = None,
) -> dict[str, Any]:
    """Apply the human reviewer's decision to the proposed action."""
    executor = refund_executor or execute_approved_refund
    decision = state.approval_decision
    action = state.proposed_action

    if decision == "approved" and action is not None:
        user_id = str(action.arguments["user_id"])
        amount = float(action.arguments["amount"])
        result = executor(user_id=user_id, amount=amount)
        return {
            "messages": [AIMessage(
                content=(
                    f"Approved by reviewer — refund of ${amount:.2f} processed. "
                    f"Reference: {result.transaction_id}."
                )
            )],
            "requires_approval": False,
            "current_assignee": "auditor",
        }

    if decision == "denied":
        return {
            "messages": [AIMessage(
                content="A reviewer declined this refund; no funds were moved."
            )],
            "requires_approval": False,
            "current_assignee": "auditor",
        }

    # Reached only if resumed without a recorded decision; leave state untouched.
    return {"current_assignee": "auditor"}
