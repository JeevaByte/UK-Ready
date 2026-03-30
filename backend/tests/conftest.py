"""
Pytest configuration and shared fixtures for UKReady backend tests.

Sets up environment variables required by the application before any tests run.
All AI and vector store calls are mocked — no real external services are needed.
"""

import os

import pytest

# Set required environment variables before importing the app.
# This must happen before any app module is imported so pydantic-settings
# picks up the test values.
os.environ.setdefault("AI_PROVIDER", "anthropic")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-placeholder")
os.environ.setdefault("CHROMA_HOST", "localhost")
os.environ.setdefault("CHROMA_PORT", "8001")
os.environ.setdefault(
    "DATABASE_URL", "postgresql://ukready:test@localhost:5432/ukready"
)
os.environ.setdefault("ENVIRONMENT", "development")
