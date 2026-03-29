"""
OpenAI provider — fallback AI backend.

Use this if neither Anthropic nor Bedrock is available.
Set AI_PROVIDER=openai and OPENAI_API_KEY in your environment.
"""

import logging

from app.services.ai_provider import AIProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """
    Calls the OpenAI Chat Completions API.

    The model is configurable via OPENAI_MODEL env var (default: gpt-4o).
    """

    def __init__(self) -> None:
        """Initialise the OpenAI async client."""
        from openai import AsyncOpenAI

        from app.config import get_settings

        settings = get_settings()

        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. "
                "Set it in .env.local, or switch to AI_PROVIDER=anthropic."
            )

        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model
        logger.info("OpenAI provider initialised", extra={"model": self._model})

    async def complete(self, system: str, user: str) -> str:
        """
        Call the OpenAI Chat Completions API.

        Args:
            system: System prompt with visa context + RAG chunks.
            user: The user's question.

        Returns:
            The model's text response.
        """
        logger.debug("Calling OpenAI API", extra={"model": self._model})

        response = await self._client.chat.completions.create(
            model=self._model,
            max_tokens=1500,
            temperature=0.1,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )

        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError("OpenAI returned an empty response")

        return content

    @property
    def provider_name(self) -> str:
        """Return provider identifier used in /health response."""
        return "openai"
