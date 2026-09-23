"""
DPDP Privacy & Citizen Data Rights API Router for SIH 26043.
Provides:
- GET /notices: Statutory transparency, purpose specification, and DPO grievance contacts.
- GET /my-data: Citizen data export / portability.
- PUT /correct-data: Citizen data correction and rectification.
- POST /request-erasure: Anonymization / erasure preserving statutory audit integrity.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.models import User
from backend.app.routers.deps import get_current_user
from backend.app.services.dpdp_service import dpdp_service

router = APIRouter(prefix="/privacy", tags=["DPDP Citizen Data Rights & Privacy"])


class DataCorrectionRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    phone_number: Optional[str] = Field(None, min_length=10, max_length=15)
    district_name: Optional[str] = Field(None, max_length=100)
    block_name: Optional[str] = Field(None, max_length=100)


class ErasureRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500, description="Mandatory reason for erasure/anonymization")
    confirmation: bool = Field(..., description="Must confirm understanding that account will be deactivated")


@router.get("/notices")
def get_privacy_notices():
    """
    Returns public privacy and data fiduciary transparency disclosures,
    including purpose specification, retention policies, and State DPO contacts.
    """
    return dpdp_service.get_privacy_notices()


@router.get("/my-data")
def export_my_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Right to Access / Data Portability (DPDP Act):
    Returns full personal profile, challenges, project roles, and preferences in JSON format.
    """
    return dpdp_service.export_user_data(user=current_user, db=db)


@router.put("/correct-data")
def correct_my_data(
    payload: DataCorrectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Right to Correction:
    Allows citizens and portal participants to rectify their personal data with an immutable audit log.
    """
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for correction.")

    updated_user = dpdp_service.correct_user_data(user=current_user, updates=updates, db=db)
    return {
        "status": "success",
        "message": "Personal records corrected successfully.",
        "user_id": updated_user.id,
        "updated_fields": list(updates.keys())
    }


@router.post("/request-erasure")
def request_data_erasure(
    payload: ErasureRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Right to Erasure / Pseudonymization:
    Anonymizes citizen personal identifiers, revokes active access, and preserves
    verifiable transaction records and audit hash chain integrity.
    """
    if not payload.confirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must explicitly confirm data erasure request."
        )

    return dpdp_service.anonymize_user_data(
        user=current_user,
        reason=payload.reason,
        db=db
    )
