"""Security Agent: performs vulnerability audits and assigns CWE/OWASP classifications."""

import logging
from typing import Optional
from app.schemas.security import SecurityAnalysisResult, SecurityFinding
from app.chains.review_chains import run_security_chain
from app.agents.bug_agent import format_numbered_code
from app.services.code.line_mapper import LineMap, remap_finding_line
from app.services.llm.router import LLMRouter

logger = logging.getLogger(__name__)


async def run_security_agent(
    code: str,
    language: str,
    line_map: Optional[LineMap] = None,
    context: str = "",
    router: Optional[LLMRouter] = None,
) -> SecurityAnalysisResult:
    """Audit code for security flaws and remap line numbers."""
    try:
        numbered_code = format_numbered_code(code)
        raw_result = await run_security_chain(
            numbered_code=numbered_code,
            language=language,
            context=context,
            router=router,
        )

        if line_map:
            remapped_vulnerabilities = []
            for vuln in raw_result.vulnerabilities:
                if vuln.line is not None:
                    orig_line = remap_finding_line(vuln.line, line_map, direction="norm_to_orig")
                    remapped_vulnerabilities.append(vuln.model_copy(update={"line": orig_line}))
                else:
                    remapped_vulnerabilities.append(vuln)
            return SecurityAnalysisResult(
                vulnerabilities=remapped_vulnerabilities,
                risk_level=raw_result.risk_level,
                summary=raw_result.summary,
            )

        return raw_result
    except Exception as exc:
        logger.error(f"[security_agent] Failed: {exc}")
        return SecurityAnalysisResult(
            vulnerabilities=[],
            risk_level="none",
            summary="Security audit was unavailable.",
        )
