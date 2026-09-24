import pytest
import io
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.models import (
    User, UserRole, AccountStatus, Challenge, ChallengeLocation,
    ChallengeAttachment, ChallengeDraft, District
)
from backend.app.core.security import get_password_hash, create_access_token


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _get_or_create_user(db: Session, email: str, role: UserRole, full_name: str, district: str = "Ranchi", block: str = "Angara") -> User:
    u = db.query(User).filter(User.email == email).first()
    if not u:
        u = User(
            email=email,
            hashed_password=get_password_hash("StrongTestPass!2026"),
            full_name=full_name,
            role=role,
            account_status=AccountStatus.ACTIVE,
            district_name=district,
            block_name=block
        )
        db.add(u)
        db.commit()
        db.refresh(u)
    return u


def _headers_for(user: User) -> dict:
    token = create_access_token(
        subject=user.id,
        role=user.role.value,
        tier=user.admin_tier,
        district_name=user.district_name,
        block_name=user.block_name
    )
    return {"Authorization": f"Bearer {token}"}


def test_taxonomy_endpoint(client):
    """GET /challenges/taxonomy must return canonical 11 domains and subdomains."""
    res = client.get("/api/v1/challenges/taxonomy")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 11
    codes = [d["code"] for d in data]
    assert "WATER_RESOURCES" in codes
    assert "EDUCATION" in codes
    assert "AGRICULTURE" in codes
    assert "HEALTHCARE" in codes
    assert "RURAL_LIVELIHOODS" in codes


def test_controlled_taxonomy_validation(client, db):
    """Submissions with non-existent or unapproved categories must be rejected with 422."""
    citizen = _get_or_create_user(db, "citizen_taxo@example.com", UserRole.CITIZEN, "Taxo Citizen")
    headers = _headers_for(citizen)

    # Invalid category
    invalid_payload = {
        "title": "Industrial Furnace Heat in Angara",
        "description": "Industrial furnace causing power grid drops and high ambient heat in the village area.",
        "category": "InvalidDomainCategory",
        "affected_population": 50,
        "location": {
            "district_name": "Ranchi",
            "block_name": "Angara",
            "village_or_city": "Getalsud",
            "location_address": "Near Sub-station",
            "latitude": 23.3980,
            "longitude": 85.5520
        },
        "consent_given": True
    }
    res = client.post("/api/v1/challenges", json=invalid_payload, headers=headers)
    assert res.status_code == 422
    assert "Invalid domain category" in res.json()["detail"]


def test_geographic_boundary_and_district_validation(client, db):
    """Coordinates outside Jharkhand state boundaries or unknown districts must be rejected with 422."""
    citizen = _get_or_create_user(db, "citizen_geo@example.com", UserRole.CITIZEN, "Geo Citizen")
    headers = _headers_for(citizen)

    # 1. Invalid District (Patna is in Bihar, not Jharkhand)
    payload_bad_district = {
        "title": "Road Repair Required Urgently",
        "description": "Major potholes on main link road disrupting public transport.",
        "category": "Urban Infrastructure",
        "affected_population": 300,
        "location": {
            "district_name": "Patna",
            "block_name": "Central",
            "village_or_city": "Town",
            "location_address": "Near Gandhi Maidan",
            "latitude": 23.3441,
            "longitude": 85.3096
        },
        "consent_given": True
    }
    res1 = client.post("/api/v1/challenges", json=payload_bad_district, headers=headers)
    assert res1.status_code == 422
    assert "not recognized as one of the 24 districts" in res1.json()["detail"]

    # 2. Out-of-bounds coordinates (Delhi coords: 28.6139 N, 77.2090 E)
    payload_bad_coords = {
        "title": "Road Repair Required Urgently",
        "description": "Major potholes on main link road disrupting public transport.",
        "category": "Urban Infrastructure",
        "affected_population": 300,
        "location": {
            "district_name": "Ranchi",
            "block_name": "Angara",
            "village_or_city": "Getalsud",
            "location_address": "Near Main Market",
            "latitude": 28.6139,
            "longitude": 77.2090
        },
        "consent_given": True
    }
    res2 = client.post("/api/v1/challenges", json=payload_bad_coords, headers=headers)
    assert res2.status_code == 422
    assert "outside Jharkhand state boundary" in res2.json()["detail"]


