"""
Request and response schemas for the /chat endpoint.

Uses Pydantic v2 models with strict typing. The ChatResponse format is
designed to be trust-building: it always includes confidence level, sources,
and a legal disclaimer — because migrants make high-stakes decisions based
on these answers.
"""

import uuid
from typing import Literal

from pydantic import BaseModel, Field

from app.models.visa import VisaType


class ChatRequest(BaseModel):
    """
    Incoming chat request from the frontend.

    The visa_type is provided on every request (not stored server-side)
    so the frontend is the single source of truth for the user's visa context.
    """

    visa_type: VisaType = Field(
        description="The user's current UK visa type. Controls answer context and filtering."
    )
    message: str = Field(
        min_length=1,
        max_length=2000,
        description="The user's question. Max 2000 characters.",
    )
    conversation_id: uuid.UUID | None = Field(
        default=None,
        description=(
            "Optional session UUID for conversation continuity. "
            "If omitted, a new conversation is started."
        ),
    )


class Source(BaseModel):
    """A gov.uk source document cited in an answer."""

    url: str = Field(description="The gov.uk page URL")
    title: str = Field(description="The page title")
    last_updated: str = Field(description="ISO date string of when the page was last scraped")


class ChatResponse(BaseModel):
    """
    Response from the Q&A engine.

    Every response includes:
    - The answer in plain English
    - A confidence level (HIGH/MEDIUM/LOW) indicating how directly the
      retrieved documents address the question
    - Source citations from gov.uk
    - A disclaimer that this is information, not legal advice
    - The conversation ID for follow-up questions
    """

    answer: str = Field(description="The answer in plain English, specific to the user's visa type")
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description=(
            "How confident we are in this answer. "
            "HIGH = directly stated in retrieved gov.uk docs. "
            "MEDIUM = inferred from context. "
            "LOW = uncertain, recommend professional advice."
        )
    )
    sources: list[Source] = Field(
        default_factory=list,
        description="gov.uk source documents used to generate this answer",
    )
    conversation_id: uuid.UUID = Field(
        description="Session UUID — send this back to continue the conversation"
    )
    disclaimer: str = Field(
        default=(
            "This is information, not legal advice. "
            "For visa decisions, always consult a registered immigration solicitor or adviser. "
            "Visa rules change — always verify at gov.uk."
        ),
        description="Legal disclaimer, always included",
    )


class HealthResponse(BaseModel):
    """Response from the GET /health endpoint."""

    status: Literal["ok", "degraded"] = Field(description="Overall service status")
    vector_store: Literal["ok", "degraded", "empty"] = Field(
        description="ChromaDB availability and population status"
    )
    ai_provider: str = Field(description="Which AI provider is currently configured")
    documents_indexed: int = Field(description="Number of document chunks in the vector store")
