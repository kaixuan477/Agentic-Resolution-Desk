"""Provider-abstracted LLM client.

Keeping construction behind a single function lets us swap providers without
touching agent code. The project uses Google Gemini (free tier via Google AI
Studio); switching providers is a change here alone.
"""

from __future__ import annotations

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import SecretStr

from src.config import get_settings


def get_llm() -> ChatGoogleGenerativeAI:
    """Return a configured Gemini chat model instance."""
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        api_key=SecretStr(settings.google_api_key) if settings.google_api_key else None,
    )
