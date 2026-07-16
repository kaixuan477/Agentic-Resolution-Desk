"""Typed request/response contracts for MCP tools.

Returning validated Pydantic models (instead of raw dicts) gives every tool a
stable, self-documenting schema and lets callers rely on types across the
sandbox boundary.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RefundStatus = Literal["success", "requires_human_auditor", "rejected"]


class UserProfile(BaseModel):
    user_id: str
    tier: str
    email: str


class AccountBalance(BaseModel):
    user_id: str
    balance: float
    currency: str


class PolicyResult(BaseModel):
    user_id: str
    summary: str
    auto_approve_limit: float


class RefundResult(BaseModel):
    status: RefundStatus
    user_id: str
    amount: float
    transaction_id: str | None = None
    limit: float | None = None
    reason: str | None = None


class ToolError(BaseModel):
    """Structured error envelope returned instead of raising across the boundary."""

    error: str
    detail: str
    user_id: str | None = Field(default=None)
