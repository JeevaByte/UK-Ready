"""
Abstract AI provider interface and factory.

Defines a single AIProvider ABC with one async method: complete().
Concrete implementations live in bedrock.py, anthropic_direct.py, and openai_provider.py.

The factory function get_ai_provider() reads the AI_PROVIDER env var and
returns the right implementation — callers never import a concrete class directly.

This abstraction means the RAG pipeline is completely provider-agnostic:
swapping from Anthropic to Bedrock is a one-line env var change.
"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """
    Abstract base class for all AI completion providers.

    Every provider must implement complete(), which takes a system prompt
    and a user message and returns the model's text response.
    """

    @abstractmethod
    async def complete(self, system: str, user: str) -> str:
        """
        Request a text completion from the AI model.

        Args:
            system: The system prompt (visa context + RAG context injected here).
            user: The user's question.

        Returns:
            The model's response as a plain string.

        Raises:
            ValueError: If the provider is not configured (missing API key, etc.).
            RuntimeError: If the API call fails after retries.
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name for this provider (used in /health response)."""
        ...


def get_ai_provider() -> AIProvider:
    """
    Factory function: returns the configured AI provider.

    Reads AI_PROVIDER from settings and instantiates the matching class.
    Import is deferred to avoid loading optional dependencies (boto3, openai)
    when they're not in use.
    """
    from app.config import get_settings

    settings = get_settings()
    provider = settings.ai_provider

    logger.info("Initialising AI provider", extra={"provider": provider})

    if provider == "anthropic":
        from app.services.anthropic_direct import AnthropicProvider

        return AnthropicProvider()
    elif provider == "bedrock":
        from app.services.bedrock import BedrockProvider

        return BedrockProvider()
    elif provider == "openai":
        from app.services.openai_provider import OpenAIProvider

        return OpenAIProvider()
    else:
        raise ValueError(
            f"Unknown AI_PROVIDER: '{provider}'. "
            "Must be one of: anthropic, bedrock, openai."
        )
