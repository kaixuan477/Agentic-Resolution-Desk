# 8. Human-in-the-loop approval via interrupt/resume

Date: 2026

## Status

Accepted

## Context

High-value refunds must not be executed by an autonomous agent. A human reviewer
has to approve them first. The system also needs to survive process restarts
between the moment a refund is escalated and the moment a human decides —
possibly minutes or hours later — without losing context.

We also need the entire approval flow to be testable offline (no database, no
LLM, no API cost) so it runs in CI on every push.

## Decision

- **Interrupt/resume, not polling.** The graph is compiled with
  `interrupt_before=["auditor"]`. When the billing worker escalates, execution
  suspends *before* the auditor node and the checkpointer persists the full
  state. A human decision is written via `update_state`, then the graph is
  resumed; only then does the auditor node run and act on the decision.
- **Deterministic auditor.** The auditor node never decides *whether* to refund;
  it executes the human's recorded decision. Approved refunds are finalized with
  `execute_approved_refund` (audited as `success_after_approval`); denials move
  no money.
- **Injectable checkpointer.** `compile_workflow(checkpointer, router)` lets the
  same graph run on an in-memory saver (tests/CI) or durable Postgres
  (production). Combined with the injectable supervisor router, the full
  submit → suspend → approve/deny flow is exercised offline.
- **`WorkflowService` boundary.** All graph interaction (submit / pending /
  resume) sits behind one service, which the API consumes via dependency
  injection. Tests inject an in-memory service; production injects the
  Postgres-backed one built at startup.

## Consequences

- Governance is enforced structurally: an over-limit refund cannot execute
  without a persisted human decision.
- State survives restarts; a reviewer can approve long after escalation.
- The complete human-in-the-loop path is covered by fast, free CI tests.
- `/pending` is tracked in-process for fast listing; the authoritative suspended
  state lives in the checkpointer. A future multi-replica deployment would query
  the checkpointer directly instead (noted for M6/scale-out).
