-- SIH 2026 Societal Innovation Collaboration Portal
-- Problem Statement 26043 - Government of Jharkhand
-- Department of Higher & Technical Education
-- PostgreSQL Relational Schema & Indexes

CREATE TYPE user_role AS ENUM (
    'CITIZEN', 'UNIVERSITY', 'STUDENT', 'FACULTY_MENTOR', 'INDUSTRY', 'GOVERNMENT_ADMIN'
);

CREATE TYPE challenge_priority AS ENUM (
    'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
);

CREATE TYPE challenge_status AS ENUM (
    'SUBMITTED', 'AI_ANALYSIS', 'UNDER_REVIEW', 'VALIDATED',
    'UNIVERSITY_ASSIGNED', 'TEAM_FORMED', 'SOLUTION_PROPOSED',
    'APPROVED', 'PROTOTYPE', 'FIELD_TESTING', 'DEPLOYMENT', 'RESOLVED', 'REJECTED'
);

CREATE TYPE milestone_status AS ENUM (
    'NOT_STARTED', 'IN_PROGRESS', 'SUBMITTED', 'APPROVED', 'COMPLETED'
);

-- 1. Districts
CREATE TABLE districts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    state VARCHAR(100) DEFAULT 'Jharkhand' NOT NULL,
    latitude FLOAT,
    longitude FLOAT,
    total_population INTEGER,
    rural_population_pct FLOAT
);
CREATE INDEX idx_districts_name ON districts(name);

-- 2. Users & Roles
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20),
    role user_role NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- 3. Citizens
CREATE TABLE citizens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    address VARCHAR(255),
    district_name VARCHAR(100),
    block_name VARCHAR(100),
    village_or_city VARCHAR(100),
    pincode VARCHAR(10)
);

-- 4. Universities
CREATE TABLE universities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    institution_name VARCHAR(255) NOT NULL,
    district_name VARCHAR(100) NOT NULL,
    address VARCHAR(255),
    website VARCHAR(255),
    has_incubation_center BOOLEAN DEFAULT TRUE,
    has_innovation_center BOOLEAN DEFAULT TRUE,
    facilities_description TEXT,
    nirf_ranking INTEGER
);
CREATE INDEX idx_universities_name ON universities(institution_name);

-- 5. Departments
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    university_id INTEGER NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    head_of_department VARCHAR(150)
);

-- 6. Faculty
CREATE TABLE faculty (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    university_id INTEGER NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    designation VARCHAR(100),
    expertise VARCHAR(255),
    research_interests TEXT,
    experience_years INTEGER DEFAULT 5
);

-- 7. Students
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    university_id INTEGER NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    roll_number VARCHAR(50),
    degree VARCHAR(100) DEFAULT 'B.Tech',
    year_of_study INTEGER DEFAULT 3,
    skills VARCHAR(500)
);

-- 8. Industry Partners
CREATE TABLE industry_partners (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_name VARCHAR(255) NOT NULL,
    industry_domain VARCHAR(150) NOT NULL,
    contact_person VARCHAR(150),
    website VARCHAR(255),
    csr_focus_areas TEXT,
    technologies TEXT,
    available_support TEXT
);
CREATE INDEX idx_industry_company ON industry_partners(company_name);

-- 9. Government Departments
CREATE TABLE government_departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    state VARCHAR(100) DEFAULT 'Jharkhand',
    description TEXT
);

-- 10. Challenge Categories
CREATE TABLE challenge_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    icon_name VARCHAR(50) DEFAULT 'category'
);

