"""
RAG (Retrieval-Augmented Generation) pipeline.

This is the heart of UKReady. Given a user's question and visa type, it:
1. Embeds the query using the local sentence-transformer model
2. Retrieves the top-k most relevant gov.uk document chunks from ChromaDB
3. Assembles a visa-context-aware prompt (per spec)
4. Calls the configured AI provider
5. Parses confidence and sources from the response
6. Returns a structured ChatResponse

The prompt structure is deliberately explicit about visa type — we inject
the full visa context string (from models/visa.py) so the LLM cannot give
a generic or wrong-visa answer.
"""

import logging
import re
import uuid
from typing import Any, Literal, cast

from app.models.chat import ChatResponse, Source
from app.models.visa import VISA_CONTEXT, VisaType, get_visa_display_name
from app.services.ai_provider import AIProvider, get_ai_provider
from app.services.vector_store import SearchResult, VectorStore, get_vector_store

# Module-level cache for the sentence-transformer model.
# Loaded once on first request, then reused. Avoids reloading ~90MB on every call.
_cached_embedder: Any = None

logger = logging.getLogger(__name__)

# The disclaimer is always appended — non-negotiable for user safety
DISCLAIMER = (
    "This is information, not legal advice. "
    "For visa decisions, always consult a registered immigration solicitor or adviser. "
    "Visa rules change frequently — always verify current rules at gov.uk."
)

# System prompt template — visa context and retrieved docs are injected here
SYSTEM_PROMPT_TEMPLATE = """You are a knowledgeable assistant helping skilled migrants navigate UK visa rules, work rights, and government systems.

VISA CONTEXT:
The user is on a {visa_display_name}.
{visa_context}

IMPORTANT INSTRUCTIONS:
- Answer ONLY based on the context documents provided below and your knowledge of UK visa rules.
- If the context documents don't directly answer the question, say so clearly and give your best answer based on general knowledge of this visa type.
- All answers must be specific to the user's visa type ({visa_display_name}).
- Write in plain English — no legal jargon. Use short sentences and bullet points where helpful.
- At the END of your answer, on a new line, write exactly one of:
  CONFIDENCE: HIGH   (if the answer is directly stated in the context documents)
  CONFIDENCE: MEDIUM (if the answer is inferred or partially covered)
  CONFIDENCE: LOW    (if you are uncertain or the documents don't cover this well)
- Always cite the specific gov.uk pages you used.
- When uncertain about anything visa-related, recommend consulting a registered immigration solicitor.

CONTEXT DOCUMENTS:
{context_documents}

Answer the user's question based on the above context and visa-specific knowledge."""


def _build_context_documents(results: list[SearchResult]) -> str:
    """
    Format retrieved document chunks into a numbered context block.

    Each chunk includes its source URL and title so the LLM can reference
    specific pages in its answer (which we then parse into citations).
    """
    if not results:
        return "No relevant documents found in the knowledge base for this query."

    parts = []
    for i, result in enumerate(results, 1):
        parts.append(
            f"[Document {i}]\n"
            f"Source: {result.source_url}\n"
            f"Title: {result.page_title}\n"
            f"Content: {result.text}\n"
        )
    return "\n".join(parts)


def _parse_confidence(answer_text: str) -> tuple[str, Literal["HIGH", "MEDIUM", "LOW"]]:
    """
    Extract confidence level from the model's response.

    The model is instructed to end its answer with "CONFIDENCE: HIGH/MEDIUM/LOW".
    We parse this out and return (clean_answer, confidence_level).

    Falls back to MEDIUM if no confidence marker is found.
    """
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"
    clean_answer = answer_text.strip()

    # Look for "CONFIDENCE: HIGH/MEDIUM/LOW" (case-insensitive) anywhere in the response
    pattern = r"\bCONFIDENCE:\s*(HIGH|MEDIUM|LOW)\b"
    match = re.search(pattern, answer_text, re.IGNORECASE)
    if match:
        confidence = cast(Literal["HIGH", "MEDIUM", "LOW"], match.group(1).upper())
        # Remove the confidence marker from the answer text
        clean_answer = re.sub(pattern, "", answer_text, flags=re.IGNORECASE).strip()
        # Clean up any trailing newlines left after removing the marker
        clean_answer = re.sub(r"\n{3,}", "\n\n", clean_answer).strip()

    return clean_answer, confidence