def test_affected_population_positive_integer_enforcement(client, db):
    """affected_population must be strictly >= 1."""
    citizen = _get_or_create_user(db, "citizen_pop@example.com", UserRole.CITIZEN, "Pop Citizen")
    headers = _headers_for(citizen)

    payload_zero_pop = {
        "title": "Fluoride in Groundwater Borewell",
        "description": "Severe dental and skeletal fluorosis reported across the village.",
        "category": "Water Resources",
        "affected_population": 0,
        "location": {
            "district_name": "Ranchi",
            "block_name": "Angara",
            "village_or_city": "Nawagarh",
            "location_address": "Near Primary School",
            "latitude": 23.3980,
            "longitude": 85.5520
        },
        "consent_given": True
    }
    res = client.post("/api/v1/challenges", json=payload_zero_pop, headers=headers)
    assert res.status_code == 422


def test_multi_stakeholder_creation_and_submitter_metadata(client, db):
    """
    Verifies that CITIZEN, PRI, and ULB submitters record metadata correctly, and
    that submitter identity (submitter_role, server-derived from the authenticated
    account) is kept strictly separate from source_type (the submission CHANNEL,
    e.g. MOBILE_APP/WEB_PORTAL/FIELD_VISIT/COMMUNITY_SURVEY). A client cannot spoof
    submitter_role by sending a role-like value in source_type.
    """
    roles_to_test = [
        ("pri_user@jharkhand.gov.in", UserRole.PRI, "Panchayat Mukhiya", "WEB_PORTAL"),
        ("ulb_user@jharkhand.gov.in", UserRole.ULB, "Ward Commissioner", "FIELD_VISIT"),
        ("citizen_actor@example.com", UserRole.CITIZEN, "Citizen Submitter", "MOBILE_APP")
    ]

    for email, role, full_name, src_type in roles_to_test:
        user = _get_or_create_user(db, email, role, full_name)
        headers = _headers_for(user)

        payload = {
            "title": f"Drainage Overflow Reported by {full_name}",
            "description": "Stagnant open drainage breeding mosquitoes and causing water contamination.",
            "category": "Sanitation",
            "affected_population": 250,
            "location": {
                "district_name": "Ranchi",
                "block_name": "Angara",
                "village_or_city": "Rupru",
                "location_address": "Near Gram Panchayat Bhavan",
                "latitude": 23.3980,
                "longitude": 85.5520
            },
            "source_type": src_type,
            "contact_preference": "IN_APP",
            "consent_version": "v1.0",
            "consent_given": True,
            "data_sharing_choice": "PUBLIC_AGGREGATED",
            "is_anonymous_public": False,
            "idempotency_key": str(uuid.uuid4())
        }

        res = client.post("/api/v1/challenges", json=payload, headers=headers)
        assert res.status_code == 201
        data = res.json()
        assert data["category"] == "SANITATION"
        assert data["submitter_role"] == role.value
        assert data["source_type"] == src_type
        assert data["affected_population"] == 250


def test_source_type_rejects_identity_spoofing_values(client, db):
    """
    source_type only accepts channel values. A client sending a role-like value
    (e.g. "PRI", "GOVERNMENT_AGENCY") to masquerade as an official submission
    must be rejected with 422, since that is not a real submission channel.
    """
    user = _get_or_create_user(db, "spoof_attempt@example.com", UserRole.CITIZEN, "Spoof Attempt")
    headers = _headers_for(user)

    payload = {
        "title": "Attempted Source Type Spoofing Report",
        "description": "Testing that identity cannot be spoofed via source_type field.",
        "category": "Sanitation",
        "affected_population": 100,
        "location": {
            "district_name": "Ranchi",
            "block_name": "Angara",
            "village_or_city": "Rupru",
            "location_address": "Near Gram Panchayat Bhavan",
            "latitude": 23.3980,
            "longitude": 85.5520
        },
        "source_type": "GOVERNMENT_AGENCY",
        "consent_given": True,
        "idempotency_key": str(uuid.uuid4())
    }

    res = client.post("/api/v1/challenges", json=payload, headers=headers)
    assert res.status_code == 422


