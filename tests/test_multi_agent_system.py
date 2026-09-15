"""Tests for Multi-Agent Review System (Phase 6)."""

import sys
import os
import pytest
from unittest.mock import AsyncMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.schemas.bug import IssueFinding, BugAnalysisResult
from app.schemas.security import SecurityFinding, SecurityAnalysisResult
from app.schemas.agent_outputs import (
    CodeAnalysisOutput,
    QualityAnalysisOutput,
    ComplexityAnalysisOutput,
    RefactoringOutput,
)
from app.services.code.line_mapper import build_line_map
from app.agents.code_analysis_agent import run_code_analysis_agent
from app.agents.bug_agent import run_bug_agent
from app.agents.security_agent import run_security_agent
from app.agents.quality_agent import run_quality_agent
from app.agents.complexity_agent import run_complexity_agent
from app.agents.refactoring_agent import run_refactoring_agent
from app.agents.validation_agent import run_validation_agent
from app.agents.synthesizer_agent import synthesize_review_result, deduplicate_findings


@pytest.mark.asyncio
async def test_code_analysis_agent():
    mock_router = AsyncMock()
    mock_router.generate_structured.return_value = CodeAnalysisOutput(
        explanation="Sorts numbers using quicksort.",
        key_components=["quicksort()", "partition()"],
        summary="Quicksort algorithm implementation",
    )
    res = await run_code_analysis_agent("def quicksort(): pass", "python", router=mock_router)
    assert "quicksort" in res.explanation.lower()
    assert len(res.key_components) == 2


@pytest.mark.asyncio
async def test_bug_agent_with_line_remapping():
    mock_router = AsyncMock()
    mock_router.generate_structured.return_value = BugAnalysisResult(
        issues=[
            IssueFinding(line=2, category="bug", severity="high", description="Off-by-one loop index", suggestion="Use < instead of <="),
        ],
        summary="Found 1 loop defect",
    )
    original_code = "# Comment\ndef loop():\n    for i in range(10):\n        pass\n"
    normalized_code = "def loop():\n    for i in range(10):\n        pass\n"
    line_map = build_line_map(original_code, normalized_code)

    res = await run_bug_agent(normalized_code, "python", line_map=line_map, router=mock_router)
    assert len(res.issues) == 1
    # Check that line is mapped back to original coordinates
    assert res.issues[0].line is not None


@pytest.mark.asyncio
async def test_security_agent():
    mock_router = AsyncMock()
    mock_router.generate_structured.return_value = SecurityAnalysisResult(
        vulnerabilities=[
            SecurityFinding(line=5, category="vulnerability", severity="critical", description="Hardcoded API secret key", cwe_id="CWE-798"),
        ],
        risk_level="critical",
        summary="Critical hardcoded secret detected",
    )
    res = await run_security_agent("API_KEY = 'secret123'", "python", router=mock_router)
    assert len(res.vulnerabilities) == 1
    assert res.risk_level == "critical"


@pytest.mark.asyncio
async def test_quality_agent():
    mock_router = AsyncMock()
    mock_router.generate_structured.return_value = QualityAnalysisOutput(
        readability_score=82.0,
        style_issues=[
            IssueFinding(line=1, category="style", severity="low", description="Variable name 'x' is ambiguous"),
        ],
        maintainability_notes="Good modularity.",
    )
    res = await run_quality_agent("x = 10", "python", router=mock_router)
    assert res.readability_score == 82.0


@pytest.mark.asyncio
async def test_complexity_agent():
    mock_router = AsyncMock()
    mock_router.generate_structured.return_value = ComplexityAnalysisOutput(
        time_complexity="O(N log N)",
        space_complexity="O(log N)",
        cyclomatic_estimate="Medium",
        complexity_assessment="Divide and conquer algorithm with logarithmic stack depth.",
    )
    res = await run_complexity_agent("def sort(): pass", "python", router=mock_router)
    assert res.time_complexity == "O(N log N)"


@pytest.mark.asyncio
async def test_refactoring_agent():
    mock_router = AsyncMock()
    mock_router.generate_structured.return_value = RefactoringOutput(
        refactored_code="def clean_func():\n    return 42\n",
        changes_summary="Added type annotations and cleaned return.",
        reasoning=["Improves type safety."],
    )
    issues = [IssueFinding(line=1, category="style", severity="low", description="Missing typing")]
    res = await run_refactoring_agent("def clean_func(): return 42", "python", issues=issues, router=mock_router)
    assert "clean_func" in res.refactored_code


@pytest.mark.asyncio
async def test_validation_agent():
    # Valid Python refactor
    valid, err = await run_validation_agent("def f(): pass", "def f():\n    return 1\n", "python")
    assert valid is True
    assert err is None

    # Invalid Python syntax refactor
    invalid, err = await run_validation_agent("def f(): pass", "def f( return 1", "python")
    assert invalid is False
    assert err is not None


def test_deduplicate_overlapping_findings():
    findings = [
        IssueFinding(line=10, category="bug", severity="medium", description="Possible SQL injection in query concat"),
        IssueFinding(line=10, category="vulnerability", severity="critical", description="Critical SQL injection vulnerability in user query"),
        IssueFinding(line=15, category="style", severity="low", description="Missing docstring"),
    ]
    deduped = deduplicate_findings(findings)
    assert len(deduped) == 2
    # The line 10 critical finding should be kept over the medium one
    line_10 = next(f for f in deduped if f.line == 10)
    assert line_10.severity == "critical"


def test_synthesizer_partial_failure_tolerance():
    # Simulate: bug_agent failed (None / empty), but code_analysis and quality succeeded
    analysis = CodeAnalysisOutput(explanation="A web scraper script.", key_components=[], summary="Web scraper")
    quality = QualityAnalysisOutput(readability_score=78.0, style_issues=[], maintainability_notes="Clean script")

    result = synthesize_review_result(
        language="python",
        original_code="import requests\n",
        analysis_output=analysis,
        bug_output=None,  # Simulated failure
        security_output=None,  # Skipped
        quality_output=quality,
        complexity_output=None,  # Simulated failure
        refactoring_output=None,
        review_mode="quick",
    )

    assert result.detected_language == "python"
    assert "web scraper" in result.explanation.lower()
    assert result.readability_score == 78.0
    assert result.refactored_code == "import requests\n"
    assert result.refactoring_validated is True
