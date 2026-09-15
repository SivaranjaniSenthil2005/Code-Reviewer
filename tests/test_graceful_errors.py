"""Tests simulating system-wide edge cases, network disruptions, and graceful degradations (Phase 17)."""

import sys
import os
import pytest
from unittest.mock import AsyncMock, patch
from starlette.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app
from app.schemas.review import ReviewResult
from app.schemas.agent_outputs import RefactoringOutput
from app.services.llm.provider import LLMProviderError
from app.graph.nodes import validation_node
from app.rag.pipeline import RAGPipeline


@pytest.fixture
def client():
    return TestClient(app)


# 1. Edge Cases: Input Screening
def test_edge_case_empty_input(client):
    res = client.post("/api/review", json={"code": ""})
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


def test_edge_case_plain_prose_rejection(client):
    res = client.post(
        "/api/review",
        json={
            "code": "Once upon a time in a faraway kingdom there lived a kind king and queen who loved everyone in their castle.",
        },
    )
    assert res.status_code == 400
    assert "prose" in res.json()["detail"].lower()


def test_edge_case_unknown_obscure_language_handled_safely(client):
    with patch("app.api.routes.review.run_review", new_callable=AsyncMock) as mock_review:
        mock_review.return_value = ReviewResult(
            detected_language="unknown",
            summary="Review of custom dialect.",
            explanation="Custom script.",
            issues=[],
            refactored_code="CUSTOM_OP 123",
            complexity_assessment="Unknown",
            readability_score=70.0,
        )
        res = client.post("/api/review", json={"code": "CUSTOM_OP 123"})
        assert res.status_code == 200
        assert res.json()["detected_language"] == "unknown"


# 2. Total LLM Provider Failure Graceful Degradation
def test_edge_case_all_llm_providers_down(client):
    with patch("app.api.routes.review.run_review", side_effect=LLMProviderError("router", "Gemini & Mistral offline")):
        res = client.post("/api/review", json={"code": "def func(): return 1"})
        assert res.status_code == 502
        assert "temporarily unavailable" in res.json()["detail"]


# 3. RAG Failure Degradation
@pytest.mark.asyncio
async def test_edge_case_rag_failure_does_not_break_pipeline():
    pipeline = RAGPipeline()
    with patch.object(pipeline.retriever, "retrieve", side_effect=RuntimeError("Vector DB timeout")):
        context = await pipeline.get_context_for_review("python", "def f(): pass", "security")
        # Should return empty string without raising
        assert context == ""


# 4. Refactoring Failure Safe Fallback
@pytest.mark.asyncio
async def test_edge_case_refactoring_validation_failure_fallback():
    original = "def delicate_logic():\n    return 99\n"
    state = {
        "raw_code": original,
        "language": "python",
        "refactoring_output": RefactoringOutput(
            refactored_code="def broken_syntax( return 99",
            changes_summary="Bad code",
            reasoning=[],
        ),
    }
    with patch("app.agents.refactoring_agent.run_refactoring_retry", new_callable=AsyncMock) as mock_retry:
        mock_retry.return_value = RefactoringOutput(
            refactored_code="def still_broken( return 99",
            changes_summary="Bad code again",
            reasoning=[],
        )
        result = await validation_node(state)
        assert result["refactoring_validated"] is False
        assert result["refactoring_output"].refactored_code == original


# 5. MongoDB Outage Resilience
def test_edge_case_mongodb_down_still_returns_review(client):
    mock_review_result = ReviewResult(
        detected_language="python",
        summary="Review completed successfully.",
        explanation="Valid function.",
        issues=[],
        refactored_code="def foo(): return 1\n",
        complexity_assessment="O(1)",
        readability_score=90.0,
    )
    with (
        patch("app.api.routes.review.run_review", new_callable=AsyncMock) as mock_review,
        patch("app.api.routes.review.get_database", return_value=None),  # DB offline
    ):
        mock_review.return_value = mock_review_result
        res = client.post("/api/review", json={"code": "def foo(): return 1\n"})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "completed"
        assert data["review_id"] is None
        assert data["refactored_code"] == "def foo(): return 1\n"
