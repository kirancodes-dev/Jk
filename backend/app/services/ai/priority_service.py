import time
import json
from typing import Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.models import ChallengePriority, AIPriorityWeightConfig
from backend.app.services.ai.base import (
    BasePriorityEngine, AIModelResult, compute_input_snapshot_hash
)
from backend.app.services.ai.classification_service import clean_text
from backend.app.services.ai.multilingual_service import multilingual_service

DEFAULT_PRIORITY_WEIGHTS = {
    "severity_weight": 0.30,
    "urgency_weight": 0.20,
    "population_weight": 0.20,
    "health_safety_weight": 0.15,
    "vulnerability_weight": 0.15
}

PRIORITY_SIGNALS = {
    "CRITICAL": ["death", "outbreak", "poison", "life threatening", "severe casualty", "immediate danger", "fatal", "disaster", "epidemic", "arsenic", "fluoride", "collapse", "electrocution"],
    "HIGH": ["shortage", "contamination", "urgent", "loss", "failing", "crisis", "damage", "acute", "emergency", "sick", "dying", "broken bridge", "dry well", "overflowing"],
    "MEDIUM": ["difficult", "irregular", "poor", "needs repair", "delay", "slow", "inadequate", "problem", "maintenance"],
    "LOW": ["improvement", "upgrade", "enhancement", "suggestion", "future", "request", "beautification"]
}

HEALTH_SAFETY_SIGNALS = [
    "poison", "arsenic", "fluoride", "contamination", "disease", "malaria", "epidemic",
    "casualty", "electrocution", "collapse", "toxic", "death", "child", "hospital", "phc"
]

# The 19 (of 24) Jharkhand districts under NITI Aayog's Aspirational Districts
# Programme — used as a static fallback when a DB lookup isn't available (e.g. no
# session was passed in). When a Session is available, District.is_aspirational
# is authoritative; see AIPriorityService._is_aspirational_district below.
JHARKHAND_ASPIRATIONAL_DISTRICTS = {
    "bokaro", "chatra", "dumka", "garhwa", "giridih", "godda", "gumla",
    "hazaribagh", "khunti", "latehar", "lohardaga", "pakur", "palamu",
    "west singhbhum", "east singhbhum", "ramgarh", "ranchi", "sahebganj", "simdega",
}

