"""
AWS Bedrock provider — production AI backend.

Uses Bedrock's Converse API (unified interface across all Bedrock models).
Requires AWS credentials or an IAM role with bedrock:InvokeModel permission.

Region is eu-west-2 (London) for UK data residency — important for
compliance and for the Global Talent visa portfolio.
"""

import json
import logging

from app.services.ai_provider import AIProvider

logger = logging.getLogger(__name__)


class BedrockProvider(AIProvider):
    """
    Calls AWS Bedrock using the boto3 Converse API.

    The Converse API is model-agnostic — the same code works for Claude,
    Llama, Titan, etc. The model is configurable via BEDROCK_MODEL_ID.
    """

    def __init__(self) -> None:
        """Initialise the boto3 Bedrock client."""
        import boto3

        from app.config import get_settings

        settings = get_settings()
        self._model_id = settings.bedrock_model_id

        # boto3 will use IAM role credentials in Lambda/EC2,
        # or explicit key/secret from env vars in local dev.
        session_kwargs: dict[str, str] = {"region_name": settings.aws_region}
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            session_kwargs["aws_access_key_id"] = settings.aws_access_key_id
            session_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key

        session = boto3.Session(**session_kwargs)  # type: ignore[arg-type]
        self._client = session.client("bedrock-runtime")

        logger.info(
            "Bedrock provider initialised",
            extra={"model_id": self._model_id, "region": settings.aws_region},
        )

    async def complete(self, system: str, user: str) -> str:
        """
        Call the Bedrock Converse API.

        Note: boto3 is sync, so we run it in a thread pool via asyncio.
        This avoids blocking the event loop on IO-bound Bedrock calls.

        Args:
            system: System prompt with visa context + RAG chunks.
            user: The user's question.

        Returns:
            The model's text response.
        """
        import asyncio

        # Run synchronous boto3 call in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, self._invoke, system, user)
        return response

    def _invoke(self, system: str, user: str) -> str:
        """Synchronous Bedrock invocation (runs in thread pool)."""
        logger.debug("Calling Bedrock Converse API", extra={"model_id": self._model_id})

        response = self._client.converse(
            modelId=self._model_id,
            system=[{"text": system}],
            messages=[{"role": "user", "content": [{"text": user}]}],
            inferenceConfig={
                "maxTokens": 1500,
                "temperature": 0.1,  # Low temperature for factual accuracy
            },
        )

        output = response["output"]["message"]["content"][0]["text"]
        return str(output)

    @property
    def provider_name(self) -> str:
        """Return provider identifier used in /health response."""
        return "bedrock"


class BedrockEmbeddingProvider:
    """
    Generates embeddings using AWS Bedrock Titan Embed Text v2.

    Used by the ingestion pipeline when AI_PROVIDER=bedrock.
    """

    def __init__(self) -> None:
        """Initialise Bedrock client for embeddings."""
        import boto3

        from app.config import get_settings

        settings = get_settings()
        self._model_id = "amazon.titan-embed-text-v2:0"

        session = boto3.Session(region_name=settings.aws_region)
        self._client = session.client("bedrock-runtime")

    def embed(self, text: str) -> list[float]:
        """
        Generate an embedding vector for a piece of text.

        Args:
            text: The text to embed (typically a document chunk or query).

        Returns:
            A list of floats representing the embedding vector.
        """
        body = json.dumps({"inputText": text, "dimensions": 1024})
        response = self._client.invoke_model(
            modelId=self._model_id,
            contentType="application/json",
            accept="application/json",
            body=body,
        )
        result = json.loads(response["body"].read())
        return list(result["embedding"])
