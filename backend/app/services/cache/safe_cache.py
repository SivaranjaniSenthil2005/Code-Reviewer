"""Safe in-memory caching for language detection and vector embeddings."""

import hashlib
from typing import Any, Dict, List, Optional


class SafeLRUCache:
    """Bounded in-memory LRU cache with hash-based key indexing."""

    def __init__(self, maxsize: int = 500):
        self.maxsize = maxsize
        self._cache: Dict[str, Any] = {}
        self._keys: List[str] = []

    def get(self, key: str) -> Optional[Any]:
        """Get cached value by key."""
        if key in self._cache:
            # Move key to end (most recently used)
            self._keys.remove(key)
            self._keys.append(key)
            return self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Store value with key and enforce max size."""
        if key in self._cache:
            self._keys.remove(key)
        elif len(self._cache) >= self.maxsize:
            oldest = self._keys.pop(0)
            self._cache.pop(oldest, None)

        self._cache[key] = value
        self._keys.append(key)

    def clear(self) -> None:
        """Clear all entries."""
        self._cache.clear()
        self._keys.clear()


# Global caches for non-sensitive repeated tasks
LANGUAGE_DETECTION_CACHE = SafeLRUCache(maxsize=1000)
EMBEDDING_VECTOR_CACHE = SafeLRUCache(maxsize=500)


def compute_code_hash(code: str) -> str:
    """Compute sha256 hash for code snippet caching."""
    return hashlib.sha256(code.encode("utf-8")).hexdigest()