class AIPriorityService(BasePriorityEngine):
    MODEL_NAME = "JHARKHAND_MULTIFACTOR_PRIORITY_ENGINE_V2"
    MODEL_VERSION = "2.2.0"
    PROVIDER_NAME = "LOCAL_DETERMINISTIC_ENGINE"
    POLICY_VERSION = "v2026.1"

    def get_active_weights(self, db: Optional[Session] = None, weights_override: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, float], str]:
        """Fetch active configurable weights from database or fall back to versioned defaults."""
        if weights_override:
            return {k: float(v) for k, v in weights_override.items()}, "CUSTOM_OVERRIDE"

        if db:
            try:
                active_cfg = db.query(AIPriorityWeightConfig).filter(AIPriorityWeightConfig.is_active == True).order_by(AIPriorityWeightConfig.id.desc()).first()
                if active_cfg and active_cfg.weights_json:
                    parsed = json.loads(active_cfg.weights_json)
                    return {k: float(v) for k, v in parsed.items()}, active_cfg.config_version
            except Exception:
                pass

        return DEFAULT_PRIORITY_WEIGHTS.copy(), "v2026.1-DEFAULT"

    @staticmethod
    def _is_aspirational_district(district_name: str, db: Optional[Session] = None) -> bool:
        """
        District.is_aspirational is authoritative when a DB session is available.
        Falls back to the static NITI Aayog list (e.g. for callers with no session,
        or a district name not yet seeded in the districts table).
        """
        dist_clean = (district_name or "").strip()
        if db and dist_clean:
            try:
                from backend.app.models.models import District
                row = db.query(District).filter(District.name.ilike(dist_clean)).first()
                if row is not None:
                    return bool(row.is_aspirational)
            except Exception:
                pass
        return dist_clean.lower() in JHARKHAND_ASPIRATIONAL_DISTRICTS

    def calculate_priority(
        self,
        title: str,
        description: str,
        urgency: str = "Medium",
        affected_population: int = 100,
        district_name: Optional[str] = None,
        weights_config: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None
    ) -> AIModelResult:
        """
        Calculates multi-factor transparent priority score using versioned configured weights:
        1. Severity (keywords & hazard signals)
        2. Urgency Flag (citizen/field operator)
        3. Population Impact Scale
        4. Health & Safety Threat
        5. Regional Vulnerability (Aspirational Districts)
        """
        start_time = time.perf_counter()
        snapshot_hash = compute_input_snapshot_hash(title, description, urgency, affected_population, district_name)

        weights, config_ver = self.get_active_weights(db=db, weights_override=weights_config)
        w_sev = weights.get("severity_weight", 0.30)
        w_urg = weights.get("urgency_weight", 0.20)
        w_pop = weights.get("population_weight", 0.20)
        w_hs = weights.get("health_safety_weight", 0.15)
        w_vuln = weights.get("vulnerability_weight", 0.15)

        # Normalize incoming text across Indic/English
        lang_meta = multilingual_service.process_text(title, description)
        norm_text = clean_text(f"{lang_meta['translated_title']} {lang_meta['translated_description']}")

        # 1. Severity Score (0 - 100)
        severity_score = 35.0
        for word in PRIORITY_SIGNALS["CRITICAL"]:
            if word in norm_text:
                severity_score = max(severity_score, 95.0)
        for word in PRIORITY_SIGNALS["HIGH"]:
            if word in norm_text:
                severity_score = max(severity_score, 80.0)
        for word in PRIORITY_SIGNALS["MEDIUM"]:
            if word in norm_text:
                severity_score = max(severity_score, 50.0)

        # 2. Urgency Input Score (0 - 100)
        urgency_map = {"Critical": 100.0, "High": 80.0, "Medium": 50.0, "Low": 25.0}
        urgency_score = urgency_map.get(urgency, 50.0)

        # 3. Affected Population Score (0 - 100)
        pop = affected_population or 100
        if pop >= 5000:
            pop_score = 100.0
        elif pop >= 1000:
            pop_score = 80.0
        elif pop >= 200:
            pop_score = 60.0
        elif pop >= 50:
            pop_score = 40.0
        else:
            pop_score = 20.0

        # 4. Health & Safety Threat Score (0 - 100)
        hs_matches = sum(1 for kw in HEALTH_SAFETY_SIGNALS if kw in norm_text)
        hs_score = min(100.0, 30.0 + (hs_matches * 25.0))

        # 5. Regional Vulnerability (Aspirational Districts of Jharkhand)
        vuln_score = 85.0 if self._is_aspirational_district(district_name, db=db) else 50.0

        # Composite Weighted Calculation
        composite = (
            (severity_score * w_sev) +
            (urgency_score * w_urg) +
            (pop_score * w_pop) +
            (hs_score * w_hs) +
            (vuln_score * w_vuln)
        )
        composite = round(min(100.0, max(10.0, composite)), 1)

        # Map to Priority Level
        if composite >= 78.0 or severity_score >= 95.0:
            level = ChallengePriority.CRITICAL
        elif composite >= 60.0 or severity_score >= 80.0:
            level = ChallengePriority.HIGH
        elif composite >= 35.0:
            level = ChallengePriority.MEDIUM
        else:
            level = ChallengePriority.LOW

        breakdown = {
            "config_version": config_ver,
            "composite_score": composite,
            "weights": {
                "severity": w_sev,
                "urgency": w_urg,
                "population": w_pop,
                "health_safety": w_hs,
                "vulnerability": w_vuln
            },
            "scores": {
                "severity_score": severity_score,
                "urgency_score": urgency_score,
                "population_score": pop_score,
                "health_safety_score": hs_score,
                "vulnerability_score": vuln_score
            },
            "affected_population": pop,
            "district": district_name or "Unspecified"
        }

        explanation = (
            f"Calculated {level.value} Priority (Composite: {composite}/100) under policy {config_ver}. "
            f"Severity: {severity_score} (weight {int(w_sev*100)}%), Urgency: {urgency_score} (weight {int(w_urg*100)}%), "
            f"Population Scale: {pop_score} ({pop} people), Health/Safety: {hs_score}, Vulnerability: {vuln_score}."
        )

        exec_time_ms = int((time.perf_counter() - start_time) * 1000)

        output_payload = {
            "priority": level,
            "composite_score": composite,
            "breakdown": breakdown,
            "explanation": explanation
        }

        return AIModelResult(
            model_name=self.MODEL_NAME,
            model_version=self.MODEL_VERSION,
            provider_name=self.PROVIDER_NAME,
            execution_time_ms=exec_time_ms,
            input_snapshot_hash=snapshot_hash,
            detected_language=lang_meta["detected_language"],
            language_confidence=lang_meta["language_confidence"],
            calibration_status="CALIBRATED_FALLBACK",
            is_fallback=True,
            fallback_reason="Configurable multi-factor rule-based priority engine executed as safe deterministic baseline",
            policy_version=config_ver,
            explanation=explanation,
            features_json=breakdown,
            output=output_payload
        )

priority_service = AIPriorityService()
