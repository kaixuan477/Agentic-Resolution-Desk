# ADR 0001 — Supervisor/Worker Multi-Agent Architecture

- **Status:** Accepted
- **Date:** 2026-07-15

## Context

The system must handle heterogeneous support requests (billing vs. how-to) that
require different tools, different privileges, and different risk profiles. A
single monolithic agent with every tool bound to it is hard to constrain, prone
to using the wrong tool, expensive (large prompts), and impossible to reason
about for least-privilege security.

## Decision

Adopt a **supervisor/worker** topology:

- A **supervisor** node classifies intent and routes — it holds **no tools**.
- **Worker** nodes (Billing, Support) are narrow specialists, each bound only to
  the tools their role requires.
- An **auditor** node gates high-value actions for human approval.

We use the industry-standard term "supervisor/worker" and deliberately avoid
invented acronyms in code, docs, and interviews.

## Consequences

- **+** Least privilege is enforceable per worker (Support cannot issue refunds).
- **+** Smaller, role-specific prompts reduce token cost and latency.
- **+** Routing is a deterministic, testable decision.
- **−** More moving parts than a single agent; mitigated by LangGraph's explicit
  graph structure and topology tests.

## Alternatives considered

- **Single ReAct agent with all tools** — rejected: weak privilege boundaries,
  higher cost, harder to test.
- **Hardcoded rules-only router (no LLM)** — rejected: too brittle for natural
  language; we instead constrain the LLM with structured output.
