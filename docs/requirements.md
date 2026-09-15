# System Requirements & Mode Specifications

This document outlines the functional, non-functional, and operational requirements for the **AI Code Review & Refactoring Platform**.

---

## 1. Executive Summary & Core Objectives

The platform provides automated, multi-agent code analysis and refactoring. Developers submit source code, select an execution mode (**Quick Scan** or **Deep Review**), and receive a comprehensive, structured code review report consisting of:
- Automatic programming language detection.
- High-level plain-English architectural explanation.
- Categorized issues (bugs, security flaws, anti-patterns) with line-level accuracy.
- Syntax-validated refactored code with side-by-side comparison capability.
- Quantitative complexity and readability metrics.
- Exportable Markdown summaries.

---

## 2. Review Modes: Quick Scan vs. Deep Review

The system supports two distinct execution paths designed for different user workflows:

| Feature Dimension | Quick Scan | Deep Review |
| :--- | :--- | :--- |
| **Primary Use Case** | Instant feedback during typing, quick sanity checks, commit pre-hooks | In-depth code reviews, security auditing, complex refactoring, PR reviews |
| **Target Latency** | **< 5 seconds** (p95) | **15 – 30 seconds** (p95) |
| **Agent Execution Graph** | **Lightweight Pipeline**<br>• Code Analysis Agent<br>• Fast Quality & Bug Agent<br>• Synthesizer Agent | **Full Multi-Agent Orchestration**<br>• Code Analysis Agent<br>• Bug Detection Agent<br>• Security Agent<br>• Quality & Readability Agent<br>• Complexity Agent<br>• Refactoring Agent<br>• Validation Agent<br>• Synthesizer Agent |
| **RAG System Usage** | **Disabled / Cache-Only**<br>Avoids retrieval overhead to meet latency targets. | **Fully Enabled**<br>Retrieves code style guidelines, CWE definitions, and repository patterns from MongoDB Atlas Vector Search. |
| **Analysis Depth** | High-level summary, top 3 critical bugs, basic cyclomatic estimation, quick refactoring. | Deep AST inspection, line-by-line vulnerability mapping (OWASP/CWE), cognitive load calculation, full syntax-validated refactored code diff. |
| **LLM Tiering** | High-throughput fast models (e.g., `gemini-2.0-flash` or `mistral-small`). | Deep reasoning models (e.g., `gemini-1.5-pro` or `mistral-large`). |

---

## 3. Functional Requirements

### FR-1: Code Ingestion & Language Detection
- **FR-1.1**: The platform must accept plain-text code snippets up to 2,000 lines or 100 KB in size per request.
- **FR-1.2**: The backend must auto-detect the programming language (supporting Python, JavaScript, TypeScript, Java, Go, C++, Rust, C#).
- **FR-1.3**: Users must be able to manually override the detected language via the UI dropdown.

### FR-2: Plain-English Code Explanation
- **FR-2.1**: The system must generate a concise, high-level summary explaining what the code accomplishes, its inputs/outputs, and core logic.

### FR-3: Multi-Category Issue Detection & Line Referencing
- **FR-3.1**: Issues must be categorized into `BUG`, `SECURITY`, `PERFORMANCE`, `STYLE`, and `COMPLEXITY`.
- **FR-3.2**: Each issue must include:
  - `line`: 1-based exact line number (or range).
  - `severity`: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`.
  - `description`: Explanation of the issue.
  - `suggestion`: Concrete actionable fix.

### FR-4: Refactoring & Verification
- **FR-4.1**: The platform must generate a clean, refactored version of the input code addressing the detected issues.
- **FR-4.2**: The **Validation Agent** must run syntax parsing (AST compilation) on the generated refactored code before returning it to the user.
- **FR-4.3**: If syntax verification fails, the system must trigger an automated retry loop (max 2 retries) before falling back safely.

### FR-5: Complexity & Readability Metrics
- **FR-5.1**: Provide cyclomatic complexity score and cognitive complexity assessment.
- **FR-5.2**: Provide a readability score on a scale of 1 to 100.
- **FR-5.3**: Summarize key maintainability recommendations.

### FR-6: Export & Reporting
- **FR-6.1**: The frontend must render a clean Markdown report of the full review.
- **FR-6.2**: The user must be able to copy the raw Markdown or download a `.md` file with one click.

---

## 4. Non-Functional Requirements

### NFR-1: Performance & Latency
- Quick Scan responses must return within 5 seconds for code snippets under 200 lines.
- Deep Review responses must return within 30 seconds for code snippets up to 1,000 lines.
- Streaming responses (via Server-Sent Events / SSE) must provide progress updates as each graph node completes execution.

### NFR-2: Reliability & Resilience
- **LLM Failover**: If the primary LLM provider (Gemini) encounters rate limits (`429`), timeouts, or service errors (`5xx`), requests must automatically route to the fallback provider (Mistral) without failing the review.
- **Graceful Degradation**: If vector search (RAG) is unreachable, Deep Review must fall back to zero-shot LLM review with a notice flag in the output metadata.

### NFR-3: Observability & Tracing
- All LangGraph agent node executions, LLM prompts, input/output tokens, and latency metrics must be logged to **LangSmith**.
- Execution runs in MongoDB must store execution metadata (`execution_time_ms`, `mode`, `llm_provider`, `agent_chain_trace`).

---

## 5. Canonical Output Schema Standard

All components across Quick Scan and Deep Review must conform strictly to the following target JSON schema structure:

```json
{
  "detected_language": "python",
  "summary": "High-level overview of code functionality and overall quality.",
  "explanation": "Detailed plain-English breakdown of code logic, components, and flow.",
  "issues": [
    {
      "line": 14,
      "severity": "HIGH",
      "category": "BUG",
      "description": "Potential NullReferenceException when accessing user properties without checking for null.",
      "suggestion": "Use optional chaining user?.profile or add explicit check if user is None."
    }
  ],
  "refactored_code": "def process_user(user):\n    if not user:\n        return None\n    return user.profile",
  "complexity_assessment": {
    "cyclomatic_complexity": 5,
    "cognitive_complexity": 3,
    "assessment": "Low complexity. Easy to maintain and test."
  },
  "readability_score": 88
}
```
