import re
import time
from collections import Counter
from typing import Dict, List, Tuple, Optional, Any
from backend.app.services.ai.base import (
    BaseClassifier, AIModelResult, compute_input_snapshot_hash
)
from backend.app.services.ai.multilingual_service import multilingual_service

# Controlled Government of Jharkhand Societal Challenge Taxonomy.
# Keys match the canonical PS 26043 domain names in taxonomy_service.CANONICAL_DOMAINS
# exactly. "Water Management" was the pre-alignment name for this domain; it remains
# a resolvable alias (see TaxonomyService.LEGACY_ALIASES) for old category_hint values.
CONTROLLED_TAXONOMY: Dict[str, List[str]] = {
    "Water Resources": ["water", "drinking", "shortage", "borewell", "well", "pipeline", "contamination", "fluoride", "arsenic", "irrigation", "groundwater", "tap", "jal", "drought", "canal", "handpump", "chapakal"],
    "Agriculture": ["farmer", "crop", "pest", "soil", "harvest", "seeds", "fertilizer", "monsoon", "plant disease", "paddy", "mandi", "storage", "yield", "livestock", "vegetables", "khet", "kisan"],
    "Healthcare": ["hospital", "clinic", "doctor", "medicine", "malaria", "anemia", "maternal", "infant", "ambulance", "phc", "disease", "health", "nutrition", "vaccination", "aspataal"],
    "Education": ["school", "teacher", "student", "classroom", "books", "digital learning", "dropout", "literacy", "laboratory", "smart class", "midday meal", "attendance", "vidyalaya"],
    "Sanitation": ["toilet", "drainage", "sewage", "garbage", "waste", "cleanliness", "swachh", "plastic", "dumping", "solid waste", "kachra", "shauchalay", "naali"],
    "Environment": ["pollution", "forest", "mining", "dust", "coal dust", "deforestation", "air quality", "wildlife", "smog", "tree"],
    "Energy": ["electricity", "power", "grid", "solar", "transformer", "load shedding", "voltage", "renewable", "biogas", "blackout", "bijli"],
    "Urban Infrastructure": ["road", "bridge", "pothole", "traffic", "street light", "flyover", "bus stop", "drain", "transport", "pavement", "sadak"],
    "Rural Livelihoods": ["handicraft", "tribal", "employment", "artisan", "self help group", "shg", "lac", "tussar", "silk", "forest produce"],
    "Accessibility": ["disabled", "wheelchair", "ramp", "blind", "braille", "differently abled", "hearing", "divyang"],
    "Public Administration": ["grievance", "pension", "dbt", "ration", "panchayat", "aadhaar", "certificate", "corruption", "bureaucracy", "service delivery"]
}

DOMAIN_EXPERTISE_MAP: Dict[str, List[str]] = {
    "Water Management": ["Civil Engineering", "Environmental Engineering", "IoT & Sensor Systems", "Hydrology", "Chemical Engineering"],
    "Water Resources": ["Civil Engineering", "Environmental Engineering", "IoT & Sensor Systems", "Hydrology", "Chemical Engineering"],
    "Agriculture": ["Agricultural Engineering", "Computer Vision & AI", "Soil Science", "IoT Smart Farming", "Biotechnology"],
    "Healthcare": ["Biomedical Engineering", "Telemedicine Systems", "Public Health", "Embedded Systems", "Mobile Health Apps"],
    "Education": ["EdTech & Software Engineering", "Data Analytics", "UI/UX Design", "Pedagogy & Child Psychology"],
    "Sanitation": ["Environmental Engineering", "Solid Waste Management", "Civil Engineering", "Biochemical Processing"],
    "Environment": ["Environmental Science", "Remote Sensing & GIS", "Chemical Engineering", "IoT Air Monitoring"],
    "Energy": ["Electrical Engineering", "Solar Photovoltaics", "Power Electronics", "Renewable Energy Systems"],
    "Urban Infrastructure": ["Civil & Structural Engineering", "Smart City IoT", "Geotechnical Engineering", "Urban Planning"],
    "Rural Livelihoods": ["Supply Chain & Logistics", "Mobile Application Dev", "E-Commerce", "Value-Addition Processing"],
    "Accessibility": ["Assistive Technology", "Robotics & Mechatronics", "Speech Processing", "Ergonomics"],
    "Public Administration": ["Public Policy", "E-Governance Systems", "Information Systems", "Data Science", "Administrative Law"]
}

RECOMMENDED_SOLUTIONS: Dict[str, str] = {
    "Water Management": "Deployment of IoT-enabled solar water purification kiosks and community groundwater monitoring systems.",
    "Water Resources": "Deployment of IoT-enabled solar water purification kiosks and community groundwater monitoring systems.",
    "Agriculture": "AI-powered mobile crop disease identification and early warning advisory with localized weather sensors.",
    "Healthcare": "Low-cost portable telemedicine diagnostics kit for primary health centers with offline sync capability.",
    "Education": "Solar-powered smart interactive learning devices with regional language interactive STEM modules.",
    "Sanitation": "Automated community bio-digester and smart municipal solid waste segregation sensor network.",
    "Environment": "Low-cost particulate matter (PM2.5/PM10) air quality sensor grids with real-time solar alerts.",
    "Energy": "Micro-grid solar rooftop with decentralized battery storage for continuous rural household lighting.",
    "Urban Infrastructure": "Computer-vision enabled road pothole assessment and intelligent municipal drainage monitors.",
    "Rural Livelihoods": "Direct-to-consumer digital tribal artisan marketplace with QR traceability and fair-price escrow.",
    "Accessibility": "AI-driven low-cost ultrasonic obstacle detection wearable and voice-guided navigational assistant.",
    "Public Administration": "Automated grievance triage, digital citizen tracking, and blockchain-audited DBT workflow verification."
}

