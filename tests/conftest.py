"""Shared pytest fixtures.

Guarantees the offline test suite is deterministic regardless of any ambient
``.env`` file. Without a real LLM key, worker nodes fall back to their offline
implementations (e.g. the extractive answerer), so no network calls are made.
"""

from __future__ import annotations

import pytest

from src.config import get_settings


@pytest.fixture(autouse=True)
def _offline_llm(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Force offline mode by clearing the cached LLM key.

    Integration tests (which exercise the live routing path) are exempt.
    """
    if request.node.get_closest_marker("integration"):
        return
    monkeypatch.setattr(get_settings(), "google_api_key", "", raising=False)