-- 11. Challenges
CREATE TABLE challenges (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    sub_category VARCHAR(100),
    urgency VARCHAR(50) DEFAULT 'Medium',
    priority challenge_priority DEFAULT 'MEDIUM',
    expected_impact TEXT,
    status challenge_status DEFAULT 'SUBMITTED',
    citizen_id INTEGER REFERENCES citizens(id) ON DELETE SET NULL,
    assigned_university_id INTEGER REFERENCES universities(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_challenges_title ON challenges(title);
CREATE INDEX idx_challenges_category ON challenges(category);
CREATE INDEX idx_challenges_status ON challenges(status);
CREATE INDEX idx_challenges_priority ON challenges(priority);

-- 12. Challenge Locations
CREATE TABLE challenge_locations (
    id SERIAL PRIMARY KEY,
    challenge_id INTEGER UNIQUE NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    district_id INTEGER REFERENCES districts(id) ON DELETE SET NULL,
    district_name VARCHAR(100) NOT NULL,
    block_name VARCHAR(100),
    village_or_city VARCHAR(100),
    location_address VARCHAR(255),
    latitude FLOAT,
    longitude FLOAT
);
CREATE INDEX idx_challenge_locations_district ON challenge_locations(district_name);

-- 13. Challenge Media
CREATE TABLE challenge_media (
    id SERIAL PRIMARY KEY,
    challenge_id INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    media_type VARCHAR(50) NOT NULL,
    file_url VARCHAR(500) NOT NULL,
    file_name VARCHAR(255),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 14. AI Analysis
CREATE TABLE ai_analysis (
    id SERIAL PRIMARY KEY,
    challenge_id INTEGER UNIQUE NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    cleaned_text TEXT,
    classified_domain VARCHAR(100) NOT NULL,
    detected_priority challenge_priority NOT NULL,
    extracted_keywords TEXT,
    required_expertise TEXT,
    recommended_solution TEXT,
    confidence_score FLOAT DEFAULT 0.92,
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 15. Challenge Similarity
CREATE TABLE challenge_similarity (
    id SERIAL PRIMARY KEY,
    challenge_id INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    similar_challenge_id INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    similarity_score FLOAT NOT NULL,
    matched_keywords TEXT
);

-- 16. University Expertise
CREATE TABLE university_expertise (
    id SERIAL PRIMARY KEY,
    university_id INTEGER NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    domain VARCHAR(100) NOT NULL,
    department VARCHAR(150),
    focus_area VARCHAR(255),
    score_weight FLOAT DEFAULT 1.0
);
CREATE INDEX idx_univ_expertise_domain ON university_expertise(domain);

-- 17. University Matches
CREATE TABLE university_matches (
    id SERIAL PRIMARY KEY,
    challenge_id INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    university_id INTEGER NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    match_percentage FLOAT NOT NULL,
    ranking INTEGER DEFAULT 1,
    matching_factors TEXT
);

-- 18. Projects
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    challenge_id INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    university_id INTEGER NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    faculty_mentor_id INTEGER REFERENCES faculty(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    objectives TEXT,
    expected_outcome TEXT,
    required_skills TEXT,
    timeline_months INTEGER DEFAULT 6,
    progress_percentage FLOAT DEFAULT 0.0,
    current_stage VARCHAR(100) DEFAULT 'Research & Ideation',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 19. Project Members (Multidisciplinary Team)
CREATE TABLE project_members (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    role_in_team VARCHAR(100) DEFAULT 'Researcher & Developer',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 20. Project Milestones
CREATE TABLE project_milestones (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    completion_percentage FLOAT DEFAULT 0.0,
    status milestone_status DEFAULT 'NOT_STARTED',
    due_date TIMESTAMP WITH TIME ZONE,
    approved_by_faculty BOOLEAN DEFAULT FALSE,
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 21. Project Tasks
CREATE TABLE project_tasks (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    assigned_to_student_id INTEGER REFERENCES students(id) ON DELETE SET NULL,
    is_completed BOOLEAN DEFAULT FALSE,
    due_date TIMESTAMP WITH TIME ZONE,
    submission_notes TEXT,
    submission_attachment VARCHAR(500)
);

-- 22. Solution Proposals
CREATE TABLE solution_proposals (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    proposed_solution TEXT NOT NULL,
    technical_approach TEXT NOT NULL,
    required_resources TEXT,
    expected_impact TEXT,
    estimated_cost FLOAT,
    timeline_weeks INTEGER DEFAULT 12,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_approved_by_gov BOOLEAN DEFAULT FALSE
);

-- 23. Industry Collaborations
CREATE TABLE industry_collaborations (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    industry_id INTEGER NOT NULL REFERENCES industry_partners(id) ON DELETE CASCADE,
    offer_type VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'Offered',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 24. Project Documents
CREATE TABLE project_documents (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    doc_type VARCHAR(50) DEFAULT 'Report',
    file_url VARCHAR(500) NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 25. Comments
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    challenge_id INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 26. Notifications
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) DEFAULT 'INFO',
    reference_id INTEGER,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);

-- 27. Status History
CREATE TABLE status_history (
    id SERIAL PRIMARY KEY,
    challenge_id INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    from_status VARCHAR(50),
    to_status VARCHAR(50) NOT NULL,
    updated_by VARCHAR(100) DEFAULT 'System',
    remarks TEXT,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_status_history_challenge ON status_history(challenge_id);

-- 28. Impact Metrics
CREATE TABLE impact_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) UNIQUE NOT NULL,
    metric_value INTEGER DEFAULT 0,
    category VARCHAR(100) DEFAULT 'General',
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
