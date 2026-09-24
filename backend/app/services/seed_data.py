from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from backend.app.core.security import get_password_hash
from backend.app.models.models import (
    Base, User, UserRole, Citizen, University, Department, Faculty, Student,
    IndustryPartner, GovernmentDepartment, ChallengeCategory, Challenge,
    ChallengeLocation, ChallengeMedia, AIAnalysis, ChallengeSimilarity,
    UniversityExpertise, UniversityMatch, Project, ProjectMember,
    ProjectMilestone, ProjectTask, SolutionProposal, IndustryCollaboration,
    ProjectDocument, Comment, Notification, StatusHistory, ImpactMetrics,
    District, ChallengePriority, ChallengeStatus, MilestoneStatus,
    AccountStatus, GovernmentScope, IPRecord, IPRecordType, IPOwnership,
    CollaborationOfferType, AgreementStatus
)
from backend.app.core.config import settings
from backend.app.services.ai.priority_service import JHARKHAND_ASPIRATIONAL_DISTRICTS

JHARKHAND_DISTRICTS = [
    {"name": "Ranchi", "lat": 23.3441, "lon": 85.3096, "pop": 2914253, "rural": 56.9},
    {"name": "Dhanbad", "lat": 23.7957, "lon": 86.4304, "pop": 2684487, "rural": 41.9},
    {"name": "East Singhbhum", "lat": 22.8046, "lon": 86.2029, "pop": 2293919, "rural": 44.4},
    {"name": "Bokaro", "lat": 23.6693, "lon": 86.1511, "pop": 2062330, "rural": 52.3},
    {"name": "Palamu", "lat": 24.0416, "lon": 84.0734, "pop": 1939869, "rural": 88.3},
    {"name": "Hazaribagh", "lat": 23.9925, "lon": 85.3637, "pop": 1734495, "rural": 84.1},
    {"name": "Deoghar", "lat": 24.4826, "lon": 86.7000, "pop": 1492073, "rural": 82.8},
    {"name": "Giridih", "lat": 24.1860, "lon": 86.3072, "pop": 2445474, "rural": 91.0},
    {"name": "Dumka", "lat": 24.2677, "lon": 87.2489, "pop": 1321442, "rural": 93.2},
    {"name": "West Singhbhum", "lat": 22.5667, "lon": 85.8167, "pop": 1502338, "rural": 85.0},
    {"name": "Garhwa", "lat": 24.1600, "lon": 83.8100, "pop": 1322784, "rural": 94.7},
    {"name": "Chatra", "lat": 24.2087, "lon": 84.8711, "pop": 1042886, "rural": 94.0},
    {"name": "Gumla", "lat": 23.0428, "lon": 84.5422, "pop": 1025213, "rural": 93.6},
    {"name": "Godda", "lat": 24.8267, "lon": 87.2144, "pop": 1313551, "rural": 95.1},
    {"name": "Sahebganj", "lat": 25.2425, "lon": 87.6436, "pop": 1150567, "rural": 86.4},
    {"name": "Latehar", "lat": 23.7431, "lon": 84.4983, "pop": 726978, "rural": 92.8},
    {"name": "Koderma", "lat": 24.4678, "lon": 85.5939, "pop": 716259, "rural": 80.3},
    {"name": "Khunti", "lat": 23.0736, "lon": 85.2789, "pop": 531885, "rural": 91.5},
    {"name": "Lohardaga", "lat": 23.4358, "lon": 84.6828, "pop": 461790, "rural": 87.6},
    {"name": "Pakur", "lat": 24.6333, "lon": 87.8500, "pop": 900422, "rural": 94.4},
    {"name": "Ramgarh", "lat": 23.6300, "lon": 85.5100, "pop": 949443, "rural": 55.9},
    {"name": "Saraikela Kharsawan", "lat": 22.7000, "lon": 85.9300, "pop": 1065056, "rural": 74.5},
    {"name": "Simdega", "lat": 22.6167, "lon": 84.5000, "pop": 599578, "rural": 92.9},
    {"name": "Jamtara", "lat": 23.9592, "lon": 86.8028, "pop": 791042, "rural": 90.4}
]

CATEGORIES = [
    ("Water Resources", "Groundwater recharge, drinking water kiosks, filtration, smart irrigation and water bodies conservation."),
    ("Agriculture", "Smart farming, crop disease detection, localized weather stations, precision irrigation, post-harvest processing."),
    ("Healthcare", "Portable telemedicine, point-of-care diagnostics, maternal health, sickle cell screening, rural ambulance routing."),
    ("Education", "Digital smart classrooms, tribal language translation tools, interactive STEM labs, student retention systems."),
    ("Sanitation", "Solid and liquid waste management, smart septic systems, bio-toilets, segregation at source."),
    ("Environment", "Air quality monitoring in mining corridors, afforestation tracking, fly ash recycling, watershed protection."),
    ("Energy", "Solar micro-grids, decentralized battery storage, biomass energy, rural grid power quality monitors."),
    ("Urban Infrastructure", "Pothole detection, smart traffic lighting, municipal asset tracking, flood warning systems."),
    ("Rural Livelihoods", "Tribal forest produce, tussar silk value chain, lac processing, direct handicrafts digital market."),
    ("Accessibility", "Assistive devices for Divyangjan, smart tactile canes, voice-guided interfaces, disabled-friendly public spaces."),
    ("Public Administration", "Citizen grievance redressal, welfare scheme saturation tracker, transparent ration distribution."),
    ("Other", "Cross-cutting societal innovations and interdisciplinary technological solutions.")
]

