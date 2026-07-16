"""Unit tests for the in-memory policy retriever."""

from __future__ import annotations

from src.rag.policies import get_policy_docs
from src.rag.retriever import InMemoryRetriever, get_default_retriever


def test_retrieves_relevant_policy_first() -> None:
    retriever = InMemoryRetriever()
    chunks = retriever.retrieve("how do I reset my password", k=3)
    assert chunks
    assert "password" in (chunks[0].title + chunks[0].content).lower()


def test_respects_k_limit() -> None:
    chunks = InMemoryRetriever().retrieve("refund policy account billing password", k=2)
    assert len(chunks) <= 2


def test_empty_query_returns_nothing() -> None:
    assert InMemoryRetriever().retrieve("   ", k=3) == []


def test_scores_are_descending() -> None:
    chunks = InMemoryRetriever().retrieve("refund policy limit approval", k=5)
    scores = [c.score for c in chunks]
    assert scores == sorted(scores, reverse=True)


def test_default_retriever_is_offline() -> None:
    assert isinstance(get_default_retriever(), InMemoryRetriever)


def test_corpus_is_non_empty() -> None:
    assert len(get_policy_docs()) >= 5
