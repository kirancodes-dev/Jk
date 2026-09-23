"""
Multilingual processing engine for Jharkhand citizen challenges.
Preserves original Hindi / Devanagari / Indic / Santhali text, detects script and dialect hints,
provides transliteration/translation normalization for downstream indexing,
and flags low-confidence or unsupported languages for human review.
"""

import re
from typing import Dict, Any, Tuple
from backend.app.services.ai.base import BaseMultilingualService

# Devanagari character range (Hindi, Bhojpuri, Magahi, Maithili)
DEVANAGARI_REGEX = re.compile(r"[\u0900-\u097F]")
# Ol Chiki character range (Santhali indigenous script)
OL_CHIKI_REGEX = re.compile(r"[\u1C50-\u1C7F]")

# Common Hindi/Indic keywords mapped to English concepts for normalized domain matching
HINDI_CONCEPT_MAP = {
    # Water
    "पानी": "water", "जल": "water", "चापाकल": "handpump", "नल": "tap", "बोरवेल": "borewell",
    "सूखा": "drought", "तालाब": "pond", "कुआं": "well", "प्रदूषित": "contaminated",
    # Agriculture
    "किसान": "farmer", "खेती": "agriculture", "फसल": "crop", "खाद": "fertilizer",
    "कीड़ा": "pest", "बीज": "seeds", "धान": "paddy", "सिंचाई": "irrigation",
    # Healthcare
    "अस्पताल": "hospital", "दवा": "medicine", "डॉक्टर": "doctor", "बीमारी": "disease",
    "मलेरिया": "malaria", "स्वास्थ्य": "health", "इलाज": "treatment", "एम्बुलेंस": "ambulance",
    # Education
    "स्कूल": "school", "विद्यालय": "school", "शिक्षक": "teacher", "छात्र": "student",
    "किताब": "books", "पढ़ाई": "education", "कक्षा": "classroom",
    # Sanitation
    "शौचालय": "toilet", "कचरा": "garbage", "नाली": "drain", "सफाई": "cleanliness",
    "गंदगी": "waste", "सीवर": "sewage",
    # Electricity / Energy
    "बिजली": "electricity", "तार": "wire", "ट्रांसफार्मर": "transformer", "सोलर": "solar",
    # Infrastructure
    "सड़क": "road", "पुल": "bridge", "गड्ढा": "pothole", "स्ट्रीट लाइट": "street light",
    # Hinglish phonetics
    "pani": "water", "chapakal": "handpump", "bijli": "electricity", "sadak": "road",
    "kisan": "farmer", "khet": "agriculture", "aspataal": "hospital", "kachra": "garbage",
    "naali": "drain", "shauchalay": "toilet", "vidyalaya": "school"
}

class MultilingualService(BaseMultilingualService):
    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detects language and script confidence.
        Returns: (lang_code, confidence)
        Supported codes: 'hi' (Devanagari Hindi/Jharkhandi), 'sat' (Santhali Ol Chiki), 'en' (English), 'hi-Latn' (Hinglish), 'und' (Undetermined).
        """
        if not text or len(text.strip()) < 3:
            return "und", 0.30

        clean = text.strip()
        total_chars = len(re.sub(r"\s+", "", clean))
        if total_chars == 0:
            return "und", 0.0

        devanagari_chars = len(DEVANAGARI_REGEX.findall(clean))
        ol_chiki_chars = len(OL_CHIKI_REGEX.findall(clean))

        if ol_chiki_chars / total_chars > 0.30:
            return "sat", 0.95

        if devanagari_chars / total_chars > 0.30:
            return "hi", min(0.98, 0.70 + (devanagari_chars / total_chars) * 0.30)

        # Check for Latin characters
        latin_chars = len(re.findall(r"[a-zA-Z]", clean))
        if latin_chars / total_chars > 0.60:
            # Check if text contains predominant Hinglish words
            words = [w.lower() for w in re.findall(r"\w+", clean)]
            hinglish_hits = sum(1 for w in words if w in HINDI_CONCEPT_MAP)
            if len(words) > 0 and (hinglish_hits / len(words)) >= 0.25:
                return "hi-Latn", 0.82
            return "en", 0.94

        # Insufficient or ambiguous character distribution
        return "und", 0.45

    def translate_to_english_baseline(self, text: str, detected_lang: str) -> str:
        """
        Deterministic, local fallback translation/concept projection to English.
        Preserves meaning while mapping recognized Indic terms for taxonomy classifier.
        """
        if not text:
            return ""
        if detected_lang == "en":
            return text

        words = text.split()
        translated_tokens = []
        for word in words:
            clean_w = re.sub(r"[^\w\u0900-\u097F]", "", word.lower())
            if clean_w in HINDI_CONCEPT_MAP:
                translated_tokens.append(HINDI_CONCEPT_MAP[clean_w])
            else:
                translated_tokens.append(word)

        return " ".join(translated_tokens)

    def process_text(self, title: str, description: str) -> Dict[str, Any]:
        """
        Full multilingual pipeline:
        - Preserves original title & description
        - Detects language code & calibration confidence
        - Translates/normalizes concept vocabulary to English for downstream models
        - Flags low confidence (< 0.60) or 'und' for mandatory human language review
        """
        combined = f"{title} {description}"
        lang_code, confidence = self.detect_language(combined)
        requires_review = (confidence < 0.60) or (lang_code == "und")

        translated_title = self.translate_to_english_baseline(title, lang_code)
        translated_desc = self.translate_to_english_baseline(description, lang_code)

        return {
            "original_title": title,
            "original_description": description,
            "detected_language": lang_code,
            "language_confidence": round(confidence, 3),
            "translated_title": translated_title,
            "translated_description": translated_desc,
            "requires_human_language_review": requires_review,
            "explanation": f"Detected script/language '{lang_code}' with {int(confidence*100)}% confidence." +
                           (" Flagged for human review due to ambiguity." if requires_review else "")
        }

multilingual_service = MultilingualService()
