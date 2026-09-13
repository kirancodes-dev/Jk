from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from backend.app.core.database import get_db
from backend.app.services.ai_service import ai_service, DOMAIN_EXPERTISE_MAP, RECOMMENDED_SOLUTIONS

router = APIRouter(prefix="/ai", tags=["AI Engine"])

class TextAnalysisRequest(BaseModel):
    title: str
    description: str
    category_hint: Optional[str] = None
    urgency_hint: Optional[str] = "Medium"
    district_name: Optional[str] = "Ranchi"

@router.post("/analyze-text")
def analyze_text(payload: TextAnalysisRequest, db: Session = Depends(get_db)):
    domain = ai_service.classify_domain(payload.title, payload.description, payload.category_hint)
    priority = ai_service.detect_priority(payload.title, payload.description, payload.urgency_hint)
    keywords = ai_service.extract_keywords(payload.title, payload.description, 5)
    expertise = DOMAIN_EXPERTISE_MAP.get(domain, ["Engineering", "Computer Science", "Project Management"])
    solution = RECOMMENDED_SOLUTIONS.get(domain, "Community-led technical prototype solution.")
    
    univ_matches = ai_service.match_universities(domain, payload.district_name, db)
    
    return {
        "domain": domain,
        "priority": priority.value,
        "keywords": keywords,
        "required_expertise": expertise,
        "recommended_solution": solution,
        "recommended_universities": [
            {
                "university_id": m["university"].id,
                "institution_name": m["university"].institution_name,
                "district_name": m["university"].district_name,
                "match_percentage": m["percentage"],
                "matching_factors": m["factors"]
            } for m in univ_matches
        ]
    }
