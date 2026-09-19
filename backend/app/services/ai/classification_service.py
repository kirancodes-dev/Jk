import re
from collections import Counter
from typing import Dict, List, Tuple, Optional

# Controlled Government of Jharkhand Societal Challenge Taxonomy
CONTROLLED_TAXONOMY: Dict[str, List[str]] = {
    "Water Management": ["water", "drinking", "shortage", "borewell", "well", "pipeline", "contamination", "fluoride", "arsenic", "irrigation", "groundwater", "tap", "jal", "drought", "canal"],
    "Agriculture": ["farmer", "crop", "pest", "soil", "harvest", "seeds", "fertilizer", "monsoon", "plant disease", "paddy", "mandi", "storage", "yield", "livestock", "vegetables"],
    "Healthcare": ["hospital", "clinic", "doctor", "medicine", "malaria", "anemia", "maternal", "infant", "ambulance", "phc", "disease", "health", "nutrition", "vaccination"],
    "Education": ["school", "teacher", "student", "classroom", "books", "digital learning", "dropout", "literacy", "laboratory", "smart class", "midday meal", "attendance"],
    "Sanitation": ["toilet", "drainage", "sewage", "garbage", "waste", "cleanliness", "swachh", "plastic", "dumping", "solid waste"],
    "Environment": ["pollution", "forest", "mining", "dust", "coal dust", "deforestation", "air quality", "wildlife", "smog", "tree"],
    "Energy": ["electricity", "power", "grid", "solar", "transformer", "load shedding", "voltage", "renewable", "biogas", "blackout"],
    "Urban Infrastructure": ["road", "bridge", "pothole", "traffic", "street light", "flyover", "bus stop", "drain", "transport", "pavement"],
    "Rural Livelihoods": ["handicraft", "tribal", "employment", "artisan", "self help group", "shg", "lac", "tussar", "silk", "forest produce"],
    "Accessibility": ["disabled", "wheelchair", "ramp", "blind", "braille", "differently abled", "hearing", "divyang"]
}

DOMAIN_EXPERTISE_MAP: Dict[str, List[str]] = {
    "Water Management": ["Civil Engineering", "Environmental Engineering", "IoT & Sensor Systems", "Hydrology", "Chemical Engineering"],
    "Agriculture": ["Agricultural Engineering", "Computer Vision & AI", "Soil Science", "IoT Smart Farming", "Biotechnology"],
    "Healthcare": ["Biomedical Engineering", "Telemedicine Systems", "Public Health", "Embedded Systems", "Mobile Health Apps"],
    "Education": ["EdTech & Software Engineering", "Data Analytics", "UI/UX Design", "Pedagogy & Child Psychology"],
    "Sanitation": ["Environmental Engineering", "Solid Waste Management", "Civil Engineering", "Biochemical Processing"],
    "Environment": ["Environmental Science", "Remote Sensing & GIS", "Chemical Engineering", "IoT Air Monitoring"],
    "Energy": ["Electrical Engineering", "Solar Photovoltaics", "Power Electronics", "Renewable Energy Systems"],
    "Urban Infrastructure": ["Civil & Structural Engineering", "Smart City IoT", "Geotechnical Engineering", "Urban Planning"],
    "Rural Livelihoods": ["Supply Chain & Logistics", "Mobile Application Dev", "E-Commerce", "Value-Addition Processing"],
    "Accessibility": ["Assistive Technology", "Robotics & Mechatronics", "Speech Processing", "Ergonomics"]
}

RECOMMENDED_SOLUTIONS: Dict[str, str] = {
    "Water Management": "Deployment of IoT-enabled solar water purification kiosks and community groundwater monitoring systems.",
    "Agriculture": "AI-powered mobile crop disease identification and early warning advisory with localized weather sensors.",
    "Healthcare": "Low-cost portable telemedicine diagnostics kit for primary health centers with offline sync capability.",
    "Education": "Solar-powered smart interactive learning devices with regional language interactive STEM modules.",
    "Sanitation": "Automated community bio-digester and smart municipal solid waste segregation sensor network.",
    "Environment": "Low-cost particulate matter (PM2.5/PM10) air quality sensor grids with real-time solar alerts.",
    "Energy": "Micro-grid solar rooftop with decentralized battery storage for continuous rural household lighting.",
    "Urban Infrastructure": "Computer-vision enabled road pothole assessment and intelligent municipal drainage monitors.",
    "Rural Livelihoods": "Direct-to-consumer digital tribal artisan marketplace with QR traceability and fair-price escrow.",
    "Accessibility": "AI-driven low-cost ultrasonic obstacle detection wearable and voice-guided navigational assistant."
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

class AIClassificationService:
    MODEL_NAME = "JHARKHAND_TAXONOMY_CLASSIFIER"
    MODEL_VERSION = "2.1.0"

    def classify(self, title: str, description: str, category_hint: Optional[str] = None) -> Tuple[str, float, List[str], List[str], str]:
        """
        Classifies problem description into controlled domain taxonomy.
        Returns: (domain, confidence_score, extracted_keywords, required_expertise, recommended_solution)
        """
        text = clean_text(f"{title} {description}")
        domain_scores = Counter()

        for domain, keywords in CONTROLLED_TAXONOMY.items():
            for kw in keywords:
                if kw in text:
                    domain_scores[domain] += 2

        if category_hint and category_hint in CONTROLLED_TAXONOMY:
            domain_scores[category_hint] += 4

        if not domain_scores:
            domain = category_hint if category_hint in CONTROLLED_TAXONOMY else "Urban Infrastructure"
            confidence = 0.70
        else:
            top_match, score = domain_scores.most_common(1)[0]
            domain = top_match
            confidence = min(0.96, 0.75 + (score * 0.03))

        keywords = extract_keywords(f"{title} {description}")
        expertise = DOMAIN_EXPERTISE_MAP.get(domain, ["Engineering & Technology", "Problem Solving"])
        solution = RECOMMENDED_SOLUTIONS.get(domain, "Deploy technical field intervention team for rapid prototyping.")

        return domain, round(confidence, 2), keywords, expertise, solution

classification_service = AIClassificationService()
