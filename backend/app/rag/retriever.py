"""Knowledge retriever for agent prompt enrichment."""

import logging
from typing import List, Optional
from app.rag.vector_store import VectorStore
from app.rag.embeddings import EmbeddingService
from app.rag.chunker import DocumentChunk

logger = logging.getLogger(__name__)


class KnowledgeRetriever:
    """Retrieves relevant domain knowledge chunks tailored to specific agents and languages."""

    def __init__(self, vector_store: VectorStore, embedding_service: Optional[EmbeddingService] = None):
        self.vector_store = vector_store
        self.embedding_service = embedding_service or EmbeddingService()

    async def retrieve(
        self,
        query: str,
        category: Optional[str] = None,
        language: Optional[str] = None,
        top_k: int = 2,
    ) -> List[DocumentChunk]:
        """Retrieve most relevant knowledge chunks matching query and filters."""
        try:
            query_emb = await self.embedding_service.embed_query(query)
            return self.vector_store.search(
                query_embedding=query_emb,
                category=category,
                language=language,
                top_k=top_k,
            )
        except Exception as exc:
            logger.warning(f"[KnowledgeRetriever] Retrieval failed gracefully: {exc}")
            return []

    async def retrieve_formatted_context(
        self,
        query: str,
        category: Optional[str] = None,
        language: Optional[str] = None,
        top_k: int = 2,
    ) -> str:
        """Retrieve and format chunks into a concise context block for LLM prompts."""
        chunks = await self.retrieve(query, category=category, language=language, top_k=top_k)
        if not chunks:
            return ""

        formatted_sections = []
        for idx, chunk in enumerate(chunks, start=1):
            formatted_sections.append(
                f"[{idx}] {chunk.title} ({chunk.heading}):\n{chunk.content}"
            )
        return "\n\n".join(formatted_sections)
