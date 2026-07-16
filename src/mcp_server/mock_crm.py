"""In-memory mock CRM datastore.

Provides deterministic, testable user records so tool responses do not rely on
string-prefix guessing. Replaced by a real CRM integration behind the same MCP
interface in a later release.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CrmUser:
    """A mock customer record."""

    user_id: str
    tier: str          # "VIP" | "standard"
    email: str
    balance: float
    currency: str = "USD"


_USERS: dict[str, CrmUser] = {
    "VIP-01": CrmUser("VIP-01", "VIP", "vip-01@example.com", 250.00),
    "VIP-02": CrmUser("VIP-02", "VIP", "vip-02@example.com", 980.50),
    "USER-100": CrmUser("USER-100", "standard", "user-100@example.com", 45.00),
    "USER-200": CrmUser("USER-200", "standard", "user-200@example.com", 12.75),
}


class UserNotFoundError(LookupError):
    """Raised when a user id has no CRM record."""

    def __init__(self, user_id: str) -> None:
        super().__init__(f"No CRM record for user '{user_id}'")
        self.user_id = user_id


def get_user(user_id: str) -> CrmUser:
    """Return the CRM record for ``user_id`` or raise ``UserNotFoundError``."""
    key = user_id.strip().upper()
    if key not in _USERS:
        raise UserNotFoundError(user_id)
    return _USERS[key]


def user_exists(user_id: str) -> bool:
    """Return True if a record exists for ``user_id``."""
    return user_id.strip().upper() in _USERS
