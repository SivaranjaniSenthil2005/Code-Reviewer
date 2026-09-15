# Review Execution Workflow & State Diagrams

This document details the complete end-to-end runtime lifecycle of a code review request across the frontend, FastAPI backend, LangGraph multi-agent orchestrator, RAG layer, and persistence layers.

---

## 🔁 End-to-End Execution Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User as Developer / User
    participant UI as Next.js 15 Frontend
    participant API as FastAPI Backend (/api/review)
    participant Sec as RateLimiter & Sanitizer
    participant Val as Code Validator & Language Detector
    participant LG as LangGraph Orchestrator
    participant RAG as RAG Knowledge Base (Vector Search)
    participant Agents as Specialized Agent Panel
    participant LLM as Multi-Provider LLM (Gemini / Mistral)
    participant ValAgent as Validation Agent
    participant Syn as Review Synthesis Node
    participant DB as MongoDB Atlas Persistence
    participant LS as LangSmith Tracing

    User->>UI: Paste Code Snippet & Select Depth (Quick / Deep)
    User->>UI: Click "Run Review"
    UI->>API: POST /api/review {code, language_hint, depth}
    
    API->>Sec: Check IP Rate Limits & Sanitize Tokens
    alt Rate Limit Exceeded or Invalid Input
        Sec-->>UI: Return 429 Too Many Requests or 400 Bad Request
        UI-->>User: Display user-friendly warning banner
    end

    API->>Val: Validate code payload & Detect language
    Val-->>API: {detected_language, normalized_code, line_map}

    API->>LG: Initialize ReviewState & Execute Workflow
    LG->>LS: Start Trace Run (Session ID, Review ID)

    alt Review Depth == "deep" (Deep Review)
        LG->>RAG: Retrieve OWASP / CWE / Idiom Context
        RAG-->>LG: Injected RAG Context Chunks

        par Parallel Multi-Agent Execution
            LG->>Agents: Run Code Analysis Agent
            LG->>Agents: Run Bug Detection Agent (with RAG)
            LG->>Agents: Run Security Agent (with RAG)
            LG->>Agents: Run Quality & Style Agent (with RAG)
            LG->>Agents: Run Algorithmic Complexity Agent
        and Sequential Refactoring Loop
            LG->>Agents: Run Refactoring Agent
            Agents->>LLM: Generate Refactored Code Proposal
            LLM-->>Agents: Refactored Code Candidate
            LG->>ValAgent: Validate AST Syntax & Signatures
            alt Validation Succeeded
                ValAgent-->>LG: Validated Refactored Code
            else Validation Failed (Attempt 1)
                ValAgent->>Agents: Trigger 1-shot Correction Retry
                Agents->>LLM: Regenerate Refactor with Error Context
                LLM-->>Agents: Corrected Code
                LG->>ValAgent: Re-validate AST
                alt Validation Succeeded on Retry
                    ValAgent-->>LG: Validated Refactored Code
                else Still Invalid (Attempt 2)
                    ValAgent-->>LG: Safe Fallback (Return Original Code + Warning Flag)
                end
            end
        end
    else Review Depth == "quick" (Quick Scan)
        par Lightweight Agent Execution
            LG->>Agents: Run Code Analysis Agent
            LG->>Agents: Run Bug Detection Agent (Zero-shot)
            LG->>Agents: Run Complexity Agent
            LG->>Agents: Run Refactoring Agent (Fast Pass)
        end
    end

    Agents->>Syn: Pass Agent Outputs to Synthesis Node
    Syn->>Syn: Deduplicate overlapping findings & Generate unified summary
    Syn-->>LG: Final ReviewResult JSON

    par Persist & Trace
        LG->>DB: Persist Review (`code_reviews`, `review_findings`, `agent_runs`)
        LG->>LS: Finalize Trace Span with Token & Latency Metrics
    end

    LG-->>API: Complete ReviewResponse
    API-->>UI: Return 200 OK with Review JSON
    UI-->>User: Render Summary, Findings, Metrics, and Side-by-Side Diff

    opt Download Report
        User->>UI: Click "Download as Markdown"
        UI->>UI: Format and trigger client-side `.md` file download
    end
