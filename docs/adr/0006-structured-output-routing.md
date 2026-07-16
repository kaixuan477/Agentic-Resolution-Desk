# ADR 0006 — Structured-Output Routing for the Supervisor

- **Status:** Accepted
- **Date:** 2026-07-16

## Context

The supervisor makes the system's most safety-critical decision: which worker
handles a ticket. Parsing this from free-form LLM text is brittle (formatting
drift, hallucinated routes) and hard to test deterministically.

## Decision

Constrain the supervisor LLM with **structured output** bound to a Pydantic
`RoutingDecision` (`intent`, `user_id`, `reasoning`). The classifier is injected
via a `StructuredRouter` protocol, so:

- Production uses `ChatOpenAI(...).with_structured_output(RoutingDecision)`.
- Tests inject a deterministic fake and run fully offline.

A regex `extract_user_id` provides a deterministic cross-check/fallback when the
model omits the id.

## Consequences

- **+** Routing is a typed, validated contract — no fragile text parsing.
- **+** Fully offline, zero-cost routing regression tests via the injected fake.
- **+** Clear separation: the supervisor holds no tools and only decides a route.
- **−** Structured output constrains prompt flexibility slightly; acceptable for
  a classification task.

## Alternatives considered

- **Free-text + keyword parsing** — rejected: brittle and non-deterministic.
- **Rules-only router (no LLM)** — rejected: too rigid for natural language;
  the regex remains only as a fallback for id extraction.
