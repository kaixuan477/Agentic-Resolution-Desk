"""FastAPI surface for the Resolution Desk.

Exposes the human-in-the-loop workflow: submit a ticket (`POST /tickets`), list
workflows suspended awaiting approval (`GET /pending`), and resume one with a
reviewer decision (`POST /approve`). All graph interaction is delegated to a
``WorkflowService`` resolved via dependency injection, so tests supply an
in-memory-saver service and production supplies the durable Postgres-backed one.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from src.api.schemas import (
    ApprovalRequest,
    HealthResponse,
    TicketRequest,
    TicketResponse,
)
from src.workflow_service import WorkflowService, WorkflowSnapshot

logger = logging.getLogger(__name__)

# Process-wide service, initialized at startup when a database is reachable.
_service: WorkflowService | None = None


def set_service(service: WorkflowService | None) -> None:
    """Install the process-wide workflow service (used by startup and tests)."""
    global _service
    _service = service


def get_service() -> WorkflowService:
    """Dependency that yields the active workflow service or 503 if unavailable."""
    if _service is None:
        raise HTTPException(
            status_code=503,
            detail="Workflow service unavailable (no database configured).",
        )
    return _service


ServiceDep = Annotated[WorkflowService, Depends(get_service)]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Build a durable Postgres-backed service on startup, if reachable.

    Failure to connect is non-fatal: the health probe still works and the
    workflow endpoints return 503 until a database is available.
    """
    with suppress(Exception):
        from src.graph import compiled_app

        graph_app = compiled_app().__enter__()
        set_service(WorkflowService(graph_app))
        logger.info("Workflow service initialized with Postgres checkpointer.")
    yield
    set_service(None)


app = FastAPI(
    title="Enterprise Resolution Desk",
    version="1.0.0",
    description="Supervisor/worker agents with sandboxed tools and human-in-the-loop governance.",
    lifespan=lifespan,
)


def _to_response(snapshot: WorkflowSnapshot) -> TicketResponse:
    return TicketResponse(
        thread_id=snapshot.thread_id,
        status=snapshot.status,
        current_assignee=snapshot.current_assignee,
        requires_approval=snapshot.requires_approval,
        messages=snapshot.messages,
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness probe."""
    return HealthResponse(status="ok", version=app.version)


@app.post("/tickets", response_model=TicketResponse)
def create_ticket(request: TicketRequest, service: ServiceDep) -> TicketResponse:
    """Ingest a ticket and run the workflow to completion or first suspension."""
    snapshot = service.submit(request.message, request.thread_id)
    return _to_response(snapshot)


@app.get("/pending")
def list_pending(service: ServiceDep) -> dict[str, list[str]]:
    """List workflows suspended awaiting human approval."""
    return {"pending": service.pending()}


@app.get("/pending/details", response_model=list[WorkflowSnapshot])
def list_pending_details(service: ServiceDep) -> list[WorkflowSnapshot]:
    """Full snapshots (incl. proposed action) for every pending workflow."""
    return service.pending_details()


@app.get("/workflows/{thread_id}", response_model=WorkflowSnapshot)
def get_workflow(thread_id: str, service: ServiceDep) -> WorkflowSnapshot:
    """Return the current snapshot for a single workflow."""
    return service.get(thread_id)


@app.post("/approve", response_model=TicketResponse)
def approve(request: ApprovalRequest, service: ServiceDep) -> TicketResponse:
    """Resume a suspended workflow with a human decision."""
    snapshot = service.resume(request.thread_id, request.decision)
    return _to_response(snapshot)


# Server-rendered reviewer dashboard (no SPA build step). Served at /dashboard/.
_STATIC_DIR = Path(__file__).parent / "static"
app.mount("/dashboard", StaticFiles(directory=_STATIC_DIR, html=True), name="dashboard")