def seed_database(db: Session):
    # Strictly disallow seeding in production environments
    if settings.ENVIRONMENT == "production" or not settings.DEMO_MODE:
        return

    # Check if already seeded
    if db.query(User).first():
        return

    print("[*] Seeding Jharkhand Districts...")
    district_map = {}
    for d in JHARKHAND_DISTRICTS:
        dist = District(
            name=d["name"],
            state="Jharkhand",
            latitude=d["lat"],
            longitude=d["lon"],
            total_population=d["pop"],
            rural_population_pct=d["rural"],
            is_aspirational=d["name"].lower() in JHARKHAND_ASPIRATIONAL_DISTRICTS
        )
        db.add(dist)
        district_map[d["name"]] = dist
    db.commit()

    print("[*] Seeding Categories...")
    for name, desc in CATEGORIES:
        cat = ChallengeCategory(name=name, description=desc)
        db.add(cat)
    db.commit()

    print("[*] Seeding Government Department...")
    gov_dept = GovernmentDepartment(
        name="Department of Higher & Technical Education",
        state="Jharkhand",
        description="Nodal department fostering technological research, university incubation centers, and youth societal innovation."
    )
    db.add(gov_dept)
    db.commit()

    print("[*] Seeding Predefined Users for All 6 Roles...")
    hashed_pwd = get_password_hash("password123")

    # 1. Government Admin
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

    # 2. Citizen User
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

    citizen_profile = Citizen(
        user_id=citizen_user.id,
        address="Village Nawagarh, Angara Block",
        district_name="Ranchi",
        block_name="Angara",
        village_or_city="Nawagarh",
        pincode="835103"
    )
    db.add(citizen_profile)

    # 3. University User 1: BIT Mesra
    univ_user1 = User(
        email="university@bitmesra.ac.in",
        hashed_password=hashed_pwd,
        full_name="Birla Institute of Technology, Mesra",
        phone_number="+91-651-2275444",
        role=UserRole.UNIVERSITY,
        is_active=True,
        is_verified=True
    )
    db.add(univ_user1)
    db.commit()

    univ1 = University(
        user_id=univ_user1.id,
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

    # Departments & Expertise for BIT Mesra
    dept_env = Department(university_id=univ1.id, name="Department of Environmental Science & Civil Engg", head_of_department="Dr. Ananya Sharma")
    dept_cse = Department(university_id=univ1.id, name="Department of Computer Science & Engineering", head_of_department="Dr. Sandip Dutta")
    dept_ece = Department(university_id=univ1.id, name="Department of Electronics & Communication", head_of_department="Dr. S. K. Ghorai")
    db.add_all([dept_env, dept_cse, dept_ece])
    db.commit()

    db.add_all([
        UniversityExpertise(university_id=univ1.id, domain="Water Resources", department="Civil & Environmental Engg", focus_area="Fluoride Removal & Solar Kiosks", score_weight=1.5),
        UniversityExpertise(university_id=univ1.id, domain="Agriculture", department="CSE & ECE", focus_area="AI Vision Pest Identification", score_weight=1.4),
        UniversityExpertise(university_id=univ1.id, domain="Environment", department="Environmental Science", focus_area="Mining Dust Particulate Sensors", score_weight=1.3),
        UniversityExpertise(university_id=univ1.id, domain="Energy", department="Electrical Engineering", focus_area="Microgrid Storage & Inverters", score_weight=1.2)
    ])

    # University User 2: NIT Jamshedpur
    univ_user2 = User(
        email="nitjsr@jharkhand.ac.in",
        hashed_password=hashed_pwd,
        full_name="National Institute of Technology, Jamshedpur",
        phone_number="+91-657-2373407",
        role=UserRole.UNIVERSITY,
        is_active=True,
        is_verified=True
    )
    db.add(univ_user2)
    db.commit()

    univ2 = University(
        user_id=univ_user2.id,
        institution_name="National Institute of Technology (NIT), Jamshedpur",
        district_name="East Singhbhum",
        address="Adityapur, Jamshedpur, Jharkhand 831014",
        website="https://www.nitjsr.ac.in",
        has_incubation_center=True,
        has_innovation_center=True,
        facilities_description="Industry 4.0 Center of Excellence, Structural Engineering Testing Facility, Advanced Materials Lab",
        nirf_ranking=86
    )
    db.add(univ2)
    db.commit()

    db.add_all([
        UniversityExpertise(university_id=univ2.id, domain="Urban Infrastructure", department="Civil Engineering", focus_area="Durable Road Surfaces & Smart Pothole Detection", score_weight=1.5),
        UniversityExpertise(university_id=univ2.id, domain="Sanitation", department="Civil & Chemical", focus_area="Effluent Treatment & Municipal Composting", score_weight=1.3),
        UniversityExpertise(university_id=univ2.id, domain="Water Resources", department="Mechanical & Civil", focus_area="Deep Borewell Pumps & Water Testing", score_weight=1.2)
    ])

    # University User 3: IIT (ISM) Dhanbad
    univ_user3 = User(
        email="iitism@jharkhand.ac.in",
        hashed_password=hashed_pwd,
        full_name="Indian Institute of Technology (ISM), Dhanbad",
        phone_number="+91-326-2235001",
        role=UserRole.UNIVERSITY,
        is_active=True,
        is_verified=True
    )
    db.add(univ_user3)
    db.commit()

    univ3 = University(
        user_id=univ_user3.id,
        institution_name="Indian Institute of Technology (IIT-ISM), Dhanbad",
        district_name="Dhanbad",
        address="Sardar Patel Nagar, Dhanbad, Jharkhand 826004",
        website="https://www.iitism.ac.in",
        has_incubation_center=True,
        has_innovation_center=True,
        facilities_description="TexMin Center of Excellence in Mining Technology, Environmental Sensing Labs, Remote Sensing & GIS Center",
        nirf_ranking=24
    )
    db.add(univ3)
    db.commit()

    db.add_all([
        UniversityExpertise(university_id=univ3.id, domain="Environment", department="Mining & Environmental Engg", focus_area="Mine Dust Suppression & Realtime AQI", score_weight=1.6),
        UniversityExpertise(university_id=univ3.id, domain="Energy", department="Electrical & Renewable", focus_area="Solar-Biomass Hybrid Grids", score_weight=1.4),
        UniversityExpertise(university_id=univ3.id, domain="Water Resources", department="Applied Geology", focus_area="Groundwater Aquifer Mapping", score_weight=1.3)
    ])

    # 4. Faculty Mentor User
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

    faculty_profile = Faculty(
        user_id=faculty_user.id,
        university_id=univ1.id,
        department_id=dept_env.id,
        designation="Associate Professor & Head",
        expertise="Water Quality Engineering, Membrane Filtration, IoT Water Sensors",
        research_interests="Community-level fluoride decontamination, low-cost solar drinking water purification in Chota Nagpur plateau.",
        experience_years=14
    )
    db.add(faculty_profile)

    # 5. Student Users (Multidisciplinary Team)
    student_user1 = User(
        email="student@bitmesra.ac.in",
        hashed_password=hashed_pwd,
        full_name="Priya Singh",
        phone_number="+91-7903112233",
        role=UserRole.STUDENT,
        is_active=True,
        is_verified=True
    )
    student_user2 = User(
        email="rahul.verma@bitmesra.ac.in",
        hashed_password=hashed_pwd,
        full_name="Rahul Verma",
        phone_number="+91-7903112244",
        role=UserRole.STUDENT,
        is_active=True,
        is_verified=True
    )
    student_user3 = User(
        email="amit.kujur@bitmesra.ac.in",
        hashed_password=hashed_pwd,
        full_name="Amit Kujur",
        phone_number="+91-7903112255",
        role=UserRole.STUDENT,
        is_active=True,
        is_verified=True
    )
    db.add_all([student_user1, student_user2, student_user3])
    db.commit()

    student_profile1 = Student(
        user_id=student_user1.id,
        university_id=univ1.id,
        department_id=dept_cse.id,
        roll_number="BTECH/CSE/2023/042",
        degree="B.Tech Computer Science & Engineering",
        year_of_study=3,
        skills="Python, Flutter, IoT, Embedded C, AI/ML, FastAPI"
    )
    student_profile2 = Student(
        user_id=student_user2.id,
        university_id=univ1.id,
        department_id=dept_env.id,
        roll_number="BTECH/CIV/2023/018",
        degree="B.Tech Civil & Environmental Engg",
        year_of_study=3,
        skills="Water Filtration Design, CAD, Hydrology, Soil Mechanics"
    )
    student_profile3 = Student(
        user_id=student_user3.id,
        university_id=univ1.id,
        department_id=dept_ece.id,
        roll_number="BTECH/ECE/2023/029",
        degree="B.Tech Electronics & Communication",
        year_of_study=3,
        skills="Sensor Hardware, Solar Charge Controllers, LoRaWAN Telemetry"
    )
    db.add_all([student_profile1, student_profile2, student_profile3])

    # 6. Industry Partner User: Tata Steel CSR
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

    ind_profile = IndustryPartner(
        user_id=ind_user.id,
        company_name="Tata Steel Foundation",
        industry_domain="Heavy Engineering & CSR Innovation",
        contact_person="Vikramaditya Sharma, Head of Rural Development",
        website="https://www.tatasteelfoundation.org",
        csr_focus_areas="Safe Drinking Water, Rural Healthcare, Sustainable Livelihoods, Youth Skilling in Jharkhand",
        technologies="Industrial Automation, IoT Sensors, High-grade Metallurgy, Renewable Energy Integration",
        available_support="Field Pilot Testing in Tribal Blocks, Prototype Grant Funding, Technical Mentorship, Manufacturing Facilities"
    )
    db.add(ind_profile)
    db.commit()

    print("[*] Seeding 10+ Societal Challenges across Jharkhand...")

    # CHALLENGE 1: The flagship SIH scenario
    now = datetime.now(timezone.utc)
    ch1 = Challenge(
        title="Severe Drinking Water Shortage and Fluoride Contamination in Angara Block",
        description="Our village Nawagarh in Angara block is facing severe drinking water shortage as three community handpumps dried up. The only operational deep borewell produces water with hazardous fluoride content exceeding 3.5 mg/L, causing dental and skeletal fluorosis among children and elderly villagers.",
        category="Water Resources",
        sub_category="Drinking Water Purification",
        urgency="High",
        priority=ChallengePriority.HIGH,
        expected_impact="Ensure safe, fluoride-free drinking water for 350 rural tribal households (over 1,600 villagers) and eradicate water-borne diseases.",
        status=ChallengeStatus.IN_PROGRESS,
        citizen_id=citizen_profile.id,
        assigned_university_id=univ1.id,
        created_at=now - timedelta(days=20)
    )
    db.add(ch1)
    db.commit()

    db.add(ChallengeLocation(
        challenge_id=ch1.id,
        district_id=district_map["Ranchi"].id,
        district_name="Ranchi",
        block_name="Angara",
        village_or_city="Nawagarh",
        location_address="Near Angara Community Primary School, NH-320",
        latitude=23.3980,
        longitude=85.5520
    ))
    db.add(ChallengeMedia(
        challenge_id=ch1.id,
        media_type="image",
        file_url="/uploads/demo/water_shortage_angara.jpg",
        file_name="dry_handpump_testing.jpg"
    ))
    db.add(AIAnalysis(
        challenge_id=ch1.id,
        cleaned_text="village nawagarh angara block facing severe drinking water shortage handpumps dried borewell hazardous fluoride content",
        classified_domain="Water Resources",
        detected_priority=ChallengePriority.HIGH,
        extracted_keywords="Drinking Water, Fluoride Contamination, Angara Village, Groundwater, Solar Purification",
        required_expertise="Civil Engineering, Environmental Engineering, IoT & Sensor Systems, Chemical Engineering",
        recommended_solution="Deployment of IoT-enabled solar water purification kiosks with activated alumina fluoride adsorption filters and community telemetry.",
        confidence_score=0.96
    ))
    db.add_all([
        UniversityMatch(challenge_id=ch1.id, university_id=univ1.id, match_percentage=94.5, ranking=1, matching_factors="Local District Presence, Specialized Water Resources Research Center, SIH Innovation Lab"),
        UniversityMatch(challenge_id=ch1.id, university_id=univ3.id, match_percentage=82.0, ranking=2, matching_factors="Groundwater Aquifer Mapping Lab, Atal Incubation Center"),
        UniversityMatch(challenge_id=ch1.id, university_id=univ2.id, match_percentage=76.5, ranking=3, matching_factors="Deep Borewell Pumps & Water Testing")
    ])
    db.add_all([
        StatusHistory(challenge_id=ch1.id, from_status=None, to_status="SUBMITTED", updated_by="Citizen (Ramesh Kumar)", remarks="Citizen submitted challenge with GPS coordinates and water report photo", changed_at=now - timedelta(days=20)),
        StatusHistory(challenge_id=ch1.id, from_status="SUBMITTED", to_status="AI_ANALYSIS", updated_by="AI Engine", remarks="Domain classified as Water Resources; Priority flagged as HIGH; Top Match: BIT Mesra (94.5%)", changed_at=now - timedelta(days=20)),
        StatusHistory(challenge_id=ch1.id, from_status="AI_ANALYSIS", to_status="VALIDATED", updated_by="Govt Admin (Dr. Alok Verma)", remarks="Validated by Jharkhand Technical Education Mission Directorate", changed_at=now - timedelta(days=18)),
        StatusHistory(challenge_id=ch1.id, from_status="VALIDATED", to_status="UNIVERSITY_ASSIGNED", updated_by="Govt Admin", remarks="Assigned to BIT Mesra Technology Incubation Center", changed_at=now - timedelta(days=17)),
        StatusHistory(challenge_id=ch1.id, from_status="UNIVERSITY_ASSIGNED", to_status="TEAM_FORMED", updated_by="University Admin", remarks="Multidisciplinary student team and faculty mentor Dr. Ananya Sharma assigned", changed_at=now - timedelta(days=15)),
        StatusHistory(challenge_id=ch1.id, from_status="TEAM_FORMED", to_status="SOLUTION_PROPOSED", updated_by="Team Lead (Priya Singh)", remarks="Submitted technical design for low-cost activated alumina filter kiosk with solar power", changed_at=now - timedelta(days=12)),
        StatusHistory(challenge_id=ch1.id, from_status="SOLUTION_PROPOSED", to_status="PROTOTYPE", updated_by="Faculty Mentor", remarks="Prototype filter column and LoRa-based turbidity sensor assembled", changed_at=now - timedelta(days=8)),
        StatusHistory(challenge_id=ch1.id, from_status="PROTOTYPE", to_status="IN_PROGRESS", updated_by="System", remarks="Tata Steel CSR provided prototype grant and pilot validation support", changed_at=now - timedelta(days=4))
    ])

    # Flagship Project for Challenge 1
    proj1 = Project(
        challenge_id=ch1.id,
        university_id=univ1.id,
        faculty_mentor_id=faculty_profile.id,
        name="Jal-Sanjeevani: Solar IoT Defluoridation Kiosk for Angara",
        description="A low-cost, gravity-fed defluoridation unit powered by a 500W rooftop solar panel. Utilizes locally regenerable activated alumina beads and an ESP32 IoT module with GSM/LoRa to report daily water output and filtration performance to the block administration.",
        objectives="1. Reduce fluoride concentration from 3.5 mg/L to < 1.0 mg/L (WHO standard)\n2. Deliver 2,500 liters/day of clean drinking water\n3. Solar autonomous operation with cloud alert telemetry",
        expected_outcome="Functional clean water kiosk installed in Nawagarh, operating continuously with community water committee stewardship.",
        required_skills="Civil Water Filtration, IoT Sensor Integration, Mobile Dashboard, Community Stakeholder Management",
        timeline_months=4,
        progress_percentage=65.0,
        current_stage="Field Testing & Pilot Assembly",
        created_at=now - timedelta(days=15)
    )
    db.add(proj1)
    db.commit()

    db.add_all([
        ProjectMember(project_id=proj1.id, student_id=student_profile1.id, role_in_team="Software & IoT Telemetry Lead"),
        ProjectMember(project_id=proj1.id, student_id=student_profile2.id, role_in_team="Filtration Column & Hydraulics Design"),
        ProjectMember(project_id=proj1.id, student_id=student_profile3.id, role_in_team="Solar Power & Embedded Hardware")
    ])

    # Milestones for Project 1
    m1 = ProjectMilestone(project_id=proj1.id, title="Water Sample Chemical Profiling & Site Survey", description="Collected 12 water samples from Angara and conducted ICP-MS spectroscopic fluoride quantification.", completion_percentage=100.0, status=MilestoneStatus.APPROVED, approved_by_faculty=True, approved_at=now - timedelta(days=13))
    m2 = ProjectMilestone(project_id=proj1.id, title="Laboratory Filter Column & Media Optimization", description="Fabricated 50-liter activated alumina adsorption bed achieving 92% fluoride retention.", completion_percentage=100.0, status=MilestoneStatus.APPROVED, approved_by_faculty=True, approved_at=now - timedelta(days=9))
    m3 = ProjectMilestone(project_id=proj1.id, title="Solar Hardware & IoT Telemetry Assembly", description="Integrated solar battery bank with turbidity, pH, and flow sensor transmitting to dashboard.", completion_percentage=85.0, status=MilestoneStatus.IN_PROGRESS, approved_by_faculty=False)
    m4 = ProjectMilestone(project_id=proj1.id, title="Community Field Pilot Deployment in Nawagarh", description="Civil installation of the kiosk structure and connection to the village overhead line.", completion_percentage=30.0, status=MilestoneStatus.IN_PROGRESS, approved_by_faculty=False)
    m5 = ProjectMilestone(project_id=proj1.id, title="Final Validation, Handover & Impact Audit", description="7-day continuous water testing, community training, and final handover to Gram Panchayat.", completion_percentage=0.0, status=MilestoneStatus.NOT_STARTED, approved_by_faculty=False)
    db.add_all([m1, m2, m3, m4, m5])

    # Tasks for Project 1
    db.add_all([
        ProjectTask(project_id=proj1.id, title="Complete GSM MQTT sensor firmware for ESP32", assigned_to_student_id=student_profile1.id, is_completed=True, submission_notes="Firmware tested with SIM800L module; sending packets every 15 minutes."),
        ProjectTask(project_id=proj1.id, title="Run 48-hour continuous breakthrough test on alumina column", assigned_to_student_id=student_profile2.id, is_completed=True, submission_notes="Breakthrough reached at 2,400 bed volumes; regeneration protocol verified."),
        ProjectTask(project_id=proj1.id, title="Assemble weatherproof enclosure with solar MPPT charge controller", assigned_to_student_id=student_profile3.id, is_completed=True, submission_notes="IP65 enclosure assembled with 12V 42Ah LiFePO4 battery pack."),
        ProjectTask(project_id=proj1.id, title="Coordinate site foundation with Angara Gram Panchayat head", assigned_to_student_id=student_profile2.id, is_completed=False),
        ProjectTask(project_id=proj1.id, title="Deploy Flutter mobile tracking dashboard for village water operators", assigned_to_student_id=student_profile1.id, is_completed=False)
    ])

    # Solution Proposal & Industry Collaboration for Project 1
    db.add(SolutionProposal(
        project_id=proj1.id,
        proposed_solution="Decentralized Solar-Powered IoT Water Defluoridation Kiosk (Jal-Sanjeevani)",
        technical_approach="Two-stage gravity filtration using food-grade activated alumina followed by silver-impregnated ceramic candle for pathogen exclusion. Automated ultrasonic level control and LoRa/GSM telemetry.",
        required_resources="500W Solar Panels, Adsorption Columns, Sensor Suite, Mild Steel Skid Frame",
        expected_impact="1,600+ direct beneficiaries with 100% reduction in dental fluorosis risk.",
        estimated_cost=85000.0,
        timeline_weeks=12,
        is_approved_by_gov=True
    ))

    db.add(IndustryCollaboration(
        project_id=proj1.id,
        industry_id=ind_profile.id,
        offer_type="Prototype Support & Pilot Implementation",
        description="Tata Steel Foundation approved a Rs. 1,00,000 prototype fabrication grant and assigned an environmental senior engineer for weekly technical reviews and site validation.",
        status="Active"
    ))

    # A completed technology-transfer agreement + IP outcomes, so the admin dashboard's
    # live patent/startup/technology-transfer KPIs show real, non-zero, non-hardcoded numbers.
    db.add(IndustryCollaboration(
        project_id=proj1.id,
        industry_id=ind_profile.id,
        offer_type=CollaborationOfferType.TECHNOLOGY_TRANSFER.value,
        description="Tata Steel Foundation licensed the regenerable activated-alumina defluoridation media and IoT telemetry design for replication across its CSR command area.",
        status="Completed",
        agreement_status=AgreementStatus.COMPLETED,
        scope="Transfer of filtration media formulation and IoT telemetry firmware for replication at 5 additional sites.",
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(days=2)
    ))

    db.add(IPRecord(
        project_id=proj1.id,
        record_type=IPRecordType.PATENT,
        title="Regenerable Activated-Alumina Cartridge for Solar-Powered Defluoridation Kiosks",
        description="Patent application covering the regenerable adsorption cartridge and automated backwash cycle used in the Jal-Sanjeevani kiosk.",
        ownership=IPOwnership.JOINT,
        patent_reference="TEMP/JH/2026/WATER/00147 (provisional filing)",
        status="APPROVED",
        created_by_user_id=faculty_user.id
    ))

    db.add(IPRecord(
        project_id=proj1.id,
        record_type=IPRecordType.SOFTWARE,
        title="AquaSanjeevani IoT Telemetry & Water-Quality Dashboard",
        description="Embedded firmware and cloud dashboard spun off into an independent startup to commercialize rural water-quality telemetry statewide.",
        ownership=IPOwnership.JOINT,
        startup_spinoff_name="AquaSanjeevani Innovations Pvt Ltd",
        status="APPROVED",
        created_by_user_id=faculty_user.id
    ))

    # Comments for Challenge 1
    db.add_all([
        Comment(challenge_id=ch1.id, user_id=admin_user.id, content="Priority verified. Angara block is situated on the Ranchi granitic belt known for high groundwater fluoride. Approved for immediate university fast-track funding."),
        Comment(challenge_id=ch1.id, user_id=faculty_user.id, content="BIT Mesra Water Quality Lab has taken this up. Our students have completed the initial water testing and are assembling the filter media."),
        Comment(challenge_id=ch1.id, user_id=ind_user.id, content="Tata Steel Foundation is pleased to sponsor the field pilot kiosk deployment and provide the fabrication hardware.")
    ])

    # 9 Additional Diverse Realistic Challenges across Jharkhand
    challenges_seed = [
        {
            "title": "Early Blight Fungus Destroying Tomato and Potato Crops in Ormanjhi Block",
            "desc": "Smallholder farmers in Ormanjhi vegetable belt are facing heavy losses as an unidentified fungal infection is rapidly turning tomato and potato leaves dark brown with concentric rings, destroying 40% of the standing crop within one week.",
            "cat": "Agriculture", "district": "Ranchi", "urgency": "High", "priority": ChallengePriority.HIGH, "status": ChallengeStatus.PROTOTYPE,
            "kw": "Crop Disease, Tomato Blight, Fungus, Ormanjhi Farmers, Computer Vision",
            "sol": "Smartphone-based offline AI crop disease diagnostic app with localized tribal language spraying advisory."
        },
        {
            "title": "Coal Dust Air Pollution and Respiratory Hazards near Jharia Open Cast Mines",
            "desc": "Heavy coal transport dumpers and open-pit blasting in Jharia coalfield generate severe fugitive particulate matter. PM2.5 and PM10 levels regularly surpass 450 ug/m3, causing chronic bronchitis and asthma among schoolchildren.",
            "cat": "Environment", "district": "Dhanbad", "urgency": "Critical", "priority": ChallengePriority.CRITICAL, "status": ChallengeStatus.VALIDATED,
            "kw": "Coal Dust, Air Quality, Mining Corridor, PM2.5, Jharia",
            "sol": "Solar-powered IoT particulate monitoring network with automated dry fog mist water cannons."
        },
        {
            "title": "Inadequate Cold Storage and Processing for Tussar Silk and Forest Produce",
            "desc": "Tribal women collecting forest produce and silkworm cocoons in Torpa and Rania blocks suffer distress sales due to absence of humidity-controlled preservation, losing nearly 35% of their seasonal income.",
            "cat": "Rural Livelihoods", "district": "Khunti", "urgency": "Medium", "priority": ChallengePriority.MEDIUM, "status": ChallengeStatus.SOLUTION_PROPOSED,
            "kw": "Tussar Silk, Tribal Artisans, Cold Storage, Forest Produce, Khunti",
            "sol": "Solar micro-cold storage unit with phase change material (PCM) backup and mobile artisan marketplace."
        },
        {
            "title": "Lack of Digital STEM Education Laboratories in Remote Santhal Pargana Schools",
            "desc": "Over 20 Kasturba Gandhi Balika Vidyalayas (KGBVs) and government secondary schools across Dumka lack functional science experimental equipment and digital computing infrastructure.",
            "cat": "Education", "district": "Dumka", "urgency": "Medium", "priority": ChallengePriority.MEDIUM, "status": ChallengeStatus.UNIVERSITY_ASSIGNED,
            "kw": "Digital Learning, STEM Labs, Tribal Schools, Dumka, Virtual Simulation",
            "sol": "Low-cost Raspberry Pi based offline digital experiential science kits with Santhali and Hindi interactive modules."
        },
        {
            "title": "High Incidence of Sickle Cell Anemia and Lack of Rapid Screening Kits",
            "desc": "Tribal populations in Chaibasa and surrounding mining belts have over 14% sickle cell trait prevalence. Current diagnostic samples take 3 to 4 weeks to receive electrophoresis reports from distant city hospitals.",
            "cat": "Healthcare", "district": "West Singhbhum", "urgency": "Critical", "priority": ChallengePriority.CRITICAL, "status": ChallengeStatus.IN_PROGRESS,
            "kw": "Sickle Cell Anemia, Rapid Screening, Tribal Health, Chaibasa, Microfluidics",
            "sol": "Paper-based microfluidic lateral flow cassette for 15-minute point-of-care sickle hemoglobin identification."
        },
        {
            "title": "Frequent Transformer Burnouts and Voltage Drops in Rural Irrigation Feeders",
            "desc": "Farmers in Chandankiyari block face prolonged power cuts during paddy sowing season because distribution transformers burn out due to unbalanced inductive motor loads and lightning surges.",
            "cat": "Energy", "district": "Bokaro", "urgency": "High", "priority": ChallengePriority.HIGH, "status": ChallengeStatus.APPROVED,
            "kw": "Transformer Burnout, Rural Feeder, Power Quality, Voltage Fluctuation, Bokaro",
            "sol": "Smart IoT transformer thermal and load monitor with automatic phase load balancer and surge bypass."
        },
        {
            "title": "Open Drainage Overflow and Solid Waste Accumulation near Deoghar Temple Complex",
            "desc": "During the Shravani Mela pilgrimage, over 40 lakh pilgrims visit the Baidyanath Dham temple. Drainage lines clog with discarded single-use plastics and wet offerings, causing foul smell and health hazards.",
            "cat": "Sanitation", "district": "Deoghar", "urgency": "High", "priority": ChallengePriority.HIGH, "status": ChallengeStatus.FIELD_TESTING,
            "kw": "Pilgrimage Waste, Plastic Shredding, Drainage Overflow, Deoghar Temple, Biogas",
            "sol": "Automated floating waste skimmer for drainage canals coupled with quick-composting organic waste digester."
        },
        {
            "title": "Severe Road Potholes and Bridge Deck Erosion on Rural NH-33 Link Road",
            "desc": "Heavy transport trucks carrying iron ore have caused extensive crater-like potholes and bridge expansion joint damages on the Barhi-Hazaribagh route, leading to fatal two-wheeler accidents.",
            "cat": "Urban Infrastructure", "district": "Hazaribagh", "urgency": "Medium", "priority": ChallengePriority.MEDIUM, "status": ChallengeStatus.TEAM_FORMED,
            "kw": "Road Potholes, Highway Safety, Structural Erosion, Hazaribagh, Asphalt Repair",
            "sol": "Cold-mix geo-polymer asphalt repair material synthesized with blast furnace slag and smartphone pothole LiDAR survey."
        },
        {
            "title": "Lack of Assistive Walking Devices and Braille Navigation in District Hospitals",
            "desc": "Visually impaired and elderly patients visiting Jamshedpur district civil hospital face immense hurdles navigating between OPD, pathology labs, and pharmacy counters without human escort.",
            "cat": "Accessibility", "district": "East Singhbhum", "urgency": "Medium", "priority": ChallengePriority.MEDIUM, "status": ChallengeStatus.UNDER_REVIEW,
            "kw": "Visually Impaired, Braille Navigation, Hospital Wayfinding, Assistive Stick, Divyangjan",
            "sol": "Bluetooth low energy (BLE) audio beacon indoor navigation app coupled with smart ultrasonic cane."
        },
        {
            "title": "Solar Powered Drinking Water Filtration Plant Deployed in Namkum Block",
            "desc": "Namkum panchayat had requested drinking water assistance for 500 households due to iron and bacterial contamination. A 3-stage filtration kiosk was designed, tested, and handed over to the local community committee.",
            "cat": "Water Resources", "district": "Ranchi", "urgency": "High", "priority": ChallengePriority.HIGH, "status": ChallengeStatus.RESOLVED,
            "kw": "Solar Filtration, Drinking Water, Namkum, Water Kiosk, Community Handover",
            "sol": "Complete 3-stage sand-carbon-UV solar water purification facility operating successfully."
        }
    ]

    for item in challenges_seed:
        ch = Challenge(
            title=item["title"],
            description=item["desc"],
            category=item["cat"],
            urgency=item["urgency"],
            priority=item["priority"],
            expected_impact=f"Significantly improve quality of life and public health in {item['district']} district.",
            status=item["status"],
            citizen_id=citizen_profile.id,
            created_at=now - timedelta(days=10)
        )
        db.add(ch)
        db.commit()

        db.add(ChallengeLocation(
            challenge_id=ch.id,
            district_id=district_map[item["district"]].id,
            district_name=item["district"],
            block_name=f"{item['district']} Central",
            village_or_city=item["district"],
            location_address=f"Main Sector, {item['district']}, Jharkhand",
            latitude=district_map[item["district"]].latitude,
            longitude=district_map[item["district"]].longitude
        ))

        db.add(AIAnalysis(
            challenge_id=ch.id,
            cleaned_text=item["desc"][:250],
            classified_domain=item["cat"],
            detected_priority=item["priority"],
            extracted_keywords=item["kw"],
            required_expertise="Multidisciplinary Engineering & Technology",
            recommended_solution=item["sol"],
            confidence_score=0.92
        ))

        db.add(StatusHistory(
            challenge_id=ch.id,
            from_status="SUBMITTED",
            to_status=item["status"].value,
            updated_by="System & Admin",
            remarks=f"Challenge progressed to {item['status'].value}",
            changed_at=now - timedelta(days=5)
        ))

    print("[*] Seeding Impact Metrics...")
    # NOTE: Patents Filed, Startups Incubated, Technology Transfers, Prototypes Developed
    # and Pilots Deployed are NOT seeded here — they are computed live by
    # AnalyticsService.get_dashboard_summary() from real IPRecord / IndustryCollaboration /
    # Challenge state (see backend/app/services/analytics_service.py). Only figures that
    # cannot yet be derived from transactional state stay as manually tracked ImpactMetrics.
    metrics = [
        ("Challenges Resolved", 14, "Impact"),
        ("Projects Completed", 18, "Impact"),
        ("Students Involved", 240, "Academic"),
        ("Universities Involved", 12, "Academic"),
        ("Industry Partnerships", 19, "Industry"),
        ("Beneficiaries Reached", 48500, "Societal")
    ]
    for m_name, m_val, cat in metrics:
        db.add(ImpactMetrics(metric_name=m_name, metric_value=m_val, category=cat))

    # Initial Notifications for users
    db.add(Notification(
        user_id=citizen_user.id,
        title="Challenge Status Updated",
        message="Your challenge 'Severe Drinking Water Shortage in Angara Block' is now IN_PROGRESS with prototype development underway at BIT Mesra!",
        notification_type="STATUS_UPDATE",
        reference_id=ch1.id
    ))
    db.add(Notification(
        user_id=univ_user1.id,
        title="New Challenge Assigned",
        message="Government of Jharkhand assigned Challenge #1 (Angara Water Shortage) to your institution.",
        notification_type="ASSIGNMENT",
        reference_id=ch1.id
    ))
    db.add(Notification(
        user_id=student_user1.id,
        title="Added to Multidisciplinary Project Team",
        message="You were appointed as Software & IoT Telemetry Lead for project Jal-Sanjeevani!",
        notification_type="TEAM",
        reference_id=proj1.id
    ))

    db.commit()
    print("[✓] Realistic Jharkhand Demo Dataset seeded successfully!")


def ensure_sapthagiri_seeded(db: Session):
    existing = db.query(University).filter(University.institution_name.ilike("%Sapthagiri%")).first()
    if existing:
        return existing

    hashed_pwd = get_password_hash("password123")

    # 1. University Admin User
    admin_user = db.query(User).filter(User.email == "university@sapthagiri.edu.in").first()
    if not admin_user:
        admin_user = User(
            email="university@sapthagiri.edu.in",
            hashed_password=hashed_pwd,
            full_name="Sapthagiri NPS University Admin",
            phone_number="+91-80-28372800",
            role=UserRole.UNIVERSITY,
            is_active=True,
            is_verified=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

    univ = University(
        user_id=admin_user.id,
        institution_name="Sapthagiri NPS University",
        district_name="Bengaluru",
        address="Hesaraghatta Main Rd, Bengaluru, Karnataka 560057",
        website="https://www.sapthagiri.edu.in",
        has_incubation_center=True,
        has_innovation_center=True,
        facilities_description="DST & Industry supported Incubation Center, AI & Robotics Center of Excellence, IoT Solutions Lab",
        nirf_ranking=42
    )
    db.add(univ)
    db.commit()
    db.refresh(univ)

    dept_cse = Department(university_id=univ.id, name="Computer Science & Engineering", head_of_department="Dr. H. N. Suresh")
    dept_ece = Department(university_id=univ.id, name="Electronics & Communication Engg", head_of_department="Dr. Ravi Kumar")
    db.add_all([dept_cse, dept_ece])
    db.commit()

    db.add_all([
        UniversityExpertise(university_id=univ.id, domain="Water Resources", department="Environmental & IoT", focus_area="Smart Water Telemetry & Leak Detection", score_weight=1.5),
        UniversityExpertise(university_id=univ.id, domain="Agriculture", department="CSE & Robotics", focus_area="Autonomous Soil Moisture & Crop Health Drones", score_weight=1.4),
        UniversityExpertise(university_id=univ.id, domain="Energy", department="Electrical & Automation", focus_area="Solar Microgrids & Battery Optimization", score_weight=1.3)
    ])
    db.commit()

    # 2. Faculty Mentor User
    fac_user = db.query(User).filter(User.email == "faculty@sapthagiri.edu.in").first()
    if not fac_user:
        fac_user = User(
            email="faculty@sapthagiri.edu.in",
            hashed_password=hashed_pwd,
            full_name="Dr. Ramesh Babu",
            phone_number="+91-9845012345",
            role=UserRole.FACULTY_MENTOR,
            is_active=True,
            is_verified=True
        )
        db.add(fac_user)
        db.commit()
        db.refresh(fac_user)

    fac_profile = Faculty(
        user_id=fac_user.id,
        university_id=univ.id,
        department_id=dept_cse.id,
        designation="Professor & R&D Lead",
        expertise="Artificial Intelligence, Edge IoT, Distributed Systems",
        research_interests="Applied AI for rural governance and environmental monitoring.",
        experience_years=16
    )
    db.add(fac_profile)

    # 3. Student User (Kiran Biradar)
    stu_user = db.query(User).filter(User.email == "student@sapthagiri.edu.in").first()
    if not stu_user:
        stu_user = User(
            email="student@sapthagiri.edu.in",
            hashed_password=hashed_pwd,
            full_name="Kiran Biradar",
            phone_number="+91-9900112233",
            role=UserRole.STUDENT,
            is_active=True,
            is_verified=True
        )
        db.add(stu_user)
        db.commit()
        db.refresh(stu_user)

    stu_profile = Student(
        user_id=stu_user.id,
        university_id=univ.id,
        department_id=dept_cse.id,
        roll_number="SNPU/CSE/2024/001",
        degree="B.Tech Computer Science & Engineering",
        year_of_study=3,
        skills="Python, Flutter, Machine Learning, FastAPI, Cloud Architecture"
    )
    db.add(stu_profile)
    db.commit()
    print("[✓] Sapthagiri NPS University seeded successfully!")
    return univ