def test_idempotency_key_replay(client, db):
    """Submitting with the exact same idempotency_key must return the existing record without duplicates."""
    citizen = _get_or_create_user(db, "citizen_idem@example.com", UserRole.CITIZEN, "Idempotent Citizen")
    headers = _headers_for(citizen)
    idem_key = f"idem-key-{uuid.uuid4()}"

    payload = {
        "title": "Soil Erosion Threatening Paddy Fields",
        "description": "Monsoon flash floods washing away topsoil in terraced farming plots.",
        "category": "Agriculture",
        "affected_population": 120,
        "location": {
            "district_name": "Ranchi",
            "block_name": "Angara",
            "village_or_city": "Helta",
            "location_address": "Lower Watershed Plot 4",
            "latitude": 23.3980,
            "longitude": 85.5520
        },
        "consent_given": True,
        "idempotency_key": idem_key
    }

    # 1. First submission
    res1 = client.post("/api/v1/challenges", json=payload, headers=headers)
    assert res1.status_code == 201
    ch_id_1 = res1.json()["id"]

    # 2. Second submission with identical idempotency_key (simulating network retry)
    res2 = client.post("/api/v1/challenges", json=payload, headers=headers)
    assert res2.status_code in (200, 201)
    ch_id_2 = res2.json()["id"]

    # IDs must be identical, no duplicate row in DB
    assert ch_id_1 == ch_id_2
    count = db.query(Challenge).filter(Challenge.idempotency_key == idem_key).count()
    assert count == 1


def test_secure_attachment_pipeline_and_magic_byte_verification(client, db):
    """
    Verifies:
    1. Valid PNG upload passes magic-byte check, computes SHA-256 and scan_status=CLEAN.
    2. Disguised executable / ELF binary fails validation with 400.
    3. Unauthorized user cannot link someone else's attachment.
    4. Arbitrary external URL is rejected.
    """
    citizen1 = _get_or_create_user(db, "citizen_att1@example.com", UserRole.CITIZEN, "Att Citizen 1")
    citizen2 = _get_or_create_user(db, "citizen_att2@example.com", UserRole.CITIZEN, "Att Citizen 2")
    headers1 = _headers_for(citizen1)
    headers2 = _headers_for(citizen2)

    # 1. Upload valid 1x1 PNG file
    png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    files = {"file": ("ground_evidence.png", io.BytesIO(png_bytes), "image/png")}
    res_up = client.post("/api/v1/challenges/attachments/upload", files=files, headers=headers1)
    assert res_up.status_code == 201
    up_data = res_up.json()
    att_id = up_data["attachment_id"]
    assert up_data["detected_mime"] == "image/png"
    assert up_data["scan_status"] == "CLEAN"
    assert len(up_data["sha256_checksum"]) == 64

    # 2. Upload fake file: Windows EXE (MZ header) disguised as .jpg
    fake_exe = b'MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00This program cannot be run in DOS mode.'
    files_fake = {"file": ("malware.jpg", io.BytesIO(fake_exe), "image/jpeg")}
    res_fake = client.post("/api/v1/challenges/attachments/upload", files=files_fake, headers=headers1)
    assert res_fake.status_code == 400
    # The MZ (Windows executable) magic bytes are caught by the dangerous-signature
    # check before generic MIME-detection even runs — a more specific rejection reason
    # for the same underlying threat, so either wording is an acceptable rejection.
    detail = res_fake.json()["detail"]
    assert "Malicious" in detail and ("binary signature" in detail or "executable script" in detail)

    # 3. Citizen 2 tries to link Citizen 1's attachment -> Rejected 403 Forbidden
    payload_theft = {
        "title": "Borewell Pump Motor Burnt",
        "description": "Submersible pump motor burnt during lightning storm; drinking water cut off.",
        "category": "Water Resources",
        "affected_population": 80,
        "location": {
            "district_name": "Ranchi",
            "block_name": "Angara",
            "village_or_city": "Getalsud",
            "location_address": "Near Pump House",
            "latitude": 23.3980,
            "longitude": 85.5520
        },
        "attachment_ids": [att_id],
        "consent_given": True
    }
    res_theft = client.post("/api/v1/challenges", json=payload_theft, headers=headers2)
    assert res_theft.status_code == 403
    assert "Unauthorized attachment" in res_theft.json()["detail"]

    # 4. Reject arbitrary external URL
    payload_bad_url = {
        "title": "Borewell Pump Motor Burnt",
        "description": "Submersible pump motor burnt during lightning storm; drinking water cut off.",
        "category": "Water Resources",
        "affected_population": 80,
        "location": {
            "district_name": "Ranchi",
            "block_name": "Angara",
            "village_or_city": "Getalsud",
            "location_address": "Near Pump House",
            "latitude": 23.3980,
            "longitude": 85.5520
        },
        "media_urls": ["https://evil-phishing-site.com/exploit.jpg"],
        "consent_given": True
    }
    res_bad_url = client.post("/api/v1/challenges", json=payload_bad_url, headers=headers1)
    assert res_bad_url.status_code == 400
    assert "Arbitrary external media URL rejected" in res_bad_url.json()["detail"]

    # 5. Legitimate submission with verified attachment by owner
    payload_valid = {
        "title": "Borewell Pump Motor Burnt",
        "description": "Submersible pump motor burnt during lightning storm; drinking water cut off.",
        "category": "Water Resources",
        "affected_population": 80,
        "location": {
            "district_name": "Ranchi",
            "block_name": "Angara",
            "village_or_city": "Getalsud",
            "location_address": "Near Pump House",
            "latitude": 23.3980,
            "longitude": 85.5520
        },
        "attachment_ids": [att_id],
        "consent_given": True
    }
    res_valid = client.post("/api/v1/challenges", json=payload_valid, headers=headers1)
    assert res_valid.status_code == 201
    ch_data = res_valid.json()
    assert len(ch_data["attachments"]) == 1
    assert ch_data["attachments"][0]["object_id"] == att_id

    # 6. Access control for download
    # Owner can download
    res_dl_owner = client.get(f"/api/v1/files/attachments/{att_id}", headers=headers1)
    assert res_dl_owner.status_code == 200
    assert res_dl_owner.headers["X-Checksum-SHA256"] == up_data["sha256_checksum"]

    # Citizen 2 cannot download
    res_dl_c2 = client.get(f"/api/v1/files/attachments/{att_id}", headers=headers2)
    assert res_dl_c2.status_code == 403


