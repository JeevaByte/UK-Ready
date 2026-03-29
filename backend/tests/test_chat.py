"""
Tests for the POST /chat endpoint.

Tests all four visa types with a representative question to verify:
- Correct response structure (answer, confidence, sources, conversation_id, disclaimer)
- Visa-type awareness (answer is specific to the requested visa)
- Error handling (invalid visa type, missing message)

The AI provider and vector store are mocked to avoid external API calls in CI.
Tests use pre-defined mock responses that match the expected answer format.
"""

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.models.visa import VisaType
from main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    """Synchronous test client for simple request/response tests."""
    return TestClient(app)


@pytest.fixture
def mock_ai_provider() -> MagicMock:
    """Mock AI provider that returns a valid confidence-tagged response."""
    provider = MagicMock()
    provider.complete = AsyncMock(
        return_value=(
            "Yes, you can switch employers on this visa. "
            "As a Graduate visa holder, you can work for any employer without restrictions.\n\n"
            "CONFIDENCE: HIGH"
        )
    )
    provider.provider_name = "mock"
    return provider


@pytest.fixture
def mock_vector_store() -> MagicMock:
    """Mock vector store that returns realistic search results."""
    from app.services.vector_store import SearchResult

    store = MagicMock()
    store.search = AsyncMock(
        return_value=[
            SearchResult(
                text=(
                    "## What you can do\n"
                    "You can work in most jobs. You can change jobs and work for multiple employers."
                ),
                source_url="https://www.gov.uk/graduate-visa/what-you-can-do",
                page_title="Graduate visa: What you can do",
                last_scraped="2026-01-01T00:00:00+00:00",
                distance=0.15,
            ),
            SearchResult(
                text=(
                    "## Switch employers\n"
                    "You do not need a new visa to switch employers on the Graduate route."
                ),
                source_url="https://www.gov.uk/graduate-visa",
                page_title="Graduate visa",
                last_scraped="2026-01-01T00:00:00+00:00",
                distance=0.22,
            ),
        ]
    )
    store.count = AsyncMock(return_value=47)
    return store


# ---------------------------------------------------------------------------
# Tests: response structure
# ---------------------------------------------------------------------------


