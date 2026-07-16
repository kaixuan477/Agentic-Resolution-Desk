"""Integration tests that require a live Postgres checkpointer.

Skipped automatically when ``DATABASE_URL`` is unset or unreachable, so CI stays
green offline while these still run in a provisioned environment. They prove the
durability claim: state written by one compiled app is readable afterwards.
"""

from __future__ import annotations

import os

import pytest
from langchain_core.messages import HumanMessage

from src.graph import compiled_app

pytestmark = pytest.mark.integration


def _db_reachable() -> bool:
    url = os.getenv("DATABASE_URL")
    if not url:
        return False
    try:
        import psycopg

        with psycopg.connect(url, connect_timeout=2):
            return True
    except Exception:
        return False


requires_db = pytest.mark.skipif(not _db_reachable(), reason="No reachable DATABASE_URL")


@requires_db
def test_state_persists_across_invocations() -> None:
    thread_id = "integration-test-thread"
    config = {"configurable": {"thread_id": thread_id}}

    with compiled_app() as app:
        app.invoke(  # type: ignore[attr-defined]
            {"messages": [HumanMessage(content="how do I reset my password?")]},
            config,
        )

    # A fresh compiled app (new pool/checkpointer) must see the persisted state.
    with compiled_app() as app:
        snapshot = app.get_state(config)  # type: ignore[attr-defined]
        assert snapshot.values["messages"]
