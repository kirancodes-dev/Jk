from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.models import University, UniversityExpertise, Project

class AIUniversityMatchingService:
    MODEL_NAME = "JHARKHAND_UNIVERSITY_CAPABILITY_MATCHER"
    MODEL_VERSION = "2.1.0"

    def match_universities(
        self,
        db: Session,
        domain: str,
        keywords: List[str],
        district_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Ranks universities by academic department fit, research expertise,
        incubation capacity, and geographic proximity to Jharkhand districts.
        """
        universities = db.query(University).all()
        matches = []

        domain_lower = domain.lower()
        keyword_set = set(k.lower() for k in keywords)

        for univ in universities:
            score = 45.0  # Base institutional competence
            factors = []

            # 1. Check verified expertise areas
            expertise_entries = univ.expertise_areas
            has_domain_match = False
            for exp in expertise_entries:
                if domain_lower in exp.domain.lower():
                    score += 25.0 * (exp.score_weight or 1.0)
                    has_domain_match = True
                    factors.append(f"Specialized in {exp.domain} ({exp.focus_area or 'Core Research'})")
                    break

            # 2. Check department alignment
            for dept in univ.departments:
                dept_name = dept.name.lower()
                matched_kw = [k for k in keyword_set if k in dept_name]
                if matched_kw:
                    score += 15.0
                    factors.append(f"Active Department of {dept.name}")
                    break

            # 3. Incubation / Innovation Center Bonus
            if univ.has_incubation_center:
                score += 5.0
                factors.append("Active Incubation Center")
            if univ.has_innovation_center:
                score += 5.0

            # 4. NIRF Ranking / Tier Weighting
            if univ.nirf_ranking and univ.nirf_ranking <= 100:
                score += 5.0

            # 5. Geographic Proximity to Challenge District
            if district_name and univ.district_name.lower() == district_name.lower():
                score += 10.0
                factors.append(f"Local Institution ({univ.district_name} District)")

            # 6. Current Project Workload Balancing
            active_projects = db.query(Project).filter(
                Project.university_id == univ.id,
                Project.current_stage != "Closed"
            ).count()
            if active_projects >= 5:
                score -= 5.0  # Workload damping
                factors.append("High Active Project Workload (-5%)")
            else:
                score += 5.0  # Available capacity

            final_pct = min(98.0, max(50.0, score))
            matches.append({
                "university_id": univ.id,
                "institution_name": univ.institution_name,
                "district_name": univ.district_name,
                "match_percentage": round(final_pct, 1),
                "matching_factors": "; ".join(factors) if factors else f"General Engineering Capability in {domain}"
            })

        matches.sort(key=lambda x: x["match_percentage"], reverse=True)
        for idx, m in enumerate(matches, 1):
            m["ranking"] = idx

        return matches[:5]

matching_service = AIUniversityMatchingService()
