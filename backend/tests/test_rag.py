"""
Tests for the RAG pipeline components.

Tests chunking logic, embedding pipeline, and the RAG pipeline itself.
Uses in-memory/mock dependencies to avoid real API calls or network access.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ingestion.embedder import chunk_text, page_to_chunks
from app.ingestion.scraper import ScrapedPage
from app.models.visa import VisaType
from app.services.rag_pipeline import (
    RagPipeline,
    _build_context_documents,
    _extract_sources,
    _parse_confidence,
)
from app.services.vector_store import SearchResult


# ---------------------------------------------------------------------------
# Tests: text chunking
# ---------------------------------------------------------------------------


class TestChunking:
    """Verify the text chunking logic produces correct, overlapping chunks."""

    def test_short_text_returns_single_chunk(self) -> None:
        """Text shorter than chunk_size must return a single chunk."""
        text = "This is a short document about the Graduate visa."
        chunks = chunk_text(text, chunk_size=512, overlap=50)
        assert len(chunks) == 1
        assert chunks[0] == text.strip()

    def test_long_text_is_split(self) -> None:
        """Text longer than chunk_size must be split into multiple chunks."""
        # Create text with enough tokens to force multiple chunks
        # ~10 words per sentence × ~2 tokens per word = ~20 tokens per sentence
        # Need > 512 tokens = > ~25 sentences
        long_text = " ".join(["The Graduate visa allows skilled migrants to work in the UK."] * 40)
        chunks = chunk_text(long_text, chunk_size=128, overlap=20)
        assert len(chunks) > 1

    def test_chunk_overlap_shares_tokens(self) -> None:
        """Adjacent chunks must share overlapping content."""
        # Use a deterministic text and small chunk size for predictability
        text = " ".join([f"word{i}" for i in range(200)])
        chunk_size = 50
        overlap = 10
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)

        assert len(chunks) >= 2
        # The end of chunk[0] and start of chunk[1] should share content
        # (exact overlap depends on tokenisation, but the last word of chunk[0]
        #  should appear somewhere near the start of chunk[1])
        last_word_of_first_chunk = chunks[0].split()[-1]
        second_chunk_words = set(chunks[1].split()[:20])
        assert last_word_of_first_chunk in second_chunk_words, (
            "Expected overlap between adjacent chunks"
        )

    def test_empty_text_returns_empty_list_or_single_empty(self) -> None:
        """Empty input should not crash."""
        chunks = chunk_text("", chunk_size=512, overlap=50)
        # Either empty list or single empty string is acceptable
        assert len(chunks) <= 1

    def test_page_to_chunks_creates_correct_metadata(self) -> None:
        """page_to_chunks must create chunks with correct source metadata."""
        page = ScrapedPage(
            url="https://www.gov.uk/graduate-visa",
            title="Graduate visa",
            content="You can work in any job. You can change employers freely.",
            last_scraped="2026-01-01T00:00:00+00:00",
        )
        chunks = page_to_chunks(page)

        assert len(chunks) >= 1
        for i, chunk in enumerate(chunks):
            assert chunk.source_url == "https://www.gov.uk/graduate-visa"
            assert chunk.page_title == "Graduate visa"
            assert chunk.last_scraped == "2026-01-01T00:00:00+00:00"
            assert chunk.chunk_index == i
            assert len(chunk.text) > 0


# ---------------------------------------------------------------------------
# Tests: RAG pipeline helpers
# ---------------------------------------------------------------------------


class TestRagPipelineHelpers:
    """Unit tests for the RAG pipeline helper functions."""

    def test_build_context_documents_formats_correctly(self) -> None:
        """Context documents must be formatted with source and title headers."""
        results = [
            SearchResult(
                text="You can work full time.",
                source_url="https://www.gov.uk/graduate-visa",
                page_title="Graduate visa",
                last_scraped="2026-01-01T00:00:00+00:00",
                distance=0.1,
            ),
        ]
        context = _build_context_documents(results)
        assert "[Document 1]" in context
        assert "https://www.gov.uk/graduate-visa" in context
        assert "Graduate visa" in context
        assert "You can work full time." in context

    def test_build_context_empty_results(self) -> None:
        """Empty results should return a 'no documents found' message."""
        context = _build_context_documents([])
        assert "No relevant documents" in context

    def test_parse_confidence_high(self) -> None:
        """HIGH confidence marker must be extracted correctly."""
        text = "You can switch employers freely.\n\nCONFIDENCE: HIGH"
        clean, confidence = _parse_confidence(text)
        assert confidence == "HIGH"
        assert "CONFIDENCE" not in clean

    def test_parse_confidence_medium(self) -> None:
        """MEDIUM confidence marker must be extracted correctly."""
        text = "This may be possible.\nCONFIDENCE: MEDIUM"
        clean, confidence = _parse_confidence(text)
        assert confidence == "MEDIUM"

    def test_parse_confidence_low(self) -> None:
        """LOW confidence marker must be extracted correctly."""
        text = "Unclear from documents. CONFIDENCE: LOW"
        clean, confidence = _parse_confidence(text)
        assert confidence == "LOW"

    def test_parse_confidence_missing_defaults_to_medium(self) -> None:
        """When no confidence marker is present, default to MEDIUM."""
        text = "Some answer without a confidence marker."
        clean, confidence = _parse_confidence(text)
        assert confidence == "MEDIUM"
        assert clean == text  # Text unchanged if no marker found

    def test_extract_sources_deduplicates_urls(self) -> None:
        """Multiple chunks from the same URL must produce a single Source."""
        results = [
            SearchResult(
                text="Chunk 1 from gov.uk/graduate-visa",
                source_url="https://www.gov.uk/graduate-visa",
                page_title="Graduate visa",
                last_scraped="2026-01-01T00:00:00+00:00",
                distance=0.1,
            ),
            SearchResult(
                text="Chunk 2 from gov.uk/graduate-visa",
                source_url="https://www.gov.uk/graduate-visa",
                page_title="Graduate visa",
                last_scraped="2026-01-01T00:00:00+00:00",
                distance=0.2,
            ),
            SearchResult(
                text="Chunk from different page",
                source_url="https://www.gov.uk/graduate-visa/what-you-can-do",
                page_title="What you can do",
                last_scraped="2026-01-01T00:00:00+00:00",
                distance=0.3,
            ),
        ]
        sources = _extract_sources(results)
        assert len(sources) == 2  # 3 chunks, but only 2 unique URLs
        urls = [s.url for s in sources]
        assert "https://www.gov.uk/graduate-visa" in urls
        assert "https://www.gov.uk/graduate-visa/what-you-can-do" in urls


# ---------------------------------------------------------------------------
# Tests: RAG pipeline integration (mocked)
# ---------------------------------------------------------------------------


class TestRagPipelineIntegration:
    """Integration tests for the full RAG pipeline with mocked dependencies."""

    @pytest.fixture
    def mock_vector_store(self) -> MagicMock:
        """Vector store mock returning realistic search results."""
        store = MagicMock()
        store.search = AsyncMock(
            return_value=[
                SearchResult(
                    text="You can work in any job on the Graduate visa.",
                    source_url="https://www.gov.uk/graduate-visa/what-you-can-do",
                    page_title="Graduate visa: What you can do",
                    last_scraped="2026-01-01T00:00:00+00:00",
                    distance=0.1,
                )
            ]
        )
        return store

    @pytest.fixture
    def mock_ai_provider(self) -> MagicMock:
        """AI provider mock returning a HIGH-confidence answer."""
        provider = MagicMock()
        provider.complete = AsyncMock(
            return_value=(
                "Yes, you can switch employers freely on the Graduate visa. "
                "There is no restriction on changing employers or roles.\n\n"
                "CONFIDENCE: HIGH"
            )
        )
        return provider

    @pytest.mark.asyncio
    async def test_pipeline_returns_chat_response(
        self, mock_vector_store: MagicMock, mock_ai_provider: MagicMock
    ) -> None:
        """Pipeline must return a valid ChatResponse for a Graduate visa question."""
        with patch(
            "app.services.rag_pipeline._get_embedder"
        ) as mock_embedder:
            mock_model = MagicMock()
            mock_model.encode = MagicMock(return_value=MagicMock(tolist=lambda: [0.1] * 384))
            mock_embedder.return_value = mock_model

            pipeline = RagPipeline(
                vector_store=mock_vector_store,
                ai_provider=mock_ai_provider,
            )

            result = await pipeline.answer(
                visa_type=VisaType.GRADUATE,
                question="Can I switch employers?",
                conversation_id=uuid.uuid4(),
            )

        assert result.answer
        assert result.confidence == "HIGH"
        assert len(result.sources) == 1
        assert result.sources[0].url == "https://www.gov.uk/graduate-visa/what-you-can-do"
        assert result.disclaimer
        assert result.conversation_id

    @pytest.mark.asyncio
    async def test_pipeline_injects_visa_context(
        self, mock_vector_store: MagicMock, mock_ai_provider: MagicMock
    ) -> None:
        """The AI provider must be called with a system prompt containing visa context."""
        with patch("app.services.rag_pipeline._get_embedder") as mock_embedder:
            mock_model = MagicMock()
            mock_model.encode = MagicMock(return_value=MagicMock(tolist=lambda: [0.1] * 384))
            mock_embedder.return_value = mock_model

            pipeline = RagPipeline(
                vector_store=mock_vector_store,
                ai_provider=mock_ai_provider,
            )

            await pipeline.answer(
                visa_type=VisaType.SKILLED_WORKER,
                question="Can I change employers?",
                conversation_id=uuid.uuid4(),
            )

        # Verify the system prompt contained Skilled Worker specific context
        call_args = mock_ai_provider.complete.call_args
        system_prompt = call_args[1]["system"] if "system" in call_args[1] else call_args[0][0]
        assert "SKILLED WORKER" in system_prompt.upper()
        assert "sponsor" in system_prompt.lower()