```

---

## 🔀 Workflow State Machine (Quick Scan vs. Deep Review)

The following state machine illustrates the two divergent execution pipelines and how they converge at the deterministic **Review Synthesis** phase:

```mermaid
stateDiagram-v2
    [*] --> RequestReceived: POST /api/review
    
    state RequestReceived {
        [*] --> RateLimitCheck
        RateLimitCheck --> InputSanitization
        InputSanitization --> LanguageDetection
        LanguageDetection --> NormalizationAndLineMapping
        NormalizationAndLineMapping --> [*]
    }

    RequestReceived --> DepthRouter: Initialize ReviewState

    state DepthRouter <<choice>>
    DepthRouter --> QuickScanPath: depth == "quick"
    DepthRouter --> DeepReviewPath: depth == "deep"

    state QuickScanPath {
        [*] --> FastAnalysis
        FastAnalysis --> FastBugCheck
        FastBugCheck --> FastComplexity
        FastComplexity --> FastRefactor
        FastRefactor --> [*]
    }

    state DeepReviewPath {
        [*] --> RAGContextRetrieval
        
        state ParallelDeepAnalysis {
            [*] --> DeepCodeAnalysis
            [*] --> DeepBugScan
            [*] --> OWASPSecurityScan
            [*] --> CodeQualityStyleScan
            [*] --> AlgorithmicBigOAnalysis
        }
        
        RAGContextRetrieval --> ParallelDeepAnalysis

        state RefactorValidationLoop {
            [*] --> GenerateRefactor
            GenerateRefactor --> ASTSyntaxCheck
            ASTSyntaxCheck --> ValidationPassed: Valid Syntax & Signatures
            ASTSyntaxCheck --> RetryWithCorrection: Syntax Error (Attempt 1)
            RetryWithCorrection --> ASTSyntaxCheck: Re-test
            ASTSyntaxCheck --> SafeOriginalFallback: Syntax Error (Attempt 2)
            ValidationPassed --> [*]
            SafeOriginalFallback --> [*]
        }

        ParallelDeepAnalysis --> RefactorValidationLoop
        RefactorValidationLoop --> [*]
    }

    QuickScanPath --> ReviewSynthesisNode: Aggregate Quick Outputs
    DeepReviewPath --> ReviewSynthesisNode: Aggregate Deep Outputs

    state ReviewSynthesisNode {
        [*] --> DeduplicateFindings
        DeduplicateFindings --> RankBySeverity
        RankBySeverity --> GenerateUnifiedSummary
        GenerateUnifiedSummary --> BuildReviewResultSchema
        BuildReviewResultSchema --> [*]
    }

    ReviewSynthesisNode --> AsyncPersistence: Fire-and-Forget
    
    state AsyncPersistence {
        [*] --> SaveCodeReview
        SaveCodeReview --> SaveReviewFindings
        SaveReviewFindings --> SaveAgentRunMetrics
        SaveAgentRunMetrics --> [*]
    }

    ReviewSynthesisNode --> ResponseDelivery: Return ReviewResponse JSON
    ResponseDelivery --> [*]
```

---

## 🔍 Stage-by-Stage Breakdown

### 1. Ingestion & Security Screening
- **Rate Limiting**: Checks the client IP against a token bucket algorithm to prevent abuse.
- **Payload Inspection**: The request body is screened for length and minimum token count to ensure it is authentic source code.
- **Language Identification**: Pygments scans token distributions to identify the language (Python, JavaScript, TypeScript, Java, Go, C++, Rust, etc.).

### 2. Context Grounding (RAG)
- In **Deep Review** mode, the detected language and code tokens are used to retrieve targeted security rules (e.g., OWASP Injection, XSS, CSRF, insecure deserialization) and language style rules from MongoDB Atlas Vector Search.

### 3. Agent Execution & Isolation
- Each agent operates in its own isolated try/except execution boundary.
- If one LLM call fails or times out, fallback providers (Mistral) are attempted. If both fail, an error stub is recorded in state without failing the rest of the review.

### 4. Deterministic Refactoring Loop
- Refactored code must pass AST parsing.
- If code fails parsing, an exact error message is fed back into the refactoring prompt for a single repair attempt.
- If the repair attempt also fails, the original code is returned with `refactoring_validated: false`.

### 5. Synthesis & Deduplication
- Overlapping issues reported by bug, security, and quality agents are grouped by exact line number and cosine text similarity.
- Findings are mapped to the highest severity category: `vulnerability` > `bug` > `style`.
- A concise, cohesive summary paragraph is compiled.

### 6. Persistence & Presentation
- The review is saved to MongoDB Atlas collections (`code_reviews`, `review_findings`, `agent_runs`).
- LangSmith records end-to-end token latency and generation traces.
- The Next.js frontend renders findings, metrics, and side-by-side diff views.
