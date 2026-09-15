"""Dedicated LangChain execution chains for each review aspect."""

from typing import Optional
from app.services.llm.router import LLMRouter
from app.chains.structured_runner import execute_structured_chain
from app.prompts.templates import (
    EXPLAIN_PROMPT,
    BUG_PROMPT,
    SECURITY_PROMPT,
    QUALITY_PROMPT,
    COMPLEXITY_PROMPT,
    REFACTORING_PROMPT,
)
from app.schemas.agent_outputs import (
    CodeAnalysisOutput,
    QualityAnalysisOutput,
    ComplexityAnalysisOutput,
    RefactoringOutput,
)
from app.schemas.bug import BugAnalysisResult
from app.schemas.security import SecurityAnalysisResult


async def run_explain_chain(
    code: str,
    language: str,
    depth: str = "quick",
    router: Optional[LLMRouter] = None,
) -> CodeAnalysisOutput:
    """Run code explanation chain."""
    return await execute_structured_chain(
        prompt_template=EXPLAIN_PROMPT,
        prompt_inputs={"code": code, "language": language, "depth": depth},
        schema_cls=CodeAnalysisOutput,
        router=router,
    )


async def run_bug_chain(
    numbered_code: str,
    language: str,
    depth: str = "quick",
    context: str = "",
    router: Optional[LLMRouter] = None,
) -> BugAnalysisResult:
    """Run bug detection chain."""
    context_section = f"\nRelevant Reference Knowledge:\n{context}\n" if context else ""
    return await execute_structured_chain(
        prompt_template=BUG_PROMPT,
        prompt_inputs={
            "numbered_code": numbered_code,
            "language": language,
            "depth": depth,
            "context_section": context_section,
        },
        schema_cls=BugAnalysisResult,
        router=router,
    )


async def run_security_chain(
    numbered_code: str,
    language: str,
    context: str = "",
    router: Optional[LLMRouter] = None,
) -> SecurityAnalysisResult:
    """Run security audit chain."""
    context_section = f"\nSecurity Reference Guidelines:\n{context}\n" if context else ""
    return await execute_structured_chain(
        prompt_template=SECURITY_PROMPT,
        prompt_inputs={
            "numbered_code": numbered_code,
            "language": language,
            "context_section": context_section,
        },
        schema_cls=SecurityAnalysisResult,
        router=router,
    )


async def run_quality_chain(
    numbered_code: str,
    language: str,
    context: str = "",
    router: Optional[LLMRouter] = None,
) -> QualityAnalysisOutput:
    """Run code quality & readability analysis chain."""
    context_section = f"\nLanguage Best Practice Guidelines:\n{context}\n" if context else ""
    return await execute_structured_chain(
        prompt_template=QUALITY_PROMPT,
        prompt_inputs={
            "numbered_code": numbered_code,
            "language": language,
            "context_section": context_section,
        },
        schema_cls=QualityAnalysisOutput,
        router=router,
    )


async def run_complexity_chain(
    code: str,
    language: str,
    router: Optional[LLMRouter] = None,
) -> ComplexityAnalysisOutput:
    """Run complexity assessment chain."""
    return await execute_structured_chain(
        prompt_template=COMPLEXITY_PROMPT,
        prompt_inputs={"code": code, "language": language},
        schema_cls=ComplexityAnalysisOutput,
        router=router,
    )


async def run_refactoring_chain(
    code: str,
    language: str,
    issues_summary: str,
    router: Optional[LLMRouter] = None,
) -> RefactoringOutput:
    """Run refactoring generation chain."""
    return await execute_structured_chain(
        prompt_template=REFACTORING_PROMPT,
        prompt_inputs={
            "code": code,
            "language": language,
            "issues_summary": issues_summary,
        },
        schema_cls=RefactoringOutput,
        router=router,
    )
