"""Ingest policy documents into pgvector.

Creates the ``policy_chunks`` table (if absent), embeds each policy document with
OpenAI embeddings, and upserts the vectors. Invoked via
``scripts/seed_policies.py``. Heavy dependencies are imported lazily so this
module is import-safe even where they are unavailable.
"""

from __future__ import annotations

from src.rag.policies import get_policy_docs

EMBED_DIM = 1536  # text-embedding-3-small
TABLE = "policy_chunks"


def _create_table_sql() -> str:
    return (
        f"CREATE TABLE IF NOT EXISTS {TABLE} ("
        "  doc_id text PRIMARY KEY,"
        "  title text NOT NULL,"
        "  content text NOT NULL,"
        f"  embedding vector({EMBED_DIM})"
        ");"
    )


def ingest_policies(database_url: str) -> int:  # pragma: no cover - requires DB + API
    """Embed and upsert all policy docs into pgvector. Returns rows written."""
    import psycopg
    from langchain_openai import OpenAIEmbeddings

    docs = get_policy_docs()
    embedder = OpenAIEmbeddings(model="text-embedding-3-small")
    vectors = embedder.embed_documents([f"{d.title}\n{d.content}" for d in docs])

    written = 0
    with psycopg.connect(database_url) as conn, conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute(_create_table_sql())
        for doc, vec in zip(docs, vectors, strict=True):
            vec_literal = "[" + ",".join(str(x) for x in vec) + "]"
            cur.execute(
                f"INSERT INTO {TABLE} (doc_id, title, content, embedding) "
                "VALUES (%s, %s, %s, %s::vector) "
                "ON CONFLICT (doc_id) DO UPDATE SET "
                "title = EXCLUDED.title, content = EXCLUDED.content, "
                "embedding = EXCLUDED.embedding;",
                (doc.doc_id, doc.title, doc.content, vec_literal),
            )
            written += 1
        conn.commit()
    return written
