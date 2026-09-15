# AI Code Review & Refactoring Platform

> **Paste code, get a senior developer review without the ego.**

[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-FF6F00?style=flat-square&logo=langchain)](https://github.com/langchain-ai/langgraph)
[![LangChain](https://img.shields.io/badge/LangChain-Structured%20Output-1C3C3C?style=flat-square&logo=langchain)](https://www.langchain.com/)
[![MongoDB Atlas](https://img.shields.io/badge/MongoDB%20Atlas-Vector%20Search-47A248?style=flat-square&logo=mongodb)](https://www.mongodb.com/atlas)
[![LLM Providers](https://img.shields.io/badge/LLM-Gemini%20%7C%20Mistral-8E75B2?style=flat-square)](https://ai.google.dev/)
[![LangSmith](https://img.shields.io/badge/Observability-LangSmith-20232A?style=flat-square)](https://smith.langchain.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.flat-square)](LICENSE)

---

## 🌐 Live Web Application

> **Production Deployment:** [https://ai-code-reviewer-platform.vercel.app](https://ai-code-reviewer-platform.vercel.app) *(Coming Soon / Replace with active deployment URL)*

---

## 💡 What It Does

1. **Paste Code & Pick Depth**: Submit any code snippet and choose between **Quick Scan** (rapid feedback) or **Deep Review** (exhaustive multi-agent analysis with RAG context).
2. **Automatic Language Detection & Validation**: Automatically detects the programming language, normalizes line breaks, and maps line numbers while rejecting plain English prose or oversized payloads.
3. **Specialized Agent Panel**: Orchestrates 8 purpose-built AI agents covering logic bugs, security vulnerabilities (OWASP/CWE), code quality/style, algorithmic complexity (Big-O), and architectural explanation.
4. **Validated Refactoring Loop**: Generates a clean refactored version of the code and runs AST syntax checks and intent validation before showing it to you—falling back safely to original code if validation fails.
5. **Interactive Side-by-Side Comparison**: Visually inspect the original vs. refactored code with syntax-highlighted diffs and synchronized line scrolling.
6. **One-Click Markdown Export**: Download a structured, formatted markdown report of the entire code review with code blocks safely escaped.

---

## 🎯 Problem Statement & Solution

### The Problem
- **Generic Linters** only catch static syntax errors or style nitpicks; they miss deep algorithmic flaws, architectural anti-patterns, and security vulnerabilities.
- **Generic Chat Models (Copy-Pasting into ChatGPT/Claude)** hallucinate non-existent line numbers, return unvalidated refactors that break syntax, drop context, and give messy unstructured answers without guaranteed schema enforcement.
- **Human Code Reviews** can be slow, inconsistent, and bottleneck development velocity.

### The Solution
The **AI Code Review & Refactoring Platform** solves this by combining **LangGraph multi-agent orchestration**, **deterministic parsing validation**, **RAG domain knowledge**, and **multi-provider LLM failover**:
- **Multi-Agent Specialization**: Each agent has a single responsibility and isolated error boundary.
- **Fail-Safe Provider Layer**: Primary calls go to Google Gemini with automatic, seamless failover to Mistral AI if rate-limited or unavailable.
- **AST-Powered Safety Validation**: Refactored code is verified for valid syntax and signature preservation before reaching the user.
- **Structured Schema & Deduplication**: Findings from bug, security, and quality agents are deduplicated and categorized by severity (`bug`, `vulnerability`, `style`).

---

## ⚡ Quickstart

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & `npm`
- *(Optional)* MongoDB Atlas connection string (or local MongoDB)
- API Keys for Google Gemini and Mistral AI

---

### 1. Clone the Repository
```bash
git clone https://github.com/SivaranjaniSenthil2005/Code-Reviewer.git
cd Code-Reviewer
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` with your API keys:
```env
ENVIRONMENT=development
DEBUG=true
PORT=8000
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# LLM Providers
GEMINI_API_KEY=your_gemini_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here

# MongoDB Atlas Persistence & Vector Store
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=code_review_db

# Observability
LANGCHAIN_TRACING_V2=true
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=ai-code-review-platform
```

---

### 3. Backend Setup (FastAPI)

```bash
# Create and activate virtual environment
python -m venv .venv

# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# Start the FastAPI server
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 4. Frontend Setup (Next.js 15)

In a separate terminal window:
```bash
cd frontend
npm install
npm run dev
```

- **Web Application**: [http://localhost:3000](http://localhost:3000)

---

### 5. Running the Test Suite

Run the full automated test suite (107 unit, integration, and regression tests):

```bash
# From repository root
.\.venv\Scripts\pytest.exe tests/ -v
```

---

## 🏛️ Architecture Stack

| Tier / Component | Technology | Purpose |
|---|---|---|
| **Frontend Client** | Next.js 15 (App Router, TypeScript, Vanilla CSS) | Responsive UI, Monaco code editor, side-by-side diff viewer, export engine |
| **Backend API Engine** | FastAPI, Uvicorn, Pydantic v2 | High-performance async REST API, validation, rate limiting, error routing |
| **Orchestrator** | LangGraph (`StateGraph`) | Stateful multi-agent graph with parallel branches, retry loops, and depth routing |
| **AI Framework** | LangChain | Prompt engineering, structured schema parsing, repair retries |
| **Primary LLM** | Google Gemini (`gemini-1.5-flash` / `gemini-1.5-pro`) | High-speed, high-token reasoning and code analysis |
| **Fallback LLM** | Mistral AI (`mistral-small-latest` / `mistral-large-latest`) | Automatic failover when primary provider hits timeouts or rate limits |
| **Persistence & Vector DB** | MongoDB Atlas (+ Vector Search) | Review history, raw agent logs, CWE/OWASP vulnerability embeddings |
| **Observability & Traces** | LangSmith | End-to-end token tracing, latency monitoring, and evaluation datasets |

---

## 📂 Repository Layout

```
ai-code-review-platform/
├── README.md
├── .env.example
├── .gitignore
├── docs/
│   ├── architecture.md          # Full architectural data flow & system design
│   ├── workflow.md              # Sequence & state diagrams for execution paths
│   ├── requirements.md          # Product specs & depth requirements
│   ├── agent-design.md          # 8-agent specifications & I/O contracts
│   ├── RAG.md                   # RAG vector search & knowledge pipeline
│   ├── API.md                   # Complete REST API reference
│   ├── evaluation.md            # Benchmark dataset metrics & evaluation harness
│   └── deployment.md            # Cloud deployment guide (Vercel & Render)
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── main.py              # FastAPI application entrypoint
│       ├── config.py            # Pydantic Settings & environment manager
│       ├── api/routes/          # REST route handlers (/api/review, /health)
│       ├── schemas/             # Pydantic data contracts (API, review, bugs)
│       ├── services/
│       │   ├── code/            # Validation, language detection, line mapping
│       │   ├── llm/             # Multi-provider router (Gemini + Mistral)
│       │   └── security/        # Rate limiting, input sanitizer, redactor
│       ├── agents/              # 8 specialized review agents
│       ├── chains/              # LangChain prompt execution & JSON repair
│       ├── prompts/             # Reusable agent prompt templates
│       ├── graph/               # LangGraph StateGraph, Quick & Deep workflows
│       ├── rag/                 # Chunker, vector store, embeddings, retriever
│       └── database/            # MongoDB connection, client, index management
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── app/
│   │   ├── layout.tsx           # Global Next.js layout & metadata
│   │   ├── page.tsx             # Main dashboard page
│   │   └── globals.css          # Design system & dark mode aesthetics
│   ├── components/
│   │   ├── CodeEditor.tsx       # Code input with auto-formatting & line numbers
│   │   ├── ReviewModeSelector.tsx # Quick Scan / Deep Review toggle
│   │   ├── ReviewPanel.tsx      # Unified review results container
│   │   ├── FindingsList.tsx     # Filterable severity issue cards
│   │   ├── ComplexityCard.tsx   # Big-O & readability metrics card
│   │   ├── CodeComparison.tsx   # Side-by-side synchronized diff view
│   │   └── ExportButton.tsx     # Client-side Markdown export trigger
│   └── lib/
│       └── markdown-export.ts   # Safe markdown formatter with backtick escaping
└── tests/
    ├── test_validator.py
    ├── test_llm_provider.py
    ├── test_multi_agent_review.py
    ├── test_langgraph_orchestration.py
    ├── test_rag_knowledge.py
    ├── test_refactoring_validation.py
    ├── test_review_synthesis.py
    ├── test_api_review.py
    ├── test_security_hardening.py
    └── test_ai_evaluation_suite.py
```

---

## 📚 Documentation Index

| Document | Purpose |
|---|---|
| [System Architecture](docs/architecture.md) | Detailed architectural breakdown, component interactions, and data flow |
| [Execution Workflow](docs/workflow.md) | Sequence diagrams and state machine transitions for review requests |
| [Requirements Specification](docs/requirements.md) | Functional and non-functional requirements, Quick vs. Deep review depth |
| [Multi-Agent Design](docs/agent-design.md) | Responsibilities, system prompts, and schemas for all 8 review agents |
| [RAG Knowledge Base](docs/RAG.md) | Vector embeddings, chunking strategy, and retrieval mechanics |
| [REST API Reference](docs/API.md) | Request/response schemas, error codes, and curl examples |
| [AI Evaluation & Benchmarks](docs/EVALUATION.md) | Precision/recall test dataset results and regression harness |
| [Production Deployment Guide](docs/deployment.md) | Production setup for Vercel, Render/Fly.io, and MongoDB Atlas |

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.
