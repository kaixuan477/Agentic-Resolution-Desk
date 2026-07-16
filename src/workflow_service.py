"""Application service that drives the compiled workflow.

Encapsulates all interaction with the LangGraph app — submitting a ticket,
listing suspended workflows, and resuming one with a human decision — behind a
small, testable surface. It is constructed with an already-compiled graph, so
tests inject an in-memory-saver graph and production injects the durable
Postgres-backed one; the service itself is storage-agnostic.
"""

from __future__ import annotations

import uuid
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import BaseModel, Field

from src.state import ApprovalDecision

_AUDITOR = "auditor"


class WorkflowSnapshot(BaseModel):
    """A serializable view of a workflow's current state."""

    thread_id: str
    status: str  # "resolved" | "awaiting_approval"
    current_assignee: str
    requires_approval: bool
    messages: list[str] = Field(default_factory=list)

    # Details of the action awaiting approval (present when suspended).
    proposed_tool: str | None = None
    proposed_user_id: str | None = None
    proposed_amount: float | None = None


class WorkflowService:
    """Coordinates ticket submission and human-in-the-loop approvals."""

    def __init__(self, app: Any) -> None:
        self._app = app
        # Threads currently suspended awaiting a human decision. Tracked here for
        # a fast /pending listing; the authoritative state lives in the
        # checkpointer, which survives restarts.
        self._pending: set[str] = set()

    # -- public API -------------------------------------------------------- #
    def submit(self, message: str, thread_id: str | None = None) -> WorkflowSnapshot:
        """Ingest a ticket and run the graph to completion or first suspension."""
        thread_id = thread_id or uuid.uuid4().hex
        config = self._config(thread_id)
        self._app.invoke({"messages": [HumanMessage(content=message)]}, config)
        return self._snapshot(thread_id)

    def resume(self, thread_id: str, decision: ApprovalDecision) -> WorkflowSnapshot:
        """Record a human decision and resume a suspended workflow."""
        config = self._config(thread_id)
        self._app.update_state(config, {"approval_decision": decision})
        self._app.invoke(None, config)  # resume from the auditor interrupt
        return self._snapshot(thread_id)

    def pending(self) -> list[str]:
        """Thread ids currently awaiting human approval."""
        return sorted(self._pending)

    def get(self, thread_id: str) -> WorkflowSnapshot:
        """Return the current snapshot for a single workflow."""
        return self._snapshot(thread_id)

    def pending_details(self) -> list[WorkflowSnapshot]:
        """Snapshots for every workflow currently awaiting approval."""
        return [self._snapshot(tid) for tid in self.pending()]

    # -- internals --------------------------------------------------------- #
    @staticmethod
    def _config(thread_id: str) -> dict[str, Any]:
        return {"configurable": {"thread_id": thread_id}}

    @staticmethod
    def _proposed_fields(proposed: Any) -> tuple[str | None, str | None, float | None]:
        """Extract (tool, user_id, amount) from a ProposedAction (model or dict)."""
        if proposed is None:
            return None, None, None
        if isinstance(proposed, dict):
            tool = proposed.get("tool")
            args = proposed.get("arguments", {})
        else:  # pydantic ProposedAction
            tool = getattr(proposed, "tool", None)
            args = getattr(proposed, "arguments", {})
        user_id = args.get("user_id") if isinstance(args, dict) else None
        amount = args.get("amount") if isinstance(args, dict) else None
        return (
            str(tool) if tool is not None else None,
            str(user_id) if user_id is not None else None,
            float(amount) if amount is not None else None,
        )

    def _snapshot(self, thread_id: str) -> WorkflowSnapshot:
        state = self._app.get_state(self._config(thread_id))
        values = state.values
        next_nodes = tuple(state.next)
        awaiting = _AUDITOR in next_nodes

        if awaiting:
            self._pending.add(thread_id)
        else:
            self._pending.discard(thread_id)

        messages = [
            str(m.content) for m in values.get("messages", []) if isinstance(m, BaseMessage)
        ]
        tool, user_id, amount = self._proposed_fields(values.get("proposed_action"))
        return WorkflowSnapshot(
            thread_id=thread_id,
            status="awaiting_approval" if awaiting else "resolved",
            current_assignee=str(values.get("current_assignee", "supervisor")),
            requires_approval=awaiting,
            messages=messages,
            proposed_tool=tool,
            proposed_user_id=user_id,
            proposed_amount=amount,
        )