def test_voice_note_attachment_upload_and_video_mp4_still_distinct(client, db):
    """
    Phase 2, Item 13: citizens can attach a voice-note recording as real
    evidence. An M4A voice note (audio, `ftyp` box with an `M4A ` subtype)
    must be detected as audio/mp4 and accepted — and must NOT be misdetected
    as a video/mp4 file, even though both use the same ISO-BMFF container.
    """
    citizen = _get_or_create_user(db, "citizen_voice1@example.com", UserRole.CITIZEN, "Voice Citizen")
    headers = _headers_for(citizen)

    # Minimal valid M4A container: ftyp box with M4A subtype.
    m4a_bytes = b'\x00\x00\x00\x20ftypM4A \x00\x00\x00\x00M4A mp42isom' + b'\x00' * 32
    files = {"file": ("voice_note.m4a", io.BytesIO(m4a_bytes), "audio/mp4")}
    res = client.post("/api/v1/challenges/attachments/upload", files=files, headers=headers)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["detected_mime"] == "audio/mp4"
    assert data["scan_status"] == "CLEAN"

    # A genuine MP4 video container (non-M4A subtype) must still be video/mp4.
    mp4_bytes = b'\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2avc1mp41' + b'\x00' * 32
    files_video = {"file": ("evidence_clip.mp4", io.BytesIO(mp4_bytes), "video/mp4")}
    res_video = client.post("/api/v1/challenges/attachments/upload", files=files_video, headers=headers)
    assert res_video.status_code == 201, res_video.text
    assert res_video.json()["detected_mime"] == "video/mp4"

    # WAV voice note is also accepted.
    wav_bytes = b'RIFF' + (36).to_bytes(4, 'little') + b'WAVEfmt ' + b'\x00' * 20
    files_wav = {"file": ("voice_note.wav", io.BytesIO(wav_bytes), "audio/wav")}
    res_wav = client.post("/api/v1/challenges/attachments/upload", files=files_wav, headers=headers)
    assert res_wav.status_code == 201, res_wav.text
    assert res_wav.json()["detected_mime"] == "audio/wav"


