"""FastAPI surface for the Resolution Desk.

M1 exposes a health check and stub endpoints so the service boots and the
contract is defined. The ticket-ingest and approval flows are wired to the
compiled graph in M5–M6.
"""

from __future__ import annotations

from fastapi import FastAPI

from src.api.schemas import (
    ApprovalRequest,
    HealthResponse,
    TicketRequest,
    TicketResponse,
)

app = FastAPI(
    title="Enterprise Resolution Desk",
    version="1.0.0",
    description="Supervisor/worker agents with sandboxed tools and human-in-the-loop governance.",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness probe."""
    return HealthResponse(status="ok", version=app.version)


@app.post("/tickets", response_model=TicketResponse)
def create_ticket(request: TicketRequest) -> TicketResponse:
    """Ingest a ticket and invoke the resolution workflow.

    M5 wires this to ``compiled_app`` and streams the graph to completion or to
    the first ``interrupt_before`` suspension.
    """
    thread_id = request.thread_id or "pending-thread"
    return TicketResponse(
        thread_id=thread_id,
        status="not_implemented",
        current_assignee="supervisor",
        requires_approval=False,
        messages=["M1 scaffold: graph invocation lands in M5."],
    )


@app.get("/pending")
def list_pending() -> dict[str, list[str]]:
    """List workflows suspended awaiting human approval (M5)."""
    return {"pending": []}


@app.post("/approve", response_model=TicketResponse)
def approve(request: ApprovalRequest) -> TicketResponse:
    """Resume a suspended workflow with a human decision (M5)."""
    return TicketResponse(
        thread_id=request.thread_id,
        status="not_implemented",
        current_assignee="auditor",
        requires_approval=True,
        messages=[f"M1 scaffold: resume with decision '{request.decision}' lands in M5."],
    )
