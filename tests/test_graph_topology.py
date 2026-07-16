"""M1 smoke tests: state schema and graph topology.

These run without any external services (no Postgres, no LLM, no network) so CI
stays fast and deterministic. Durable-checkpointer and end-to-end tests arrive
with the milestones that introduce those dependencies.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from src.graph import build_workflow, route_from_supervisor
from src.state import ProposedAction, ResolutionState


def test_state_defaults() -> None:
    state = ResolutionState()
    assert state.current_assignee == "supervisor"
    assert state.intent == "unknown"
    assert state.requires_approval is False
    assert state.audit_trail == []


def test_state_accepts_messages_and_action() -> None:
    state = ResolutionState(
        messages=[HumanMessage(content="I need a refund")],
        intent="billing",
        proposed_action=ProposedAction(tool="execute_refund", arguments={"amount": 100}),
    )
    assert state.intent == "billing"
    assert state.proposed_action is not None
    assert state.proposed_action.tool == "execute_refund"


def test_routing_billing() -> None:
    assert route_from_supervisor(ResolutionState(intent="billing")) == "billing"


def test_routing_support() -> None:
    assert route_from_supervisor(ResolutionState(intent="support")) == "support"


def test_routing_unknown_ends() -> None:
    from langgraph.graph import END

    assert route_from_supervisor(ResolutionState(intent="unknown")) == END


def test_workflow_builds_with_expected_nodes() -> None:
    workflow = build_workflow()
    for node in ("supervisor", "billing", "support", "auditor"):
        assert node in workflow.nodes