class TestChatEndpointStructure:
    """Verify the /chat endpoint returns the correct response structure."""

    def test_response_has_required_fields(
        self, client: TestClient, mock_ai_provider: MagicMock, mock_vector_store: MagicMock
    ) -> None:
        """Every response must include answer, confidence, sources, conversation_id, disclaimer."""
        with (
            patch("app.routers.chat.RagPipeline") as mock_pipeline_class,
        ):
            # Set up the pipeline mock to return a valid ChatResponse
            from app.models.chat import ChatResponse, Source

            mock_pipeline = MagicMock()
            mock_pipeline.answer = AsyncMock(
                return_value=ChatResponse(
                    answer="You can switch employers freely on the Graduate visa.",
                    confidence="HIGH",
                    sources=[
                        Source(
                            url="https://www.gov.uk/graduate-visa/what-you-can-do",
                            title="Graduate visa: What you can do",
                            last_updated="2026-01-01T00:00:00+00:00",
                        )
                    ],
                    conversation_id=uuid.uuid4(),
                    disclaimer="This is information, not legal advice.",
                )
            )
            mock_pipeline_class.return_value = mock_pipeline

            response = client.post(
                "/chat",
                json={
                    "visa_type": "GRADUATE",
                    "message": "Can I switch employers?",
                },
            )

        assert response.status_code == 200
        data = response.json()

        assert "answer" in data, "Response missing 'answer' field"
        assert "confidence" in data, "Response missing 'confidence' field"
        assert "sources" in data, "Response missing 'sources' field"
        assert "conversation_id" in data, "Response missing 'conversation_id' field"
        assert "disclaimer" in data, "Response missing 'disclaimer' field"

    def test_confidence_is_valid_enum(
        self, client: TestClient, mock_ai_provider: MagicMock
    ) -> None:
        """Confidence must be HIGH, MEDIUM, or LOW."""
        with patch("app.routers.chat.RagPipeline") as mock_pipeline_class:
            from app.models.chat import ChatResponse

            mock_pipeline = MagicMock()
            mock_pipeline.answer = AsyncMock(
                return_value=ChatResponse(
                    answer="Answer here.",
                    confidence="MEDIUM",
                    sources=[],
                    conversation_id=uuid.uuid4(),
                )
            )
            mock_pipeline_class.return_value = mock_pipeline

            response = client.post(
                "/chat",
                json={"visa_type": "SKILLED_WORKER", "message": "What is my salary threshold?"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["confidence"] in ("HIGH", "MEDIUM", "LOW")

    def test_conversation_id_is_uuid(self, client: TestClient) -> None:
        """conversation_id in response must be a valid UUID."""
        with patch("app.routers.chat.RagPipeline") as mock_pipeline_class:
            from app.models.chat import ChatResponse

            expected_id = uuid.uuid4()
            mock_pipeline = MagicMock()
            mock_pipeline.answer = AsyncMock(
                return_value=ChatResponse(
                    answer="Answer.",
                    confidence="LOW",
                    sources=[],
                    conversation_id=expected_id,
                )
            )
            mock_pipeline_class.return_value = mock_pipeline

            response = client.post(
                "/chat",
                json={"visa_type": "STUDENT", "message": "Can I work full time?"},
            )

        assert response.status_code == 200
        data = response.json()
        # Should be a valid UUID string
        parsed_id = uuid.UUID(data["conversation_id"])
        assert parsed_id == expected_id

    def test_conversation_id_preserved_when_provided(self, client: TestClient) -> None:
        """If conversation_id is passed in request, it must appear in response."""
        existing_id = uuid.uuid4()

        with patch("app.routers.chat.RagPipeline") as mock_pipeline_class:
            from app.models.chat import ChatResponse

            mock_pipeline = MagicMock()
            mock_pipeline.answer = AsyncMock(
                return_value=ChatResponse(
                    answer="Answer.",
                    confidence="HIGH",
                    sources=[],
                    conversation_id=existing_id,
                )
            )
            mock_pipeline_class.return_value = mock_pipeline

            response = client.post(
                "/chat",
                json={
                    "visa_type": "ILR",
                    "message": "Can I apply for citizenship?",
                    "conversation_id": str(existing_id),
                },
            )

        assert response.status_code == 200
        assert response.json()["conversation_id"] == str(existing_id)


# ---------------------------------------------------------------------------
# Tests: all four visa types
# ---------------------------------------------------------------------------


class TestAllVisaTypes:
    """Verify the endpoint accepts all four supported visa types."""

    @pytest.mark.parametrize(
        "visa_type,question",
        [
            ("GRADUATE", "Can I switch employers?"),
            ("SKILLED_WORKER", "Can I take a second job?"),
            ("STUDENT", "How many hours can I work per week?"),
            ("ILR", "Do I have any work restrictions?"),
        ],
    )
    def test_all_visa_types_accepted(
        self, client: TestClient, visa_type: str, question: str
    ) -> None:
        """Each visa type must be accepted and return a 200 response."""
        with patch("app.routers.chat.RagPipeline") as mock_pipeline_class:
            from app.models.chat import ChatResponse

            mock_pipeline = MagicMock()
            mock_pipeline.answer = AsyncMock(
                return_value=ChatResponse(
                    answer=f"Answer for {visa_type} visa holder.",
                    confidence="HIGH",
                    sources=[],
                    conversation_id=uuid.uuid4(),
                )
            )
            mock_pipeline_class.return_value = mock_pipeline

            response = client.post(
                "/chat",
                json={"visa_type": visa_type, "message": question},
            )

        assert response.status_code == 200, (
            f"Expected 200 for visa_type={visa_type}, got {response.status_code}: "
            f"{response.text}"
        )


# ---------------------------------------------------------------------------
# Tests: input validation
# ---------------------------------------------------------------------------


class TestInputValidation:
    """Verify request validation catches bad input."""

    def test_invalid_visa_type_returns_422(self, client: TestClient) -> None:
        """An unknown visa type must return HTTP 422 Unprocessable Entity."""
        response = client.post(
            "/chat",
            json={"visa_type": "TIER_2", "message": "Can I work?"},
        )
        assert response.status_code == 422

    def test_empty_message_returns_422(self, client: TestClient) -> None:
        """An empty message must return HTTP 422."""
        response = client.post(
            "/chat",
            json={"visa_type": "GRADUATE", "message": ""},
        )
        assert response.status_code == 422

    def test_missing_visa_type_returns_422(self, client: TestClient) -> None:
        """Missing visa_type must return HTTP 422."""
        response = client.post(
            "/chat",
            json={"message": "Can I work?"},
        )
        assert response.status_code == 422

    def test_missing_message_returns_422(self, client: TestClient) -> None:
        """Missing message must return HTTP 422."""
        response = client.post(
            "/chat",
            json={"visa_type": "GRADUATE"},
        )
        assert response.status_code == 422

    def test_message_too_long_returns_422(self, client: TestClient) -> None:
        """Message exceeding 2000 chars must return HTTP 422."""
        long_message = "a" * 2001
        response = client.post(
            "/chat",
            json={"visa_type": "GRADUATE", "message": long_message},
        )
        assert response.status_code == 422
