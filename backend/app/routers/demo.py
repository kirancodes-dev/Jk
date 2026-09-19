from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db, Base, engine
from backend.app.core.config import settings
from backend.app.services.seed_data import seed_database

router = APIRouter(prefix="/demo", tags=["Demo & Seeding"])

@router.post("/reset")
def reset_demo_data(db: Session = Depends(get_db)):
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Database reset is disabled in production (DEMO_MODE=false)."
        )
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_database(db)
    return {
        "status": "success",
        "message": "Database successfully reset and re-seeded with realistic Jharkhand SIH demo data!"
    }

@router.get("/accounts")
def get_demo_accounts():
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Demo account discovery is disabled in production (DEMO_MODE=false)."
        )
    return {
        "password_for_all": "password123",
        "accounts": [
            {
                "role": "CITIZEN",
                "email": "citizen@jharkhand.gov.in",
                "name": "Ramesh Kumar Mahto",
                "description": "Rural citizen from Angara Block, Ranchi reporting water crisis."
            },
            {
                "role": "GOVERNMENT_ADMIN",
                "email": "admin@jharkhand.gov.in",
                "name": "Dr. Alok Verma, IAS",
                "description": "Higher & Technical Education Admin with statewide analytics & validation powers."
            },
            {
                "role": "UNIVERSITY",
                "email": "university@bitmesra.ac.in",
                "name": "Birla Institute of Technology (BIT), Mesra",
                "description": "University administrator mobilizing research teams and projects."
            },
            {
                "role": "FACULTY_MENTOR",
                "email": "faculty@bitmesra.ac.in",
                "name": "Dr. Ananya Sharma",
                "description": "Head of Environmental Engineering supervising student teams & approving milestones."
            },
            {
                "role": "STUDENT",
                "email": "student@bitmesra.ac.in",
                "name": "Priya Singh",
                "description": "B.Tech CSE & IoT 3rd year student working on field sensors and Flutter dashboard."
            },
            {
                "role": "INDUSTRY",
                "email": "industry@tatasteel.com",
                "name": "Tata Steel Foundation",
                "description": "Corporate CSR partner providing prototype grants and pilot testing sites."
            }
        ]
    }
