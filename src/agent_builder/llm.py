"""LLM factory — creates chat model instances."""

from __future__ import annotations

from langchain_anthropic import ChatAnthropic


def create_llm(model: str = "claude-sonnet-4-20250514", **kwargs):
    """Create an Anthropic chat model.

    Keeping this centralised so we can add Groq / Gemini / xAI later
    without touching pattern code.
    """
    return ChatAnthropic(model=model, temperature=0, **kwargs)
