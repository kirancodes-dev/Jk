from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db, Base, engine
from backend.app.core.config import settings
from backend.app.services.seed_data import seed_database

router = APIRouter(prefix="/demo", tags=["Demo & Seeding"])

@router.post("/reset")
def reset_demo_data(db: Session = Depends(get_db)):
    if not settings.DEMO_MODE or settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Database reset is strictly prohibited in production environments."
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
    if not settings.DEMO_MODE or settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Demo account discovery is disabled in production environments."
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
                "description": "Higher & Technical Education Admin with statewide analytics, CSR approval & project closure powers."
            },
            {
                "role": "GOVERNMENT_OFFICER",
                "email": "officer.ranchi@jharkhand.gov.in",
                "name": "Sunil Soren",
                "description": "District Reviewing Officer (Ranchi) validating incoming grassroots challenges."
            },
            {
                "role": "VERIFIER",
                "email": "verifier.ranchi@jharkhand.gov.in",
                "name": "Amit Kumar Verma",
                "description": "Empanelled Field Inspector submitting on-site geotagged audits and lab test metrics."
            },
            {
                "role": "PRI",
                "email": "pri.angara@jharkhand.gov.in",
                "name": "Sunita Devi (Gram Mukhiya)",
                "description": "Panchayati Raj representative verifying village challenges on the ground."
            },
            {
                "role": "UNIVERSITY",
                "email": "university@bitmesra.ac.in",
                "name": "Birla Institute of Technology (BIT), Mesra",
                "description": "University administration adopting validated challenges and allocating research labs."
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
                "role": "STUDENT",
                "email": "student@sapthagiri.edu.in",
                "name": "Kiran Biradar",
                "description": "Student innovator working on embedded firmware and AI sensor diagnostics."
            },
            {
                "role": "INDUSTRY",
                "email": "industry@tatasteel.com",
                "name": "Tata Steel Foundation",
                "description": "Corporate CSR partner providing prototype grants, milestone co-funding, and signing IP agreements."
            }
        ]
    }
