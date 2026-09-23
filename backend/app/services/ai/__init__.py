"""
Modular AI Decision-Support Services Package for SIH 26043.
"""

from backend.app.services.ai.base import (
    AIModelResult, BaseClassifier, BasePriorityEngine,
    BaseDeduplicator, BaseMatcher, BaseMultilingualService,
    compute_input_snapshot_hash
)
from backend.app.services.ai.classification_service import classification_service
from backend.app.services.ai.priority_service import priority_service
from backend.app.services.ai.deduplication_service import deduplication_service
from backend.app.services.ai.matching_service import matching_service
from backend.app.services.ai.multilingual_service import multilingual_service
from backend.app.services.ai.queue_service import queue_service
from backend.app.services.ai.evaluation_service import evaluation_service

__all__ = [
    "AIModelResult",
    "BaseClassifier",
    "BasePriorityEngine",
    "BaseDeduplicator",
    "BaseMatcher",
    "BaseMultilingualService",
    "compute_input_snapshot_hash",
    "classification_service",
    "priority_service",
    "deduplication_service",
    "matching_service",
    "multilingual_service",
    "queue_service",
    "evaluation_service"
]
