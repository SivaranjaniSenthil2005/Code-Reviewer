"""Tests for RAG Knowledge System (Phase 8)."""

import sys
import os
import pytest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.rag.loaders import load_starter_knowledge_base
from app.rag.chunker import chunk_all_documents, chunk_document
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore
from app.rag.retriever import KnowledgeRetriever
from app.rag.pipeline import RAGPipeline


def test_starter_knowledge_base_loading():
    docs = load_starter_knowledge_base()
    assert len(docs) >= 5
    categories = {d.category for d in docs}
    assert "security" in categories
    assert "bug" in categories
    assert "quality" in categories


def test_chunking_preserves_metadata():
    docs = load_starter_knowledge_base()
    chunks = chunk_all_documents(docs)
    assert len(chunks) > len(docs)
    for chunk in chunks:
        assert chunk.chunk_id
        assert chunk.doc_id
        assert chunk.content


@pytest.mark.asyncio
async def test_embedding_service_deterministic():
    service = EmbeddingService()
    emb1 = await service.embed_query("SQL injection vulnerability")
    emb2 = await service.embed_query("SQL injection vulnerability")
    assert len(emb1) == 128
    assert emb1 == emb2


@pytest.mark.asyncio
async def test_vector_store_ingestion_and_search():
    store = VectorStore()
    emb_service = EmbeddingService()
    docs = load_starter_knowledge_base()
    chunks = chunk_all_documents(docs)
    embeddings = await emb_service.embed_documents([c.content for c in chunks])

    added = store.add_records(chunks, embeddings)
    assert added == len(chunks)
    assert store.count() == len(chunks)

    # Search for SQL injection
    query_emb = await emb_service.embed_query("SELECT * FROM users WHERE id =")
    results = store.search(query_emb, category="security", top_k=2)
    assert len(results) > 0
    assert any("sql" in r.title.lower() or "injection" in r.title.lower() for r in results)


@pytest.mark.asyncio
async def test_rag_pipeline_end_to_end():
    pipeline = RAGPipeline()
    count = await pipeline.initialize()
    assert count > 0

    context = await pipeline.get_context_for_review(
        language="python",
        code_snippet="def query_user(user_id): return f'SELECT * FROM users WHERE id={user_id}'",
        category="security",
        top_k=1,
    )
    assert len(context) > 0
    assert "SQL" in context or "CWE" in context or "OWASP" in context


@pytest.mark.asyncio
async def test_rag_pipeline_graceful_failure_handling():
    pipeline = RAGPipeline()
    # Simulate embedding service failure
    with patch.object(pipeline.embedding_service, "embed_query", side_effect=RuntimeError("Embedding API down")):
        context = await pipeline.get_context_for_review(
            language="python",
            code_snippet="x = 1",
            category="security",
        )
        # Should NOT raise, but return empty string gracefully
        assert context == ""
