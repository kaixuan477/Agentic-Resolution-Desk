# ADR 0004 — pgvector over a Managed Vector Database

- **Status:** Accepted
- **Date:** 2026-07-15

## Context

The Support worker answers policy questions via retrieval-augmented generation
(RAG), which needs a vector store for policy-document embeddings.

## Decision

Use **pgvector** inside the existing PostgreSQL instance rather than a managed
service such as Pinecone or Milvus.

## Consequences

- **+** Zero additional infrastructure or cost — same database as the
  checkpointer and audit log.
- **+** Self-hostable and fully reproducible via Docker Compose (`pgvector/pgvector`).
- **+** Transactional consistency between operational data and embeddings.
- **−** Not tuned for billion-scale vector workloads; irrelevant at this project's
  scale. Can be revisited if corpus size grows dramatically.

## Alternatives considered

- **Pinecone** — rejected for v1.0: managed cost, external dependency, API keys,
  harder reproducibility for reviewers cloning the repo.
- **Milvus** — rejected for v1.0: heavier operational footprint than warranted.
