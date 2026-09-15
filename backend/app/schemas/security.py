"""Security vulnerability finding schemas."""

from typing import Literal, Optional
from pydantic import BaseModel, Field
from app.schemas.bug import IssueFinding


class SecurityFinding(IssueFinding):
    """Security vulnerability with security-specific fields."""
    category: Literal["vulnerability"] = Field("vulnerability", description="Always vulnerability")
    cwe_id: Optional[str] = Field(None, description="Common Weakness Enumeration ID, e.g. 'CWE-89'")
    owasp_category: Optional[str] = Field(None, description="OWASP Top 10 category, e.g. 'A03:2021-Injection'")
    remediation: Optional[str] = Field(None, description="Detailed guidance on how to fix the security issue")


class SecurityAnalysisResult(BaseModel):
    """Output schema for security analysis agent/chain."""
    vulnerabilities: list[SecurityFinding] = Field(
        default_factory=list, description="List of identified security vulnerabilities"
    )
    risk_level: Literal["none", "low", "medium", "high", "critical"] = Field(
        "none", description="Overall evaluated security risk level"
    )
    summary: str = Field("", description="Summary of security assessment")
