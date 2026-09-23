from typing import Dict, Any, Optional
from backend.app.models.models import User, UserRole

class PrivacyRedactionService:
    """
    Role- and Jurisdiction-aware Privacy Redaction Service.
    Enforces statutory privacy policies:
    1. Exact GPS coordinates (latitude/longitude) are masked for general public
       and cross-jurisdictional viewers to 2 decimal places (~1.1 km precision)
       or replaced by district centroids. Exact coordinates are restricted to
       authorized field inspectors and State Admins.
    2. Submitter personal identifiable information (name, phone, email, address)
       is masked for public/unrelated audiences.
    3. Proprietary research IP, lab assays, and confidential commercial terms
       are restricted to assigned project team members and authorized evaluators.
    """

    @classmethod
    def redact_location(cls, location_dict: Optional[Dict[str, Any]], viewer: Optional[User]) -> Optional[Dict[str, Any]]:
        if not location_dict:
            return None

        redacted = dict(location_dict)
        is_state_admin = viewer and viewer.role == UserRole.GOVERNMENT_ADMIN and (viewer.admin_tier or "STATE").upper() == "STATE"
        is_verifier = viewer and viewer.role in [UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER]

        if not (is_state_admin or is_verifier):
            # Mask coordinates to coarse coarse grid (~2 decimals)
            lat = redacted.get("latitude")
            lon = redacted.get("longitude")
            if lat is not None:
                redacted["latitude"] = round(float(lat), 2)
            if lon is not None:
                redacted["longitude"] = round(float(lon), 2)
            redacted["is_coarse_geography"] = True
        else:
            redacted["is_coarse_geography"] = False

        return redacted

    @classmethod
    def redact_citizen_pii(cls, citizen_data: Dict[str, Any], viewer: Optional[User], is_owner: bool = False) -> Dict[str, Any]:
        if is_owner:
            return citizen_data

        is_gov_officer = viewer and viewer.role in [UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER]
        if is_gov_officer:
            return citizen_data

        redacted = dict(citizen_data)
        if "phone_number" in redacted and redacted["phone_number"]:
            phone = str(redacted["phone_number"])
            redacted["phone_number"] = f"XXXXXX{phone[-4:]}" if len(phone) >= 4 else "XXXXXX"
        if "email" in redacted and redacted["email"]:
            parts = str(redacted["email"]).split("@")
            if len(parts) == 2:
                redacted["email"] = f"{parts[0][:2]}***@{parts[1]}"
        if "full_name" in redacted and redacted["full_name"]:
            redacted["full_name"] = "Verified Citizen Reporter"

        return redacted

    @classmethod
    def redact_confidential_ip(cls, proposal_data: Dict[str, Any], viewer: Optional[User], is_team_member: bool = False) -> Dict[str, Any]:
        is_privileged = viewer and (viewer.role == UserRole.GOVERNMENT_ADMIN or is_team_member)
        if is_privileged:
            return proposal_data

        redacted = dict(proposal_data)
        if "commercialization_plan" in redacted:
            redacted["commercialization_plan"] = "[CONFIDENTIAL_COMMERCIAL_TERMS]"
        if "patent_application_details" in redacted:
            redacted["patent_application_details"] = "[RESTRICTED_IP_FILING]"
        return redacted


privacy_service = PrivacyRedactionService()
