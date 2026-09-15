# AI Code Review & Refactoring Platform

An automated, multi-agent code analysis platform built with Next.js 15, FastAPI, LangGraph, Google Gemini (Primary LLM), Mistral AI (Fallback LLM), MongoDB Atlas Vector Search, and LangSmith.

---

## 🏗️ Architecture Stack

- **Frontend**: Next.js 15 (App Router), TypeScript, Tailwind CSS, Monaco Editor
- **Backend API**: FastAPI, Uvicorn, Pydantic Settings
- **Agent Orchestration**: LangGraph, LangChain
- **LLM Providers**: Primary: Google Gemini (`gemini-2.0-flash` / `gemini-1.5-pro`) | Fallback: Mistral AI (`mistral-small` / `mistral-large`)
- **Database & RAG**: MongoDB Atlas Document Store + Vector Search (`text-embedding-004`)
- **Observability**: LangSmith Execution Tracing

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites

- **Python**: 3.11+
- **Node.js**: 20+ (with `npm`)

---

### 2. Environment Configuration

Copy `.env.example` to create your local `.env` file:

```bash
cp .env.example .env
```

Set the required API keys in `.env`:

```env
GEMINI_API_KEY=your_gemini_api_key
MISTRAL_API_KEY=your_mistral_api_key
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/
MONGODB_DATABASE=code_review_db
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=ai-code-review-platform
```

---

### 3. Backend Setup (FastAPI)

1. Navigate to the project root and create a virtual environment:

   ```bash
   python -m venv backend/.venv
   ```

2. Activate the virtual environment:

   - **Windows (PowerShell)**:
     ```powershell
     .\backend\.venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS**:
     ```bash
     source backend/.venv/bin/activate
     ```

3. Install dependencies:

   ```bash
   pip install -r backend/requirements.txt
   ```

4. Run the development server:

   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. Verify backend health check:

   - Open [http://localhost:8000/health](http://localhost:8000/health) in your browser. Expected response: `{"status": "ok"}`.
   - Interactive API docs available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

### 4. Frontend Setup (Next.js)

1. Navigate to the `frontend` directory:

   ```bash
   cd frontend
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Start the Next.js development server:

   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser. The landing page will automatically perform a health check fetch to the FastAPI backend.

---

### 5. Running Tests

Run backend smoke tests via `pytest`:

```bash
backend/.venv/Scripts/pytest tests/
```

---

## 📁 Repository Layout

```text
capstone2/
├── README.md                  # Setup & architecture overview
├── .env.example               # Template environment configuration
├── .gitignore                 # Monorepo git ignores
├── docs/                      # Foundational system architecture & design specs
│   ├── requirements.md        # Quick Scan vs. Deep Review specifications
│   ├── architecture.md        # Data flow, failover strategy & canonical output schema
│   └── agent-design.md        # 8-agent catalog & LangGraph state definitions
├── backend/                   # FastAPI service
│   ├── requirements.txt       # Backend dependencies
│   └── app/                   # FastAPI application package
│       ├── main.py            # Entrypoint & CORS setup
│       ├── config.py          # Pydantic settings & .env loading
│       └── api/routes/        # REST & SSE API route handlers
├── frontend/                  # Next.js 15 Web Application
│   ├── app/                   # App Router pages & layouts
│   └── components/            # UI components (Monaco Editor, Diff Viewer, etc.)
└── tests/                     # Automated smoke & integration test suite
```
