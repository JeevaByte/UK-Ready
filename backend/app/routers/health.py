"""
Health check endpoint — GET /health

Returns the operational status of the service including:
- ChromaDB availability and document count
- Which AI provider is configured

Used by Docker Compose health checks, load balancers, and monitoring.
"""

import logging

from fastapi import APIRouter

from app.config import get_settings
from app.models.chat import HealthResponse
from app.services.vector_store import get_vector_store

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Service health check")
async def health_check() -> HealthResponse:
    """
    Check the health of all UKReady backend dependencies.

    Returns overall status plus per-dependency detail so operators can
    quickly identify which component is degraded.
    """
    settings = get_settings()
    vector_store_status: str = "ok"
    documents_indexed = 0

    try:
        vector_store = get_vector_store()
        documents_indexed = await vector_store.count()
        if documents_indexed == 0:
            # ChromaDB is reachable but no documents have been ingested yet.
            # This is expected on first run before the ingest service completes.
            vector_store_status = "empty"
    except Exception as exc:
        logger.warning("ChromaDB health check failed", exc_info=exc)
        vector_store_status = "degraded"

    overall_status = "ok" if vector_store_status in ("ok", "empty") else "degraded"

    return HealthResponse(
        status=overall_status,  # type: ignore[arg-type]
        vector_store=vector_store_status,  # type: ignore[arg-type]
        ai_provider=settings.ai_provider,
        documents_indexed=documents_indexed,
    )
