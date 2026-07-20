# ADR 0011 — LLM Provider: Google Gemini

- **Status:** Accepted
- **Date:** 2026-07-18

## Context

The system was originally wired to OpenAI (`ChatOpenAI` /
`text-embedding-3-small`). We need a free-tier provider so the workflow can run
end-to-end without a paid OpenAI account, while preserving the provider
abstraction established earlier.

## Decision

Adopt **Google Gemini** (free tier via Google AI Studio) as the LLM provider:

- Chat: `ChatGoogleGenerativeAI` (default model `gemini-2.0-flash`).
- Embeddings: `GoogleGenerativeAIEmbeddings` (`models/text-embedding-004`,
  768-dim) for the pgvector RAG path.
- Key read from `GOOGLE_API_KEY`.

The swap is confined to `src/llm/client.py`, `src/config.py`, and the RAG
embedding sites — validating the `get_llm()` seam from ADR 0006/0007. Agent
nodes and the graph are unchanged; injected fakes keep tests fully offline.

## Consequences

- **+** Free-tier execution — the live HITL refund workflow can run at no cost.
- **+** Confirms the provider abstraction: a provider swap touched ~5 files, no
  agent logic.
- **+** pgvector embedding dimension drops 1536 → 768 (re-ingest required).
- **−** `langchain-google-genai` currently depends on the deprecated
  `google.generativeai` package (emits a `FutureWarning`); migrate to
  `google.genai` when the LangChain integration does.

## Alternatives considered

- **Stay on OpenAI** — rejected: requires a paid account for live runs.
- **Local model via Ollama** — deferred: heavier local setup; Gemini free tier
  is lower-friction for demos. Remains a future option behind the same seam.