def test_location_privacy_and_anonymity_preservation(client, db):
    """
    Verifies privacy preservation:
    - Public / other citizens see coordinates rounded to 2 decimal places and masked address.
    - If is_anonymous_public=True, public view sees "Anonymous Citizen".
    - Author and Statewide Government Admin see exact GPS and precise address.
    """
    author = _get_or_create_user(db, "citizen_privacy@example.com", UserRole.CITIZEN, "Sita Soren")
    other_citizen = _get_or_create_user(db, "other_citizen@example.com", UserRole.CITIZEN, "Other Citizen")
    admin = _get_or_create_user(db, "state_admin_priv@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN, "State Admin")

    author_headers = _headers_for(author)
    other_headers = _headers_for(other_citizen)
    admin_headers = _headers_for(admin)

    # Submit challenge with exact GPS (5 decimal places), precise address, and anonymous public flag
    exact_lat = 23.34418
    exact_lng = 85.30962
    exact_addr = "House 42, Near Primary School Handpump, Nawagarh Toli"

    payload = {
        "title": "Fluoride Water Filter Membrane Broken",
        "description": "Community water filter unit offline for 3 weeks; children developing dental fluorosis.",
        "category": "Water Resources",
        "affected_population": 450,
        "location": {
            "district_name": "Ranchi",
            "block_name": "Angara",
            "village_or_city": "Nawagarh",
            "location_address": exact_addr,
            "latitude": exact_lat,
            "longitude": exact_lng
        },
        "is_anonymous_public": True,
        "consent_given": True
    }

    create_res = client.post("/api/v1/challenges", json=payload, headers=author_headers)
    assert create_res.status_code == 201
    ch_id = create_res.json()["id"]

    # 1. Author view: Exact GPS, exact address, actual name
    res_author = client.get(f"/api/v1/challenges/{ch_id}", headers=author_headers)
    assert res_author.status_code == 200
    data_author = res_author.json()
    assert abs(data_author["location"]["latitude"] - exact_lat) < 1e-4
    assert abs(data_author["location"]["longitude"] - exact_lng) < 1e-4
    assert data_author["location"]["location_address"] == exact_addr
    assert data_author["submitted_by_name"] == "Sita Soren"

    # 2. Public / Other Citizen view: Rounded coordinates (2 decimals), masked address, Anonymous Citizen
    res_public = client.get(f"/api/v1/challenges/{ch_id}", headers=other_headers)
    assert res_public.status_code == 200
    data_public = res_public.json()
    assert data_public["location"]["latitude"] == round(exact_lat, 2)
    assert data_public["location"]["longitude"] == round(exact_lng, 2)
    assert exact_addr not in data_public["location"]["location_address"]
    assert "Angara, Ranchi, Jharkhand" in data_public["location"]["location_address"]
    assert data_public["submitted_by_name"] == "Anonymous Citizen"

    # 3. State Admin view: Exact coordinates and address
    res_admin = client.get(f"/api/v1/challenges/{ch_id}", headers=admin_headers)
    assert res_admin.status_code == 200
    data_admin = res_admin.json()
    assert abs(data_admin["location"]["latitude"] - exact_lat) < 1e-4
    assert data_admin["location"]["location_address"] == exact_addr
    assert data_admin["submitted_by_name"] == "Sita Soren"


def test_challenge_draft_crud_lifecycle(client, db):
    """Verifies creating, listing, and deleting draft challenges."""
    citizen = _get_or_create_user(db, "citizen_draft@example.com", UserRole.CITIZEN, "Draft Citizen")
    headers = _headers_for(citizen)
    draft_id = f"draft-{uuid.uuid4().hex[:8]}"

    draft_payload = {
        "draft_id": draft_id,
        "idempotency_key": str(uuid.uuid4()),
        "payload": {
            "title": "Incomplete Rural Electrification Pole",
            "category": "Energy",
            "affected_population": 65,
            "district_name": "Ranchi"
        }
    }

    # 1. Save draft
    res_save = client.post("/api/v1/challenges/drafts", json=draft_payload, headers=headers)
    assert res_save.status_code == 200
    assert res_save.json()["draft_id"] == draft_id
    assert res_save.json()["payload"]["title"] == "Incomplete Rural Electrification Pole"

    # 2. List drafts
    res_list = client.get("/api/v1/challenges/drafts", headers=headers)
    assert res_list.status_code == 200
    drafts = res_list.json()
    assert any(d["draft_id"] == draft_id for d in drafts)

    # 3. Delete draft
    res_del = client.get(f"/api/v1/challenges/drafts/{draft_id}", headers=headers)
    assert res_del.status_code == 200

    del_res = client.delete(f"/api/v1/challenges/drafts/{draft_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # Verify deleted
    res_verify = client.get(f"/api/v1/challenges/drafts/{draft_id}", headers=headers)
    assert res_verify.status_code == 404
