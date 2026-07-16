# ADR 0005 — Typed Tool Contracts, Structured Errors, and Audit Trail

- **Status:** Accepted
- **Date:** 2026-07-16

## Context

In M1 the MCP tools returned raw dictionaries and signaled problems implicitly.
As the security boundary between the LLM and business systems, the tool layer
needs stable schemas, explicit error handling, and a tamper-evident record of
every action for governance and debugging.

## Decision

1. **Typed contracts** — every tool returns a validated Pydantic model
   (`UserProfile`, `AccountBalance`, `PolicyResult`, `RefundResult`).
2. **Structured errors** — failures return a `ToolError` envelope rather than
   raising across the boundary or returning `None`, so agents can reason about
   outcomes deterministically.
3. **Central policy** — the refund approval threshold lives in `src/policy.py`,
   referenced by both the tool layer and (from M5) the auditor node, so the rule
   cannot drift between components.
4. **Audit trail** — an append-only `AuditLog` records every tool call with PII
   redaction (email masking, sensitive-key masking).

## Consequences

- **+** Self-documenting, type-checked tool surface (mypy strict passes).
- **+** Governance decisions are deterministic and single-sourced.
- **+** Every action is auditable with PII protected — seeds the guardrails and
  RBAC/audit roadmap items.
- **−** More types and boilerplate than raw dicts; justified by safety and
  testability at the security boundary.

## Alternatives considered

- **Raw dicts + exceptions** — rejected: implicit schemas, harder for agents to
  handle failures, no audit guarantees.
- **Deferring audit to M5** — rejected: recording from the first hardened tool
  layer is cheaper than retrofitting and strengthens the governance narrative
  early.

## Notes

The audit sink is in-memory plus structured application logs in M2. A
Postgres-backed audit table is introduced alongside the durable
human-in-the-loop flow (M5), reusing the same `AuditLog.record` interface.
