import os
import hashlib
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal
from backend.app.core.security import get_password_hash
from backend.app.models.models import (
    User, UserRole, Citizen, University, Department, Faculty, Student,
    IndustryPartner, GovernmentDepartment, ChallengeCategory, Challenge,
    ChallengeLocation, ChallengeMedia, AIAnalysis, ChallengeSimilarity,
    UniversityExpertise, UniversityMatch, Project, ProjectMember,
    ProjectMilestone, ProjectTask, SolutionProposal, IndustryCollaboration,
    ProjectDocument, Comment, Notification, StatusHistory, ImpactMetrics,
    District, ChallengePriority, ChallengeStatus, MilestoneStatus,
    AccountStatus, GovernmentScope, IPRecord, IPRecordType, IPOwnership,
    CollaborationOfferType, AgreementStatus, VerificationRecord,
    DomainAuditEvent, AuditLog
)

def run_seed():
    db: Session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        hashed_pwd = get_password_hash("password123")
        print("[1/5] Ensuring All 8 Stakeholder Roles & Demo Accounts...")

        # 1. State Government Admin
        admin_user = db.query(User).filter(User.email == "admin@jharkhand.gov.in").first()
        if not admin_user:
            admin_user = User(
                email="admin@jharkhand.gov.in",
                hashed_password=hashed_pwd,
                full_name="Dr. Alok Verma, IAS",
                phone_number="+91-651-2400112",
                role=UserRole.GOVERNMENT_ADMIN,
                is_active=True,
                is_verified=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

        # 2. District Reviewing Officer (Ranchi)
        officer_user = db.query(User).filter(User.email == "officer.ranchi@jharkhand.gov.in").first()
        if not officer_user:
            officer_user = User(
                email="officer.ranchi@jharkhand.gov.in",
                hashed_password=hashed_pwd,
                full_name="Sunil Soren, State Civil Service",
                phone_number="+91-9431100991",
                role=UserRole.GOVERNMENT_OFFICER,
                is_active=True,
                is_verified=True
            )
            db.add(officer_user)
            db.commit()
            db.refresh(officer_user)

        # 3. Field Verifier / Technical Auditor
        verifier_user = db.query(User).filter(User.email == "verifier.ranchi@jharkhand.gov.in").first()
        if not verifier_user:
            verifier_user = User(
                email="verifier.ranchi@jharkhand.gov.in",
                hashed_password=hashed_pwd,
                full_name="Amit Kumar Verma",
                phone_number="+91-9431100992",
                role=UserRole.GOVERNMENT_OFFICER,
                is_active=True,
                is_verified=True
            )
            db.add(verifier_user)
            db.commit()
            db.refresh(verifier_user)

        # 4. PRI Representative (Angara Gram Panchayat Mukhiya)
        pri_user = db.query(User).filter(User.email == "pri.angara@jharkhand.gov.in").first()
        if not pri_user:
            pri_user = User(
                email="pri.angara@jharkhand.gov.in",
                hashed_password=hashed_pwd,
                full_name="Sunita Devi (Gram Mukhiya)",
                phone_number="+91-9835100993",
                role=UserRole.PRI,
                is_active=True,
                is_verified=True
            )
            db.add(pri_user)
            db.commit()
            db.refresh(pri_user)

        # 5. Citizen Submitter
        citizen_user = db.query(User).filter(User.email == "citizen@jharkhand.gov.in").first()
        if not citizen_user:
            citizen_user = User(
                email="citizen@jharkhand.gov.in",
                hashed_password=hashed_pwd,
                full_name="Ramesh Kumar Mahto",
                phone_number="+91-9835100223",
                role=UserRole.CITIZEN,
                is_active=True,
                is_verified=True
            )
            db.add(citizen_user)
            db.commit()
            db.refresh(citizen_user)

        citizen_prof = db.query(Citizen).filter(Citizen.user_id == citizen_user.id).first()
        if not citizen_prof:
            citizen_prof = Citizen(
                user_id=citizen_user.id,
                address="Village Nawagarh, Angara Block",
                district_name="Ranchi",
                block_name="Angara",
                village_or_city="Nawagarh",
                pincode="835103"
            )
            db.add(citizen_prof)
            db.commit()
            db.refresh(citizen_prof)

        # 6. University Admin (BIT Mesra)
        univ_user = db.query(User).filter(User.email == "university@bitmesra.ac.in").first()
        if not univ_user:
            univ_user = User(
                email="university@bitmesra.ac.in",
                hashed_password=hashed_pwd,
                full_name="Birla Institute of Technology (BIT), Mesra",
                phone_number="+91-651-2275444",
                role=UserRole.UNIVERSITY,
                is_active=True,
                is_verified=True
            )
            db.add(univ_user)
            db.commit()
            db.refresh(univ_user)

        univ1 = db.query(University).filter(University.user_id == univ_user.id).first()
        if not univ1:
            univ1 = University(
                user_id=univ_user.id,
                institution_name="Birla Institute of Technology (BIT), Mesra",
                district_name="Ranchi",
                address="Mesra, Ranchi, Jharkhand 835215",
                website="https://www.bitmesra.ac.in",
                has_incubation_center=True,
                has_innovation_center=True,
                facilities_description="DST-supported Technology Incubation Center, IoT & Embedded Systems Lab, Water Quality Analysis Center",
                nirf_ranking=53
            )
            db.add(univ1)
            db.commit()
            db.refresh(univ1)

        # Department
        dept_env = db.query(Department).filter(Department.university_id == univ1.id, Department.name.like("%Environmental%")).first()
        if not dept_env:
            dept_env = Department(university_id=univ1.id, name="Department of Environmental Science & Civil Engg", head_of_department="Dr. Ananya Sharma")
            db.add(dept_env)
            db.commit()
            db.refresh(dept_env)

        # 7. Faculty Mentor
        faculty_user = db.query(User).filter(User.email == "faculty@bitmesra.ac.in").first()
        if not faculty_user:
            faculty_user = User(
                email="faculty@bitmesra.ac.in",
                hashed_password=hashed_pwd,
                full_name="Dr. Ananya Sharma",
                phone_number="+91-9431123456",
                role=UserRole.FACULTY_MENTOR,
                is_active=True,
                is_verified=True
            )
            db.add(faculty_user)
            db.commit()
            db.refresh(faculty_user)

        fac_prof = db.query(Faculty).filter(Faculty.user_id == faculty_user.id).first()
        if not fac_prof:
            fac_prof = Faculty(
                user_id=faculty_user.id,
                university_id=univ1.id,
                department_id=dept_env.id,
                designation="Associate Professor & Head",
                expertise="Water Quality Engineering, Membrane Filtration, IoT Water Sensors",
                research_interests="Community-level fluoride decontamination, low-cost solar drinking water purification in Chota Nagpur plateau.",
                experience_years=14
            )
            db.add(fac_prof)
            db.commit()
            db.refresh(fac_prof)

        # 8. Student Innovator (Lead)
        student_user = db.query(User).filter(User.email == "student@bitmesra.ac.in").first()
        if not student_user:
            student_user = User(
                email="student@bitmesra.ac.in",
                hashed_password=hashed_pwd,
                full_name="Priya Singh",
                phone_number="+91-7903112233",
                role=UserRole.STUDENT,
                is_active=True,
                is_verified=True
            )
            db.add(student_user)
            db.commit()
            db.refresh(student_user)

        stu_prof = db.query(Student).filter(Student.user_id == student_user.id).first()
        if not stu_prof:
            stu_prof = Student(
                user_id=student_user.id,
                university_id=univ1.id,
                department_id=dept_env.id,
                roll_number="BTECH/CSE/2023/042",
                degree="B.Tech Computer Science & IoT",
                year_of_study=3,
                skills="Python, Flutter, IoT, Embedded C, AI/ML, FastAPI"
            )
            db.add(stu_prof)
            db.commit()
            db.refresh(stu_prof)

        # Additional Student: Kiran Biradar
        kiran_user = db.query(User).filter(User.email == "student@sapthagiri.edu.in").first()
        kiran_prof = db.query(Student).filter(Student.user_id == kiran_user.id).first() if kiran_user else None

        # 9. Corporate CSR Partner (Tata Steel)
        ind_user = db.query(User).filter(User.email == "industry@tatasteel.com").first()
        if not ind_user:
            ind_user = User(
                email="industry@tatasteel.com",
                hashed_password=hashed_pwd,
                full_name="Tata Steel CSR & Sustainability Foundation",
                phone_number="+91-657-6644000",
                role=UserRole.INDUSTRY,
                is_active=True,
                is_verified=True
            )
            db.add(ind_user)
            db.commit()
            db.refresh(ind_user)

        ind_prof = db.query(IndustryPartner).filter(IndustryPartner.user_id == ind_user.id).first()
        if not ind_prof:
            ind_prof = IndustryPartner(
                user_id=ind_user.id,
                company_name="Tata Steel Foundation",
                industry_domain="Heavy Engineering & CSR Innovation",
                contact_person="Vikramaditya Sharma, Head of Rural Development",
                website="https://www.tatasteelfoundation.org",
                csr_focus_areas="Safe Drinking Water, Rural Healthcare, Sustainable Livelihoods, Youth Skilling in Jharkhand",
                technologies="Industrial Automation, IoT Sensors, High-grade Metallurgy, Renewable Energy Integration",
                available_support="Field Pilot Testing in Tribal Blocks, Prototype Grant Funding, Technical Mentorship"
            )
            db.add(ind_prof)
            db.commit()
            db.refresh(ind_prof)

        # Ranchi District
        ranchi_dist = db.query(District).filter(District.name == "Ranchi").first()
        ranchi_dist_id = ranchi_dist.id if ranchi_dist else 1

        print("[2/5] Creating / Updating Flagship Showcase Challenge (End-to-End Completed Closed Loop)...")
        # Check if flagship challenge exists
        flagship = db.query(Challenge).filter(Challenge.title.like("%[FLAGSHIP SIH DEMO]%")).first()
        if not flagship:
            flagship = Challenge(
                title="[FLAGSHIP SIH DEMO] Severe Groundwater Fluoride Contamination in Angara Tribal Habitations",
                description="Our tribal hamlet Nawagarh in Angara block (Ranchi) faces severe groundwater fluoride contamination exceeding 6.4 ppm (safe limit < 1.0 ppm). Over 3,200 villagers and 450 schoolchildren suffer from acute dental fluorosis, skeletal deformities, and chronic kidney ailments. The 3 existing borewells pump hazardous contaminated water with high turbidity and arsenic traces.",
                category="Water Resources",
                sub_category="Drinking Water Purification & Telemetry",
                urgency="Critical",
                priority=ChallengePriority.CRITICAL,
                expected_impact="Deliver 5,000 liters/day of zero-fluoride WHO-compliant potable water, eradicating fluorosis for 3,200 tribal villagers and 450 schoolchildren.",
                status=ChallengeStatus.CLOSED,
                citizen_id=citizen_prof.id,
                assigned_university_id=univ1.id,
                created_at=now - timedelta(days=45)
            )
            db.add(flagship)
            db.commit()
            db.refresh(flagship)
        else:
            flagship.status = ChallengeStatus.CLOSED
            db.commit()

        # Location
        loc = db.query(ChallengeLocation).filter(ChallengeLocation.challenge_id == flagship.id).first()
        if not loc:
            db.add(ChallengeLocation(
                challenge_id=flagship.id,
                district_id=ranchi_dist_id,
                district_name="Ranchi",
                block_name="Angara",
                village_or_city="Nawagarh",
                location_address="Near Angara Community Primary School & Panchayat Bhawan, NH-320",
                latitude=23.3980,
                longitude=85.5520
            ))
            db.commit()

        # Media
        med = db.query(ChallengeMedia).filter(ChallengeMedia.challenge_id == flagship.id).first()
        if not med:
            db.add(ChallengeMedia(
                challenge_id=flagship.id,
                media_type="image",
                file_url="/uploads/demo/water_shortage_angara.jpg",
                file_name="fluoride_affected_borewell_sample.jpg"
            ))
            db.commit()

        # AI Analysis
        ai_an = db.query(AIAnalysis).filter(AIAnalysis.challenge_id == flagship.id).first()
        if not ai_an:
            db.add(AIAnalysis(
                challenge_id=flagship.id,
                cleaned_text="tribal hamlet nawagarh angara block ranchi groundwater fluoride contamination exceeding 6.4 ppm dental skeletal fluorosis children villagers",
                classified_domain="Water Resources",
                detected_priority=ChallengePriority.CRITICAL,
                extracted_keywords="Groundwater Fluoride, Arsenic, Angara Tribal Hamlet, Solar Kiosk, IoT Telemetry, ICP-MS",
                required_expertise="Civil & Environmental Engineering, IoT Embedded Firmware, Solar MPPT Systems, Hydrology",
                recommended_solution="Deployment of Automated Solar IoT Defluoridation Kiosk using Regenerable Activated Alumina & LoRaWAN Remote Telemetry.",
                confidence_score=0.98
            ))
            db.commit()

        # University Matches
        if not db.query(UniversityMatch).filter(UniversityMatch.challenge_id == flagship.id).first():
            db.add_all([
                UniversityMatch(challenge_id=flagship.id, university_id=univ1.id, match_percentage=96.5, ranking=1, matching_factors="Local District Presence, Water Resources Research Center of Excellence, DST Incubation"),
            ])
            db.commit()

        print("[3/5] Seeding Project Execution, Tasks, Milestones & CSR Co-Funding...")
        proj = db.query(Project).filter(Project.challenge_id == flagship.id).first()
        if not proj:
            proj = Project(
                challenge_id=flagship.id,
                university_id=univ1.id,
                faculty_mentor_id=fac_prof.id,
                name="Jal-Sanjeevani: Solar IoT Defluoridation Kiosk for Angara Habitations",
                description="An automated, gravity-assisted defluoridation kiosk powered by a 1.2 kW solar rooftop array. Features food-grade regenerable activated alumina columns, real-time ESP32 IoT sensors for fluoride, turbidity, and pH telemetry, and smart RFID citizen dispensing cards.",
                objectives="1. Reduce fluoride concentration from 6.4 ppm to < 0.8 ppm (WHO / BIS 10500 standard)\n2. Deliver 5,000 liters/day continuous potable water\n3. Solar autonomous battery backup with GSM cloud monitoring\n4. Transparent community stewardship via Angara Gram Panchayat",
                expected_outcome="Complete eradication of new fluorosis cases across 3,200 beneficiaries; self-sustaining water kiosk operated by local Women Self Help Group (SHG).",
                required_skills="Civil Hydraulics, Environmental Chemistry, ESP32 Embedded C, Flutter Mobile Telemetry, Solar Power",
                timeline_months=3,
                progress_percentage=100.0,
                current_stage="Completed & State Impact Certified",
                created_at=now - timedelta(days=40)
            )
            db.add(proj)
            db.commit()
            db.refresh(proj)
        else:
            proj.progress_percentage = 100.0
            proj.current_stage = "Completed & State Impact Certified"
            db.commit()

        # Project Members
        if not db.query(ProjectMember).filter(ProjectMember.project_id == proj.id).first():
            members = [
                ProjectMember(project_id=proj.id, student_id=stu_prof.id, role_in_team="Student Team Lead & IoT Telemetry Architect"),
            ]
            if kiran_prof:
                members.append(ProjectMember(project_id=proj.id, student_id=kiran_prof.id, role_in_team="AI Sensor Diagnostics & Embedded Firmware"))
            db.add_all(members)
            db.commit()

        # Milestones (All 5 Approved & Completed)
        if not db.query(ProjectMilestone).filter(ProjectMilestone.project_id == proj.id).first():
            m1 = ProjectMilestone(project_id=proj.id, title="Water Sample Chemical Profiling & Baseline ICP-MS Testing", description="Collected 24 water samples across Angara tribal habitations; quantified fluoride (6.4 ppm) and arsenic (48 ppb) baselines.", completion_percentage=100.0, status=MilestoneStatus.APPROVED, approved_by_faculty=True, approved_at=now - timedelta(days=35))
            m2 = ProjectMilestone(project_id=proj.id, title="Laboratory Adsorption Media Optimization & Column Fabrication", description="Fabricated 150-liter food-grade activated alumina column achieving 93.8% fluoride retention under dynamic flow.", completion_percentage=100.0, status=MilestoneStatus.APPROVED, approved_by_faculty=True, approved_at=now - timedelta(days=28))
            m3 = ProjectMilestone(project_id=proj.id, title="Solar MPPT Power & ESP32 IoT Telemetry Assembly", description="Integrated 1.2 kW solar panels with LiFePO4 battery storage, ultrasonic tank level, turbidity, and GSM telemetry board.", completion_percentage=100.0, status=MilestoneStatus.APPROVED, approved_by_faculty=True, approved_at=now - timedelta(days=20))
            m4 = ProjectMilestone(project_id=proj.id, title="Civil Kiosk Installation & Community Commissioning at Nawagarh", description="Erected brick-and-mortar kiosk enclosure with overhead stainless steel tanks and multi-tap dispensing station.", completion_percentage=100.0, status=MilestoneStatus.APPROVED, approved_by_faculty=True, approved_at=now - timedelta(days=12))
            m5 = ProjectMilestone(project_id=proj.id, title="30-Day Field Validation, Lab Delta Testing & Gram Panchayat Handover", description="Conducted 30-day continuous test run; independent lab audit confirmed 0.8 ppm fluoride; formally transferred to Gram Panchayat.", completion_percentage=100.0, status=MilestoneStatus.APPROVED, approved_by_faculty=True, approved_at=now - timedelta(days=3))
            db.add_all([m1, m2, m3, m4, m5])
            db.commit()

        # Tasks
        if not db.query(ProjectTask).filter(ProjectTask.project_id == proj.id).first():
            db.add_all([
                ProjectTask(project_id=proj.id, title="Baseline water sample collection across Angara wells", assigned_to_student_id=stu_prof.id, is_completed=True, submission_notes="Collected 24 samples; documented GPS coordinates of each borewell."),
                ProjectTask(project_id=proj.id, title="Fabricate and test activated alumina column with regeneration backwash", assigned_to_student_id=stu_prof.id, is_completed=True, submission_notes="Column designed with 0.1 N NaOH regenerant cycle; achieved 93.8% retention."),
                ProjectTask(project_id=proj.id, title="Program ESP32 GSM telemetry firmware and Flutter dashboard sync", assigned_to_student_id=stu_prof.id, is_completed=True, submission_notes="Firmware deployed; telemetry packets streaming every 15 minutes to server.")
            ])
            db.commit()

        # Solution Proposal
        if not db.query(SolutionProposal).filter(SolutionProposal.project_id == proj.id).first():
            db.add(SolutionProposal(
                project_id=proj.id,
                proposed_solution="Jal-Sanjeevani Decentralized Solar Water Purification Kiosk",
                technical_approach="Multi-stage adsorption filtration utilizing regenerable activated alumina beads and automated backwash, solar autonomous power, and cloud telemetry.",
                required_resources="1.2 kW Solar Array, Food-Grade Adsorption Columns, ESP32 IoT Board, Stainless Steel Reservoir, Dispensing Kiosk",
                expected_impact="3,200 villagers provided safe fluoride-free drinking water; complete prevention of juvenile fluorosis.",
                estimated_cost=850000.0,
                timeline_weeks=12,
                is_approved_by_gov=True
            ))
            db.commit()

        # CSR Collaboration (Tata Steel Foundation)
        if not db.query(IndustryCollaboration).filter(IndustryCollaboration.project_id == proj.id).first():
            db.add(IndustryCollaboration(
                project_id=proj.id,
                industry_id=ind_prof.id,
                offer_type="Full CSR Grant Funding & Manufacturing Assistance",
                description="Tata Steel Foundation sponsored the complete project with a ₹8,50,000 CSR Grant disbursed in 3 milestone tranches. Technical engineers from Tata Steel Rural Development Society supervised structural fabrication.",
                status="Completed",
                agreement_status=AgreementStatus.COMPLETED,
                scope="Statewide pilot for rural fluoride decontamination; replication rights across 10 additional tribal blocks.",
                created_at=now - timedelta(days=38)
            ))
            db.commit()

        # IP Rights & Patent Record
        if not db.query(IPRecord).filter(IPRecord.project_id == proj.id).first():
            db.add_all([
                IPRecord(
                    project_id=proj.id,
                    record_type=IPRecordType.PATENT,
                    title="Regenerable Activated-Alumina Cartridge with Automated Solar Backwash for Rural Water Kiosks",
                    description="Patent covering the high-surface-area regenerable fluoride adsorption media and automatic low-pressure backwash manifold.",
                    ownership=IPOwnership.JOINT,
                    patent_reference="TEMP/JH/2026/WATER/00147 (Provisional Filing Certified)",
                    status="APPROVED",
                    created_by_user_id=faculty_user.id
                ),
                IPRecord(
                    project_id=proj.id,
                    record_type=IPRecordType.SOFTWARE,
                    title="Jal-Sanjeevani IoT Water Quality & Telemetry Operating System",
                    description="Real-time sensor telemetry and predictive filter maintenance algorithm licensed for state public deployment.",
                    ownership=IPOwnership.JOINT,
                    startup_spinoff_name="AquaSanjeevani Innovations Pvt Ltd (BIT Mesra Incubated)",
                    status="APPROVED",
                    created_by_user_id=faculty_user.id
                )
            ])
            db.commit()

        print("[4/5] Seeding Field Verification Audit (Lab Deltas & Geofence)...")
        # Verification Record
        if not db.query(VerificationRecord).filter(VerificationRecord.project_id == proj.id).first():
            db.add(VerificationRecord(
                project_id=proj.id,
                verification_type="FIELD_INSPECTION",
                inspector_name="Amit Kumar Verma",
                inspector_role="Empanelled Technical Auditor",
                inspector_user_id=verifier_user.id,
                verification_status="VERIFIED",
                evidence_urls='["/uploads/demo/angara_field_kiosk_verified.jpg"]',
                before_media_urls='["/uploads/demo/water_shortage_angara.jpg"]',
                after_media_urls='["/uploads/demo/angara_field_kiosk_verified.jpg"]',
                lab_report_references='[{"parameter": "Fluoride", "baseline": 6.4, "measured": 0.8, "unit": "ppm", "status": "PASS"}, {"parameter": "Arsenic", "baseline": 48, "measured": 6, "unit": "ppb", "status": "PASS"}, {"parameter": "Turbidity", "baseline": 18, "measured": 1.2, "unit": "NTU", "status": "PASS"}]',
                beneficiary_sample_size=120,
                beneficiary_feedback_summary="94.2% community satisfaction rate; zero reported new fluorosis symptoms in children over last 3 months.",
                geotagged_lat=23.3981,
                geotagged_lng=85.5521,
                inspection_notes="On-site inspection completed. Solar defluoridation kiosk fully operational. Lab analysis confirms fluoride drop from 6.4 ppm to 0.8 ppm (87.5% reduction, compliant with BIS 10500). Turbidity measured at 1.2 NTU (compliant). Villagers actively using RFID cards.",
                reviewed_by_user_id=admin_user.id,
                review_decision="APPROVED",
                review_notes="State Inspection Passed. Verified zero physical defects and authentic water quality remediation.",
                verified_at=now - timedelta(days=4)
            ))
            db.commit()

        # Outcome Metrics (Baseline vs Actual Deltas)
        from backend.app.models.models import OutcomeMetric
        if not db.query(OutcomeMetric).filter(OutcomeMetric.project_id == proj.id).first():
            db.add_all([
                OutcomeMetric(
                    project_id=proj.id,
                    challenge_id=flagship.id,
                    metric_name="Groundwater Fluoride Concentration",
                    metric_definition="Measurement of fluoride ions in community drinking water tap output via ICP-MS spectroscopy",
                    metric_type="QUANTITATIVE",
                    unit_of_measure="ppm (mg/L)",
                    baseline_value="6.4",
                    baseline_date=now - timedelta(days=45),
                    baseline_source="District Water Testing Laboratory, Ranchi",
                    target_value="1.0",
                    actual_value="0.8",
                    actual_date=now - timedelta(days=4),
                    actual_source="State Public Health & Engineering Department Certified Audit",
                    collection_method="Spectrophotometric / Ion Selective Electrode",
                    sample_size=24,
                    district_name="Ranchi",
                    block_name="Angara",
                    verification_status="INDEPENDENTLY_VERIFIED",
                    verified_by_user_id=verifier_user.id,
                    verified_at=now - timedelta(days=4)
                ),
                OutcomeMetric(
                    project_id=proj.id,
                    challenge_id=flagship.id,
                    metric_name="Water Turbidity",
                    metric_definition="Suspended particulate clarity in filtered water supply",
                    metric_type="QUANTITATIVE",
                    unit_of_measure="NTU",
                    baseline_value="18.0",
                    baseline_date=now - timedelta(days=45),
                    baseline_source="District Water Testing Laboratory, Ranchi",
                    target_value="5.0",
                    actual_value="1.2",
                    actual_date=now - timedelta(days=4),
                    actual_source="State Public Health & Engineering Department Certified Audit",
                    collection_method="Digital Nephelometric Turbidimeter",
                    sample_size=24,
                    district_name="Ranchi",
                    block_name="Angara",
                    verification_status="INDEPENDENTLY_VERIFIED",
                    verified_by_user_id=verifier_user.id,
                    verified_at=now - timedelta(days=4)
                ),
                OutcomeMetric(
                    project_id=proj.id,
                    challenge_id=flagship.id,
                    metric_name="Beneficiary Household Coverage",
                    metric_definition="Number of tribal households with daily access to safe defluoridated water",
                    metric_type="QUANTITATIVE",
                    unit_of_measure="Households",
                    baseline_value="0",
                    baseline_date=now - timedelta(days=45),
                    baseline_source="Angara Gram Panchayat Census Record",
                    target_value="350",
                    actual_value="350",
                    actual_date=now - timedelta(days=2),
                    actual_source="RFID Water Dispenser Automated Telemetry Log",
                    sample_size=350,
                    district_name="Ranchi",
                    block_name="Angara",
                    verification_status="INDEPENDENTLY_VERIFIED",
                    verified_by_user_id=verifier_user.id,
                    verified_at=now - timedelta(days=2)
                )
            ])
            db.commit()

        print("[5/5] Recording Status History & Cryptographic Domain Audit Ledger...")
        # Status History across the complete 13 stages
        db.query(StatusHistory).filter(StatusHistory.challenge_id == flagship.id).delete()
        history_events = [
            (None, "SUBMITTED", "Citizen (Ramesh Kumar Mahto)", "Citizen submitted challenge with GPS coordinates and water photo", now - timedelta(days=45)),
            ("SUBMITTED", "AI_ANALYSIS", "AI Background Worker", "NLP Domain: Water Resources | Priority: CRITICAL (0.94) | Recommended Solution Generated", now - timedelta(days=44)),
            ("AI_ANALYSIS", "UNDER_REVIEW", "System", "Challenge queued in Ranchi District Collectorate verification queue", now - timedelta(days=43)),
            ("UNDER_REVIEW", "VALIDATED", "District Officer (Sunil Soren)", "Validated on ground. Angara granitic aquifer confirmed high fluoride. Open for university adoption.", now - timedelta(days=41)),
            ("VALIDATED", "UNIVERSITY_ASSIGNED", "State Innovation Council", "Formally assigned to Birla Institute of Technology (BIT), Mesra Incubation Center", now - timedelta(days=39)),
            ("UNIVERSITY_ASSIGNED", "IN_PROGRESS", "Faculty Mentor (Dr. Ananya Sharma)", "Student team formed; CAD schematics and IoT telemetry development initiated", now - timedelta(days=38)),
            ("IN_PROGRESS", "FIELD_VERIFICATION", "System / Faculty", "All 5 milestone prototypes fabricated; requested independent state field verification", now - timedelta(days=6)),
            ("FIELD_VERIFICATION", "RESOLVED", "Field Inspector (Amit Kumar Verma)", "Physical kiosk verified on-site. Lab test passed: Fluoride 6.4 -> 0.8 ppm (87.5% reduction)", now - timedelta(days=4)),
            ("RESOLVED", "IMPACT_AUDITED", "State Innovation Council", "Community impact audited: 94.2% beneficiary satisfaction across 120 tribal households", now - timedelta(days=2)),
            ("IMPACT_AUDITED", "CLOSED", "State Innovation Council", "Final financial accounts audited; CSR utilization certificate issued to Tata Steel; 6 academic credits certified", now - timedelta(days=1)),
        ]
        for f_st, t_st, actor, rem, t_stmp in history_events:
            db.add(StatusHistory(
                challenge_id=flagship.id,
                from_status=f_st,
                to_status=t_st,
                updated_by=actor,
                remarks=rem,
                changed_at=t_stmp
            ))
        db.commit()

        # Domain Audit Events (Cryptographically Signed)
        db.query(DomainAuditEvent).filter(DomainAuditEvent.entity_type == "Challenge", DomainAuditEvent.entity_id == flagship.id).delete()
        max_seq = db.query(DomainAuditEvent.sequence_number).order_by(DomainAuditEvent.sequence_number.desc()).first()
        seq = (max_seq[0] + 1) if max_seq else 1000

        for f_st, t_st, actor, rem, t_stmp in history_events:
            sig = hashlib.sha256(f"{flagship.id}:{f_st}:{t_st}:{actor}:{t_stmp.isoformat()}".encode()).hexdigest()
            p_json = "{}"
            p_hash = hashlib.sha256(p_json.encode()).hexdigest()
            db.add(DomainAuditEvent(
                sequence_number=seq,
                entity_type="Challenge",
                entity_id=flagship.id,
                action=f"STATE_TRANSITION_{t_st}",
                previous_state=f_st,
                new_state=t_st,
                actor_id=admin_user.id,
                actor_role="SYSTEM_WORKFLOW",
                jurisdiction_level="DISTRICT",
                jurisdiction_value="Ranchi",
                reason_code="DEMO_LIFECYCLE",
                notes=rem,
                payload_json=p_json,
                payload_hash=p_hash,
                prev_event_hash=None,
                event_hash=sig,
                is_internal=False,
                created_at=t_stmp
            ))
            seq += 1
        db.commit()

        # Also create 3 other realistic challenges at different live stages
        challenges_active = [
            {
                "title": "[DEMO STAGE 3] Coal Dust Fugitive Emissions & Air Pollution in Jharia Open-Cast Mines",
                "desc": "Heavy transport dumpers and open-pit blasting in Jharia coalfield generate severe fugitive particulate matter. PM2.5 and PM10 levels regularly surpass 480 ug/m3, causing chronic asthma among schoolchildren.",
                "cat": "Environment", "dist": "Dhanbad", "urgency": "Critical", "priority": ChallengePriority.CRITICAL, "status": ChallengeStatus.UNDER_REVIEW,
                "sol": "Solar-powered IoT particulate monitoring network with automated dry-fog mist water cannons."
            },
            {
                "title": "[DEMO STAGE 6] Inadequate Cold Storage for Tussar Silk & Forest Produce in Torpa",
                "desc": "Tribal women collecting forest produce and silkworm cocoons in Torpa and Rania blocks suffer distress sales due to absence of humidity-controlled preservation, losing 35% of seasonal income.",
                "cat": "Rural Livelihoods", "dist": "Khunti", "urgency": "High", "priority": ChallengePriority.HIGH, "status": ChallengeStatus.VALIDATED,
                "sol": "Solar micro-cold storage unit with phase change material (PCM) backup and mobile artisan marketplace."
            },
            {
                "title": "[DEMO STAGE 8] AI-Powered Early Blight Detection for Tomato & Potato Crops in Ormanjhi",
                "desc": "Smallholder farmers in Ormanjhi vegetable belt face heavy losses as fungal infection turns leaves dark brown, destroying 40% of standing crop. Need low-cost offline diagnostic mobile app.",
                "cat": "Agriculture", "dist": "Ranchi", "urgency": "High", "priority": ChallengePriority.HIGH, "status": ChallengeStatus.IN_PROGRESS,
                "sol": "Smartphone-based offline AI crop disease diagnostic app with localized Santhali/Hindi spraying advisory."
            }
        ]

        for item in challenges_active:
            existing = db.query(Challenge).filter(Challenge.title == item["title"]).first()
            if not existing:
                dist_obj = db.query(District).filter(District.name == item["dist"]).first()
                d_id = dist_obj.id if dist_obj else ranchi_dist_id
                c = Challenge(
                    title=item["title"],
                    description=item["desc"],
                    category=item["cat"],
                    urgency=item["urgency"],
                    priority=item["priority"],
                    status=item["status"],
                    citizen_id=citizen_prof.id,
                    assigned_university_id=univ1.id if item["status"] in [ChallengeStatus.IN_PROGRESS, ChallengeStatus.UNIVERSITY_ASSIGNED] else None,
                    created_at=now - timedelta(days=10)
                )
                db.add(c)
                db.commit()
                db.refresh(c)
                db.add(ChallengeLocation(
                    challenge_id=c.id,
                    district_id=d_id,
                    district_name=item["dist"],
                    block_name="Block A",
                    village_or_city="Village Center",
                    latitude=23.4000,
                    longitude=85.3000
                ))
                db.add(AIAnalysis(
                    challenge_id=c.id,
                    cleaned_text=item["desc"][:200],
                    classified_domain=item["cat"],
                    detected_priority=item["priority"],
                    extracted_keywords=item["cat"],
                    required_expertise="Computer Science, Agriculture, Environmental Science",
                    recommended_solution=item["sol"],
                    confidence_score=0.95
                ))
                db.commit()

        print("[✓] Flagship Demo & All Role Accounts Seeded Successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
