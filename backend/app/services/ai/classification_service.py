"""
Explainable domain classifier for citizen-reported challenges (V3).

How a prediction is made
------------------------
1. Title and description are normalised (Unicode NFC, lower-case) and matched
   separately against DOMAIN_LEXICON: English, Hinglish (romanised Hindi) and
   Devanagari terms, each with a weight:
       3.0  anchor   - almost always this domain ("handpump", "transformer")
       2.0  strong   - usually this domain ("toilet", "road")
       1.0  support  - context only, rarely decisive ("river", "pending")
   Matching respects word boundaries ("lac" does not fire inside "black").
   A matched phrase hides shorter terms inside it, so "septic tank" counts
   for Sanitation without "tank" also counting for Water Resources.
2. Title matches count TITLE_WEIGHT (1.5x); a term counts once per field.
3. Topic negation ("not a road problem", "bijli ki samasya nahi") zeroes the
   negated term. Absences ("no doctor", "without electricity") are not
   negation: citizens describe problems as missing services.
4. A domain's score is the sum of its signals, plus HINT_WEIGHT when the
   citizen's chosen category resolves to it. If the runner-up is within
   TIE_MARGIN of the leader, title evidence, then anchor count, then the
   earliest mention decide.
5. Optional: with the sentence-embedding model enabled and installed, the
   keyword distribution is blended (1 - EMBEDDING_BLEND) / EMBEDDING_BLEND
   with embedding similarity to each domain description. Without the model
   the classifier is keywords-only, which is the default.
6. Confidence combines evidence strength with the margin over the runner-up.
   Every "Unclassified" result and every prediction below
   REVIEW_CONFIDENCE_THRESHOLD is flagged requires_human_review.

Every result carries the matched signals, per-domain scores, the runner-up
and the margin so an officer can see why a domain was chosen. Accuracy is
measured by scripts/ai_accuracy_benchmark.py (see docs/AI_GOVERNANCE.md).
"""

import math
import re
import time
import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from backend.app.services.ai.base import (
    BaseClassifier, AIModelResult, compute_input_snapshot_hash
)
from backend.app.services.ai.embedding_service import embedding_service
from backend.app.services.ai.multilingual_service import multilingual_service

TITLE_WEIGHT = 1.5
HINT_WEIGHT = 4.0
TIE_MARGIN = 0.5
EMBEDDING_BLEND = 0.4
# Smallest threshold at which auto-accepted DEV predictions are >= 98% accurate
# (scripts/ai_accuracy_benchmark.py --calibrate; DEV only, never TEST);
# see docs/AI_GOVERNANCE.md for the accuracy above and below this line.
REVIEW_CONFIDENCE_THRESHOLD = 0.70

