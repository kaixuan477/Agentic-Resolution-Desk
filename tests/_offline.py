"""Shared offline fixtures: a deterministic router and an in-memory graph app."""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver

from src.agents.supervisor import RoutingDecision
from src.graph import compile_workflow


class FakeRouter:
    """Deterministic supervisor router — keyword-based, no LLM."""

    _SUPPORT = ("how", "reset", "password", "policy", "explain", "guide", "setup")
    _BILLING = ("refund", "charge", "money", "bill", "balance", "$")

    def invoke(self, messages: list[dict[str, str]]) -> RoutingDecision:
        text = messages[-1]["content"].lower()
        if any(word in text for word in self._SUPPORT):
            return RoutingDecision(intent="support")
        if any(word in text for word in self._BILLING):
            return RoutingDecision(intent="billing")
        return RoutingDecision(intent="unknown")


def build_offline_app() -> object:
    """Compile the full graph with an in-memory saver and the fake router."""
    return compile_workflow(MemorySaver(), router=FakeRouter())
