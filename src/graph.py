"""LangGraph wiring: nodes, conditional routing, and the Postgres checkpointer.

M1 scope: the graph compiles and persists state durably. Node bodies are
minimal placeholders that will be fleshed out in M3–M5 (routing, workers,
human-in-the-loop). The structure — entry point, conditional edges, and the
``interrupt_before`` auditor gate — is already in place so later milestones
only fill in behavior, not plumbing.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, StateGraph
from psycopg_pool import ConnectionPool

from src.config import get_settings
from src.state import ResolutionState


# --------------------------------------------------------------------------- #
# Node placeholders (behavior arrives in later milestones).
# --------------------------------------------------------------------------- #
def supervisor_node(state: ResolutionState) -> dict[str, Any]:
    """Triage/routing node. M3 will add structured-output intent classification."""
    return {"current_assignee": state.current_assignee}


def billing_node(state: ResolutionState) -> dict[str, Any]:
    """Billing worker. M4 binds MCP tools; M5 wires the approval gate."""
    return {"current_assignee": "billing"}


def support_node(state: ResolutionState) -> dict[str, Any]:
    """Support worker. M4 binds the pgvector RAG retriever."""
    return {"current_assignee": "support"}


def auditor_node(state: ResolutionState) -> dict[str, Any]:
    """Human-in-the-loop approval gate. Suspended via ``interrupt_before`` in M5."""
    return {"current_assignee": "auditor"}


# --------------------------------------------------------------------------- #
# Routing.
# --------------------------------------------------------------------------- #
def route_from_supervisor(state: ResolutionState) -> str:
    """Deterministic edge selection based on the supervisor's classified intent."""
    if state.intent == "billing":
        return "billing"
    if state.intent == "support":
        return "support"
    return END


def build_workflow() -> StateGraph:
    """Assemble the graph topology (uncompiled)."""
    workflow = StateGraph(ResolutionState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("billing", billing_node)
    workflow.add_node("support", support_node)
    workflow.add_node("auditor", auditor_node)

    workflow.set_entry_point("supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {"billing": "billing", "support": "support", END: END},
    )
    # Billing may escalate to the auditor for high-value actions (M5).
    workflow.add_edge("billing", "auditor")
    workflow.add_edge("support", END)
    workflow.add_edge("auditor", END)

    return workflow


@contextmanager
def compiled_app() -> Iterator[object]:
    """Yield a compiled graph backed by a durable Postgres checkpointer.

    The connection pool and checkpointer tables are created on entry. The
    ``interrupt_before=["auditor"]`` clause is what lets the graph suspend and
    later resume for human approval.
    """
    settings = get_settings()
    pool = ConnectionPool(conninfo=settings.database_url, max_size=10, open=True)
    try:
        checkpointer = PostgresSaver(pool)  # type: ignore[arg-type]
        checkpointer.setup()  # idempotent; creates checkpoint tables if absent
        app = build_workflow().compile(
            checkpointer=checkpointer,
            interrupt_before=["auditor"],
        )
        yield app
    finally:
        pool.close()
