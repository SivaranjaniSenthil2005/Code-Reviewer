# Architecture Reference & Data Flow

This document details the final architecture, component interfaces, state management, and data lifecycle of the AI Code Review & Refactoring Platform.

---

## 1. System Topology & Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as Developer / UI
    participant FE as Next.js Frontend
    participant API as FastAPI /api/review
    participant Prep as Code Preprocessor
    participant Graph as LangGraph Engine
    participant LLM as Multi-Provider LLM (Gemini / Mistral)
    participant RAG as RAG Knowledge Store
    participant DB as MongoDB Atlas

    User->>FE: Pastes code, selects Quick/Deep mode, clicks "Run Review"
    FE->>API: POST /api/review (JSON payload)
    API->>Prep: Screening (size, prose, non-code rejection) & normalization
    Prep-->>API: Normalized code, detected language, LineMap
    API->>Graph: Initialize ReviewState and invoke graph
    opt If Deep Review Mode
        Graph->>RAG: Query domain security & style rules
        RAG-->>Graph: Enriched context chunks
    end
    par Parallel Agent Execution
        Graph->>LLM: Code Analysis Agent
        Graph->>LLM: Bug Agent
        Graph->>LLM: Security Agent
        Graph->>LLM: Quality & Style Agent
        Graph->>LLM: Complexity Agent
    end
    Graph->>LLM: Refactoring Agent (generate optimized code)
    Graph->>Graph: Validation Agent (AST & structural intent check)
    alt If validation fails
        Graph->>LLM: Single retry with error diagnostics
    end
    Graph->>Graph: Synthesis & Deduplication (unified ReviewResult)
    opt If DB Connected
        Graph->>DB: Persist ReviewResult, Findings, & AgentRuns
    end
    Graph-->>API: Return final ReviewResult
    API-->>FE: HTTP 200 ReviewResponse
    FE-->>User: Render interactive ReviewPanel, side-by-side diff, & Export button
```

---

## 2. Core Subsystems

### 1. Code Preprocessing Layer (`app/services/code/`)
- `language_detector.py`: 4-tier detection (explicit hint → SHA256 cache → extension → shebang → keyword heuristics).
- `validator.py`: Input screening (prose vs code, size limits) + language AST parser.
- `normalizer.py`: CRLF to LF, trailing whitespace removal, Python 4-space tab expansion, excessive blank line collapse.
- `line_mapper.py`: Bidirectional index mapping original coordinates to normalized lines so finding references stay 100% accurate.

### 2. Multi-Provider LLM Layer (`app/services/llm/`)
- `GeminiProvider`: Primary high-throughput provider using Gemini 1.5.
- `MistralProvider`: Automatic fallback provider on rate limits, timeouts, or quota errors.
- `LLMRouter`: Unifies primary-to-fallback routing with structured schema output parsing.

### 3. Orchestration Engine (`app/graph/`)
- Built on LangGraph `StateGraph` with explicit `ReviewState` transitions.
- Dynamically compiles `quick_review.py` or `deep_review.py` based on user depth preference.

### 4. Persistence Layer (`app/repositories/`)
- `ReviewRepository`: Stores high-level review metadata and executive summaries.
- `FindingRepository`: Stores granular defect items indexed by line, severity, and category.
- `AgentRunRepository`: Logs audit execution metrics per agent.
