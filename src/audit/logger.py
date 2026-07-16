"""Append-only audit logging with PII redaction.

Every tool invocation and governance decision is recorded here. In M2 the sink
is in-memory plus a structured application log; a Postgres-backed audit table is
introduced alongside the human-in-the-loop work (M5). Sensitive fields (emails,
long identifiers) are masked before they are ever written.
"""

from __future__ import annotations

import logging
import re
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("resolution_desk.audit")

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# Argument keys whose values should always be masked in the audit trail.
_SENSITIVE_KEYS = {"email", "password", "token", "api_key", "secret"}


def mask_email(value: str) -> str:
    """Mask the local part of an email: ``jane.doe@x.com`` -> ``j***@x.com``."""

    def _mask(match: re.Match[str]) -> str:
        local, _, domain = match.group(0).partition("@")
        head = local[0] if local else "*"
        return f"{head}***@{domain}"

    return _EMAIL_RE.sub(_mask, value)


def redact(value: Any) -> Any:
    """Recursively redact PII from arbitrary tool arguments/results."""
    if isinstance(value, str):
        return mask_email(value)
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, val in value.items():
            if key.lower() in _SENSITIVE_KEYS:
                out[key] = "***"
            else:
                out[key] = redact(val)
        return out
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


class AuditLog:
    """In-memory append-only audit trail with structured-log mirroring."""

    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []

    def record(
        self,
        *,
        tool: str,
        arguments: dict[str, Any],
        result_status: str,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Append a redacted audit record and return it."""
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "tool": tool,
            "user_id": user_id,
            "arguments": redact(deepcopy(arguments)),
            "result_status": result_status,
        }
        self._records.append(entry)
        logger.info("audit %s", entry)
        return entry

    @property
    def records(self) -> list[dict[str, Any]]:
        """Return a copy of all audit records."""
        return list(self._records)

    def clear(self) -> None:
        """Clear the in-memory trail (test/support helper)."""
        self._records.clear()


# Module-level singleton used by the tool layer.
audit_log = AuditLog()
