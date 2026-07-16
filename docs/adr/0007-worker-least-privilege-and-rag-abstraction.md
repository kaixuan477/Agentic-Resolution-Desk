# 7. Worker least-privilege and injectable RAG retriever

Date: 2025

## Status

Accepted

## Context

The worker agents (Billing and Support) act on user requests. Billing can move
money; Support answers policy questions from a knowledge base. Two risks follow:

1. **Over-broad capability.** If every agent can call every tool, a prompt
   injection or classification error in the Support path could trigger a refund.
2. **Testability and cost.** RAG normally depends on a live vector database and
   an embeddings API, which makes unit tests slow, flaky, and expensive.

## Decision

- **Least privilege per worker.** Each worker imports only the tools it needs.
  `billing.py` imports `execute_refund` (and nothing from `rag`); `support.py`
  imports only the retriever (and no billing tools). Capability is enforced by
  the import graph, not by runtime checks.
- **Retriever behind a protocol.** `PolicyRetriever` has two implementations:
  `InMemoryRetriever` (dependency-free lexical overlap) and `PgVectorRetriever`
  (production, lazy-imported). Workers accept an injected retriever; the default
  is offline.
- **Injectable answerer.** The Support worker takes an `Answerer`. The default is
  `ExtractiveAnswerer` when no API key is present (keeps the system runnable
  offline) and `LLMAnswerer` in production. Tests inject deterministic fakes.

## Consequences

- Refund capability is structurally unreachable from the Support path.
- The full agent workflow runs and is unit-tested with no network, database, or
  API key — CI stays fast and free.
- Swapping in semantic search for production is a one-line default change with no
  worker code changes.
- The lexical retriever is weaker than embeddings; acceptable because it is only
  a fallback/test double, not the production path.
