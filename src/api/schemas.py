"""API request/response schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TicketRequest(BaseModel):
    """Inbound support ticket."""

    message: str = Field(..., description="Natural-language customer request")
    thread_id: str | None = Field(
        default=None,
        description="Optional existing workflow thread id; a new one is created if omitted.",
    )


class TicketResponse(BaseModel):
    """Result of invoking (or suspending) a workflow."""

    thread_id: str
    status: str
    current_assignee: str
    requires_approval: bool
    messages: list[str] = Field(default_factory=list)


class ApprovalRequest(BaseModel):
    """Human decision on a suspended high-value action."""

    thread_id: str
    decision: Literal["approved", "denied"] = Field(
        ..., description="Reviewer's decision on the escalated refund."
    )


class HealthResponse(BaseModel):
    status: str
    version: str
