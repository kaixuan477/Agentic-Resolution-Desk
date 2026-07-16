"""Routing tests for the supervisor agent.

A fake structured router keeps these tests fully offline (no LLM, no network).
The keyword-based fake mimics how the real structured-output LLM should behave,
letting us regression-test the routing contract deterministically.
"""

from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage

from src.agents.supervisor import (
    RoutingDecision,
    classify_intent,
    extract_user_id,
    supervisor_node,
)
from src.state import ResolutionState


class FakeRouter:
    """Deterministic stand-in for an LLM constrained to ``RoutingDecision``."""

    def invoke(self, messages: list) -> RoutingDecision:
        text = messages[-1]["content"].lower()
        # Support intent (how-to / policy explanations) is checked first so that
        # phrases like "explain your refund policy" route to support, not billing.
        if any(k in text for k in ("how do i", "how to", "reset", "policy", "setup", "explain")):
            intent = "support"
        elif any(k in text for k in ("refund", "charge", "money", "balance", "billed")):
            intent = "billing"
        else:
            intent = "unknown"
        return RoutingDecision(intent=intent, user_id=None, reasoning="fake")


# (request text, expected intent)
LABELED_SET = [
    ("I am VIP-01 and I need a $100 refund", "billing"),
    ("Why was I charged twice this month?", "billing"),
    ("What is my account balance?", "billing"),
    ("How do I reset my password?", "support"),
    ("How to set up two-factor auth?", "support"),
    ("Can you explain your refund policy?", "support"),
    ("The weather is nice today", "unknown"),
]


@pytest.mark.parametrize("text,expected", LABELED_SET)
def test_routing_accuracy(text: str, expected: str) -> None:
    decision = classify_intent(text, router=FakeRouter())
    assert decision.intent == expected


def test_extract_user_id_variants() -> None:
    assert extract_user_id("I am VIP-01") == "VIP-01"
    assert extract_user_id("user-100 here") == "USER-100"
    assert extract_user_id("no id present") is None


def test_classify_backfills_user_id_from_text() -> None:
    decision = classify_intent("VIP-02 wants a refund", router=FakeRouter())
    assert decision.user_id == "VIP-02"


def test_supervisor_node_sets_routing_state() -> None:
    state = ResolutionState(messages=[HumanMessage(content="I am VIP-01, need a refund")])
    update = supervisor_node(state, router=FakeRouter())
    assert update["intent"] == "billing"
    assert update["extracted_user_id"] == "VIP-01"
    assert update["current_assignee"] == "billing"


def test_supervisor_node_unknown_stays_with_supervisor() -> None:
    state = ResolutionState(messages=[HumanMessage(content="hello there")])
    update = supervisor_node(state, router=FakeRouter())
    assert update["intent"] == "unknown"
    assert update["current_assignee"] == "supervisor"