def _extract_sources(results: list[SearchResult]) -> list[Source]:
    """
    Deduplicate retrieved chunks into a list of unique Source citations.

    Multiple chunks from the same URL are collapsed into a single Source.
    """
    seen_urls: set[str] = set()
    sources: list[Source] = []

    for result in results:
        if result.source_url and result.source_url not in seen_urls:
            seen_urls.add(result.source_url)
            sources.append(
                Source(
                    url=result.source_url,
                    title=result.page_title,
                    last_updated=result.last_scraped,
                )
            )

    return sources


def _get_embedder() -> Any:
    """
    Return a sentence-transformer embedder for query embedding.

    Uses the same model as the ingestion pipeline for consistency.
    all-MiniLM-L6-v2 is lightweight (22M params), fast, and accurate enough
    for this use case. Downloads on first use (~90MB), then cached locally.
    """
    global _cached_embedder
    if _cached_embedder is None:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading sentence-transformer model (first request may be slow)")
        _cached_embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _cached_embedder


class RagPipeline:
    """
    Orchestrates the full RAG flow: retrieve → prompt → generate → parse.

    Instantiated per-request (lightweight — no state beyond config).
    """

    def __init__(
        self,
        vector_store: VectorStore | None = None,
        ai_provider: AIProvider | None = None,
    ) -> None:
        """
        Initialise the pipeline with optional dependency injection.

        When vector_store or ai_provider are None, defaults are loaded from
        config. Explicit injection is used in tests to avoid real API calls.
        """
        self._vector_store = vector_store or get_vector_store()
        self._ai_provider = ai_provider or get_ai_provider()

    async def answer(
        self,
        visa_type: VisaType,
        question: str,
        conversation_id: uuid.UUID,
    ) -> ChatResponse:
        """
        Generate a visa-aware, sourced answer to a user question.

        Steps:
        1. Embed the question
        2. Retrieve top-k relevant chunks from ChromaDB
        3. Build the system prompt with visa context + retrieved docs
        4. Call the AI provider
        5. Parse confidence and extract sources
        6. Return structured ChatResponse

        Args:
            visa_type: The user's current visa type (controls context injection).
            question: The user's question in plain text.
            conversation_id: Session UUID for logging / future conversation memory.

        Returns:
            A ChatResponse with answer, confidence, sources, and disclaimer.
        """
        from app.config import get_settings

        settings = get_settings()

        logger.info(
            "RAG pipeline started",
            extra={
                "visa_type": visa_type.value,
                "conversation_id": str(conversation_id),
            },
        )

        # Step 1: Embed the user's question
        embedder = _get_embedder()
        query_embedding: list[float] = embedder.encode(question).tolist()

        # Step 2: Retrieve relevant document chunks
        results = await self._vector_store.search(
            query_embedding=query_embedding,
            top_k=settings.rag_top_k,
        )
        logger.info("Retrieved chunks", extra={"count": len(results)})

        # Step 3: Build the system prompt
        context_documents = _build_context_documents(results)
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            visa_display_name=get_visa_display_name(visa_type),
            visa_context=VISA_CONTEXT[visa_type],
            context_documents=context_documents,
        )

        # Step 4: Call the AI provider
        raw_answer = await self._ai_provider.complete(
            system=system_prompt,
            user=question,
        )

        # Step 5: Parse confidence level and clean the answer
        clean_answer, confidence = _parse_confidence(raw_answer)

        # Step 6: Extract unique source citations from retrieved chunks
        sources = _extract_sources(results)

        logger.info(
            "RAG pipeline complete",
            extra={
                "confidence": confidence,
                "sources_count": len(sources),
                "conversation_id": str(conversation_id),
            },
        )

        return ChatResponse(
            answer=clean_answer,
            confidence=confidence,
            sources=sources,
            conversation_id=conversation_id,
            disclaimer=DISCLAIMER,
        )
