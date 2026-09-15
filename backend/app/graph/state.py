"""Review state schema for LangGraph multi-agent orchestration."""

from typing import Any, Dict, List, Optional, TypedDict
from app.schemas.review import ReviewResult
from app.schemas.bug import BugAnalysisResult
from app.schemas.security import SecurityAnalysisResult
from app.schemas.agent_outputs import (
    CodeAnalysisOutput,
    QualityAnalysisOutput,
    ComplexityAnalysisOutput,
    RefactoringOutput,
)
from app.services.code.line_mapper import LineMap


class ReviewState(TypedDict, total=False):
    """Complete mutable state passed across LangGraph nodes."""
    # Inputs
    raw_code: str
    code: str  # Normalized code
    language: str
    depth: str  # "quick" | "deep"
    line_map: Optional[LineMap]
    user_id: Optional[str]
    repo_name: Optional[str]
    file_path: Optional[str]

    # RAG Context (injected in Deep mode)
    rag_context: Optional[str]

    # Intermediate Agent Outputs
    analysis_output: Optional[CodeAnalysisOutput]
    bug_output: Optional[BugAnalysisResult]
    security_output: Optional[SecurityAnalysisResult]
    quality_output: Optional[QualityAnalysisOutput]
    complexity_output: Optional[ComplexityAnalysisOutput]
    refactoring_output: Optional[RefactoringOutput]
    refactoring_validated: bool
    refactor_retry_count: int

    # Final Synthesized Result & Persistence
    final_result: Optional[ReviewResult]
    review_id: Optional[str]
    errors: List[str]
    agent_run_ids: List[str]
