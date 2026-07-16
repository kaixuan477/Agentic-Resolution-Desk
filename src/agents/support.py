"""Support worker.

Answers how-to and policy questions using retrieval-augmented generation over
the policy corpus. By design it has access **only** to the policy retriever — it
holds no billing tools and cannot issue refunds (least privilege, ADR 0001).

Both the retriever and the answerer are injected, so the worker is tested fully
offline. The default answerer is extractive (no LLM) when no API key is
configured, which keeps the whole system runnable without external services;
production uses the LLM answerer for fluent responses.
"""

from __future__ import annotations

from typing import Any, Protocol

from langchain_core.messages import AIMessage, HumanMessage

from src.rag.retriever import PolicyRetriever, RetrievedChunk, get_default_retriever
from src.state import ResolutionState

SYSTEM_PROMPT = (
    "You are a support specialist. Answer the user's question using ONLY the "
    "provided policy context. If the context does not contain the answer, say you "
    "don't have that information. Be concise."
)


class Answerer(Protocol):
    """Composes a final answer from a query and retrieved context."""

    def answer(self, query: str, chunks: list[RetrievedChunk]) -> str: ...


class ExtractiveAnswerer:
    """Offline answerer that returns the most relevant policy snippet."""

    def answer(self, query: str, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return "I don't have information on that topic."
        top = chunks[0]
        return f"{top.title}: {top.content}"


class LLMAnswerer:  # pragma: no cover - exercised only with a live model
    """Production answerer that composes a fluent response with the LLM."""

    def answer(self, query: str, chunks: list[RetrievedChunk]) -> str:
        from src.llm.client import get_llm

        context = "\n\n".join(f"[{c.title}] {c.content}" for c in chunks)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
        ]
        response = get_llm().invoke(messages)
        return str(response.content)


def _default_answerer() -> Answerer:
    """Pick an answerer: LLM when an API key is set, else extractive."""
    from src.config import get_settings

    return LLMAnswerer() if get_settings().openai_api_key else ExtractiveAnswerer()


def _latest_user_text(state: ResolutionState) -> str:
    for message in reversed(state.messages):
        if isinstance(message, HumanMessage):
            return str(message.content)
    return ""


def support_node(
    state: ResolutionState,
    retriever: PolicyRetriever | None = None,
    answerer: Answerer | None = None,
) -> dict[str, Any]:
    """Answer a support question via RAG over the policy corpus."""
    retriever = retriever or get_default_retriever()
    answerer = answerer or _default_answerer()

    query = _latest_user_text(state)
    chunks = retriever.retrieve(query, k=3)
    reply = answerer.answer(query, chunks)

    return {
        "messages": [AIMessage(content=reply)],
        "current_assignee": "support",
    }
