"""
Vector store abstraction and ChromaDB implementation.

Defines a VectorStore ABC with store() and search() methods.
ChromaDBVectorStore is the concrete implementation for local dev.

In production, swap to OpenSearch Serverless by implementing
OpenSearchVectorStore (Terraform skeleton already defines the resource).
The swap requires only a config change — no caller changes needed.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """A chunk of text from a gov.uk document, ready for storage or retrieval."""

    text: str
    source_url: str
    page_title: str
    last_scraped: str
    chunk_index: int
    embedding: list[float] | None = None


@dataclass
class SearchResult:
    """A retrieved document chunk with its relevance distance."""

    text: str
    source_url: str
    page_title: str
    last_scraped: str
    distance: float  # Lower = more relevant in ChromaDB (cosine distance)


class VectorStore(ABC):
    """
    Abstract base class for vector stores.

    Implementations must support:
    - store(): Add document chunks with pre-computed embeddings
    - search(): Retrieve top-k most relevant chunks for a query
    - count(): Return total number of stored chunks
    """

    @abstractmethod
    async def store(self, chunks: list[DocumentChunk]) -> None:
        """
        Store a list of document chunks in the vector store.

        Args:
            chunks: List of chunks with text, metadata, and embeddings.
        """
        ...

    @abstractmethod
    async def search(self, query_embedding: list[float], top_k: int = 5) -> list[SearchResult]:
        """
        Find the most relevant document chunks for a query.

        Args:
            query_embedding: The query's embedding vector.
            top_k: Number of results to return.

        Returns:
            List of SearchResult sorted by relevance (most relevant first).
        """
        ...

    @abstractmethod
    async def count(self) -> int:
        """Return the total number of document chunks stored."""
        ...

    @abstractmethod
    async def clear(self) -> None:
        """Delete all stored documents (used for re-ingestion)."""
        ...


class ChromaDBVectorStore(VectorStore):
    """
    ChromaDB-backed vector store for local development.

    ChromaDB runs as a Docker service (see docker-compose.yml).
    Documents are stored with pre-computed embeddings and metadata,
    so ChromaDB is used purely as a vector index + retrieval engine.
    """

    def __init__(self) -> None:
        """Connect to ChromaDB server."""
        import chromadb

        from app.config import get_settings

        settings = get_settings()

        self._client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
        )
        self._collection_name = settings.chroma_collection

        # Get or create the collection.
        # We pass None for embedding_function since we provide pre-computed embeddings.
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "ChromaDB connected",
            extra={
                "host": settings.chroma_host,
                "port": settings.chroma_port,
                "collection": self._collection_name,
            },
        )

    async def store(self, chunks: list[DocumentChunk]) -> None:
        """
        Add document chunks to ChromaDB.

        Generates chunk IDs deterministically from source URL + chunk index
        so re-running ingestion is idempotent (upsert, not insert).
        """
        if not chunks:
            return

        ids = [f"{chunk.source_url}::chunk_{chunk.chunk_index}" for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [
            {
                "source_url": chunk.source_url,
                "page_title": chunk.page_title,
                "last_scraped": chunk.last_scraped,
                "chunk_index": chunk.chunk_index,
            }
            for chunk in chunks
        ]
        embeddings = [chunk.embedding for chunk in chunks if chunk.embedding is not None]

        if len(embeddings) != len(chunks):
            raise ValueError("All chunks must have pre-computed embeddings before storing")

        # Upsert is idempotent — safe to re-run ingestion
        self._collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,  # type: ignore[arg-type]
            embeddings=embeddings,  # type: ignore[arg-type]
        )
        logger.info("Stored chunks in ChromaDB", extra={"count": len(chunks)})

    async def search(self, query_embedding: list[float], top_k: int = 5) -> list[SearchResult]:
        """
        Query ChromaDB for the most relevant chunks.

        Uses cosine similarity (lower distance = more relevant).
        """
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self._collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        search_results: list[SearchResult] = []
        if not results["documents"] or not results["documents"][0]:
            return search_results

        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],  # type: ignore[index]
            results["distances"][0],  # type: ignore[index]
        ):
            search_results.append(
                SearchResult(
                    text=doc,
                    source_url=meta.get("source_url", ""),
                    page_title=meta.get("page_title", ""),
                    last_scraped=meta.get("last_scraped", ""),
                    distance=float(dist),
                )
            )

        return search_results

    async def count(self) -> int:
        """Return the total number of document chunks in the collection."""
        return int(self._collection.count())

    async def clear(self) -> None:
        """Delete and recreate the collection (clears all documents)."""
        self._client.delete_collection(self._collection_name)
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB collection cleared", extra={"collection": self._collection_name})


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStore:
    """
    Return the configured vector store instance (cached after first call).

    Currently returns ChromaDB for all environments.
    Future: check VECTOR_STORE env var to return OpenSearch in production.
    """
    return ChromaDBVectorStore()
