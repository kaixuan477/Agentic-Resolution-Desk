"""Strict, typed workflow state shared across all graph nodes.

Using Pydantic v2 (not a bare ``TypedDict``) gives us validation at every
agent handoff, which prevents silent context-loss bugs as the state flows
between the supervisor, workers, and the auditor.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

Assignee = Literal["supervisor", "billing", "support", "auditor"]
Intent = Literal["billing", "support", "unknown"]
ApprovalDecision = Literal["pending", "approved", "denied"]


class ProposedAction(BaseModel):
    """A tool invocation a worker wants to perform, pending governance checks."""

    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False


class ResolutionState(BaseModel):
    """The single, durable state object for a resolution workflow.

    ``messages`` uses the ``add_messages`` reducer so nodes append to the
    conversation rather than overwriting it.
    """

    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)

    # Which node currently "has the ball".
    current_assignee: Assignee = "supervisor"

    # Extracted / classified context.
    intent: Intent = "unknown"
    extracted_user_id: str | None = None

    # Governance.
    proposed_action: ProposedAction | None = None
    requires_approval: bool = False
    approval_decision: ApprovalDecision | None = None

    # Append-only audit trail of every tool call and decision.
    audit_trail: list[dict[str, Any]] = Field(default_factory=list)

    model_config = {"arbitrary_types_allowed": True}