# Term syntax: lower-case; spaces or hyphens in a phrase also match the joined
# form ("hand pump" matches "handpump"); a trailing "*" matches any word ending
# ("irrigat*" -> irrigation, irrigated); Latin words also match plural -s/-es.
DOMAIN_LEXICON: Dict[str, Dict[float, List[str]]] = {
    "Water Resources": {
        3.0: [
            "drinking water", "hand pump", "chapakal", "chapaakal", "borewell", "bore well",
            "tube well", "jalminar", "water tower", "jal jeevan mission", "jjm", "fluoride",
            "arsenic", "groundwater", "ground water", "water table", "water level", "water supply",
            "piped water", "water pipeline", "water pipe", "water tanker", "dug well",
            "overhead tank", "water tank", "water atm", "water source", "lift irrigation",
            "har ghar nal", "nal jal", "peene ka paani", "pine ka pani",
            "पेयजल", "चापाकल", "जलमीनार", "बोरवेल", "बोरिंग", "भूजल", "फ्लोराइड", "आर्सेनिक",
            "नल जल", "पीने का पानी", "पाइपलाइन",
        ],
        2.0: [
            "well", "tap", "pipeline", "tanker", "check dam", "pond", "dobha", "spring",
            "drought", "rainwater", "canal", "purification", "chlorinat*", "contaminat*",
            "water meter", "water bill", "nal", "kuan", "kuwan", "tanki", "boring",
            "नल", "कुआं", "कुएं", "कुँआ", "टंकी", "तालाब", "डोभा", "सूखा", "नहर", "जल",
        ],
        1.5: ["water", "paani", "pani", "पानी"],
        1.0: [
            "supply", "flood*", "stream", "litre", "pump", "motor", "tank", "river", "nadi",
            "sookh*", "sukh gaya", "बाढ़", "नदी",
        ],
    },
    "Agriculture": {
        3.0: [
            "farmer", "farming", "crop", "paddy", "harvest*", "sowing", "fertilizer", "fertiliser",
            "urea", "dap", "pesticide", "pest", "msp", "mandi", "procurement centre",
            "purchase centre", "kisan credit card", "kcc", "crop insurance", "fasal bima",
            "soil health", "agricultur*", "horticultur*", "veterinar*", "vet", "vet doctor",
            "livestock", "cattle", "plant hopper", "blight", "rabi", "kharif", "ppr",
            "foot and mouth", "crop disease", "plant disease", "fungal disease", "leaf curl",
            "pashu doctor", "kisan", "kisaan", "kisano", "fasal", "dhaan", "beej", "khaad",
            "khet", "kheti", "mawesh*",
            "किसान*", "फसल", "धान", "बीज", "खाद", "यूरिया", "डीएपी", "कीटनाशक", "मंडी", "कृषि",
            "मवेशी*", "पशु चिकित्सक", "मुंहपका", "खुरपका", "ओलावृष्टि", "बुवाई", "कीड़ा",
        ],
        2.0: [
            "seed", "maize", "wheat", "potato", "tomato", "vegetable", "millet", "ragi",
            "mustard", "groundnut", "sweet potato", "chilli", "mushroom", "spawn", "farm", "plough*",
            "tractor", "insect", "keeda", "keede", "fungal", "spray", "goat", "cow", "buffalo", "cultivat*", "yield",
            "cold storage", "hail*", "seed distribution", "custom hiring", "fencing",
            "sabzi", "sabji", "tamatar", "gehu", "gehun", "bowai", "bakri*", "pashu", "dawai daal*",
            "गेहूं", "मक्का", "मक्के", "सब्जी", "टमाटर", "गोभी", "खेत*", "पैदावार", "पशु", "समिति",
        ],
        1.0: [
            "field", "irrigat*", "procurement", "rainfall", "poultry", "dairy", "trader",
            "loan", "wild boar", "elephant", "orchard", "सिंचाई", "vyapari",
        ],
    },
    "Healthcare": {
        3.0: [
            "hospital", "phc", "chc", "primary health centre", "health centre", "health center",
            "sub-centre", "subcentre", "health sub-centre", "doctor", "nurse", "anm", "sahiya",
            "asha worker", "medicine", "ambulance", "malaria", "dengue", "tuberculosis",
            "anemia", "anaemia", "malnutrition", "malnourish*", "underweight", "vaccin*",
            "immunis*", "immuniz*", "antenatal", "maternal", "pregnan*", "labour room",
            "neonatal", "newborn", "infant", "patient", "anti-venom", "anti-rabies", "rabies",
            "snakebite", "snake bite", "dog bite", "x-ray", "blood bank", "telemedicine",
            "psychiatr*", "health camp", "diarrh*", "typhoid", "cholera", "jaundice", "fever",
            "sickle cell", "silicosis", "arogya mandir", "medical officer",
            "aspatal", "aspataal", "haspatal", "dawai", "davai", "dawa", "bukhar", "teeka",
            "tika", "prasav", "garbhvati", "mareez", "marij", "ilaaj", "ilaj", "swasthya",
            "kuposhit", "kuposhan",
            "अस्पताल", "स्वास्थ्य", "डॉक्टर", "दवा*", "एम्बुलेंस", "मलेरिया", "डेंगू", "टीकाकरण",
            "टीका", "प्रसव", "गर्भवती", "मरीज*", "सहिया", "एएनएम", "पीएचसी", "कुपोषण", "कुपोषित",
            "बुखार", "इलाज",
        ],
        2.0: [
            "health", "disease", "illness", "sick", "ors", "tablet", "injection", "clinic",
            "medical", "treatment", "diagnos*", "screening", "cough", "breathless*", "addiction",
            "depression", "mental health", "counsellor", "births", "bimari", "बीमारी", "बीमार",
        ],
        1.0: ["fogging", "mosquito", "nutrition", "ayushman card*", "died", "death"],
    },
    "Education": {
        3.0: [
            "teacher", "student", "classroom", "class room", "textbook", "midday meal",
            "mid day meal", "mdm", "scholarship", "dropout", "drop out", "dropped out", "exam",
            "examination", "college", "university", "syllabus", "literacy", "para teacher",
            "headmaster", "kasturba", "iti", "lecturer", "faculty", "smart class",
            "computer lab", "library", "tuition", "masterji", "shikshak", "padhai", "kitab",
            "kitaab", "chhatravritti", "pariksha",
            "शिक्षक*", "छात्र*", "छात्रवृत्ति", "पढ़ाई", "किताब*", "मध्याह्न भोजन", "परीक्षा",
            "कॉलेज", "कक्षा", "पढ़ाया", "पारा शिक्षक",
        ],
        2.0: [
            "school", "books", "uniform", "class", "classes", "education", "learning",
            "preschool", "pre-school", "hostel", "teach*", "admission", "re-admi*", "session",
            "warden", "vidyalay", "vidyalaya", "master", "स्कूल", "विद्यालय", "छात्रावास",
        ],
        1.0: ["kitchen", "bicycle", "children", "bachche", "bachcho", "बच्चों"],
    },
    "Sanitation": {
        3.0: [
            "toilet", "latrine", "open defecation", "defecat*", "sewage", "sewer", "septic tank",
            "faecal sludge", "fecal sludge", "sludge", "garbage", "waste collection",
            "solid waste", "dustbin", "dumping yard", "swachh bharat", "sbm", "soak pit",
            "manual scavenging", "naali", "nali", "naliyon", "nali jaam", "naali jaam",
            "kachra", "kachre", "shauchalay", "shauchalaya", "sauchalay", "gandagi", "safai",
            "safai karmi", "badbu", "badboo", "khule me",
            "शौचालय", "शौच", "नाली", "नालियों", "नाली जाम", "कचरा", "कचरे", "गंदगी", "सफाई",
            "सीवर", "सेप्टिक टैंक", "स्वच्छ भारत", "बदबू", "खुले में",
        ],
        2.0: [
            "waste", "dump*", "stench", "cleanliness", "sanitation", "sanitary", "incinerator",
            "plastic", "flies", "desilt*", "drain", "drainage", "manhole", "gutter",
            "slaughter waste", "stagnant", "dirty water", "waste water",
        ],
        1.5: ["smell", "mosquito", "nagar nigam", "nagar panchayat", "overflow*"],
    },
    "Environment": {
        3.0: [
            "pollution", "pollut*", "deforestation", "forest fire", "tree felling", "trees cut",
            "coal dust", "fly ash", "fumes", "effluent", "emission", "air quality", "smog",
            "haze", "sand mining", "sand lifting", "stone crusher", "crusher", "quarry",
            "blasting", "brick kiln", "mining", "khadaan", "khadan", "overburden",
            "tailing pond", "radiation", "wildlife", "elephant corridor", "wetland", "sapling",
            "washery", "coal fire", "reserve forest", "ngt", "factory", "chemical", "kemical",
            "pradushan", "dhool", "dhul", "dhuan", "jangal", "jungle", "van vibhag", "balu",
            "bhatta", "bhatte", "eent bhatta",
            "प्रदूषण", "धूल", "धुआं", "धुएं", "खदान", "जंगल", "पेड़", "कटाई", "बालू", "क्रशर",
            "भट्ठ*", "फैक्ट्री", "रसायन", "वन विभाग",
        ],
        2.5: ["smoke", "elephant", "haathi", "hathi", "हाथी*"],
        2.0: [
            "dust", "coal", "noise", "forest", "trees", "tree", "plantation", "forest department",
            "forest guard", "climate", "erosion", "landslide", "subsid*", "toxic", "gas", "bear",
            "monkey", "animals", "logs", "ped", "machhli", "जीव", "मछलि*",
        ],
        1.0: [
            "mine", "river", "fish", "fire", "plastic", "waste water", "mahua", "nadi",
            "नदी", "आग",
        ],
    },
    "Energy": {
        3.0: [
            "electricity", "electric", "power cut", "power supply", "power outage", "outage",
            "blackout", "load shedding", "transformer", "voltage", "electricity bill",
            "smart meter", "prepaid meter", "feeder", "substation", "sub-station", "lineman",
            "line man", "jbvnl", "discom", "solar", "mini-grid", "micro-grid", "biogas",
            "kerosene", "net metering", "tripping", "fuse", "live wire", "electric pole",
            "electrician", "kva", "bijli", "bijlee", "light bill", "bijli bill", "khamba",
            "khambha", "pankha",
            "बिजली", "ट्रांसफार्मर", "वोल्टेज", "खंभा", "सोलर", "मीटर", "कटौती", "पंखा", "बल्ब",
        ],
        2.0: [
            "power", "grid", "meter", "wire", "bulb", "fan", "inverter", "generator", "energis*",
            "electrif*", "street light", "streetlight", "taar", "तार", "अंधेरे",
        ],
        1.5: ["light", "pole", "battery", "batteries", "trips", "kv"],
    },
    "Urban Infrastructure": {
        3.0: [
            "pothole", "bridge", "culvert", "footpath", "footbridge", "flyover", "over-bridge",
            "overbridge", "underpass", "traffic", "traffic jam", "congestion", "bus stand",
            "bus stop", "parking", "highway", "pmgsy", "level crossing", "railway crossing",
            "speed breaker", "zebra crossing", "guard rail", "retaining wall", "encroach*",
            "resurfac*", "storm drain", "all-weather road", "pakki sadak", "pulia", "pul",
            "gaddha", "gaddhe", "jaam",
            "पुल", "पुलिया", "गड्ढे", "गड्ढा", "जाम", "बस स्टैंड", "फुटपाथ", "अंडरपास", "पक्की सड़क",
        ],
        2.5: ["road", "sadak", "sarak", "सड़क"],
        2.0: [
            "street", "pedestrian", "vehicle", "accident", "railing", "approach road",
            "construction", "debris", "trench", "unpaved", "market complex", "vending zone",
            "chowk", "autos", "railway", "gaadi", "gaadiyon",
            "दुर्घटना*", "आवागमन", "रेलिंग", "रास्ता", "हादसे",
        ],
        1.0: ["bus", "street light", "drain", "waterlogging", "ditches"],
    },
    "Rural Livelihoods": {
        3.0: [
            "livelihood", "employment", "unemploy*", "jobs", "job card", "mgnrega", "mnrega",
            "nrega", "manrega", "wage", "wages", "migrat*", "self help group", "shg",
            "sakhi mandal", "jslps", "artisan", "handicraft", "dokra", "weaver", "weaving",
            "handloom", "loom", "tasar", "tussar", "cocoon", "sericulture", "forest produce",
            "sal leaf", "tendu", "chironji", "palash", "middlemen", "middleman",
            "skill training", "placement", "mudra", "ddu-gky", "rojgar", "rozgar", "rozgaar",
            "rojgaar", "majdoori", "mazdoori", "palayan", "karigar", "bunkar", "karghe", "lah",
            "रोजगार", "रोज़गार", "मनरेगा", "मजदूरी", "मज़दूरी", "पलायन", "सखी मंडल",
            "स्वयं सहायता समूह", "कारीगर*", "बुनकर*", "करघ*", "लाह", "वनोपज", "बिचौलि*",
        ],
        2.0: [
            "lac", "income", "earn*", "market access", "buyers", "buyer", "goat rearing",
            "goat-rearing", "fish farming", "fingerlings", "cooperative", "working capital",
            "enterprise", "bonded", "daily wage", "wage work", "pickle", "papad", "bamboo",
            "basket", "packaging", "mahua", "craft", "vendors", "tailors", "selling",
            "achaar", "bechne", "शिल्प", "महुआ", "ऋण", "बाजार",
        ],
        1.5: ["poultry", "dairy", "loan", "sell", "orders", "order", "trader", "bazaar"],
        1.0: ["training", "collective", "work", "kaam", "vyapari", "dukaan"],
    },
    "Accessibility": {
        3.0: [
            "disabled", "disabilit*", "divyang", "divyangjan", "viklang", "handicapped",
            "wheelchair", "ramp", "braille", "blind", "visually impaired", "deaf",
            "hearing impaired", "hearing aid", "hearing loss", "sign language", "tactile",
            "screen reader", "tricycle", "crutches", "cerebral palsy", "polio", "udid",
            "special educator", "assistive", "speech impaired", "disability certificate",
            "divyang praman patra", "viklang praman patra", "andha", "andhe", "behra", "behre",
            "goonge", "kaan ki machine", "sunai nahi", "dekh nahi",
            "दिव्यांग*", "विकलांग", "व्हीलचेयर", "रैंप", "ब्रेल", "नेत्रहीन", "बधिर", "श्रवण यंत्र",
            "ट्राइसाइकिल", "सांकेतिक भाषा", "दिव्यांग प्रमाण पत्र",
        ],
        2.5: ["accessible", "walker", "walkers", "low-floor", "physiotherapy", "locomotor"],
        1.5: ["lift", "inaccessible", "stairs", "steps", "seedhi", "सीढ़ियां", "सुनाई", "ishaaron"],
    },
    "Public Administration": {
        3.0: [
            "pension", "ration card", "pds", "fair price shop", "ration shop", "e-pos",
            "aadhaar", "aadhar", "certificate", "dbt", "direct benefit transfer", "rti",
            "corruption", "bribe", "bribery", "circle office", "block development officer",
            "bdo", "land record", "mutation", "dakhil kharij", "service guarantee", "e-kyc",
            "ekyc", "beneficiary list", "instalment", "installment", "maiyan samman",
            "gram sabha", "panchayat secretary", "public hearing", "janata darbar",
            "grievance portal", "awas yojana", "awaas yojana", "praman patra", "rishwat",
            "anchal office", "kist",
            "पेंशन", "राशन कार्ड", "प्रमाण पत्र", "रिश्वत", "भ्रष्टाचार", "दाखिल खारिज",
            "आवास योजना", "किस्त", "जन वितरण", "मंईयां सम्मान", "आधार कार्ड",
        ],
        2.5: ["ayushman card*", "अंचल", "anchal"],
        2.0: [
            "ration", "dealer", "grievance", "application", "applied", "verification",
            "documents", "portal", "helpline", "housing scheme", "abua awas", "pmay",
            "block office", "mukhiya", "panchayat funds", "server", "register", "issued",
            "राशन", "डीलर", "निष्पादित", "प्रखंड कार्यालय",
        ],
        1.5: ["आधार", "पोर्टल", "parchi"],
        1.0: [
            "pending", "approved", "approval", "rejected", "office", "officer", "receipt",
            "records", "shikayat", "शिकायत", "jaati", "jati", "जाति",
        ],
    },
}

