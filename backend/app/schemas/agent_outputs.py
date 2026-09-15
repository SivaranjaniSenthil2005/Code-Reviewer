"""Schemas for specialized agent intermediate outputs."""

from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.bug import IssueFinding


class CodeAnalysisOutput(BaseModel):
    """Output from the code analysis agent."""
    explanation: str = Field(..., description="Clear plain-English explanation of the code's purpose and functionality")
    key_components: list[str] = Field(default_factory=list, description="Key classes, functions, or structures identified")
    summary: str = Field("", description="One or two sentence summary")


class QualityAnalysisOutput(BaseModel):
    """Output from the code quality / readability agent."""
    readability_score: float = Field(..., ge=0.0, le=100.0, description="Score from 0.0 to 100.0 evaluating code readability")
    style_issues: list[IssueFinding] = Field(default_factory=list, description="List of style, naming, and standard violations")
    maintainability_notes: str = Field("", description="Assessment of maintainability and structure")


class ComplexityAnalysisOutput(BaseModel):
    """Output from the complexity analysis agent."""
    time_complexity: str = Field("O(1)", description="Big-O time complexity estimate")
    space_complexity: str = Field("O(1)", description="Big-O space complexity estimate")
    cyclomatic_estimate: str = Field("Low", description="Cyclomatic complexity estimate (Low/Medium/High)")
    complexity_assessment: str = Field(..., description="Detailed explanation of algorithmic complexity")


class RefactoringOutput(BaseModel):
    """Output from the refactoring agent."""
    refactored_code: str = Field(..., description="Complete refactored source code")
    changes_summary: str = Field(..., description="Summary of refactoring changes applied")
    reasoning: list[str] = Field(default_factory=list, description="Bullet-point justifications for refactoring")
