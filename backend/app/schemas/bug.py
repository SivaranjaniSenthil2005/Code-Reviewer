"""Bug and issue finding schemas."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class IssueFinding(BaseModel):
    """A single issue or bug detected in the source code."""
    line: Optional[int] = Field(None, description="1-based line number where the issue occurs, or null if file-wide")
    category: Literal["bug", "vulnerability", "style", "performance"] = Field(
        "bug", description="Category of the finding"
    )
    severity: Literal["low", "medium", "high", "critical"] = Field(
        "medium", description="Severity level of the issue"
    )
    description: str = Field(..., description="Clear explanation of the bug or issue")
    suggestion: Optional[str] = Field(None, description="Suggested remedy or fix")


class BugAnalysisResult(BaseModel):
    """Output schema for bug analysis agent/chain."""
    issues: list[IssueFinding] = Field(default_factory=list, description="List of identified bugs and logic issues")
    summary: str = Field("", description="Brief overview of bug detection results")
