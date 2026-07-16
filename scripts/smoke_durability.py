"""Durability smoke test (manual / requires a live database).

Proves the core durability claim end-to-end:
  1. Invoke the graph on a fresh thread; state is checkpointed to Postgres.
  2. Tear everything down (new pool + checkpointer).
  3. Read the state back and confirm the conversation survived.

Usage:
    python -m scripts.smoke_durability
"""

from __future__ import annotations

import sys
import uuid

from langchain_core.messages import HumanMessage

from src.graph import compiled_app


def main() -> int:
    thread_id = f"smoke-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}
    print(f"Thread: {thread_id}")

    try:
        with compiled_app() as app:
            app.invoke(  # type: ignore[attr-defined]
                {"messages": [HumanMessage(content="how do I reset my password?")]},
                config,
            )
        print("Wrote state; reopening a fresh app to verify persistence...")

        with compiled_app() as app:
            snapshot = app.get_state(config)  # type: ignore[attr-defined]
            messages = snapshot.values.get("messages", [])
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"Smoke test failed (is DATABASE_URL reachable?): {exc}", file=sys.stderr)
        return 1

    if messages:
        print(f"OK — recovered {len(messages)} message(s) from a new process/pool.")
        return 0
    print("FAIL — no state recovered.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
