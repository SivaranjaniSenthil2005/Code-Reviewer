"""RAG ingestion and query orchestration pipeline."""

import logging
from typing import Optional
from app.rag.loaders import load_starter_knowledge_base
from app.rag.chunker import chunk_all_documents
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore
from app.rag.retriever import KnowledgeRetriever

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Orchestrates end-to-end ingestion and knowledge retrieval."""

    def __init__(self):
        self.vector_store = VectorStore()
        self.embedding_service = EmbeddingService()
        self.retriever = KnowledgeRetriever(self.vector_store, self.embedding_service)
        self._initialized = False

    async def initialize(self) -> int:
        """Load, chunk, and embed starter knowledge base."""
        if self._initialized:
            return self.vector_store.count()

        try:
            docs = load_starter_knowledge_base()
            chunks = chunk_all_documents(docs)
            texts = [c.content for c in chunks]
            embeddings = await self.embedding_service.embed_documents(texts)
            count = self.vector_store.add_records(chunks, embeddings)
            self._initialized = True
            logger.info(f"[RAGPipeline] Initialized with {count} chunks.")
            return count
        except Exception as exc:
            logger.error(f"[RAGPipeline] Ingestion failed (will operate in degraded mode): {exc}")
            return 0

    async def get_context_for_review(
        self,
        language: str,
        code_snippet: str,
        category: str = "security",
        top_k: int = 2,
    ) -> str:
        """Retrieve relevant context for an agent query with silent degradation on failure."""
        try:
            if not self._initialized:
                await self.initialize()

            return await self.retriever.retrieve_formatted_context(
                query=code_snippet[:500],
                category=category,
                language=language,
                top_k=top_k,
            )
        except Exception as exc:
            logger.warning(f"[RAGPipeline] Context retrieval failed gracefully: {exc}")
            return ""


_global_pipeline: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create singleton RAG pipeline."""
    global _global_pipeline
    if _global_pipeline is None:
        _global_pipeline = RAGPipeline()
    return _global_pipeline
