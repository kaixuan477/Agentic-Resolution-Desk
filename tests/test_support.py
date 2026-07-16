"""Unit tests for the support worker — offline with injected retriever/answerer."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from src.agents.support import ExtractiveAnswerer, support_node
from src.rag.retriever import InMemoryRetriever, RetrievedChunk
from src.state import ResolutionState


class _StubRetriever:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self._chunks = chunks

    def retrieve(self, query: str, k: int = 3) -> list[RetrievedChunk]:
        return self._chunks


class _EchoAnswerer:
    def answer(self, query: str, chunks: list[RetrievedChunk]) -> str:
        return f"answered:{len(chunks)}"


def _state(text: str) -> ResolutionState:
    return ResolutionState(messages=[HumanMessage(content=text)], intent="support")


def test_support_uses_injected_answerer_and_retriever() -> None:
    chunks = [RetrievedChunk("d1", "T", "C", 1.0)]
    result = support_node(_state("how do I reset my password?"),
                          retriever=_StubRetriever(chunks), answerer=_EchoAnswerer())
    assert result["current_assignee"] == "support"
    assert result["messages"][0].content == "answered:1"


def test_support_with_real_inmemory_retriever() -> None:
    result = support_node(
        _state("how do I reset my password?"),
        retriever=InMemoryRetriever(),
        answerer=ExtractiveAnswerer(),
    )
    assert isinstance(result["messages"][0], AIMessage)
    assert "password" in result["messages"][0].content.lower()


def test_extractive_answerer_handles_no_chunks() -> None:
    assert "don't have" in ExtractiveAnswerer().answer("q", []).lower()
