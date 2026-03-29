"""
Anthropic API provider — direct API access (recommended for local development).

This is the fastest path for local iteration: no AWS setup required,
just an ANTHROPIC_API_KEY. In production, swap to BedrockProvider for
UK data residency and AWS-native logging.
"""

import logging

from app.services.ai_provider import AIProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(AIProvider):
    """
    Calls the Anthropic Messages API directly.

    Uses the anthropic Python SDK with async support. The model is
    configurable via ANTHROPIC_MODEL env var (default: claude-sonnet-4-6).
    """

    def __init__(self) -> None:
        """Initialise the Anthropic client. Validates API key at construction time."""
        from app.config import get_settings

        settings = get_settings()

        if not settings.anthropic_api_key or settings.anthropic_api_key.startswith("sk-ant-your"):
            raise ValueError(
                "ANTHROPIC_API_KEY is not set or is the placeholder value. "
                "Set a real key in .env.local, or switch to AI_PROVIDER=bedrock."
            )

        import anthropic

        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model
        logger.info("Anthropic provider initialised", extra={"model": self._model})

    async def complete(self, system: str, user: str) -> str:
        """
        Call Claude via the Anthropic Messages API.

        Args:
            system: System prompt containing visa context + RAG document chunks.
            user: The user's question.

        Returns:
            The model's text response.
        """
        logger.debug("Calling Anthropic API", extra={"model": self._model})

        response = await self._client.messages.create(
            model=self._model,
            max_tokens=1500,
            system=system,
            messages=[{"role": "user", "content": user}],
        )

        # Extract text from the first content block
        content = response.content[0]
        if content.type != "text":
            raise RuntimeError(f"Unexpected response type from Anthropic: {content.type}")

        return content.text

    @property
    def provider_name(self) -> str:
        """Return provider identifier used in /health response."""
        return "anthropic"
