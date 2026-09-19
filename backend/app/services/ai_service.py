from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from backend.app.models.models import (
    Challenge, AIAnalysis, ChallengeSimilarity, University,
    UniversityMatch, ChallengePriority, ChallengeStatus
)
from backend.app.services.ai.classification_service import (
    classification_service, clean_text, extract_keywords,
    DOMAIN_EXPERTISE_MAP, RECOMMENDED_SOLUTIONS, CONTROLLED_TAXONOMY
)
from backend.app.services.ai.deduplication_service import deduplication_service
from backend.app.services.ai.priority_service import priority_service
from backend.app.services.ai.matching_service import matching_service

class AIService:
    """Unified Facade delegating to specialized modular AI engines with auditability."""

    def classify_domain(self, title: str, description: str, category_hint: Optional[str] = None) -> str:
        domain, _, _, _, _ = classification_service.classify(title, description, category_hint)
        return domain

    def detect_priority(self, title: str, description: str, urgency_hint: str = "Medium", affected_population: int = 100, district_name: Optional[str] = None) -> ChallengePriority:
        priority, _, _, _ = priority_service.calculate_priority(
            title=title,
            description=description,
            urgency=urgency_hint,
            affected_population=affected_population,
            district_name=district_name
        )
        return priority

    def extract_keywords(self, title: str, description: str, top_k: int = 5) -> List[str]:
        return extract_keywords(f"{title} {description}", top_k=top_k)

    def find_similar_challenges(self, challenge_id: int, title: str, description: str, db: Session, category: str = "General", district_name: Optional[str] = None) -> List[Tuple[Challenge, float]]:
        duplicates = deduplication_service.find_duplicates(
            db=db,
            title=title,
            description=description,
            category=category,
            district_name=district_name,
            exclude_id=challenge_id
        )
        result = []
        for d in duplicates:
            cand = db.query(Challenge).filter(Challenge.id == d["similar_challenge_id"]).first()
            if cand:
                result.append((cand, round(d["similarity_score"] * 100, 1)))
        return result

    def match_universities(self, domain: str, district_name: str, db: Session) -> List[Dict[str, Any]]:
        matches = matching_service.match_universities(
            db=db,
            domain=domain,
            keywords=extract_keywords(domain, top_k=3),
            district_name=district_name
        )
        out = []
        for m in matches:
            univ = db.query(University).filter(University.id == m["university_id"]).first()
            if univ:
                out.append({
                    "university": univ,
                    "percentage": m["match_percentage"],
                    "factors": m["matching_factors"]
                })
        return out

    def analyze_challenge(self, challenge: Challenge, db: Session) -> AIAnalysis:
        dist_name = challenge.location.district_name if challenge.location else "Ranchi"
        domain, conf, keywords, exp, sol = classification_service.classify(
            challenge.title, challenge.description, challenge.category
        )
        pop = getattr(challenge, "affected_population", 100) or 100
        priority, score, breakdown, explanation = priority_service.calculate_priority(
            challenge.title, challenge.description, challenge.urgency, affected_population=pop, district_name=dist_name
        )

        analysis = AIAnalysis(
            challenge_id=challenge.id,
            cleaned_text=clean_text(f"{challenge.title} {challenge.description}")[:500],
            classified_domain=domain,
            detected_priority=priority,
            extracted_keywords=", ".join(keywords),
            required_expertise=", ".join(exp),
            recommended_solution=sol,
            confidence_score=conf
        )
        db.add(analysis)

        # Update challenge category/priority
        challenge.category = domain
        challenge.priority = priority
        challenge.status = ChallengeStatus.AI_ANALYSIS

        # University matching
        top_univs = self.match_universities(domain, dist_name, db)
        for rank, match_info in enumerate(top_univs, start=1):
            um = UniversityMatch(
                challenge_id=challenge.id,
                university_id=match_info["university"].id,
                match_percentage=match_info["percentage"],
                ranking=rank,
                matching_factors=match_info["factors"]
            )
            db.add(um)

        # Multi-factor duplicate check
        sims = self.find_similar_challenges(
            challenge.id, challenge.title, challenge.description, db, category=domain, district_name=dist_name
        )
        for sim_ch, sim_score in sims:
            cs = ChallengeSimilarity(
                challenge_id=challenge.id,
                similar_challenge_id=sim_ch.id,
                similarity_score=sim_score,
                matched_keywords=", ".join(keywords[:3])
            )
            db.add(cs)

        db.commit()
        db.refresh(analysis)
        return analysis

ai_service = AIService()
