"""
University and R&D institution capability matching engine for SIH 26043.
Routes ONLY to verified academic institutions and accredited R&D units.
Considers departmental alignment, verified faculty expertise, incubation capacity,
NIRF tier, geographic proximity, active project workload, and conflict-of-interest.
AI recommendations do NOT auto-assign projects; they require an explicit human allocation workflow.
"""

import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.models import University, UniversityExpertise, Project
from backend.app.services.ai.base import (
    BaseMatcher, AIModelResult, compute_input_snapshot_hash
)

class AIUniversityMatchingService(BaseMatcher):
    MODEL_NAME = "JHARKHAND_UNIVERSITY_CAPABILITY_MATCHER_V2"
    MODEL_VERSION = "2.2.0"
    PROVIDER_NAME = "LOCAL_DETERMINISTIC_ENGINE"
    POLICY_VERSION = "v2026.1"

    def match_universities(
        self,
        db: Session,
        domain: str,
        keywords: List[str],
        district_name: Optional[str] = None,
        coi_submitter_org_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Ranks verified universities by academic department fit, verified research expertise,
        incubation capacity, geographic proximity, and current active workload.
        """
        from backend.app.models.models import User
        # Strictly filter ONLY verified institutions via institutional user account
        query = db.query(University).join(User, University.user_id == User.id).filter(
            User.is_verified == True
        )
        verified_universities = query.all()

        matches = []
        domain_lower = domain.lower()
        keyword_set = set(k.lower() for k in keywords)

        for univ in verified_universities:
            # Conflict-of-Interest Filter
            if coi_submitter_org_id and univ.id == coi_submitter_org_id:
                continue

            score = 45.0  # Base institutional competence
            factors = []

            # 1. Verified Research & Expertise Areas
            expertise_entries = univ.expertise_areas
            has_domain_match = False
            for exp in expertise_entries:
                if domain_lower in exp.domain.lower():
                    weight = getattr(exp, "score_weight", 1.0) or 1.0
                    score += 25.0 * weight
                    has_domain_match = True
                    factors.append(f"Verified Domain Specialization in {exp.domain} ({exp.focus_area or 'Core Research'})")
                    break

            # 2. Academic Department Alignment
            for dept in univ.departments:
                dept_name = dept.name.lower()
                matched_kw = [k for k in keyword_set if k in dept_name]
                if matched_kw:
                    score += 15.0
                    factors.append(f"Department Alignment: {dept.name}")
                    break

            # 3. Incubation & Innovation Infrastructure
            if univ.has_incubation_center:
                score += 5.0
                factors.append("Active Incubation Center")
            if univ.has_innovation_center:
                score += 5.0
                factors.append("State-Recognized Innovation Hub")

            # 4. NIRF Accreditation & Ranking Tier
            if univ.nirf_ranking and univ.nirf_ranking <= 100:
                score += 5.0
                factors.append(f"NIRF Top-100 Institution (Rank {univ.nirf_ranking})")

            # 5. Geographic Proximity to Challenge Location
            if district_name and univ.district_name and univ.district_name.lower() == district_name.lower():
                score += 10.0
                factors.append(f"Local District Institution ({univ.district_name})")

            # 6. Workload Capacity Balancing & Past Outcomes
            active_projects = db.query(Project).filter(
                Project.university_id == univ.id,
                Project.current_stage.notin_(["Closed", "Resolved", "Impact Audited"])
            ).count()

            if active_projects >= 5:
                score -= 8.0  # High load penalty
                factors.append(f"Capacity Constrained ({active_projects} active projects, -8%)")
            elif active_projects <= 2:
                score += 5.0  # Available bandwidth
                factors.append("High Research Bandwidth Available (+5%)")

            final_pct = min(98.0, max(45.0, score))
            matches.append({
                "university_id": univ.id,
                "institution_name": univ.institution_name,
                "district_name": univ.district_name,
                "match_percentage": round(final_pct, 1),
                "matching_factors": "; ".join(factors) if factors else f"Verified Academic Unit in {domain}",
                "verification_status": "VERIFIED" if (univ.user and univ.user.is_verified) else "UNVERIFIED",
                "allocation_notice": "Recommendation only; requires explicit administrative assignment"
            })

        matches.sort(key=lambda x: x["match_percentage"], reverse=True)
        for idx, m in enumerate(matches, 1):
            m["ranking"] = idx

        return matches[:5]

matching_service = AIUniversityMatchingService()
