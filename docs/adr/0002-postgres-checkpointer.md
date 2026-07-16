# ADR 0002 — PostgreSQL Checkpointer for Durable State

- **Status:** Accepted
- **Date:** 2026-07-15

## Context

Workflows can suspend for human approval (potentially minutes to hours) and must
survive process crashes and restarts without losing context or re-executing side
effects (e.g. issuing a refund twice).

## Decision

Use LangGraph's **`PostgresSaver`** checkpointer over a connection pool. Graph
state is serialized to PostgreSQL after each node, enabling:

- Resumption from the exact failed/suspended step.
- Human-in-the-loop suspension via `interrupt_before` that outlives the request.
- Time-travel debugging of a thread's state history.

## Consequences

- **+** Fault tolerance: a crash mid-refund resumes; it does not restart/rebill.
- **+** Durable suspension is a prerequisite for asynchronous human approval.
- **+** One datastore also hosts pgvector and the audit trail.
- **−** Requires a running Postgres instance (provided via Docker Compose) and
  `checkpointer.setup()` on startup.

## Alternatives considered

- **In-memory checkpointer** — rejected: state lost on restart; cannot support
  long-lived human approvals.
- **Redis checkpointer** — viable, but Postgres is already required for pgvector
  and the audit log, so consolidating reduces infrastructure.
