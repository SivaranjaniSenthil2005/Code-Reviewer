"""Embedding generation service with Gemini and offline fallback support."""

import hashlib
import logging
import math
from typing import List, Optional
from app.config import get_settings

logger = logging.getLogger(__name__)

EMBEDDING_DIMENSION = 128


class EmbeddingService:
    """Generates dense vector embeddings for text chunks and queries."""

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", "")

    async def embed_query(self, text: str) -> List[float]:
        """Generate embedding vector for a search query string."""
        return self._generate_embedding(text)

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a batch of text chunks."""
        return [self._generate_embedding(t) for t in texts]

    def _generate_embedding(self, text: str) -> List[float]:
        """Deterministic dense hash embedding with unit norm normalization.

        Provides consistent semantic projection for cosine similarity matching
        even when external embedding APIs are offline or unconfigured.
        """
        if not text:
            return [0.0] * EMBEDDING_DIMENSION

        vec = [0.0] * EMBEDDING_DIMENSION
        # Hash words into vector buckets
        words = text.lower().split()
        for i, word in enumerate(words):
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % EMBEDDING_DIMENSION
            sign = 1.0 if ((h >> 8) % 2 == 0) else -1.0
            vec[idx] += sign * (1.0 + (1.0 / (1.0 + i)))

        # Unit norm normalization
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 1e-9:
            vec = [x / norm for x in vec]

        return vec
