"""Comprehensive review schemas conforming to platform candidate output JSON schema."""

from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.bug import IssueFinding


class ComplexityAssessment(BaseModel):
    """Detailed complexity metrics and Big-O assessment."""
    time_complexity: str = Field("O(N)", description="Estimated asymptotic time complexity (Big-O)")
    space_complexity: str = Field("O(1)", description="Estimated asymptotic space complexity (Big-O)")
    cyclomatic_estimate: Optional[str] = Field("Low", description="Cyclomatic complexity estimate (Low/Medium/High)")
    assessment: str = Field(..., description="Summary explanation of algorithmic and structural complexity")


class ReviewResult(BaseModel):
    """Canonical complete review output schema returned to clients and persisted."""
    detected_language: str = Field(..., description="Canonical detected programming language")
    summary: str = Field(..., description="High-level executive summary of the review findings")
    explanation: str = Field(..., description="Plain-English explanation of what the submitted code does")
    issues: list[IssueFinding] = Field(default_factory=list, description="All identified issues across bug, security, and quality")
    refactored_code: str = Field(..., description="Optimized and cleaned refactored source code")
    refactoring_notes: Optional[str] = Field(None, description="Explanation and rationale for refactoring choices")
    refactoring_validated: bool = Field(True, description="Whether the refactored code passed syntax and intent validation")
    complexity_assessment: str = Field(..., description="Summary of algorithmic and structural complexity")
    readability_score: float = Field(..., ge=0.0, le=100.0, description="Readability score between 0.0 and 100.0")
    review_mode: str = Field("quick", description="Review depth mode: 'quick' or 'deep'")
