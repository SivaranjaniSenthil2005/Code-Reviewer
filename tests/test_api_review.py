"""Integration tests for FastAPI Review endpoints (Phase 13)."""

import sys
import os
import pytest
from unittest.mock import AsyncMock, patch
from starlette.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app
from app.schemas.review import ReviewResult
from app.schemas.bug import IssueFinding
from app.services.llm.provider import LLMProviderError


@pytest.fixture
def client():
    return TestClient(app)


def test_submit_code_review_happy_path(client):
    mock_review_result = ReviewResult(
        detected_language="python",
        summary="Review completed with 1 bug found.",
        explanation="Calculates math operations.",
        issues=[
            IssueFinding(line=2, category="bug", severity="high", description="Division by zero"),
        ],
        refactored_code="def div(a, b):\n    if b == 0: raise ValueError('Zero')\n    return a / b\n",
        complexity_assessment="O(1) time",
        readability_score=92.0,
        review_mode="quick",
    )

    with patch("app.api.routes.review.run_review", new_callable=AsyncMock) as mock_runner:
        mock_runner.return_value = mock_review_result

        payload = {
            "code": "def div(a, b):\n    return a / b\n",
            "language_hint": "python",
            "depth": "quick",
        }
        response = client.post("/api/review", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["detected_language"] == "python"
        assert len(data["issues"]) == 1
        assert data["issues"][0]["line"] == 2
        assert "processing_time_ms" in data
        assert data["readability_score"] == 92.0


def test_submit_empty_code_returns_400(client):
    payload = {"code": "   \n\t  ", "depth": "quick"}
    response = client.post("/api/review", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "empty" in data["detail"].lower()


def test_submit_plain_prose_returns_400(client):
    payload = {
        "code": "This is just a regular paragraph of english text explaining why dogs are great pets and why people love them so much.",
        "depth": "quick",
    }
    response = client.post("/api/review", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "prose" in data["detail"].lower()


def test_submit_oversized_code_returns_413(client):
    huge_code = "x = 1\n" * 3000
    payload = {"code": huge_code, "depth": "quick"}
    response = client.post("/api/review", json=payload)
    assert response.status_code == 413
    data = response.json()
    assert "exceeds" in data["detail"].lower()


def test_submit_code_llm_provider_failure_returns_502(client):
    with patch("app.api.routes.review.run_review", side_effect=LLMProviderError("router", "All providers down")):
        payload = {"code": "def foo(): pass", "depth": "quick"}
        response = client.post("/api/review", json=payload)
        assert response.status_code == 502
        data = response.json()
        assert "unavailable" in data["detail"].lower()
