import math
from collections import Counter
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.models import Challenge, ChallengeLocation
from backend.app.services.ai.classification_service import clean_text

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

class AIDeduplicationService:
    MODEL_NAME = "JHARKHAND_GEO_SEMANTIC_DEDUPLICATOR"
    MODEL_VERSION = "2.1.0"
    DUPLICATE_THRESHOLD = 0.65

    def find_duplicates(
        self,
        db: Session,
        title: str,
        description: str,
        category: str,
        district_name: Optional[str] = None,
        block_name: Optional[str] = None,
        exclude_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Multi-factor duplicate evaluation combining text similarity, category match,
        and geographic locality.
        """
        query = db.query(Challenge)
        if exclude_id:
            query = query.filter(Challenge.id != exclude_id)
            
        candidates = query.all()
        target_text = f"{title} {description}"
        matches = []

        for candidate in candidates:
            cand_text = f"{candidate.title} {candidate.description}"
            text_sim = compute_cosine_similarity(target_text, cand_text)

            # Geographic proximity weighting
            geo_bonus = 0.0
            cand_loc = candidate.location
            if cand_loc and district_name:
                if cand_loc.district_name.lower() == district_name.lower():
                    geo_bonus += 0.10
                    if block_name and cand_loc.block_name and cand_loc.block_name.lower() == block_name.lower():
                        geo_bonus += 0.10

            # Category matching bonus
            cat_bonus = 0.05 if candidate.category == category else 0.0

            total_similarity = min(1.0, text_sim * 0.8 + geo_bonus + cat_bonus)

            if total_similarity >= self.DUPLICATE_THRESHOLD:
                cand_dist = cand_loc.district_name if cand_loc else "Jharkhand"
                explanation = (
                    f"Possible duplicate of Challenge #{candidate.id} ('{candidate.title}') "
                    f"in {cand_dist}. Lexical text similarity: {int(text_sim * 100)}%, "
                    f"Geographic proximity bonus: +{int(geo_bonus * 100)}%."
                )
                matches.append({
                    "similar_challenge_id": candidate.id,
                    "similarity_score": round(total_similarity, 3),
                    "text_similarity": round(text_sim, 3),
                    "matched_keywords": ", ".join(tokenize(target_text)[:5]),
                    "explanation": explanation
                })

        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        return matches[:5]

deduplication_service = AIDeduplicationService()
