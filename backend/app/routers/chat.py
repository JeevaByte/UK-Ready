"""
Chat endpoint — POST /chat

The core endpoint of UKReady. Accepts a visa-typed question and returns
a sourced, confidence-rated answer from the RAG pipeline.
"""

import logging
import uuid

from fastapi import APIRouter, HTTPException

from app.models.chat import ChatRequest, ChatResponse
from app.services.rag_pipeline import RagPipeline

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ChatResponse, summary="Ask a visa-aware question")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Ask a question about UK visa rules, work rights, or migration.

    Every answer is:
    - Specific to your visa type (Graduate / Skilled Worker / Student / ILR)
    - Sourced from official gov.uk guidance via RAG retrieval
    - Given a confidence rating (HIGH / MEDIUM / LOW)
    - Accompanied by source citations and a legal disclaimer
    """
    # Assign a new conversation ID if this is a fresh session
    conversation_id = request.conversation_id or uuid.uuid4()

    logger.info(
        "Chat request received",
        extra={
            "visa_type": request.visa_type.value,
            "conversation_id": str(conversation_id),
            "message_length": len(request.message),
        },
    )

    try:
        pipeline = RagPipeline()
        response = await pipeline.answer(
            visa_type=request.visa_type,
            question=request.message,
            conversation_id=conversation_id,
        )
        return response

    except ValueError as exc:
        # Configuration error (e.g. missing API key) — tell the user clearly
        logger.error("Configuration error in chat pipeline", exc_info=exc)
        raise HTTPException(
            status_code=503,
            detail=(
                "The AI service is not configured correctly. "
                "Please check that AI_PROVIDER and the corresponding API key are set."
            ),
        ) from exc

    except Exception as exc:
        logger.error("Unexpected error in chat pipeline", exc_info=exc)
        raise HTTPException(
            status_code=503,
            detail="The AI service is temporarily unavailable. Please try again shortly.",
        ) from exc
