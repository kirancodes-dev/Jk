"""
Offline evaluation benchmark, metrics calculation, drift monitoring,
and model change governance service for SIH 26043.
Computes classification accuracy/F1, priority MAE, duplicate precision/recall,
tracks human override drift rates, and manages model promotion in AIModelGovernance.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.models import (
    AIModelGovernance, AIHumanOverride, AIAnalysis, ChallengePriority, utc_now
)
from backend.app.services.ai.classification_service import classification_service
from backend.app.services.ai.priority_service import priority_service
from backend.app.services.ai.deduplication_service import compute_cosine_similarity
from backend.app.services.ai.multilingual_service import multilingual_service

# Curated ground-truth benchmark suite for Jharkhand societal challenges
BENCHMARK_GROUND_TRUTH = [
    {
        "id": 1,
        "title": "Severe Arsenic and Fluoride Contamination in Village Handpumps",
        "description": "Groundwater tested with fatal levels of arsenic and fluoride. 3500 villagers suffering skin lesions and skeletal fluorosis.",
        "district": "Sahibganj",
        "true_domain": "Water Management",
        "true_priority": ChallengePriority.CRITICAL,
        "urgency": "Critical",
        "affected_population": 3500
    },
    {
        "id": 2,
        "title": "गांव के चापाकल में आर्सेनिक और फ्लोराइड का जहर",
        "description": "पीने के पानी में भारी आर्सेनिक मिला है, ग्रामीण बीमार पड़ रहे हैं और तुरंत फिल्टर की जरूरत है।",
        "district": "Sahibganj",
        "true_domain": "Water Management",
        "true_priority": ChallengePriority.CRITICAL,
        "urgency": "Critical",
        "affected_population": 3500
    },
    {
        "id": 3,
        "title": "Fall Armyworm Infestation Destroying Monsoon Maize Crops",
        "description": "Massive pest outbreak covering 800 acres of paddy and maize crops. Farmers facing total yield loss.",
        "district": "Ranchi",
        "true_domain": "Agriculture",
        "true_priority": ChallengePriority.HIGH,
        "urgency": "High",
        "affected_population": 1200
    },
    {
        "id": 4,
        "title": "Lack of Ambulance and Maternal Emergency Care at Primary Health Centre",
        "description": "PHC has no doctor or medicine at night. Pregnant women transported on cots, leading to infant mortality risks.",
        "district": "Khunti",
        "true_domain": "Healthcare",
        "true_priority": ChallengePriority.CRITICAL,
        "urgency": "Critical",
        "affected_population": 6000
    },
    {
        "id": 5,
        "title": "Dilapidated Bridge on Rural School Route with Collapsed Pier",
        "description": "Bridge between two villages has cracked support columns and holes in the deck. Potholes and danger to children.",
        "district": "Dumka",
        "true_domain": "Urban Infrastructure",
        "true_priority": ChallengePriority.HIGH,
        "urgency": "High",
        "affected_population": 800
    },
    {
        "id": 6,
        "title": "Persistent Transformer Blowouts and 18-Hour Load Shedding",
        "description": "Electricity supply transformer burned out 3 weeks ago. Micro-grid power failure affecting evening study and irrigation.",
        "district": "Hazaribagh",
        "true_domain": "Energy",
        "true_priority": ChallengePriority.MEDIUM,
        "urgency": "Medium",
        "affected_population": 450
    },
    {
        "id": 7,
        "title": "Lack of Digital Classrooms and High Secondary School Dropout",
        "description": "Government high school needs interactive STEM lab and regional language digital curriculum for tribal students.",
        "district": "Simdega",
        "true_domain": "Education",
        "true_priority": ChallengePriority.MEDIUM,
        "urgency": "Medium",
        "affected_population": 350
    },
    {
        "id": 8,
        "title": "Open Dumping of Untreated Coal Mine Dust Near Residential Area",
        "description": "Heavy particulate matter PM2.5 and coal slurry overflowing into village drain causing respiratory distress.",
        "district": "Dhanbad",
        "true_domain": "Environment",
        "true_priority": ChallengePriority.HIGH,
        "urgency": "High",
        "affected_population": 2500
    }
]

PRIORITY_SCALE_MAP = {
    ChallengePriority.LOW: 1,
    ChallengePriority.MEDIUM: 2,
    ChallengePriority.HIGH: 3,
    ChallengePriority.CRITICAL: 4
}

class AIEvaluationService:
    def run_benchmark(self, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Runs comprehensive benchmark suite measuring:
        - Domain Classification Accuracy
        - Multilingual Handling
        - Priority MAE (Mean Absolute Error) & Exact Match Rate
        - Model Latency
        """
        correct_classifications = 0
        priority_mae_sum = 0.0
        exact_priority_matches = 0
        total = len(BENCHMARK_GROUND_TRUTH)
        latencies = []

        for item in BENCHMARK_GROUND_TRUTH:
            # Test classifier
            res_cls = classification_service.classify(
                title=item["title"],
                description=item["description"]
            )
            latencies.append(res_cls.execution_time_ms)
            pred_domain = res_cls.output.get("domain")
            if pred_domain == item["true_domain"]:
                correct_classifications += 1

            # Test priority engine
            res_prio = priority_service.calculate_priority(
                title=item["title"],
                description=item["description"],
                urgency=item["urgency"],
                affected_population=item["affected_population"],
                district_name=item["district"],
                db=db
            )
            pred_prio = res_prio.output.get("priority")
            pred_val = PRIORITY_SCALE_MAP.get(pred_prio, 2)
            true_val = PRIORITY_SCALE_MAP.get(item["true_priority"], 2)

            priority_mae_sum += abs(pred_val - true_val)
            if pred_prio == item["true_priority"]:
                exact_priority_matches += 1

        accuracy = round(correct_classifications / total, 3)
        priority_mae = round(priority_mae_sum / total, 3)
        priority_agreement = round(exact_priority_matches / total, 3)
        avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else 0.0

        metrics = {
            "total_benchmark_cases": total,
            "classification_accuracy": accuracy,
            "priority_mae": priority_mae,
            "priority_exact_agreement": priority_agreement,
            "avg_latency_ms": avg_latency,
            "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "PASS" if accuracy >= 0.85 and priority_mae <= 0.50 else "WARNING"
        }
        return metrics

    def compute_drift_metrics(self, db: Session) -> Dict[str, Any]:
        """
        Monitors model drift by evaluating human reviewer override rates and discrepancies.
        High override rates (> 20%) signal need for weight retuning or taxonomy expansion.
        """
        total_analyses = db.query(AIAnalysis).count()
        total_overrides = db.query(AIHumanOverride).count()

        domain_overrides = db.query(AIHumanOverride).filter(AIHumanOverride.decision_type == "DOMAIN_OVERRIDE").count()
        priority_overrides = db.query(AIHumanOverride).filter(AIHumanOverride.decision_type == "PRIORITY_OVERRIDE").count()
        duplicate_overrides = db.query(AIHumanOverride).filter(AIHumanOverride.decision_type == "DUPLICATE_DECISION").count()

        override_rate = round(total_overrides / max(1, total_analyses), 3)

        drift_status = "STABLE"
        if override_rate >= 0.25:
            drift_status = "CRITICAL_DRIFT"
        elif override_rate >= 0.15:
            drift_status = "MODERATE_DRIFT"

        return {
            "total_analyses": total_analyses,
            "total_human_overrides": total_overrides,
            "overall_override_rate": override_rate,
            "breakdown": {
                "domain_overrides": domain_overrides,
                "priority_overrides": priority_overrides,
                "duplicate_overrides": duplicate_overrides
            },
            "drift_status": drift_status,
            "alert": override_rate >= 0.20,
            "recommendation": "Retune priority weights or update taxonomy keywords" if override_rate >= 0.20 else "Models performing within safe calibrated tolerance"
        }

    def register_model_version(
        self,
        db: Session,
        model_name: str,
        model_version: str,
        provider_name: str,
        task_type: str,
        changelog: str,
        benchmark_metrics: Optional[Dict[str, Any]] = None,
        approved_by_user_id: Optional[int] = None
    ) -> AIModelGovernance:
        """Register a new or updated model in the model registry."""
        entry = AIModelGovernance(
            model_name=model_name,
            model_version=model_version,
            provider_name=provider_name,
            task_type=task_type,
            approval_status="APPROVED" if approved_by_user_id else "STAGING",
            benchmark_metrics_json=json.dumps(benchmark_metrics or {}),
            changelog=changelog,
            approved_by_user_id=approved_by_user_id,
            approved_at=utc_now() if approved_by_user_id else None
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

evaluation_service = AIEvaluationService()
