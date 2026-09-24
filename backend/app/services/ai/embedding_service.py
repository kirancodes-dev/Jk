"""
Optional, off-by-default multilingual sentence-embedding service for SIH 26043.

Provides real semantic similarity (via `sentence-transformers`, a multilingual
model) as a strictly optional enhancement layered on top of — never replacing —
the deterministic bag-of-words rule-based fallback used elsewhere in this
codebase (see `deduplication_service.compute_cosine_similarity`). Disabled by
default; enabling requires both:
  1. `AI_EMBEDDINGS_ENABLED=true` in settings, AND
  2. `pip install -r backend/requirements-optional.txt` (sentence-transformers)

If either condition isn't met, or the model fails to load or run for any
reason, every method here fails safe by returning `None` — callers must keep
using the rule-based computation in that case. `sentence-transformers` is
never imported at module load time, only inside `_ensure_loaded`.
"""

import math
from typing import Optional

from backend.app.core.config import settings


class EmbeddingService:
    MODEL_NAME = "SENTENCE_TRANSFORMERS_MULTILINGUAL"
    PROVIDER_NAME = "SENTENCE_TRANSFORMERS"

    def __init__(self):
        self._model = None
        self._load_attempted = False
        self._available = False

    def _ensure_loaded(self) -> bool:
        if self._load_attempted:
            return self._available
        self._load_attempted = True

        if not settings.AI_EMBEDDINGS_ENABLED:
            return False

        try:
            from sentence_transformers import SentenceTransformer  # optional dependency
            self._model = SentenceTransformer(settings.AI_EMBEDDINGS_MODEL_NAME)
            self._available = True
        except Exception:
            self._model = None
            self._available = False

        return self._available

    def is_available(self) -> bool:
        """True only when AI_EMBEDDINGS_ENABLED=true AND the model loaded successfully."""
        return self._ensure_loaded()

    def semantic_similarity(self, text1: str, text2: str) -> Optional[float]:
        """
        Returns real embedding-based cosine similarity in [0, 1], or None if
        embeddings are disabled/unavailable/fail for any reason — callers must
        fall back to the deterministic bag-of-words similarity in that case.
        """
        if not self._ensure_loaded():
            return None
        try:
            vectors = self._model.encode([text1, text2])
            v1, v2 = vectors[0], vectors[1]
            dot = sum(a * b for a, b in zip(v1, v2))
            norm1 = math.sqrt(sum(a * a for a in v1))
            norm2 = math.sqrt(sum(b * b for b in v2))
            if not norm1 or not norm2:
                return None
            return max(0.0, min(1.0, float(dot / (norm1 * norm2))))
        except Exception:
            return None


embedding_service = EmbeddingService()
