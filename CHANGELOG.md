# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **M2 — MCP tool server hardening & audit foundation**
  - Central deterministic governance policy (`src/policy.py`) as the single
    source of truth for the refund auto-approve threshold.
  - In-memory mock CRM datastore with VIP / standard / unknown users
    (`src/mcp_server/mock_crm.py`), including an explicit not-found path.
  - Typed Pydantic tool contracts and a structured error envelope
    (`src/mcp_server/models.py`).
  - Append-only audit logger with recursive PII redaction and email masking
    (`src/audit/logger.py`); every tool call is now recorded.
  - `execute_refund` accepts an `idempotency_key` dedupe seam and validates
    non-positive amounts.
  - Expanded tests: policy boundaries, audit/redaction, and tool valid/invalid/
    unknown/boundary cases (26 tests total).
  - ADR 0005 — typed tool contracts, structured errors, and audit trail.

### Changed
- MCP tools now return validated Pydantic models instead of raw dicts.

- **M1 — Foundations & infra**

  - Repository scaffold with `src/` layout and packaged modules.
  - Centralized environment-driven configuration (`src/config.py`).
  - Strict Pydantic v2 workflow state schema (`src/state.py`).
  - LangGraph topology with supervisor / billing / support / auditor nodes,
    conditional routing, and `interrupt_before` auditor gate (`src/graph.py`).
  - PostgreSQL checkpointer wiring for durable, resumable workflows.
  - Sandboxed MCP tool server with mocked CRM/billing tools and a deterministic
    refund-approval policy (`src/mcp_server/server.py`).
  - Provider-abstracted LLM client (`src/llm/client.py`).
  - FastAPI surface with health check and stubbed ticket/approval endpoints.
  - Docker Compose stack (pgvector Postgres, MCP server, API) + Dockerfile.
  - CI workflow: ruff lint, mypy type check, pytest.
  - Smoke tests for state schema, graph topology, and MCP tools.
  - Architecture Decision Records 0001–0004.

[Unreleased]: https://github.com/kaixuan477/Agentic-Resolution-Desk/commits/main
