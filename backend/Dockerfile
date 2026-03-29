# =============================================================================
# UKReady Backend — Dockerfile
# =============================================================================
# Multi-stage build:
#   builder — installs Python dependencies
#   runtime — lean production image
# =============================================================================

FROM python:3.11-slim AS builder

WORKDIR /app

# System dependencies for lxml, psycopg2, and chromadb
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency installation
RUN pip install --no-cache-dir uv==0.5.14

# Copy dependency spec first for layer caching
COPY pyproject.toml .

# Install all dependencies (including dev for testing in CI)
RUN uv pip install --system -e ".[dev]"

# ---------------------------------------------------------------------------
# Runtime stage
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

WORKDIR /app

# Runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Non-root user for security
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Default command — overridden in docker-compose for dev (adds --reload)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
