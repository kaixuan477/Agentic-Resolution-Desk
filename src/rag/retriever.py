"""Policy retrievers.

Two implementations behind one ``PolicyRetriever`` protocol:

- ``InMemoryRetriever`` — dependency-free lexical overlap scoring. Used for
  offline unit tests and as a graceful fallback when no database is configured.
- ``PgVectorRetriever`` — production retriever backed by pgvector embeddings.
  Imports its heavy dependencies lazily so the module stays import-safe in CI.

Keeping retrieval behind a protocol lets the Support worker be tested fully
offline while production swaps in semantic search with no code changes.
"""

from __future__ import annotations

import re
from typing import Protocol

from src.rag.policies import PolicyDoc, get_policy_docs

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


class RetrievedChunk:
    """A retrieved policy snippet with its relevance score."""

    def __init__(self, doc_id: str, title: str, content: str, score: float) -> None:
        self.doc_id = doc_id
        self.title = title
        self.content = content
        self.score = score

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"RetrievedChunk(doc_id={self.doc_id!r}, score={self.score:.3f})"


class PolicyRetriever(Protocol):
    """Interface implemented by all retrievers."""

    def retrieve(self, query: str, k: int = 3) -> list[RetrievedChunk]: ...


class InMemoryRetriever:
    """Lexical-overlap retriever over the in-process policy corpus."""

    def __init__(self, docs: list[PolicyDoc] | None = None) -> None:
        self._docs = docs if docs is not None else get_policy_docs()

    def retrieve(self, query: str, k: int = 3) -> list[RetrievedChunk]:
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []
        scored: list[RetrievedChunk] = []
        for doc in self._docs:
            doc_tokens = _tokenize(f"{doc.title} {doc.content}")
            overlap = len(query_tokens & doc_tokens)
            if overlap == 0:
                continue
            score = overlap / len(query_tokens)
            scored.append(RetrievedChunk(doc.doc_id, doc.title, doc.content, score))
        scored.sort(key=lambda c: c.score, reverse=True)
        return scored[:k]


class PgVectorRetriever:
    """Semantic retriever backed by pgvector (production)."""

    def __init__(self, database_url: str, table: str = "policy_chunks") -> None:
        self._database_url = database_url
        self._table = table

    def retrieve(self, query: str, k: int = 3) -> list[RetrievedChunk]:  # pragma: no cover
        # Heavy deps imported lazily so importing this module never requires them.
        import psycopg
        from langchain_openai import OpenAIEmbeddings

        embedding = OpenAIEmbeddings().embed_query(query)
        vec = "[" + ",".join(str(x) for x in embedding) + "]"
        sql = (
            f"SELECT doc_id, title, content, 1 - (embedding <=> %s::vector) AS score "
            f"FROM {self._table} ORDER BY embedding <=> %s::vector LIMIT %s"
        )
        with psycopg.connect(self._database_url) as conn, conn.cursor() as cur:
            cur.execute(sql, (vec, vec, k))
            rows = cur.fetchall()
        return [RetrievedChunk(r[0], r[1], r[2], float(r[3])) for r in rows]


def get_default_retriever() -> PolicyRetriever:
    """Return a retriever: pgvector if reachable, else the in-memory fallback."""
    return InMemoryRetriever()
