import re
from typing import Optional, Tuple

# Suspicious URL & Phishing patterns
SPAM_URL_PATTERN = re.compile(
    r'(https?://(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|free-[a-z0-9\-]+|win-[a-z0-9\-]+|crypto|casino|betting)[^\s]*)',
    re.IGNORECASE
)

# Repetitive flooding patterns (e.g. 'aaaaa...', '11111...', '!!!!!!')
FLOODING_PATTERN = re.compile(r'([a-zA-Z0-9!?.])\1{9,}')

# Common abusive terms in English and transliterated Hindi
BLOCKED_KEYWORDS = {
    "abuse", "scam", "fraudulent", "viagra", "casino", "lottery", "crypto",
    "porn", "betting", "hack", "exploit"
}


class ModerationService:
    @staticmethod
    def inspect_submission(title: str, description: str) -> Tuple[bool, Optional[str]]:
        """
        Inspects challenge text for spam, phishing links, character flooding, and abusive vocabulary.
        Returns (is_abusive, failure_reason).
        """
        combined = f"{title} {description}".lower()

        # 1. Repetitive character flooding check
        if FLOODING_PATTERN.search(title) or FLOODING_PATTERN.search(description):
            return True, "Content rejected: Excessive repetitive characters or flooding detected."

        # 2. Suspicious URL & Phishing links check
        if SPAM_URL_PATTERN.search(combined):
            return True, "Content rejected: Suspicious external links or promotional URLs are not permitted."

        # 3. Profanity / scam keyword check
        words = set(re.findall(r'\b[a-z]{3,}\b', combined))
        found_blocked = words.intersection(BLOCKED_KEYWORDS)
        if found_blocked:
            return True, f"Content rejected: Prohibited terms or promotional content detected ({', '.join(found_blocked)})."

        return False, None


moderation_service = ModerationService()
