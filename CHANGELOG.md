# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **M4 — Worker agents & pgvector RAG**
  - Billing worker (`src/agents/billing.py`): deterministic money specialist that
    extracts the refund amount, calls the sandboxed `execute_refund` tool, and
    escalates over-limit refunds to the auditor with a typed `ProposedAction`.
  - Support worker (`src/agents/support.py`): RAG specialist answering policy
    questions; holds only the retriever (no refund capability — least privilege).
  - Policy corpus (`src/rag/policies.py`) and a `PolicyRetriever` protocol with
    two implementations: `InMemoryRetriever` (offline lexical) and
    `PgVectorRetriever` (production, lazy-imported).
  - Injectable `Answerer` (extractive offline / LLM in production) so the whole
    workflow runs and is tested with no network, database, or API key.
  - pgvector ingestion (`src/rag/ingest.py`) + `scripts/seed_policies.py` CLI.
  - Tool bodies refactored into pure `src/mcp_server/tools_impl.py`; `server.py`
    now only registers them over MCP, so workers import tools with least
    privilege.
  - Real billing/support nodes wired into the graph, replacing placeholders;
    billing→auditor is now conditional on `requires_approval`.
  - Integration seam (`tests/test_integration.py`, skip-if-no-DB) and durability
    smoke script (`scripts/smoke_durability.py`) proving state survives across
    processes. 52 unit tests (+ 1 skipped integration).
  - ADR 0007 — worker least-privilege and injectable RAG retriever.

- **M3 — Supervisor routing (structured output)**
  - Supervisor/router agent (`src/agents/supervisor.py`) that constrains the LLM
    to emit a typed `RoutingDecision` (intent + user id + reasoning) instead of
    free-form text.
  - Injectable `StructuredRouter` seam so routing is unit-tested fully offline
    with a deterministic fake — no network, no API cost.
  - Deterministic `extract_user_id` regex fallback that backfills the id when the
    LLM omits it.
  - Real supervisor node wired into the graph, replacing the M1 placeholder.
  - Routing regression suite over a labeled request set (billing/support/unknown)
    plus node-level state assertions (37 tests total).
  - ADR 0006 — structured-output routing.

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
