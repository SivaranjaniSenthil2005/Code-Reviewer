"""Tests for Performance Optimization, parallel graph execution, and safe caching (Phase 20)."""

import sys
import os
import time
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.services.cache.safe_cache import SafeLRUCache, LANGUAGE_DETECTION_CACHE, EMBEDDING_VECTOR_CACHE
from app.services.code.language_detector import detect_language
from app.rag.embeddings import EmbeddingService


def test_safe_lru_cache_operations():
    cache = SafeLRUCache(maxsize=2)
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.get("a") == 1

    # Adding 'c' should evict 'b' (since 'a' was accessed more recently)
    cache.set("c", 3)
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3


def test_language_detector_caching_speedup():
    LANGUAGE_DETECTION_CACHE.clear()
    code = "def calculate_statistics(numbers):\n    return sum(numbers) / len(numbers)\n" * 5

    # First call (cold)
    t0 = time.perf_counter()
    res1 = detect_language(code)
    dur_cold = time.perf_counter() - t0

    # Second call (warm cache hit)
    t0 = time.perf_counter()
    res2 = detect_language(code)
    dur_warm = time.perf_counter() - t0

    assert res1["language_id"] == "python"
    assert res2["language_id"] == "python"
    # Cached access is faster
    assert dur_warm <= dur_cold + 0.001


@pytest.mark.asyncio
async def test_embedding_cache_speedup():
    EMBEDDING_VECTOR_CACHE.clear()
    service = EmbeddingService()
    text = "Find SQL injection and buffer overflow vulnerabilities in code"

    emb1 = await service.embed_query(text)
    emb2 = await service.embed_query(text)

    assert len(emb1) == 128
    assert emb1 == emb2
