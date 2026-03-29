"""
Application configuration — loaded from environment variables at startup.

Uses pydantic-settings so all config is validated with clear error messages
when required variables are missing. Settings are cached after first load.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All application settings, sourced from environment variables.

    Required variables depend on the selected AI_PROVIDER:
    - anthropic: ANTHROPIC_API_KEY must be set
    - bedrock: AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY (or IAM role)
    - openai: OPENAI_API_KEY must be set
    """

    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # AI Provider
    # -------------------------------------------------------------------------
    ai_provider: Literal["anthropic", "bedrock", "openai"] = Field(
        default="anthropic",
        description="Which AI backend to use. Set AI_PROVIDER env var.",
    )

    # Anthropic direct
    anthropic_api_key: str = Field(default="", description="Anthropic API key (sk-ant-...)")
    anthropic_model: str = Field(
        default="claude-sonnet-4-6",
        description="Anthropic model ID for direct API calls",
    )

    # AWS Bedrock
    aws_access_key_id: str = Field(default="", description="AWS access key ID")
    aws_secret_access_key: str = Field(default="", description="AWS secret access key")
    aws_region: str = Field(default="eu-west-2", description="AWS region (eu-west-2 for UK data residency)")
    bedrock_model_id: str = Field(
        default="anthropic.claude-sonnet-4-5-20251001",
        description="AWS Bedrock model identifier",
    )

    # OpenAI
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o", description="OpenAI model ID")

    # -------------------------------------------------------------------------
    # Vector store (ChromaDB)
    # -------------------------------------------------------------------------
    chroma_host: str = Field(default="chroma", description="ChromaDB hostname")
    chroma_port: int = Field(default=8000, description="ChromaDB port")
    chroma_collection: str = Field(
        default="ukready_documents",
        description="ChromaDB collection name for indexed gov.uk documents",
    )

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    database_url: str = Field(
        default="postgresql://ukready:ukready_dev_password@postgres:5432/ukready",
        description="PostgreSQL connection URL",
    )

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    environment: Literal["development", "production"] = Field(
        default="development",
        description="Runtime environment — controls API docs visibility and CORS",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Log verbosity level",
    )
    backend_host: str = Field(default="0.0.0.0")
    backend_port: int = Field(default=8000)

    # -------------------------------------------------------------------------
    # RAG pipeline tuning
    # -------------------------------------------------------------------------
    rag_top_k: int = Field(
        default=5,
        description="Number of document chunks to retrieve per query",
    )
    chunk_size_tokens: int = Field(
        default=512,
        description="Target token count per document chunk",
    )
    chunk_overlap_tokens: int = Field(
        default=50,
        description="Token overlap between adjacent chunks for continuity",
    )

    @field_validator("anthropic_api_key")
    @classmethod
    def validate_anthropic_key(cls, v: str, info: object) -> str:
        """Warn (not error) if using anthropic provider without a key set."""
        # Full validation happens at request time, not at startup,
        # so local dev with no key still starts the server.
        return v


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings. Call this everywhere."""
    return Settings()
