# RAG Subsystem Architecture

This document defines the Retrieval-Augmented Generation (RAG) architecture used during **Deep Review** to augment agent prompt contexts with coding guidelines, vulnerability standards, and enterprise best practices.

---

## 1. RAG Pipeline Overview

```text
[Coding Guidelines / Security Rules / Repo Patterns]
    │
    ├── 1. Chunking: AST-aware & Markdown Section Splitter
    ├── 2. Vectorization: Google text-embedding-004 (768 dims)
    ├── 3. Indexing: MongoDB Atlas Vector Search Index
    │
[User Code Input] ──> Semantic Query ──> Cosine Similarity Search (Top-k=3) ──> Inject into Agent Contexts
```

## 2. Components & Vector Storage

- **Document Chunking**: Split style guide documents and CWE security references into chunks of 500 tokens with 50-token overlaps.
- **Embedding Provider**: Primary: `text-embedding-004` via LangChain Google Generative AI embeddings package.
- **MongoDB Atlas Index Definition**:
  ```json
  {
    "fields": [
      {
        "type": "vector",
        "path": "embedding",
        "numDimensions": 768,
        "similarity": "cosine"
      },
      {
        "type": "filter",
        "path": "category"
      }
    ]
  }
  ```
