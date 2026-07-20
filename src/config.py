"""Centralized, environment-driven configuration.

All runtime knobs live here so agents, tools, and the API share one source of
truth. Values are read from the environment (loaded from ``.env`` in local dev).
"""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    """Strongly-typed application settings."""

    # LLM (Google Gemini — free tier via Google AI Studio)
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gemini-3-flash-preview")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0"))

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://resolution:resolution@localhost:5432/resolution_desk?sslmode=disable",
    )

    # MCP server
    mcp_server_host: str = os.getenv("MCP_SERVER_HOST", "localhost")
    mcp_server_port: int = int(os.getenv("MCP_SERVER_PORT", "8100"))

    # Governance policy — deterministic, NOT decided by the LLM.
    refund_auto_approve_limit: float = float(os.getenv("REFUND_AUTO_APPROVE_LIMIT", "50.0"))

    # API
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()
