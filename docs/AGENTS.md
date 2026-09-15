# Multi-Agent Design & Orchestration Specification

This document details the single responsibilities, input/output schemas, prompt strategies, and failure isolation for each of the 8 specialized review agents.

---

## 1. Agent Catalog

| Agent Name | Module | Primary Responsibility | Input Shape | Output Schema |
|---|---|---|---|---|
| **Code Analysis Agent** | `code_analysis_agent.py` | Produces plain-English architecture explanation and workflow breakdown | `code, language, depth` | `CodeAnalysisOutput` |
| **Bug Detection Agent** | `bug_agent.py` | Flags functional defects, logic flaws, off-by-one errors with line numbers | `numbered_code, language, line_map` | `BugAnalysisResult` |
| **Security Audit Agent** | `security_agent.py` | Audits code against OWASP/CWE security vulnerabilities | `numbered_code, language, rag_context` | `SecurityAnalysisResult` |
| **Quality & Style Agent** | `quality_agent.py` | Evaluates clean-code standards and computes readability score | `numbered_code, language, rag_context` | `QualityAnalysisOutput` |
| **Complexity Agent** | `complexity_agent.py` | Estimates Big-O asymptotic time/space and cyclomatic metrics | `code, language` | `ComplexityAnalysisOutput` |
| **Refactoring Agent** | `refactoring_agent.py` | Generates complete, robust refactored source code addressing findings | `code, language, issues_summary` | `RefactoringOutput` |
| **Validation Agent** | `validation_agent.py` | Sanity checks refactored code syntax and checks interface preservation | `original_code, refactored_code, language` | `(is_valid, error_msg)` |
| **Review Synthesizer** | `synthesizer_agent.py` | Deduplicates overlapping findings and merges all outputs into unified `ReviewResult` | `all agent outputs` | `ReviewResult` |

---

## 2. Failure Isolation & Degradation Model

To ensure high availability and prevent single-agent crashes from breaking the entire user request:
1. **Isolated Node Try/Except Blocks**: Each node wraps its LLM invocation in an isolated error boundary.
2. **Partial Result Synthesizer**: If an agent fails (e.g. `security_agent` times out), the synthesizer continues with the remaining agent outputs (e.g. `code_analysis` and `bug_agent`) without hallucinating missing data.
3. **Refactoring Safety Fallback**: If the refactored code fails validation twice, the system returns the original code with `refactoring_validated: false`.
