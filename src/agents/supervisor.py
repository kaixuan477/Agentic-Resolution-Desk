"""Supervisor / router agent.

The supervisor performs the single most safety-critical routing decision in the
system: which specialist worker handles a ticket. It holds **no tools**. To keep
routing deterministic and testable, the LLM is constrained to emit a typed
``RoutingDecision`` via structured output rather than free-form text.

The classifier is injected (``router`` argument), so unit tests can supply a
fake and run fully offline — no network, no API cost.
"""

from __future__ import annotations

import re
from typing import Literal, Protocol

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from src.state import ResolutionState

Intent = Literal["billing", "support", "unknown"]

# Matches ids like VIP-01, USER-100 (case-insensitive).
_USER_ID_RE = re.compile(r"\b([A-Za-z]+-\d+)\b")

SYSTEM_PROMPT = (
    "You are the Supervisor for an enterprise support desk. Classify the user's "
    "request and route it. Use 'billing' for anything involving money, refunds, "
    "charges, or account balances. Use 'support' for how-to questions, product "
    "usage, or policy explanations. Use 'unknown' only if the request fits "
    "neither. Extract the user id if one is present (e.g. 'VIP-01')."
)


class RoutingDecision(BaseModel):
    """The structured output the supervisor LLM must return."""

    intent: Intent = Field(description="Which specialist should handle the request.")
    user_id: str | None = Field(default=None, description="Extracted user id, if any.")
    reasoning: str = Field(default="", description="Brief justification for the route.")


class StructuredRouter(Protocol):
    """Minimal interface a router must satisfy (real LLM or test fake)."""

    def invoke(self, messages: list[dict[str, str]]) -> RoutingDecision: ...


def _default_router() -> StructuredRouter:
    """Build the production router: an LLM constrained to ``RoutingDecision``."""
    from src.llm.client import get_llm

    return get_llm().with_structured_output(RoutingDecision)  # type: ignore[return-value]


def extract_user_id(text: str) -> str | None:
    """Deterministically pull a user id from text as a fallback/cross-check."""
    match = _USER_ID_RE.search(text)
    return match.group(1).upper() if match else None


def _latest_user_text(state: ResolutionState) -> str:
    """Return the most recent human message content."""
    for message in reversed(state.messages):
        if isinstance(message, HumanMessage):
            return str(message.content)
    return ""


def classify_intent(text: str, router: StructuredRouter | None = None) -> RoutingDecision:
    """Classify a single request into a typed routing decision."""
    router = router or _default_router()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]
    decision = router.invoke(messages)
    # Prefer an explicitly extracted id; fall back to a deterministic regex.
    if not decision.user_id:
        decision.user_id = extract_user_id(text)
    return decision


def supervisor_node(
    state: ResolutionState, router: StructuredRouter | None = None
) -> dict[str, object]:
    """Graph node: classify the latest request and set routing state."""
    text = _latest_user_text(state)
    decision = classify_intent(text, router=router)
    return {
        "intent": decision.intent,
        "extracted_user_id": decision.user_id,
        "current_assignee": decision.intent if decision.intent != "unknown" else "supervisor",
    }
