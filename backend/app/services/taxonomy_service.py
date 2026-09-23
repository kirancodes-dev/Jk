from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.models.models import TaxonomyDomain, TaxonomySubdomain

# Canonical 11 Problem Statement Domains for SIH 26043 Jharkhand
CANONICAL_DOMAINS: Dict[str, Dict] = {
    "EDUCATION": {
        "name": "Education",
        "description": "Smart classrooms, digital learning, teacher shortage, and tribal language pedagogy.",
        "icon": "school",
        "subdomains": [
            "Smart Classrooms & EdTech",
            "Teacher Training & Staffing",
            "Tribal & Mother-Tongue Learning",
            "Vocational & Skill Centers",
            "School Infrastructure & Labs"
        ]
    },
    "AGRICULTURE": {
        "name": "Agriculture",
        "description": "Climate-resilient crops, micro-irrigation, soil health, farm mechanization, and mandi market linkages.",
        "icon": "agriculture",
        "subdomains": [
            "Micro-Irrigation & Water Harvesting",
            "Soil Health & Organic Farming",
            "Mandi & Cold Chain Logistics",
            "Crop Protection & Pest Alerts",
            "Horticulture & Cash Crops"
        ]
    },
    "HEALTHCARE": {
        "name": "Healthcare",
        "description": "Telemedicine, rural primary health centers, malnutrition, maternal care, and mobile diagnostics.",
        "icon": "local_hospital",
        "subdomains": [
            "Telemedicine & Remote Diagnostics",
            "Malnutrition & Anemia Alleviation",
            "Maternal & Child Health Tracking",
            "Primary Health Center (PHC) Modernization",
            "Emergency Medical Transport"
        ]
    },
    "WATER_RESOURCES": {
        "name": "Water Resources",
        "description": "Drinking water supply, check dams, watershed management, arsenic/fluoride filtration, and Jal Jeevan Mission.",
        "icon": "water_drop",
        "subdomains": [
            "Piped Drinking Water Supply",
            "Check Dam & Pond Rejuvenation",
            "Groundwater Recharge & Rainwater Harvesting",
            "Water Contamination & Arsenic Filtration",
            "Industrial Effluent Monitoring"
        ]
    },
    "SANITATION": {
        "name": "Sanitation",
        "description": "Solid & liquid waste management, faecal sludge treatment, plastic recycling, and public sanitation.",
        "icon": "cleaning_services",
        "subdomains": [
            "Solid Waste Segregation & Processing",
            "Rural Greywater Drainage",
            "Faecal Sludge Treatment Facilities",
            "Plastic Waste Recycling",
            "Public & Community Toilets"
        ]
    },
    "ENVIRONMENT": {
        "name": "Environment",
        "description": "Forest conservation, mine reclamation, air quality monitoring, biodiversity, and climate adaptation.",
        "icon": "forest",
        "subdomains": [
            "Abandoned Mine Reclamation",
            "Forest Fire Detection & Prevention",
            "Mining Dust & Industrial Air Quality",
            "Afforestation & Biodiversity Corridors",
            "Wetland Preservation"
        ]
    },
    "ENERGY": {
        "name": "Energy",
        "description": "Decentralized solar mini-grids, clean cooking energy, agricultural pump solarization, and biomass.",
        "icon": "bolt",
        "subdomains": [
            "Solar Mini-Grids for Off-Grid Hamlets",
            "PM-KUSUM Solar Agricultural Pumps",
            "Clean Cooking Fuel & Biogas",
            "Rooftop Solar for Public Institutions",
            "Grid Reliability & Fault Detection"
        ]
    },
    "URBAN_INFRASTRUCTURE": {
        "name": "Urban Infrastructure",
        "description": "Smart mobility, traffic safety, municipal drainage, GIS mapping, and urban public spaces.",
        "icon": "location_city",
        "subdomains": [
            "Stormwater Drainage & Flood Prevention",
            "Smart Street Lighting & Energy Efficiency",
            "Public Transport & Electric Mobility",
            "Municipal GIS Asset Mapping",
            "Road Safety & Blackspot Elimination"
        ]
    },
    "ACCESSIBILITY": {
        "name": "Accessibility",
        "description": "Assistive tech for Divyangjan, barrier-free public buildings, inclusive transport, and voice portals.",
        "icon": "accessible",
        "subdomains": [
            "Assistive Hardware & Devices",
            "Barrier-Free Access in Public Offices",
            "Multilingual Voice Interfaces",
            "Screen-Reader Friendly Portals",
            "Special Education Learning Tools"
        ]
    },
    "PUBLIC_ADMINISTRATION": {
        "name": "Public Administration",
        "description": "Digital citizen services, grievance redressal, DBT verification, procurement transparency, and anti-corruption.",
        "icon": "account_balance",
        "subdomains": [
            "Grievance Triage Automation",
            "Direct Benefit Transfer (DBT) Audits",
            "Panchayat Digital Record Management",
            "Land Records & Mutation Transparency",
            "Public Service Guarantee Compliance"
        ]
    },
    "RURAL_LIVELIHOODS": {
        "name": "Rural Livelihoods",
        "description": "Tribal handicrafts, lac and tussar silk value chains, minor forest produce, SHG enterprises, and eco-tourism.",
        "icon": "handshake",
        "subdomains": [
            "Minor Forest Produce (MFP) Processing",
            "Tussar Silk & Lac Cultivation",
            "Self-Help Group (SHG) Market Linkages",
            "Tribal Handicraft E-Commerce",
            "Community-Led Eco-Tourism"
        ]
    }
}

