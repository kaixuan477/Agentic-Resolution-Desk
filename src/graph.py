"""LangGraph wiring: nodes, conditional routing, and the Postgres checkpointer.

The topology — entry point, conditional edges, and the ``interrupt_before``
auditor gate — establishes durable, resumable multi-agent execution. All node
bodies are real as of M5 (routing, workers, and the human-in-the-loop auditor).
The checkpointer is injectable so the whole workflow runs and is tested offline
with an in-memory saver, while production uses durable Postgres.
"""

from __future__ import annotations

import functools
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, StateGraph
from psycopg_pool import ConnectionPool

from src.agents.auditor import auditor_node
from src.agents.billing import billing_node
from src.agents.supervisor import StructuredRouter, supervisor_node
from src.agents.support import support_node
from src.config import get_settings
from src.state import ResolutionState


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


def route_from_billing(state: ResolutionState) -> str:
    """Escalate to the auditor only when human approval is required."""
    return "auditor" if state.requires_approval else END


def build_workflow(router: StructuredRouter | None = None) -> StateGraph:
    """Assemble the graph topology (uncompiled).

    An optional ``router`` is bound to the supervisor node so tests can run the
    whole graph offline with a deterministic classifier; production leaves it
    ``None`` and the supervisor uses the LLM.
    """
    workflow = StateGraph(ResolutionState)

    supervisor = (
        functools.partial(supervisor_node, router=router)
        if router is not None
        else supervisor_node
    )
    workflow.add_node("supervisor", supervisor)
    workflow.add_node("billing", billing_node)
    workflow.add_node("support", support_node)
    workflow.add_node("auditor", auditor_node)

    workflow.set_entry_point("supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {"billing": "billing", "support": "support", END: END},
    )
    # Billing escalates to the auditor only for high-value actions; otherwise ends.
    workflow.add_conditional_edges(
        "billing",
        route_from_billing,
        {"auditor": "auditor", END: END},
    )
    workflow.add_edge("support", END)
    workflow.add_edge("auditor", END)

    return workflow


def compile_workflow(checkpointer: Any, router: StructuredRouter | None = None) -> Any:
    """Compile the graph against any LangGraph checkpointer.

    Kept separate from ``compiled_app`` so tests and the API can supply an
    in-memory saver (offline) while production supplies durable Postgres. The
    ``interrupt_before=["auditor"]`` clause is what suspends execution for human
    approval.
    """
    return build_workflow(router=router).compile(
        checkpointer=checkpointer,
        interrupt_before=["auditor"],
    )


@contextmanager
def compiled_app() -> Iterator[object]:
    """Yield a compiled graph backed by a durable Postgres checkpointer.

    The connection pool and checkpointer tables are created on entry. The
    ``interrupt_before=["auditor"]`` clause is what lets the graph suspend and
    later resume for human approval.
    """
    settings = get_settings()
    pool = ConnectionPool(
        conninfo=settings.database_url,
        max_size=10,
        open=True,
        kwargs={"autocommit": True},  # required for setup()'s CREATE INDEX CONCURRENTLY
    )
    try:
        checkpointer = PostgresSaver(pool)  # type: ignore[arg-type]
        checkpointer.setup()  # idempotent; creates checkpoint tables if absent
        app = compile_workflow(checkpointer)
        yield app
    finally:
        pool.close()
