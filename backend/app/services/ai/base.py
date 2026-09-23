"""
Provider-neutral AI governance interfaces and result contracts for SIH 26043.
Enforces auditable metadata, snapshot hashing, calibration tracking, and explicit fallback labeling.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
import hashlib
import json

def compute_input_snapshot_hash(*inputs: Any) -> str:
    """Generate deterministic SHA-256 fingerprint of input data for provenance tracking."""
    hasher = hashlib.sha256()
    for item in inputs:
        if isinstance(item, (dict, list)):
            hasher.update(json.dumps(item, sort_keys=True).encode("utf-8"))
        else:
            hasher.update(str(item or "").strip().encode("utf-8"))
    return hasher.hexdigest()

@dataclass
class AIModelResult:
    """
    Standardized result contract for all AI predictions and inferences.
    Every engine (ML or rule-based fallback) must return this complete audit trail.
    """
    model_name: str
    model_version: str
    provider_name: str
    execution_time_ms: int
    input_snapshot_hash: str
    detected_language: str = "en"
    language_confidence: float = 1.0
    calibration_status: str = "CALIBRATED_FALLBACK"
    is_fallback: bool = True
    fallback_reason: Optional[str] = "Deterministic rule-based heuristic executed as safe local baseline"
    policy_version: str = "v2026.1"
    explanation: str = ""
    features_json: Dict[str, Any] = field(default_factory=dict)
    output: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def __iter__(self):
        """Allows legacy unpacking: (domain, conf, kw, exp, sol) or (priority, score, breakdown, exp)."""
        if isinstance(self.output, dict):
            if "domain" in self.output:
                yield self.output.get("domain")
                yield self.output.get("confidence", 0.7)
                yield self.output.get("keywords", [])
                yield self.output.get("expertise", [])
                yield self.output.get("solution", "")
                return
            if "priority" in self.output:
                yield self.output.get("priority")
                yield self.output.get("composite_score", 50.0)
                yield self.output.get("breakdown", {})
                yield self.output.get("explanation", "")
                return
        if isinstance(self.output, (list, tuple)):
            for item in self.output:
                yield item
        else:
            yield self.output

class BaseClassifier(ABC):
    @abstractmethod
    def classify(
        self,
        title: str,
        description: str,
        category_hint: Optional[str] = None,
        language: str = "en"
    ) -> AIModelResult:
        pass

class BasePriorityEngine(ABC):
    @abstractmethod
    def calculate_priority(
        self,
        title: str,
        description: str,
        urgency: str = "Medium",
        affected_population: int = 100,
        district_name: Optional[str] = None,
        weights_config: Optional[Dict[str, Any]] = None
    ) -> AIModelResult:
        pass

class BaseDeduplicator(ABC):
    @abstractmethod
    def find_duplicates(
        self,
        db: Any,
        title: str,
        description: str,
        category: str,
        district_name: Optional[str] = None,
        block_name: Optional[str] = None,
        exclude_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        pass

class BaseMatcher(ABC):
    @abstractmethod
    def match_universities(
        self,
        db: Any,
        domain: str,
        keywords: List[str],
        district_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        pass

class BaseMultilingualService(ABC):
    @abstractmethod
    def process_text(
        self,
        title: str,
        description: str
    ) -> Dict[str, Any]:
        pass
