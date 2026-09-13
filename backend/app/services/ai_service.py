import re
import math
from collections import Counter
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.models.models import (
    Challenge, AIAnalysis, ChallengeSimilarity, University,
    UniversityExpertise, UniversityMatch, ChallengePriority, ChallengeStatus
)

# Domain Knowledge Base
DOMAIN_KEYWORDS = {
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

DOMAIN_EXPERTISE_MAP = {
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

RECOMMENDED_SOLUTIONS = {
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

PRIORITY_SIGNALS = {
    "CRITICAL": ["death", "outbreak", "poison", "life threatening", "severe casualty", "immediate danger", "fatal", "disaster", "epidemic"],
    "HIGH": ["shortage", "contamination", "urgent", "loss", "failing", "crisis", "damage", "acute", "emergency", "sick", "dying"],
    "MEDIUM": ["difficult", "irregular", "poor", "needs repair", "delay", "slow", "inadequate", "problem"],
    "LOW": ["improvement", "upgrade", "enhancement", "suggestion", "future", "request"]
}

def clean_text(text: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return " ".join(cleaned.split())

def tokenize(text: str) -> List[str]:
    stop_words = {"the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "or", "is", "are", "was", "were", "this", "that", "it", "with", "as", "by", "our", "we"}
    words = clean_text(text).split()
    return [w for w in words if w not in stop_words and len(w) > 2]

def compute_cosine_similarity(text1: str, text2: str) -> float:
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)
    if not tokens1 or not tokens2:
        return 0.0
    counter1 = Counter(tokens1)
    counter2 = Counter(tokens2)
    
    intersection = set(counter1.keys()) & set(counter2.keys())
    numerator = sum(counter1[x] * counter2[x] for x in intersection)
    
    sum1 = sum(v ** 2 for v in counter1.values())
    sum2 = sum(v ** 2 for v in counter2.values())
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    
    if not denominator:
        return 0.0
    return float(numerator) / denominator

class AIService:
    def classify_domain(self, title: str, description: str, category_hint: str = None) -> str:
        text = clean_text(f"{title} {description}")
        domain_scores = Counter()
        
        for domain, keywords in DOMAIN_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    domain_scores[domain] += 2
        
        if category_hint and category_hint in DOMAIN_KEYWORDS:
            domain_scores[category_hint] += 4
            
        if domain_scores:
            return domain_scores.most_common(1)[0][0]
        return category_hint if category_hint in DOMAIN_KEYWORDS else "Other"

    def detect_priority(self, title: str, description: str, urgency_hint: str = "Medium") -> ChallengePriority:
        text = clean_text(f"{title} {description}")
        
        for kw in PRIORITY_SIGNALS["CRITICAL"]:
            if kw in text:
                return ChallengePriority.CRITICAL
                
        for kw in PRIORITY_SIGNALS["HIGH"]:
            if kw in text:
                return ChallengePriority.HIGH
                
        if urgency_hint.upper() in ["HIGH", "CRITICAL"]:
            return ChallengePriority.HIGH
            
        for kw in PRIORITY_SIGNALS["MEDIUM"]:
            if kw in text:
                return ChallengePriority.MEDIUM
                
        return ChallengePriority.MEDIUM

    def extract_keywords(self, title: str, description: str, top_k: int = 5) -> List[str]:
        tokens = tokenize(f"{title} {description}")
        if not tokens:
            return ["Community", "Development", "Jharkhand"]
        counts = Counter(tokens)
        return [word.capitalize() for word, _ in counts.most_common(top_k)]

    def find_similar_challenges(self, challenge_id: int, title: str, description: str, db: Session) -> List[Tuple[Challenge, float]]:
        content = f"{title} {description}"
        all_challenges = db.query(Challenge).filter(Challenge.id != challenge_id).all()
        similar_list = []
        
        for other in all_challenges:
            other_content = f"{other.title} {other.description}"
            sim = compute_cosine_similarity(content, other_content)
            if sim >= 0.25:  # threshold for similarity notification
                similar_list.append((other, round(sim * 100, 1)))
                
        similar_list.sort(key=lambda x: x[1], reverse=True)
        return similar_list[:5]

    def match_universities(self, domain: str, district_name: str, db: Session) -> List[Dict[str, Any]]:
        universities = db.query(University).all()
        ranked = []
        
        for univ in universities:
            score = 60.0  # Base score
            factors = []
            
            # Match district proximity
            if district_name and univ.district_name.lower() == district_name.lower():
                score += 15.0
                factors.append("Local District Presence")
                
            # Match university expertise areas
            matching_expertise = [e for e in univ.expertise_areas if e.domain.lower() == domain.lower()]
            if matching_expertise:
                score += 18.0
                factors.append(f"Specialized {domain} Research Center")
            
            # Facilities check
            if univ.has_incubation_center:
                score += 4.0
                factors.append("Atal Incubation Center")
            if univ.has_innovation_center:
                score += 3.0
                factors.append("SIH Innovation Lab")
                
            match_pct = min(round(score, 1), 96.0)
            ranked.append({
                "university": univ,
                "percentage": match_pct,
                "factors": ", ".join(factors)
            })
            
        ranked.sort(key=lambda x: x["percentage"], reverse=True)
        return ranked[:3]

    def analyze_challenge(self, challenge: Challenge, db: Session) -> AIAnalysis:
        combined = f"{challenge.title} {challenge.description}"
        domain = self.classify_domain(challenge.title, challenge.description, challenge.category)
        priority = self.detect_priority(challenge.title, challenge.description, challenge.urgency)
        keywords = self.extract_keywords(challenge.title, challenge.description, 5)
        
        required_exp = DOMAIN_EXPERTISE_MAP.get(domain, ["Software Engineering", "Data Analysis", "Project Management"])
        sol_rec = RECOMMENDED_SOLUTIONS.get(domain, "Community collaborative engineering solution.")
        
        # Save AI Analysis record
        analysis = AIAnalysis(
            challenge_id=challenge.id,
            cleaned_text=clean_text(combined)[:500],
            classified_domain=domain,
            detected_priority=priority,
            extracted_keywords=", ".join(keywords),
            required_expertise=", ".join(required_exp),
            recommended_solution=sol_rec,
            confidence_score=0.94
        )
        db.add(analysis)
        
        # Update challenge category/priority if needed
        challenge.category = domain
        challenge.priority = priority
        challenge.status = ChallengeStatus.AI_ANALYSIS
        
        # University matching
        district_name = challenge.location.district_name if challenge.location else "Ranchi"
        top_univs = self.match_universities(domain, district_name, db)
        for rank, match_info in enumerate(top_univs, start=1):
            um = UniversityMatch(
                challenge_id=challenge.id,
                university_id=match_info["university"].id,
                match_percentage=match_info["percentage"],
                ranking=rank,
                matching_factors=match_info["factors"]
            )
            db.add(um)
            
        # Duplicate detection
        similar_challenges = self.find_similar_challenges(challenge.id, challenge.title, challenge.description, db)
        for sim_ch, score in similar_challenges:
            cs = ChallengeSimilarity(
                challenge_id=challenge.id,
                similar_challenge_id=sim_ch.id,
                similarity_score=score,
                matched_keywords=", ".join(keywords[:3])
            )
            db.add(cs)
            
        db.commit()
        db.refresh(analysis)
        return analysis

ai_service = AIService()
