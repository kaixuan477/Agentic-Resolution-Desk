# ADR 0003 — MCP Tool Server as the Security Boundary

- **Status:** Accepted
- **Date:** 2026-07-15

## Context

Agents must perform real actions (CRM lookups, refunds) without ever holding API
keys or database handles in their prompts/context, where they could be leaked or
abused via prompt injection.

## Decision

Expose all backend capabilities through a **Model Context Protocol (MCP)** server
(`fastmcp`). Agents call standardized tools; the server owns credentials and
enforces deterministic policy (e.g. refunds above the configured limit return a
`requires_human_auditor` flag rather than executing).

## Consequences

- **+** Clear security boundary; LLM reasoning is decoupled from execution.
- **+** Governance (approval thresholds) lives in code, not model judgment.
- **+** Tools are unit-testable as pure functions and reusable across agents.
- **−** An extra service to run; justified by the isolation and standardization.

## Alternatives considered

- **Direct SDK calls from agent code** — rejected: couples LLM layer to backends
  and risks credential exposure in agent context.
- **Custom REST glue per integration** — rejected: non-standard, more bespoke
  code; MCP gives a uniform tool interface.
