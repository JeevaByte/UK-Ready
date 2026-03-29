"""
UKReady Backend — FastAPI entry point.

Initialises the FastAPI application, registers routers, configures CORS,
and wires up startup/shutdown lifecycle events.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import chat, health

# ---------------------------------------------------------------------------
# Logging — structured JSON-compatible format (CloudWatch-ready)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: runs startup tasks before yielding, shutdown tasks after."""
    settings = get_settings()
    logger.info(
        "UKReady backend starting",
        extra={
            "ai_provider": settings.ai_provider,
            "environment": settings.environment,
            "chroma_host": settings.chroma_host,
        },
    )
    yield
    logger.info("UKReady backend shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="UKReady API",
        description=(
            "Visa-aware AI Q&A for skilled migrants in the UK. "
            "Every answer is specific to your visa type and sourced from official gov.uk guidance."
        ),
        version="0.1.0",
        docs_url="/docs" if settings.environment == "development" else None,
        redoc_url="/redoc" if settings.environment == "development" else None,
        lifespan=lifespan,
    )

    # -------------------------------------------------------------------------
    # CORS — allow the Next.js frontend to call this API
    # -------------------------------------------------------------------------
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://frontend:3000",
    ]
    if settings.environment == "production":
        # In production, restrict to the deployed frontend domain
        allowed_origins = ["https://ukready.app"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # -------------------------------------------------------------------------
    # Routers
    # -------------------------------------------------------------------------
    app.include_router(health.router, tags=["health"])
    app.include_router(chat.router, prefix="/chat", tags=["chat"])

    return app


app = create_app()
