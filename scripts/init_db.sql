-- Initialize database extensions required by the Resolution Desk.
-- Runs automatically on first container start (docker-entrypoint-initdb.d).

-- pgvector: policy-document embeddings for the Support worker's RAG (M4).
CREATE EXTENSION IF NOT EXISTS vector;

-- Note: LangGraph's PostgresSaver creates its own checkpoint tables at
-- application startup via checkpointer.setup(); we do not create them here.