# Canonical 24 Districts of Jharkhand
JHARKHAND_DISTRICTS: List[str] = [
    "Ranchi", "Dhanbad", "East Singhbhum", "Bokaro", "Palamu",
    "Hazaribagh", "Deoghar", "Giridih", "Dumka", "West Singhbhum",
    "Garhwa", "Chatra", "Gumla", "Godda", "Sahebganj", "Latehar",
    "Koderma", "Khunti", "Lohardaga", "Pakur", "Ramgarh",
    "Saraikela Kharsawan", "Simdega", "Jamtara"
]

# Geographic Bounding Box for Jharkhand State
# Latitude approx 21.9° N to 25.4° N, Longitude approx 83.3° E to 87.9° E
JHARKHAND_BBOX = {
    "min_lat": 21.8,
    "max_lat": 25.5,
    "min_lng": 83.2,
    "max_lng": 88.0
}


class TaxonomyService:
    CANONICAL_DOMAINS = CANONICAL_DOMAINS
    JHARKHAND_DISTRICTS = JHARKHAND_DISTRICTS
    JHARKHAND_BBOX = JHARKHAND_BBOX

    @staticmethod
    def normalize_code(name: str) -> str:
        """Normalizes a domain string to uppercase underscore format (e.g. 'Water Resources' -> 'WATER_RESOURCES')."""
        return name.strip().upper().replace(" ", "_").replace("-", "_")

    LEGACY_ALIASES: Dict[str, str] = {
        "WATER_MANAGEMENT": "WATER_RESOURCES",
        "WATER": "WATER_RESOURCES",
        "WATER_&_SANITATION": "WATER_RESOURCES",
        "WATER_AND_SANITATION": "WATER_RESOURCES",
        "INFRASTRUCTURE": "URBAN_INFRASTRUCTURE",
        "RENEWABLE_ENERGY": "ENERGY",
        "POWER": "ENERGY",
        "HEALTH": "HEALTHCARE",
    }

    @classmethod
    def is_valid_domain(cls, domain: str) -> bool:
        normalized = cls.normalize_code(domain)
        if normalized in cls.LEGACY_ALIASES:
            normalized = cls.LEGACY_ALIASES[normalized]
        return normalized in CANONICAL_DOMAINS

    @classmethod
    def resolve_domain_code(cls, domain: str) -> Optional[str]:
        normalized = cls.normalize_code(domain)
        if normalized in cls.LEGACY_ALIASES:
            normalized = cls.LEGACY_ALIASES[normalized]
        if normalized in CANONICAL_DOMAINS:
            return normalized
        # Case insensitive name search
        for code, meta in CANONICAL_DOMAINS.items():
            if meta["name"].lower() == domain.strip().lower():
                return code
        return None

    @classmethod
    def is_valid_district(cls, district: str) -> bool:
        clean = district.strip().lower()
        return any(d.lower() == clean for d in JHARKHAND_DISTRICTS)

    @classmethod
    def resolve_district_name(cls, district: str) -> Optional[str]:
        clean = district.strip().lower()
        for d in JHARKHAND_DISTRICTS:
            if d.lower() == clean:
                return d
        return None

    @classmethod
    def validate_coordinates(
        cls,
        latitude: Optional[float],
        longitude: Optional[float],
        district_name: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates that latitude and longitude are valid and fall within Jharkhand state boundaries.
        """
        if latitude is None and longitude is None:
            return True, None

        if latitude is None or longitude is None:
            return False, "Both latitude and longitude must be provided together."

        if not (-90.0 <= latitude <= 90.0):
            return False, f"Invalid latitude {latitude}. Latitude must be between -90 and 90 degrees."

        if not (-180.0 <= longitude <= 180.0):
            return False, f"Invalid longitude {longitude}. Longitude must be between -180 and 180 degrees."

        # Verify coordinates fall within Jharkhand territory
        if not (JHARKHAND_BBOX["min_lat"] <= latitude <= JHARKHAND_BBOX["max_lat"] and
                JHARKHAND_BBOX["min_lng"] <= longitude <= JHARKHAND_BBOX["max_lng"]):
            return False, (
                f"Coordinates ({latitude:.4f}, {longitude:.4f}) fall outside Jharkhand state boundary "
                f"(Latitude 21.9°-25.4°N, Longitude 83.3°-87.9°E)."
            )

        return True, None

    @classmethod
    def seed_taxonomy_database(cls, db: Session) -> None:
        """Seeds canonical domains and subdomains if not already populated."""
        for code, data in CANONICAL_DOMAINS.items():
            existing = db.query(TaxonomyDomain).filter(TaxonomyDomain.code == code).first()
            if not existing:
                domain_rec = TaxonomyDomain(
                    code=code,
                    name=data["name"],
                    description=data["description"],
                    icon_name=data["icon"],
                    is_active=True
                )
                db.add(domain_rec)
                db.flush()

                for sub in data["subdomains"]:
                    sub_code = cls.normalize_code(sub)
                    sub_rec = TaxonomySubdomain(
                        domain_id=domain_rec.id,
                        code=sub_code,
                        name=sub,
                        description=f"{sub} under {data['name']}",
                        is_active=True
                    )
                    db.add(sub_rec)
        db.commit()

    @classmethod
    def get_taxonomy_tree(cls, db: Optional[Session] = None) -> List[Dict]:
        """Returns the full taxonomy tree with subdomains for API serialization."""
        if db:
            domains = db.query(TaxonomyDomain).filter(TaxonomyDomain.is_active == True).all()
            if domains:
                tree = []
                for d in domains:
                    tree.append({
                        "code": d.code,
                        "name": d.name,
                        "description": d.description,
                        "icon": d.icon_name,
                        "subdomains": [s.name for s in d.subdomains if s.is_active]
                    })
                return tree

        # In-memory canonical tree fallback
        return [
            {
                "code": code,
                "name": data["name"],
                "description": data["description"],
                "icon": data["icon"],
                "subdomains": data["subdomains"]
            }
            for code, data in CANONICAL_DOMAINS.items()
        ]


taxonomy_service = TaxonomyService()
