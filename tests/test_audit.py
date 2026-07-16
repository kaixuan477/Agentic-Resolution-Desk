"""Tests for audit logging and PII redaction."""

from __future__ import annotations

import pytest

from src.audit.logger import AuditLog, mask_email, redact


@pytest.fixture
def log() -> AuditLog:
    return AuditLog()


def test_mask_email_basic() -> None:
    assert mask_email("jane.doe@example.com") == "j***@example.com"


def test_redact_masks_email_in_string() -> None:
    assert redact("contact vip-01@example.com now") == "contact v***@example.com now"


def test_redact_masks_sensitive_keys() -> None:
    out = redact({"password": "hunter2", "token": "abc", "user_id": "VIP-01"})
    assert out["password"] == "***"
    assert out["token"] == "***"
    assert out["user_id"] == "VIP-01"


def test_redact_is_recursive() -> None:
    out = redact({"nested": [{"email": "a@b.com"}]})
    assert out["nested"][0]["email"] == "***"


def test_record_appends_and_returns(log: AuditLog) -> None:
    entry = log.record(
        tool="execute_refund",
        arguments={"user_id": "VIP-01", "amount": 100.0},
        result_status="requires_human_auditor",
        user_id="VIP-01",
    )
    assert entry["tool"] == "execute_refund"
    assert entry["result_status"] == "requires_human_auditor"
    assert len(log.records) == 1


def test_clear_empties_trail(log: AuditLog) -> None:
    log.record(tool="lookup_user", arguments={}, result_status="success")
    log.clear()
    assert log.records == []
