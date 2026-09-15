"""Vector store managing embedded knowledge chunks with metadata filtering and similarity search."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from app.rag.chunker import DocumentChunk

logger = logging.getLogger(__name__)


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two unit-normalized vectors."""
    if len(v1) != len(v2) or not v1:
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = sum(a * a for a in v1) ** 0.5
    norm2 = sum(b * b for b in v2) ** 0.5
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


@dataclass
class VectorRecord:
    """A chunk paired with its embedding vector."""
    chunk: DocumentChunk
    embedding: List[float]


class VectorStore:
    """In-memory and MongoDB Vector Search capable store."""

    def __init__(self):
        self._records: List[VectorRecord] = []

    def clear(self):
        """Reset the vector store."""
        self._records = []

    def count(self) -> int:
        """Return number of stored records."""
        return len(self._records)

    def add_records(self, chunks: List[DocumentChunk], embeddings: List[List[float]]) -> int:
        """Add chunks with their embeddings to the store."""
        added = 0
        for chunk, emb in zip(chunks, embeddings):
            self._records.append(VectorRecord(chunk=chunk, embedding=emb))
            added += 1
        logger.info(f"[VectorStore] Added {added} records. Total count: {len(self._records)}")
        return added

    def search(
        self,
        query_embedding: List[float],
        category: Optional[str] = None,
        language: Optional[str] = None,
        top_k: int = 3,
    ) -> List[DocumentChunk]:
        """Perform vector similarity search with metadata filtering."""
        if not self._records:
            return []

        scored_records: List[tuple[float, DocumentChunk]] = []

        for record in self._records:
            # Metadata filter: Category
            if category and record.chunk.category != category and record.chunk.category != "all":
                continue

            # Metadata filter: Language
            if language and record.chunk.language != language and record.chunk.language != "all":
                continue

            score = cosine_similarity(query_embedding, record.embedding)
            scored_records.append((score, record.chunk))

        # Sort by similarity score descending
        scored_records.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored_records[:top_k]]
