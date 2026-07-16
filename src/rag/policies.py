"""Mock company policy corpus.

These short documents stand in for a real knowledge base. They are embedded into
pgvector by ``scripts/seed_policies.py`` for production retrieval, and are also
used directly by the in-memory retriever for offline tests.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyDoc:
    """A single policy knowledge-base entry."""

    doc_id: str
    title: str
    content: str


POLICY_DOCS: list[PolicyDoc] = [
    PolicyDoc(
        doc_id="refund-policy",
        title="Refund Policy",
        content=(
            "Customers may request a refund within 30 days of purchase. Refunds up "
            "to $50 are processed automatically. Refunds above $50 require approval "
            "from a human support manager before they are issued."
        ),
    ),
    PolicyDoc(
        doc_id="password-reset",
        title="Password Reset",
        content=(
            "To reset your password, open Settings, choose Security, then 'Reset "
            "Password'. A reset link is emailed to your registered address and "
            "expires after 15 minutes."
        ),
    ),
    PolicyDoc(
        doc_id="two-factor-auth",
        title="Two-Factor Authentication",
        content=(
            "Two-factor authentication (2FA) can be enabled under Settings > "
            "Security > Two-Factor. We support authenticator apps and SMS codes. "
            "Enabling 2FA is strongly recommended for all accounts."
        ),
    ),
    PolicyDoc(
        doc_id="account-tiers",
        title="Account Tiers",
        content=(
            "Standard accounts have basic support. VIP accounts receive priority "
            "support and higher automated refund eligibility. Tier is shown on the "
            "account overview page."
        ),
    ),
    PolicyDoc(
        doc_id="billing-cycle",
        title="Billing Cycle",
        content=(
            "Subscriptions are billed monthly on the anniversary of signup. "
            "Duplicate charges are automatically detected and reversed within two "
            "business days."
        ),
    ),
]


def get_policy_docs() -> list[PolicyDoc]:
    """Return the full policy corpus."""
    return list(POLICY_DOCS)