# Per-domain descriptions used only by the optional embedding path.
DOMAIN_DESCRIPTIONS: Dict[str, str] = {
    "Water Resources": "Drinking water supply, handpumps, borewells, wells, piped water, water tanks, contamination, groundwater and drought. पेयजल, चापाकल, कुआं और नल जल की समस्या।",
    "Agriculture": "Farmers, crops, seeds, fertiliser, pests, crop insurance, mandi prices, procurement and livestock health. किसान, फसल, बीज, खाद और मंडी की समस्या।",
    "Healthcare": "Hospitals, health centres, doctors, medicines, ambulances, vaccination, maternal care, malaria and malnutrition. अस्पताल, डॉक्टर, दवा और टीकाकरण।",
    "Education": "Schools, teachers, students, textbooks, midday meals, scholarships, exams, hostels and colleges. स्कूल, शिक्षक, किताबें और छात्रवृत्ति।",
    "Sanitation": "Toilets, open defecation, drains, sewage, septic tanks, garbage collection and solid waste. शौचालय, नाली, कचरा और सफाई।",
    "Environment": "Pollution, mining dust, forest fires, illegal tree felling, sand mining, factory effluent, wildlife and smoke. प्रदूषण, खदान की धूल, जंगल और बालू खनन।",
    "Energy": "Electricity supply, power cuts, transformers, voltage, electricity bills, meters, solar power and poles. बिजली, ट्रांसफार्मर, वोल्टेज और बिजली बिल।",
    "Urban Infrastructure": "Roads, potholes, bridges, culverts, footpaths, traffic, bus stands and railway crossings. सड़क, पुल, पुलिया, गड्ढे और जाम।",
    "Rural Livelihoods": "Employment, MGNREGA wages, migration, self help groups, artisans, weavers, lac, tasar and forest produce markets. रोजगार, मजदूरी, पलायन और सखी मंडल।",
    "Accessibility": "Disability access: ramps, wheelchairs, braille, sign language, hearing aids, tricycles and accessible buildings. दिव्यांग, रैंप, व्हीलचेयर और ब्रेल।",
    "Public Administration": "Pensions, ration cards, certificates, Aadhaar, land records, bribery, grievances and government office delays. पेंशन, राशन कार्ड, प्रमाण पत्र और रिश्वत।",
}

