"""Tests for Phase 11 Review Synthesis & Persistence."""

import sys
import os
import pytest
from unittest.mock import AsyncMock, patch
from mongomock_motor import AsyncMongoMockClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.schemas.review import ReviewResult
from app.schemas.bug import IssueFinding, BugAnalysisResult
from app.schemas.security import SecurityFinding, SecurityAnalysisResult
from app.schemas.agent_outputs import (
    CodeAnalysisOutput,
    QualityAnalysisOutput,
    ComplexityAnalysisOutput,
    RefactoringOutput,
)
from app.graph.review_synthesis import synthesize_and_persist_review
from app.agents.synthesizer_agent import deduplicate_findings
from app.repositories.review_repository import ReviewRepository
from app.repositories.finding_repository import FindingRepository
from app.repositories.agent_run_repository import AgentRunRepository


@pytest.fixture
def mock_db():
    client = AsyncMongoMockClient()
    return client["test_code_review_db"]


def test_deduplication_exact_line_preserves_higher_severity():
    findings = [
        IssueFinding(line=14, category="bug", severity="medium", description="Possible SQL injection in user query string"),
        IssueFinding(line=14, category="vulnerability", severity="critical", description="Critical SQL injection vulnerability in user query"),
        IssueFinding(line=20, category="style", severity="low", description="Unused import os"),
        IssueFinding(line=None, category="bug", severity="low", description="File lacks newline at EOF"),
    ]

    deduped = deduplicate_findings(findings)
    assert len(deduped) == 3
    line_14 = next(f for f in deduped if f.line == 14)
    assert line_14.severity == "critical"
    assert "SQL" in line_14.description
    assert line_14.line == 14


@pytest.mark.asyncio
async def test_synthesis_and_persistence_round_trip(mock_db):
    state = {
        "raw_code": "def vulnerable_fn(param):\n    eval(param)\n",
        "code": "def vulnerable_fn(param):\n    eval(param)\n",
        "language": "python",
        "depth": "deep",
        "user_id": "user-456",
        "analysis_output": CodeAnalysisOutput(
            explanation="Executes arbitrary code dynamically via eval.",
            key_components=["vulnerable_fn()"],
            summary="Dynamic code execution wrapper.",
        ),
        "bug_output": BugAnalysisResult(
            issues=[
                IssueFinding(line=2, category="bug", severity="high", description="Arbitrary code execution risk with eval()"),
            ],
            summary="Found 1 high severity bug",
        ),
        "security_output": SecurityAnalysisResult(
            vulnerabilities=[
                SecurityFinding(
                    line=2,
                    category="vulnerability",
                    severity="critical",
                    description="Arbitrary code execution vulnerability with dangerous eval() usage",
                    cwe_id="CWE-95",
                ),
            ],
            risk_level="critical",
            summary="Critical CWE-95 detected",
        ),
        "quality_output": QualityAnalysisOutput(
            readability_score=65.0,
            style_issues=[
                IssueFinding(line=1, category="style", severity="low", description="Function name is non-descriptive"),
            ],
            maintainability_notes="Poor security hygiene.",
        ),
        "complexity_output": ComplexityAnalysisOutput(
            time_complexity="O(1)",
            space_complexity="O(1)",
            cyclomatic_estimate="Low",
            complexity_assessment="Constant overhead.",
        ),
        "refactoring_output": RefactoringOutput(
            refactored_code="import ast\ndef safe_fn(param: str) -> object:\n    return ast.literal_eval(param)\n",
            changes_summary="Replaced unsafe eval with ast.literal_eval",
            reasoning=["Prevents code injection."],
        ),
        "refactoring_validated": True,
    }

    result, review_id = await synthesize_and_persist_review(mock_db, state)

    # 1. Verify Synthesized Result
    assert isinstance(result, ReviewResult)
    assert result.detected_language == "python"
    assert result.refactoring_validated is True
    assert len(result.issues) == 2  # Deduped: 1 on line 2 (critical kept), 1 on line 1

    # 2. Verify review_id returned
    assert review_id is not None

    # 3. Verify retrieval from DB
    review_repo = ReviewRepository(mock_db)
    finding_repo = FindingRepository(mock_db)
    agent_run_repo = AgentRunRepository(mock_db)

    saved_review = await review_repo.get_by_id(review_id)
    assert saved_review is not None
    assert saved_review["language"] == "python"
    assert saved_review["user_id"] == "user-456"

    saved_findings = await finding_repo.list_by_review_id(review_id)
    assert len(saved_findings) == 2

    agent_runs = await agent_run_repo.list_by_review_id(review_id)
    assert len(agent_runs) >= 4
