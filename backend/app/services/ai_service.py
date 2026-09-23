"""
Authoritative AI Decision-Support Service Facade for SIH 26043.
Orchestrates domain classification, multi-factor priority calculation,
scalable deduplication, university capability matching, and human override auditing.
Enforces that deterministic rule heuristics are explicitly labeled as local fallbacks
and never presented as validated ML models.
"""

import json
import time
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from backend.app.models.models import (
    Challenge, AIAnalysis, ChallengeSimilarity, University,
    UniversityMatch, ChallengePriority, ChallengeStatus,
    AIHumanOverride, utc_now
)
from backend.app.services.ai.classification_service import (
    classification_service, clean_text, extract_keywords,
    DOMAIN_EXPERTISE_MAP, RECOMMENDED_SOLUTIONS, CONTROLLED_TAXONOMY
)
from backend.app.services.ai.deduplication_service import deduplication_service
from backend.app.services.ai.priority_service import priority_service
from backend.app.services.ai.matching_service import matching_service
from backend.app.services.ai.multilingual_service import multilingual_service
from backend.app.services.ai.base import compute_input_snapshot_hash

class AIService:
    """Authoritative Facade delegating to specialized governable AI engines."""

    def classify_domain(self, title: str, description: str, category_hint: Optional[str] = None) -> str:
        res = classification_service.classify(title, description, category_hint)
        return res.output.get("domain", "Urban Infrastructure")

    def detect_priority(
        self,
        title: str,
        description: str,
        urgency_hint: str = "Medium",
        affected_population: int = 100,
        district_name: Optional[str] = None,
        db: Optional[Session] = None
    ) -> ChallengePriority:
        res = priority_service.calculate_priority(
            title=title,
            description=description,
            urgency=urgency_hint,
            affected_population=affected_population,
            district_name=district_name,
            db=db
        )
        return res.output.get("priority", ChallengePriority.MEDIUM)

    def extract_keywords(self, title: str, description: str, top_k: int = 5) -> List[str]:
        return extract_keywords(f"{title} {description}", top_k=top_k)

    def find_similar_challenges(
        self,
        challenge_id: int,
        title: str,
        description: str,
        db: Session,
        category: str = "General",
        district_name: Optional[str] = None
    ) -> List[Tuple[Challenge, float, Dict[str, Any]]]:
        """Finds potential duplicates with decomposed similarity signals."""
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
                result.append((cand, round(d["similarity_score"] * 100, 1), d))
        return result

    def match_universities(
        self,
        domain: str,
        district_name: str,
        db: Session,
        coi_submitter_org_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        matches = matching_service.match_universities(
            db=db,
            domain=domain,
            keywords=extract_keywords(domain, top_k=3),
            district_name=district_name,
            coi_submitter_org_id=coi_submitter_org_id
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
        """Executes full governable AI analysis for challenge."""
        return self._run_analysis_core(challenge, db, is_fallback=True, fallback_reason="Deterministic rule-based heuristics executed as safe local baseline")

    def analyze_challenge_fallback(
        self,
        challenge: Challenge,
        db: Session,
        fallback_reason: str = "Primary model timeout; local deterministic fallback triggered"
    ) -> AIAnalysis:
        """Safe fallback analyzer executed during queue retries or failures."""
        return self._run_analysis_core(challenge, db, is_fallback=True, fallback_reason=fallback_reason)

    def _run_analysis_core(
        self,
        challenge: Challenge,
        db: Session,
        is_fallback: bool = True,
        fallback_reason: Optional[str] = None
    ) -> AIAnalysis:
        start_time = time.perf_counter()
        dist_name = challenge.location.district_name if challenge.location else "Ranchi"
        pop = getattr(challenge, "affected_population", 100) or 100

        # 1. Multilingual processing
        lang_res = multilingual_service.process_text(challenge.title, challenge.description)

        # 2. Domain classification
        cls_res = classification_service.classify(
            challenge.title, challenge.description, challenge.category
        )
        domain = cls_res.output["domain"]
        conf = cls_res.output["confidence"]
        keywords = cls_res.output["keywords"]
        exp = cls_res.output["expertise"]
        sol = cls_res.output["solution"]

        # 3. Priority calculation
        prio_res = priority_service.calculate_priority(
            challenge.title, challenge.description, challenge.urgency,
            affected_population=pop, district_name=dist_name, db=db
        )
        priority = prio_res.output["priority"]
        prio_breakdown = prio_res.output["breakdown"]

        exec_time_ms = int((time.perf_counter() - start_time) * 1000)
        snapshot_hash = compute_input_snapshot_hash(
            challenge.id, challenge.title, challenge.description, challenge.category, dist_name, pop
        )

        analysis = AIAnalysis(
            challenge_id=challenge.id,
            cleaned_text=clean_text(f"{challenge.title} {challenge.description}")[:500],
            classified_domain=domain,
            detected_priority=priority,
            extracted_keywords=", ".join(keywords),
            required_expertise=", ".join(exp),
            recommended_solution=sol,
            confidence_score=conf,
            # Governance fields
            model_name="JHARKHAND_GOV_AI_SUITE",
            model_version="2.2.0",
            provider_name="LOCAL_DETERMINISTIC_ENGINE",
            execution_time_ms=exec_time_ms,
            input_snapshot_hash=snapshot_hash,
            detected_language=lang_res["detected_language"],
            language_confidence=lang_res["language_confidence"],
            calibration_status="CALIBRATED_FALLBACK",
            is_fallback=is_fallback,
            fallback_reason=fallback_reason,
            policy_version="v2026.1",
            explanation=f"Domain: {cls_res.explanation} | Priority: {prio_res.explanation}",
            features_json=json.dumps(cls_res.features_json),
            priority_breakdown_json=json.dumps(prio_breakdown),
            translated_title=lang_res["translated_title"],
            translated_description=lang_res["translated_description"]
        )
        db.add(analysis)

        from backend.app.services.taxonomy_service import TaxonomyService
        from backend.app.services.workflow_service import WorkflowService

        # Update challenge category only if invalid/not set
        if not challenge.category or not TaxonomyService.is_valid_domain(challenge.category):
            challenge.category = domain
        challenge.priority = priority

        WorkflowService.transition_challenge(
            db=db,
            challenge=challenge,
            to_status=ChallengeStatus.AI_ANALYSIS,
            actor=challenge.submitted_by_user,
            remarks="Automated AI triage and NLP domain classification"
        )

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

        # Multi-factor duplicate check with decomposed signals
        sims = self.find_similar_challenges(
            challenge.id, challenge.title, challenge.description, db, category=domain, district_name=dist_name
        )
        for sim_ch, sim_score, sim_meta in sims:
            cs = ChallengeSimilarity(
                challenge_id=challenge.id,
                similar_challenge_id=sim_ch.id,
                similarity_score=sim_score,
                matched_keywords=", ".join(keywords[:3]),
                text_similarity=sim_meta.get("text_similarity", 0.0),
                geographic_similarity=sim_meta.get("geographic_similarity", 0.0),
                temporal_similarity=sim_meta.get("temporal_similarity", 0.0),
                category_similarity=sim_meta.get("category_similarity", 0.0),
                explanation=sim_meta.get("explanation", ""),
                dismissed=False
            )
            db.add(cs)

        db.commit()
        db.refresh(analysis)
        return analysis

    def record_human_override(
        self,
        db: Session,
        challenge_id: int,
        reviewer_id: int,
        decision_type: str,
        override_value: str,
        mandatory_reason: str
    ) -> AIHumanOverride:
        """
        Records an auditable human override while NEVER modifying or deleting
        the historical AI prediction in AIAnalysis.
        Updates effective challenge attribute and records workflow audit event.
        """
        if not mandatory_reason or len(mandatory_reason.strip()) < 5:
            raise ValueError("A mandatory justification reason (min 5 characters) is required for any AI override.")

        challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
        if not challenge:
            raise ValueError(f"Challenge #{challenge_id} not found")

        analysis = db.query(AIAnalysis).filter(AIAnalysis.challenge_id == challenge_id).order_by(AIAnalysis.id.desc()).first()

        original_val = "N/A"
        if decision_type == "DOMAIN_OVERRIDE":
            original_val = analysis.classified_domain if analysis else (challenge.category or "None")
            challenge.category = override_value
        elif decision_type == "PRIORITY_OVERRIDE":
            original_val = analysis.detected_priority.value if analysis and analysis.detected_priority else challenge.priority.value
            try:
                challenge.priority = ChallengePriority(override_value)
            except ValueError:
                pass
        elif decision_type == "DUPLICATE_DECISION":
            original_val = "FLAGGED_AS_POSSIBLE_DUPLICATE"
            # Mark similarities as dismissed or confirmed
            sims = db.query(ChallengeSimilarity).filter(ChallengeSimilarity.challenge_id == challenge_id).all()
            for s in sims:
                s.dismissed = (override_value.upper() == "DISMISSED")
                s.dismissed_by_user_id = reviewer_id
                s.dismissal_reason = mandatory_reason
        elif decision_type == "FULL_ACCEPTANCE":
            original_val = "AI_RECOMMENDATION"

        override_record = AIHumanOverride(
            challenge_id=challenge_id,
            analysis_id=analysis.id if analysis else None,
            reviewer_id=reviewer_id,
            decision_type=decision_type,
            original_value=str(original_val),
            override_value=str(override_value),
            mandatory_reason=mandatory_reason.strip()
        )
        db.add(override_record)

        # Record tamper-evident audit history
        from backend.app.services.workflow_service import WorkflowService
        from backend.app.models.models import User
        reviewer = db.query(User).filter(User.id == reviewer_id).first()

        WorkflowService._record_domain_event(
            db=db,
            entity_type="Challenge",
            entity_id=challenge.id,
            action=f"AI_{decision_type}",
            previous_state=challenge.status.value if hasattr(challenge.status, "value") else str(challenge.status),
            new_state=challenge.status.value if hasattr(challenge.status, "value") else str(challenge.status),
            actor=reviewer,
            payload={
                "decision_type": decision_type,
                "original_value": str(original_val),
                "override_value": str(override_value),
                "reason": mandatory_reason.strip()
            },
            notes=f"Reviewer override: {original_val} -> {override_value}. Reason: {mandatory_reason.strip()}"
        )

        db.commit()
        db.refresh(override_record)
        return override_record

ai_service = AIService()