# Flat view kept for callers that only need the vocabulary per domain.
CONTROLLED_TAXONOMY: Dict[str, List[str]] = {
    domain: [term.rstrip("*") for tier in tiers.values() for term in tier]
    for domain, tiers in DOMAIN_LEXICON.items()
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


# ---------------------------------------------------------------------------
# Term matching
# ---------------------------------------------------------------------------

_WORD_CHARS = "0-9a-zऀ-ॿ"
_CLAUSE_BREAK = re.compile(r"[.;:!?,\n।]")

# "not a road problem", "nothing to do with the school", "not about my pension"
_NEG_BEFORE = re.compile(
    r"(?:\bnot\s+(?:a|an|the|about|related\s+to|due\s+to|because\s+of|caused\s+by)"
    r"|\bisn't\s+(?:a|an|the|about)|\bnothing\s+to\s+do\s+with|\bunrelated\s+to)\b"
    r"(?P<gap>(?:\s+[^\s]+){0,2}?)\s*$"
)
# "water is not the issue", "bijli ki samasya nahi", "बिजली की समस्या नहीं"
_NEG_AFTER = re.compile(
    r"^(?:\s+[^\s]+){0,2}?\s+(?:(?:is|are|was|were)\s+not|isn't|aren't|wasn't)\s+"
    r"(?:the\s+|a\s+|an\s+|our\s+|my\s+)?(?:issue|problem|concern|complaint)\b"
    r"|^(?:\s+[^\s]+){0,2}?\s+(?:ki|ka|ke)\s+(?:samasya|problem|dikkat|mamla|shikayat)\s+nahi"
    r"|^(?:\s+[^\s]+){0,2}?\s+(?:की|का|के)\s+(?:समस्या|मामला|शिकायत|दिक्कत)\s+नहीं"
)
# Words after "not a ..." that signal an absence, not a change of topic:
# "not a single teacher", "not even one handpump", "not a working transformer".
_DEPRIVATION_WORDS = {
    "single", "even", "one", "proper", "working", "functional", "functioning", "regular",
    "enough", "safe", "clean", "decent", "permanent", "pucca", "new", "separate", "local",
}


def _normalise(text: Optional[str]) -> str:
    text = unicodedata.normalize("NFC", text or "").lower()
    return text.replace("’", "'").replace("‘", "'")


def _compile_term(term: str) -> "re.Pattern[str]":
    stem = term.endswith("*")
    core = _normalise(term.rstrip("*"))
    body = r"[\s\-]*".join(re.escape(p) for p in re.split(r"[\s\-]+", core) if p)
    if stem:
        tail = f"[{_WORD_CHARS}]*"
    elif core.isascii() and core[-1].isalpha():
        tail = "(?:s|es)?"
    else:
        tail = ""
    return re.compile(f"(?<![{_WORD_CHARS}]){body}{tail}(?![{_WORD_CHARS}])")


_COMPILED_LEXICON: List[Tuple[str, str, float, "re.Pattern[str]"]] = [
    (domain, term, weight, _compile_term(term))
    for domain, tiers in DOMAIN_LEXICON.items()
    for weight, terms in tiers.items()
    for term in dict.fromkeys(terms)
]


@dataclass
class _Signal:
    domain: str
    term: str
    weight: float
    field: str
    start: int
    end: int
    negated: bool = False

    @property
    def contribution(self) -> float:
        if self.negated:
            return 0.0
        return self.weight * (TITLE_WEIGHT if self.field == "title" else 1.0)


def _is_topic_negated(text: str, start: int, end: int) -> bool:
    clause_start = max((m.end() for m in _CLAUSE_BREAK.finditer(text, 0, start)), default=0)
    next_break = _CLAUSE_BREAK.search(text, end)
    clause_end = next_break.start() if next_break else len(text)

    before = _NEG_BEFORE.search(text[clause_start:start])
    if before:
        gap_words = set(before.group("gap").split())
        if not gap_words & _DEPRIVATION_WORDS:
            return True
    return bool(_NEG_AFTER.search(text[end:clause_end]))


def _match_field(text: str, field: str, use_negation: bool, lexicon=_COMPILED_LEXICON) -> List[_Signal]:
    # Signals carry the matched text, so "borewell" matched by both "borewell"
    # and "bore well" (same span) or repeated mentions count only once.
    found = [
        _Signal(domain, m.group(0), weight, field, m.start(), m.end())
        for domain, _term, weight, pattern in lexicon
        for m in pattern.finditer(text)
    ]
    # Longest phrases first; a shorter, different term inside a kept phrase is dropped.
    found.sort(key=lambda s: (-(s.end - s.start), -s.weight))
    kept: List[_Signal] = []
    seen = set()
    for sig in found:
        length = sig.end - sig.start
        if any(k.start <= sig.start and sig.end <= k.end and (k.end - k.start) > length for k in kept):
            continue
        key = (sig.domain, sig.term)
        if key in seen:
            continue
        seen.add(key)
        kept.append(sig)
    if use_negation:
        for sig in kept:
            sig.negated = _is_topic_negated(text, sig.start, sig.end)
    return kept


def _cosine(a, b) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class AIClassificationService(BaseClassifier):
    MODEL_NAME = "JHARKHAND_TAXONOMY_CLASSIFIER_V3"
    MODEL_VERSION = "3.0.0"
    PROVIDER_NAME = "LOCAL_DETERMINISTIC_ENGINE"
    POLICY_VERSION = "v2026.1"

    def __init__(
        self,
        *,
        weighted: bool = True,
        negation: bool = True,
        tie_break: bool = True,
        embeddings: bool = True,
        exclude_terms: Optional[set] = None,
    ):
        # The switches exist so the benchmark can measure each step's effect
        # (exclude_terms drops (domain, term) lexicon entries for the leakage
        # audit); production always uses the defaults.
        self.weighted = weighted
        self.negation = negation
        self.tie_break = tie_break
        self.embeddings = embeddings
        self._lexicon = [e for e in _COMPILED_LEXICON if (e[0], e[1]) not in (exclude_terms or set())]
        self._prototype_vectors: Optional[Dict[str, List[float]]] = None

    def _embedding_similarities(self, text: str) -> Optional[Dict[str, float]]:
        if not self.embeddings or not embedding_service.is_available():
            return None
        if self._prototype_vectors is None:
            domains = list(DOMAIN_DESCRIPTIONS)
            vectors = embedding_service.embed([DOMAIN_DESCRIPTIONS[d] for d in domains])
            if vectors is None:
                return None
            self._prototype_vectors = dict(zip(domains, vectors))
        encoded = embedding_service.embed([text])
        if encoded is None:
            return None
        return {d: _cosine(encoded[0], v) for d, v in self._prototype_vectors.items()}

    def classify(
        self,
        title: str,
        description: str,
        category_hint: Optional[str] = None,
        language: str = "en"
    ) -> AIModelResult:
        """
        Classifies a problem report into the controlled domain taxonomy.
        Returns an auditable AIModelResult (supports tuple unpacking for legacy callers).
        """
        start_time = time.perf_counter()
        snapshot_hash = compute_input_snapshot_hash(title, description, category_hint, language)

        lang_meta = multilingual_service.process_text(title, description)

        signals = (
            _match_field(_normalise(title), "title", self.negation, self._lexicon)
            + _match_field(_normalise(description), "description", self.negation, self._lexicon)
        )
        if not self.weighted:
            for sig in signals:
                sig.weight = 2.0
                sig.field = "description"

        scores: Dict[str, float] = Counter()
        title_scores: Dict[str, float] = Counter()
        anchors: Dict[str, int] = Counter()
        first_mention: Dict[str, int] = {}
        for sig in signals:
            if sig.negated:
                continue
            scores[sig.domain] += sig.contribution
            if sig.field == "title":
                title_scores[sig.domain] += sig.contribution
            if sig.weight >= 3.0:
                anchors[sig.domain] += 1
            pos = sig.start if sig.field == "title" else 10_000 + sig.start
            first_mention[sig.domain] = min(first_mention.get(sig.domain, pos), pos)

        resolved_hint = self._resolve_hint(category_hint)
        if resolved_hint:
            scores[resolved_hint] += HINT_WEIGHT
            first_mention.setdefault(resolved_hint, 20_000)

        keyword_evidence = 0.0
        method = "keywords"
        ranking: Dict[str, float] = dict(scores)
        sims = self._embedding_similarities(f"{title}. {description}")
        if sims:
            method = "keywords+embeddings"
            total_kw = sum(scores.values())
            exp_sims = {d: math.exp(s / 0.05) for d, s in sims.items()}
            norm = sum(exp_sims.values())
            ranking = {
                d: (1 - EMBEDDING_BLEND) * (scores.get(d, 0.0) / total_kw if total_kw else 0.0)
                + EMBEDDING_BLEND * exp_sims[d] / norm
                for d in DOMAIN_LEXICON
            }

        requires_human_review = False
        runner_up: Optional[str] = None
        margin = 0.0
        if not scores and not sims:
            # No keyword signal and no resolvable category hint: do NOT guess a domain
            # (an old default of "Urban Infrastructure" silently mis-routed unrelated
            # submissions). Flag explicitly for a human reviewer instead.
            domain = "Unclassified"
            confidence = 0.30
            requires_human_review = True
            explanation = "No taxonomy keyword signals or resolvable category hint matched; flagged for human review instead of guessing a domain."
        else:
            ordered = sorted(
                ranking,
                key=lambda d: (-ranking[d], -title_scores.get(d, 0.0), -anchors.get(d, 0), first_mention.get(d, 30_000)),
            )
            domain = ordered[0]
            tie_unit = TIE_MARGIN if method == "keywords" else TIE_MARGIN / max(sum(scores.values()), 1.0)
            if self.tie_break and len(ordered) > 1 and ranking[ordered[0]] - ranking[ordered[1]] < tie_unit:
                contenders = [d for d in ordered if ranking[ordered[0]] - ranking[d] < tie_unit]
                domain = min(
                    contenders,
                    key=lambda d: (-title_scores.get(d, 0.0), -anchors.get(d, 0), first_mention.get(d, 30_000), -ranking[d]),
                )
            others = [d for d in ordered if d != domain]
            runner_up = others[0] if others and ranking[others[0]] > 0 else None
            top, second = ranking[domain], (ranking[runner_up] if runner_up else 0.0)
            margin = top - second

            keyword_evidence = 1.0 - math.exp(-scores.get(domain, 0.0) / 4.0)
            evidence = keyword_evidence
            if sims:
                emb_evidence = min(1.0, max(0.0, (sims[domain] - 0.15) / 0.45))
                evidence = (1 - EMBEDDING_BLEND) * keyword_evidence + EMBEDDING_BLEND * emb_evidence
            separation = max(0.0, margin / top) if top > 0 else 0.0
            confidence = min(0.96, 0.30 + 0.66 * (0.5 * evidence + 0.5 * separation))
            requires_human_review = confidence < REVIEW_CONFIDENCE_THRESHOLD

            top_terms = [s.term for s in signals if s.domain == domain and not s.negated]
            explanation = (
                f"Classified as '{domain}' (score {scores.get(domain, 0.0):.1f}"
                + (f"; runner-up '{runner_up}' {scores.get(runner_up, 0.0):.1f}" if runner_up else "")
                + f") from signals: {', '.join(dict.fromkeys(top_terms)) or 'category hint'}."
            )
            if requires_human_review:
                explanation += (
                    f" Confidence {confidence:.2f} is below the {REVIEW_CONFIDENCE_THRESHOLD:.2f}"
                    " review threshold; flagged for human review."
                )

        matched_signals = [
            {
                "term": s.term,
                "domain": s.domain,
                "weight": s.weight,
                "field": s.field,
                "negated": s.negated,
            }
            for s in sorted(signals, key=lambda s: -s.contribution)
        ][:30]
        if resolved_hint:
            matched_signals.append({
                "term": category_hint, "domain": resolved_hint, "weight": HINT_WEIGHT,
                "field": "category_hint", "negated": False,
            })
        matched_keywords = list(dict.fromkeys(
            s.term for s in signals if s.domain == domain and not s.negated
        ))

        keywords = extract_keywords(f"{title} {description}")
        expertise = DOMAIN_EXPERTISE_MAP.get(domain, ["Engineering & Technology", "Problem Solving"])
        solution = RECOMMENDED_SOLUTIONS.get(domain, "Deploy technical field intervention team for rapid prototyping.")

        exec_time_ms = int((time.perf_counter() - start_time) * 1000)

        output_payload = {
            "domain": domain,
            "confidence": round(confidence, 2),
            "keywords": keywords,
            "matched_keywords": matched_keywords,
            "matched_signals": matched_signals,
            "runner_up_domain": runner_up,
            "margin": round(margin, 3),
            "review_threshold": REVIEW_CONFIDENCE_THRESHOLD,
            "method": method,
            "expertise": expertise,
            "solution": solution,
            "requires_human_review": requires_human_review,
            "translated_title": lang_meta["translated_title"],
            "translated_description": lang_meta["translated_description"],
        }

        uses_embeddings = method != "keywords"
        return AIModelResult(
            model_name=self.MODEL_NAME,
            model_version=self.MODEL_VERSION,
            provider_name=self.PROVIDER_NAME + ("+SENTENCE_TRANSFORMERS" if uses_embeddings else ""),
            execution_time_ms=exec_time_ms,
            input_snapshot_hash=snapshot_hash,
            detected_language=lang_meta["detected_language"],
            language_confidence=lang_meta["language_confidence"],
            calibration_status="CALIBRATED_FALLBACK",
            is_fallback=not uses_embeddings,
            fallback_reason=None if uses_embeddings else "Deterministic rule-based keyword heuristic executed as safe local baseline",
            policy_version=self.POLICY_VERSION,
            explanation=explanation,
            features_json={
                "domain_scores": {d: round(s, 2) for d, s in scores.items()},
                "category_hint": category_hint,
                "runner_up_domain": runner_up,
                "margin": round(margin, 3),
                "method": method,
                "embedding_similarities": {d: round(s, 4) for d, s in sims.items()} if sims else None,
                "matched_signals": matched_signals,
            },
            output=output_payload
        )

    @staticmethod
    def _resolve_hint(category_hint: Optional[str]) -> Optional[str]:
        if not category_hint:
            return None
        from backend.app.services.taxonomy_service import TaxonomyService, CANONICAL_DOMAINS
        code = TaxonomyService.resolve_domain_code(category_hint)
        if code and code in CANONICAL_DOMAINS:
            name = CANONICAL_DOMAINS[code]["name"]
            return name if name in DOMAIN_LEXICON else None
        for d in DOMAIN_LEXICON:
            if d.lower() == category_hint.strip().lower():
                return d
        return None


classification_service = AIClassificationService()
