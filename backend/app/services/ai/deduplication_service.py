"""
Scalable, multi-factor duplicate challenge detection service for SIH 26043.
Eliminates in-memory table scans using targeted SQL candidate filtering by
administrative area, category taxonomy, and temporal window (last 180 days).
Persists decomposed text, geographic, temporal, and category signals separately.
NEVER automatically suppresses or rejects citizen submissions without human review.
"""

import math
import time
from datetime import datetime, timedelta, timezone
from collections import Counter
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from backend.app.models.models import Challenge, ChallengeLocation
from backend.app.services.ai.base import (
    BaseDeduplicator, AIModelResult, compute_input_snapshot_hash
)
from backend.app.services.ai.classification_service import clean_text
from backend.app.services.ai.multilingual_service import multilingual_service

def tokenize(text: str) -> List[str]:
    stop_words = {
        "the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "or", "is",
        "are", "was", "were", "this", "that", "it", "with", "as", "by", "our", "we"
    }
    words = clean_text(text).split()
    return [w for w in words if w not in stop_words and len(w) > 2]

def compute_cosine_similarity(text1: str, text2: str) -> float:
    t1 = tokenize(text1)
    t2 = tokenize(text2)
    if not t1 or not t2:
        return 0.0
    c1 = Counter(t1)
    c2 = Counter(t2)
    intersection = set(c1.keys()) & set(c2.keys())
    numerator = sum(c1[x] * c2[x] for x in intersection)
    sum1 = sum(v ** 2 for v in c1.values())
    sum2 = sum(v ** 2 for v in c2.values())
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    if not denominator:
        return 0.0
    return float(numerator) / denominator

class AIDeduplicationService(BaseDeduplicator):
    MODEL_NAME = "JHARKHAND_GEO_SEMANTIC_DEDUPLICATOR_V2"
    MODEL_VERSION = "2.2.0"
    PROVIDER_NAME = "LOCAL_DETERMINISTIC_ENGINE"
    POLICY_VERSION = "v2026.1"
    DUPLICATE_THRESHOLD = 0.65
    TEMPORAL_WINDOW_DAYS = 180

    def find_duplicates(
        self,
        db: Session,
        title: str,
        description: str,
        category: str,
        district_name: Optional[str] = None,
        block_name: Optional[str] = None,
        exclude_id: Optional[int] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Scalable candidate pre-filtering:
        1. Temporal Filter: created within last 180 days
        2. Geospatial / Category Filter: district match OR category match
        3. Never loads entire database; capped at 100 candidates for scoring
        """
        # Multilingual normalization
        lang_meta = multilingual_service.process_text(title, description)
        target_text = f"{lang_meta['translated_title']} {lang_meta['translated_description']}"
        now_dt = datetime.now(timezone.utc).replace(tzinfo=None)
        since_date = now_dt - timedelta(days=self.TEMPORAL_WINDOW_DAYS)

        # Build optimized SQL query
        query = db.query(Challenge).outerjoin(ChallengeLocation, Challenge.id == ChallengeLocation.challenge_id)
        
        # Temporal window filter
        query = query.filter(Challenge.created_at >= since_date)

        if exclude_id:
            query = query.filter(Challenge.id != exclude_id)

        # Filter by administrative district OR category to avoid scanning the entire database
        filter_conditions = []
        if category:
            filter_conditions.append(Challenge.category == category)
        if district_name:
            filter_conditions.append(ChallengeLocation.district_name.ilike(district_name.strip()))

        if filter_conditions:
            query = query.filter(or_(*filter_conditions))

        candidates = query.order_by(Challenge.created_at.desc()).limit(100).all()
        matches = []

        for cand in candidates:
            cand_text = f"{cand.title} {cand.description}"
            # 1. Text Similarity (Cosine)
            text_sim = compute_cosine_similarity(target_text, cand_text)

            # 2. Geographic Similarity
            geo_sim = 0.0
            cand_loc = cand.location
            if cand_loc and district_name:
                if (cand_loc.district_name or "").lower() == district_name.lower():
                    geo_sim = 0.70
                    if block_name and cand_loc.block_name and cand_loc.block_name.lower() == block_name.lower():
                        geo_sim = 1.00
                else:
                    geo_sim = 0.30

            # 3. Temporal Similarity (recency decay over 180 days)
            cand_dt = cand.created_at.replace(tzinfo=None) if cand.created_at else now_dt
            days_ago = max(0.0, (now_dt - cand_dt).total_seconds() / 86400.0)
            temporal_sim = max(0.0, 1.0 - (days_ago / float(self.TEMPORAL_WINDOW_DAYS)))

            # 4. Category Similarity
            cat_sim = 1.0 if cand.category == category else 0.0

            # Multi-factor Composite Score
            # Text: 50%, Geo: 25%, Category: 15%, Temporal: 10%
            total_score = (
                (text_sim * 0.50) +
                (geo_sim * 0.25) +
                (cat_sim * 0.15) +
                (temporal_sim * 0.10)
            )

            if total_score >= self.DUPLICATE_THRESHOLD:
                cand_dist = cand_loc.district_name if cand_loc else "Jharkhand"
                explanation = (
                    f"Potential duplicate of Challenge #{cand.id} ('{cand.title}') in {cand_dist}. "
                    f"Text: {int(text_sim * 100)}%, Geo: {int(geo_sim * 100)}%, "
                    f"Category: {int(cat_sim * 100)}%, Temporal: {int(temporal_sim * 100)}%. "
                    f"Requires Human Review (never auto-suppressed)."
                )
                matches.append({
                    "similar_challenge_id": cand.id,
                    "similarity_score": round(total_score, 3),
                    "text_similarity": round(text_sim, 3),
                    "geographic_similarity": round(geo_sim, 3),
                    "temporal_similarity": round(temporal_sim, 3),
                    "category_similarity": round(cat_sim, 3),
                    "matched_keywords": ", ".join(tokenize(target_text)[:5]),
                    "explanation": explanation
                })

        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        return matches[:limit]

deduplication_service = AIDeduplicationService()
