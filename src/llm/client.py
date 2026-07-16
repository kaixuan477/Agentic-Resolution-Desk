"""Provider-abstracted LLM client.

Keeping construction behind a single function lets us swap providers (or drop in
a local model via Ollama, per the roadmap) without touching agent code.
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from src.config import get_settings


def get_llm() -> ChatOpenAI:
    """Return a configured chat model instance."""
    settings = get_settings()
    return ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        api_key=SecretStr(settings.openai_api_key) if settings.openai_api_key else None,
    )