def clean_text(text: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return " ".join(cleaned.split())

def extract_keywords(text: str, top_k: int = 8) -> List[str]:
    stop_words = {
        "the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "or", "is",
        "are", "was", "were", "this", "that", "it", "with", "as", "by", "our", "we", "from"
    }
    words = [w for w in clean_text(text).split() if w not in stop_words and len(w) > 3]
    counts = Counter(words)
    return [w for w, _ in counts.most_common(top_k)]

class AIClassificationService(BaseClassifier):
    MODEL_NAME = "JHARKHAND_TAXONOMY_CLASSIFIER_V2"
    MODEL_VERSION = "2.2.0"
    PROVIDER_NAME = "LOCAL_DETERMINISTIC_ENGINE"
    POLICY_VERSION = "v2026.1"

    def classify(
        self,
        title: str,
        description: str,
        category_hint: Optional[str] = None,
        language: str = "en"
    ) -> AIModelResult:
        """
        Classifies problem description into controlled domain taxonomy.
        Returns auditable AIModelResult (supports tuple unpacking for legacy callers).
        """
        start_time = time.perf_counter()
        snapshot_hash = compute_input_snapshot_hash(title, description, category_hint, language)

        # Multilingual normalization
        lang_meta = multilingual_service.process_text(title, description)
        detected_lang = lang_meta["detected_language"]
        lang_conf = lang_meta["language_confidence"]
        norm_title = lang_meta["translated_title"]
        norm_desc = lang_meta["translated_description"]

        text = clean_text(f"{norm_title} {norm_desc}")
        domain_scores = Counter()

        for domain, keywords in CONTROLLED_TAXONOMY.items():
            for kw in keywords:
                if kw in text:
                    domain_scores[domain] += 2

        resolved_hint = None
        if category_hint:
            from backend.app.services.taxonomy_service import TaxonomyService, CANONICAL_DOMAINS
            code = TaxonomyService.resolve_domain_code(category_hint)
            if code and code in CANONICAL_DOMAINS:
                resolved_hint = CANONICAL_DOMAINS[code]["name"]
            else:
                for d in CONTROLLED_TAXONOMY:
                    if d.lower() == category_hint.strip().lower():
                        resolved_hint = d
                        break

        if resolved_hint and resolved_hint in CONTROLLED_TAXONOMY:
            domain_scores[resolved_hint] += 4

        requires_human_review = False
        if not domain_scores:
            # No keyword signal and no resolvable category hint: do NOT guess a domain
            # (previously defaulted to "Urban Infrastructure", which silently mis-routed
            # unrelated submissions). Flag explicitly for a human reviewer instead.
            domain = "Unclassified"
            confidence = 0.30
            requires_human_review = True
            explanation = "No taxonomy keyword signals or resolvable category hint matched; flagged for human review instead of guessing a domain."
        else:
            top_match, score = domain_scores.most_common(1)[0]
            domain = top_match
            confidence = min(0.96, 0.75 + (score * 0.03))
            explanation = f"Classified as '{domain}' based on {score} matching taxonomy keyword signals."

        keywords = extract_keywords(f"{title} {description}")
        expertise = DOMAIN_EXPERTISE_MAP.get(domain, ["Engineering & Technology", "Problem Solving"])
        solution = RECOMMENDED_SOLUTIONS.get(domain, "Deploy technical field intervention team for rapid prototyping.")

        exec_time_ms = int((time.perf_counter() - start_time) * 1000)

        output_payload = {
            "domain": domain,
            "confidence": round(confidence, 2),
            "keywords": keywords,
            "expertise": expertise,
            "solution": solution,
            "requires_human_review": requires_human_review,
            "translated_title": norm_title,
            "translated_description": norm_desc,
        }

        return AIModelResult(
            model_name=self.MODEL_NAME,
            model_version=self.MODEL_VERSION,
            provider_name=self.PROVIDER_NAME,
            execution_time_ms=exec_time_ms,
            input_snapshot_hash=snapshot_hash,
            detected_language=detected_lang,
            language_confidence=lang_conf,
            calibration_status="CALIBRATED_FALLBACK",
            is_fallback=True,
            fallback_reason="Deterministic rule-based keyword heuristic executed as safe local baseline",
            policy_version=self.POLICY_VERSION,
            explanation=explanation,
            features_json={"domain_scores": dict(domain_scores), "category_hint": category_hint},
            output=output_payload
        )

classification_service = AIClassificationService()
