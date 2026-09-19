from typing import Tuple, Dict, Any, Optional
from backend.app.models.models import ChallengePriority
from backend.app.services.ai.classification_service import clean_text

PRIORITY_SIGNALS = {
    "CRITICAL": ["death", "outbreak", "poison", "life threatening", "severe casualty", "immediate danger", "fatal", "disaster", "epidemic", "arsenic", "fluoride", "collapse"],
    "HIGH": ["shortage", "contamination", "urgent", "loss", "failing", "crisis", "damage", "acute", "emergency", "sick", "dying", "broken bridge", "dry well"],
    "MEDIUM": ["difficult", "irregular", "poor", "needs repair", "delay", "slow", "inadequate", "problem", "maintenance"],
    "LOW": ["improvement", "upgrade", "enhancement", "suggestion", "future", "request", "beautification"]
}

class AIPriorityService:
    MODEL_NAME = "JHARKHAND_MULTIFACTOR_PRIORITY_ENGINE"
    MODEL_VERSION = "2.1.0"

    def calculate_priority(
        self,
        title: str,
        description: str,
        urgency: str = "Medium",
        affected_population: int = 100,
        district_name: Optional[str] = None
    ) -> Tuple[ChallengePriority, float, Dict[str, Any], str]:
        """
        Calculates multi-factor transparent priority score:
        - Severity/Keywords: 35%
        - Urgency Flag: 25%
        - Population Impact Scale: 25%
        - Regional Vulnerability: 15%
        """
        text = clean_text(f"{title} {description}")

        # 1. Severity Keywords Score (0 - 100)
        severity_score = 40.0
        for word in PRIORITY_SIGNALS["CRITICAL"]:
            if word in text:
                severity_score = max(severity_score, 95.0)
        for word in PRIORITY_SIGNALS["HIGH"]:
            if word in text:
                severity_score = max(severity_score, 80.0)
        for word in PRIORITY_SIGNALS["MEDIUM"]:
            if word in text:
                severity_score = max(severity_score, 50.0)

        # 2. Urgency Input Score (0 - 100)
        urgency_map = {"Critical": 100.0, "High": 80.0, "Medium": 50.0, "Low": 25.0}
        urgency_score = urgency_map.get(urgency, 50.0)

        # 3. Affected Population Score (0 - 100)
        if affected_population >= 5000:
            pop_score = 100.0
        elif affected_population >= 1000:
            pop_score = 80.0
        elif affected_population >= 200:
            pop_score = 60.0
        elif affected_population >= 50:
            pop_score = 40.0
        else:
            pop_score = 20.0

        # 4. Regional Vulnerability (Aspirational Districts of Jharkhand)
        aspirational_districts = {
            "khunti", "dumka", "pakur", "sahibganj", "simdega", "west singhbhum", "latehar"
        }
        dist_clean = (district_name or "").lower().strip()
        vuln_score = 85.0 if dist_clean in aspirational_districts else 50.0

        # Weighted Composition
        composite = (
            (severity_score * 0.35) +
            (urgency_score * 0.25) +
            (pop_score * 0.25) +
            (vuln_score * 0.15)
        )

        if composite >= 80.0:
            level = ChallengePriority.CRITICAL
        elif composite >= 60.0 or severity_score >= 90.0:
            level = ChallengePriority.HIGH
        elif composite >= 35.0:
            level = ChallengePriority.MEDIUM
        else:
            level = ChallengePriority.LOW

        breakdown = {
            "composite_score": round(composite, 1),
            "severity_weight_pct": 35,
            "severity_score": severity_score,
            "urgency_weight_pct": 25,
            "urgency_score": urgency_score,
            "population_weight_pct": 25,
            "population_score": pop_score,
            "vulnerability_weight_pct": 15,
            "vulnerability_score": vuln_score,
        }

        explanation = (
            f"Calculated {level.value} Priority (Score: {round(composite, 1)}/100). "
            f"Severity contribution: {round(severity_score * 0.35, 1)} pts, "
            f"Population scale ({affected_population} affected): {round(pop_score * 0.25, 1)} pts."
        )

        return level, round(composite, 1), breakdown, explanation

priority_service = AIPriorityService()
