import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class ExplanationCache:
    """
    Thread-safe-ish (simple dictionary) in-memory cache for vulnerability explanations.
    Keeps API costs low and responses instant when repeating lookups.
    """

    _store: dict = {}
    MAX_ENTRIES = 500

    @classmethod
    def make_key(cls, finding: dict, snippet: dict | None) -> str:
        """
        Generates a stable cache key based on the finding details and code context.

        Args:
            finding: The normalized finding dictionary.
            snippet: The extracted code snippet or None.

        Returns:
            A unique MD5 hash string representing the finding state.
        """
        # Collect values that affect the output
        parts = [
            finding.get("category", "").strip().lower(),
            finding.get("rule_id", "").strip().lower(),
            finding.get("file", "").replace("\\", "/").strip().lower(),
            str(finding.get("line", 0)),
        ]

        if snippet and snippet.get("code"):
            parts.append(snippet["code"])

        # Compute a stable hash
        raw_key = "|".join(parts)
        return hashlib.md5(raw_key.encode("utf-8", errors="replace")).hexdigest()

    @classmethod
    def get(cls, key: str) -> dict | None:
        """Retrieve a cached explanation if present."""
        return cls._store.get(key)

    @classmethod
    def set(cls, key: str, value: dict) -> None:
        """
        Store an explanation in the cache.
        Enforces MAX_ENTRIES by removing the oldest entry if it overflows.
        """
        if len(cls._store) >= cls.MAX_ENTRIES:
            # Simple eviction: pop the first key (FIFO)
            first_key = next(iter(cls._store))
            cls._store.pop(first_key, None)
            logger.info("ExplanationCache: Evicted oldest cache entry to stay under capacity.")

        # Deep-copy value just to be safe
        cls._store[key] = dict(value)
        logger.info(f"ExplanationCache: Cached entry under key: {key}")

    @classmethod
    def clear(cls) -> None:
        """Clear all entries (primarily for testing/debugging)."""
        cls._store.clear()
        logger.info("ExplanationCache: Cache cleared.")
