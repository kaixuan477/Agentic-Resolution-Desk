"""Tests for the deterministic governance policy."""

from __future__ import annotations

from src.policy import auto_approve_limit, refund_requires_approval


def test_below_limit_auto_approved() -> None:
    assert refund_requires_approval(auto_approve_limit() - 0.01) is False


def test_at_limit_auto_approved() -> None:
    assert refund_requires_approval(auto_approve_limit()) is False


def test_above_limit_requires_approval() -> None:
    assert refund_requires_approval(auto_approve_limit() + 0.01) is True


def test_default_limit_is_fifty() -> None:
    assert auto_approve_limit() == 50.0
