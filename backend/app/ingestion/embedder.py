"""
Document chunking and embedding pipeline for UKReady's RAG knowledge base.

Takes scraped gov.uk pages, splits them into overlapping chunks of ~512 tokens,
generates embeddings for each chunk using sentence-transformers, then stores
everything in ChromaDB.

Chunking strategy:
- 512 tokens per chunk, 50-token overlap for context continuity
- Section headers (## / ###) are preserved in each chunk for context
- Source URL, page title, and scrape date are stored as metadata

Embedding model: all-MiniLM-L6-v2 (sentence-transformers)
- 384-dimensional embeddings
- ~22M parameters — fast, lightweight, no API key required
- Sufficient accuracy for this use case
- Downloads once (~90MB) and caches locally

Run this as a one-shot script: python -m app.ingestion.embedder
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

import tiktoken

from app.ingestion.scraper import ScrapedPage, scrape_all_pages
from app.services.vector_store import DocumentChunk, get_vector_store

logger = logging.getLogger(__name__)

# Chunking config — matches pyproject.toml defaults
CHUNK_SIZE_TOKENS = 512
CHUNK_OVERLAP_TOKENS = 50

# Tokenizer — gpt2 BPE tokenizer is a good approximation for most models
TOKENIZER_NAME = "gpt2"

# Sentinel file to skip re-ingestion on Docker restarts
INGEST_STATE_DIR = Path("/app/.ingest_state")
INGEST_DONE_MARKER = INGEST_STATE_DIR / "ingestion_complete"


def _get_tokenizer() -> tiktoken.Encoding:
    """Return the tiktoken tokenizer (cached after first load)."""
    return tiktoken.get_encoding(TOKENIZER_NAME)


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE_TOKENS,
    overlap: int = CHUNK_OVERLAP_TOKENS,
) -> list[str]:
    """
    Split text into overlapping token-bounded chunks.

    Uses tiktoken to count tokens accurately rather than guessing by
    character count — ensures chunks stay within model context limits.

    Args:
        text: The full document text to chunk.
        chunk_size: Target maximum tokens per chunk.
        overlap: Number of tokens shared between adjacent chunks.

    Returns:
        List of text chunks, each at most chunk_size tokens.
    """
    tokenizer = _get_tokenizer()
    tokens = tokenizer.encode(text)

    if len(tokens) <= chunk_size:
        # Document fits in a single chunk
        return [text]

    chunks: list[str] = []
    start = 0

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text_str = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text_str.strip())

        # Advance by (chunk_size - overlap) to create the sliding window
        start += chunk_size - overlap

    return chunks


def _get_embedder() -> object:
    """
    Load the sentence-transformer model for embedding.

    Downloads on first run (~90MB), then cached by the transformers library.
    all-MiniLM-L6-v2 produces 384-dimensional embeddings — fast and accurate.
    """
    from sentence_transformers import SentenceTransformer

    logger.info("Loading sentence-transformer model (downloads on first run, ~90MB)")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    logger.info("Sentence-transformer model loaded")
    return model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a list of text chunks.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors (one per input text).
    """
    model = _get_embedder()
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)  # type: ignore[union-attr]
    return [emb.tolist() for emb in embeddings]


def page_to_chunks(page: ScrapedPage) -> list[DocumentChunk]:
    """
    Convert a scraped page into DocumentChunks ready for storage.

    Each chunk gets:
    - The text content (with section headers preserved)
    - Source URL and page title as metadata
    - The scrape date for citation accuracy
    - A sequential chunk index

    Args:
        page: A successfully scraped gov.uk page.

    Returns:
        List of DocumentChunk (without embeddings — added in embed_chunks()).
    """
    text_chunks = chunk_text(page.content)
    logger.info(
        "Chunked page",
        extra={"url": page.url, "title": page.title, "chunk_count": len(text_chunks)},
    )

    return [
        DocumentChunk(
            text=chunk_text_,
            source_url=page.url,
            page_title=page.title,
            last_scraped=page.last_scraped,
            chunk_index=i,
        )
        for i, chunk_text_ in enumerate(text_chunks)
    ]


def embed_chunks(chunks: list[DocumentChunk]) -> list[DocumentChunk]:
    """
    Add embeddings to a list of DocumentChunks.

    Batches all chunk texts together for efficient embedding.

    Args:
        chunks: Chunks without embeddings.

    Returns:
        Same chunks with .embedding populated.
    """
    texts = [chunk.text for chunk in chunks]
    embeddings = embed_texts(texts)

    for chunk, embedding in zip(chunks, embeddings):
        chunk.embedding = embedding

    return chunks


async def run_ingestion(force: bool = False) -> None:
    """
    Main ingestion entry point: scrape → chunk → embed → store.

    Checks for the completion marker file to avoid re-ingesting on
    Docker Compose restarts. Pass force=True to re-ingest anyway.

    Args:
        force: If True, re-ingest even if ingestion has run before.
    """
    # Check if ingestion has already run (idempotency guard)
    if not force and INGEST_DONE_MARKER.exists():
        logger.info(
            "Ingestion already complete (marker file found). "
            "Delete %s or pass --force to re-ingest.",
            INGEST_DONE_MARKER,
        )
        return

    logger.info("Starting document ingestion pipeline")

    # Step 1: Scrape gov.uk pages
    pages = scrape_all_pages()
    if not pages:
        logger.error("No pages scraped — aborting ingestion")
        sys.exit(1)

    # Step 2: Chunk all pages
    all_chunks: list[DocumentChunk] = []
    for page in pages:
        chunks = page_to_chunks(page)
        all_chunks.extend(chunks)

    logger.info("Total chunks created", extra={"count": len(all_chunks)})

    # Step 3: Generate embeddings
    logger.info("Generating embeddings (this may take a few minutes on first run)")
    embedded_chunks = embed_chunks(all_chunks)

    # Step 4: Store in vector store
    vector_store = get_vector_store()
    await vector_store.store(embedded_chunks)

    total = await vector_store.count()
    logger.info("Ingestion complete", extra={"documents_indexed": total})

    # Write completion marker so Docker restarts skip re-ingestion
    INGEST_STATE_DIR.mkdir(parents=True, exist_ok=True)
    INGEST_DONE_MARKER.write_text(f"Ingested {total} chunks from {len(pages)} pages\n")
    logger.info("Ingestion marker written", extra={"path": str(INGEST_DONE_MARKER)})


if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    force = "--force" in sys.argv
    asyncio.run(run_ingestion(force=force))
