# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **LLM provider swapped from OpenAI to Google Gemini** (free tier via Google
  AI Studio). Chat uses `gemini-2.0-flash`; RAG embeddings use
  `text-embedding-004` (768-dim). Configured via `GOOGLE_API_KEY`. Confined to
  the `get_llm()` seam plus config/embeddings — no agent-logic changes. See
  ADR 0011.

### Fixed
- Postgres checkpointer pool now opens connections with `autocommit=True`, so
  `PostgresSaver.setup()`'s `CREATE INDEX CONCURRENTLY` succeeds.
- Test suite is now deterministic against an ambient `.env`: an autouse fixture
  forces offline mode for unit tests, and the durability integration test skips
  unless both a live database and a valid LLM key are present.

## [1.0.0]

### Added
- **M7 — Audit trail exposure & v1.0.0 polish**
  - Read-only audit endpoint `GET /audit` (optional `user_id` / `tool` filters,
    `limit`) surfacing the append-only, PII-redacted trail of every tool call and
    governance decision.
  - `AuditRecord` response schema and a dashboard **Audit Trail** view
    (`/dashboard/audit.html`) linked from the approval console.
  - Offline coverage for audit filtering, redaction, and the served view.
  - ADR 0010 — exposing the audit trail as a governance view.
  - Completes the v1.0.0 feature set (supervisor/worker agents, sandboxed tools,
    durable state, human-in-the-loop approval, reviewer + audit dashboards).

- **M6 — Approval dashboard**
  - Server-rendered reviewer console at `/dashboard/` (vanilla HTML/CSS/JS, no
    SPA build step) that lists pending refunds with user + amount and provides
    Approve / Deny actions.
  - `GET /pending/details` (full snapshots incl. the proposed action) and
    `GET /workflows/{thread_id}` endpoints.
  - `WorkflowSnapshot` now exposes `proposed_tool`, `proposed_user_id`, and
    `proposed_amount`, extracted defensively (model or dict) from state.
  - `WorkflowService.get` / `pending_details` helpers.
  - Offline API tests for the detail endpoints and the served dashboard
    (68 tests, +1 skipped integration).
  - ADR 0009 — server-rendered approval dashboard.

- **M5 — Human-in-the-loop approval**
  - Auditor node (`src/agents/auditor.py`): deterministically applies the human
    reviewer's `approved`/`denied` decision to the escalated refund. Approved
    refunds finalize via `execute_approved_refund` (audited as
    `success_after_approval`); denials move no money.
  - Interrupt/resume flow: the graph suspends before the auditor
    (`interrupt_before`), persists state, and resumes on a human decision — so
    approvals survive process restarts.
  - Injectable checkpointer and supervisor router (`compile_workflow`) so the
    full submit → suspend → approve/deny path runs and is tested offline with an
    in-memory saver.
  - `WorkflowService` (`src/workflow_service.py`) encapsulating submit / pending
    / resume behind one storage-agnostic surface.
  - FastAPI endpoints wired end-to-end: `POST /tickets`, `GET /pending`,
    `POST /approve`, with a startup lifespan that provisions the Postgres-backed
    service and 503s gracefully when no database is reachable.
  - Offline test coverage for the auditor, the end-to-end workflow, and the API
    (65 tests, +1 skipped integration).
  - ADR 0008 — human-in-the-loop approval via interrupt/resume.

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

[Unreleased]: https://github.com/kaixuan477/Agentic-Resolution-Desk/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/kaixuan477/Agentic-Resolution-Desk/releases/tag/v1.0.0
