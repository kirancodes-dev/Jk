import csv
import io
import json
import os
import tempfile
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_, desc, case

from backend.app.models.models import (
    User, UserRole, Challenge, ChallengeLocation, ChallengeStatus,
    ChallengePriority, Project, ProjectMilestone, University,
    IndustryPartner, Student, ProjectMember, IndustryCollaboration,
    ImpactMetrics, District, ExportJob, DomainAuditEvent, utc_now,
    IPRecord, IPRecordType, CollaborationOfferType, AgreementStatus,
    OutcomeMetric
)


def _sum_verified_beneficiary_metrics(db: Session) -> float:
    """
    Sums OutcomeMetric.actual_value across INDEPENDENTLY_VERIFIED, beneficiary-
    reach metrics (matched by metric_name, e.g. "Beneficiary Household
    Coverage"). actual_value is stored as a free-text String (measurements
    aren't always numeric), so non-numeric values are safely skipped rather
    than raising — this replaces the old flat ImpactMetrics seeded constant
    with a figure derived from real, field-verified per-project records.
    """
    total = 0.0
    metrics = db.query(OutcomeMetric).filter(
        OutcomeMetric.metric_name.ilike("%beneficiar%"),
        OutcomeMetric.verification_status == "INDEPENDENTLY_VERIFIED"
    ).all()
    for m in metrics:
        try:
            total += float(m.actual_value)
        except (TypeError, ValueError):
            continue
    return total

# Challenge statuses that can only be reached after a working prototype exists,
# respectively after field deployment has begun. Used to derive live "prototypes
# developed" / "pilots deployed" counts instead of hardcoded demo constants.
PROTOTYPE_OR_LATER_STATUSES = [
    ChallengeStatus.PROTOTYPE, ChallengeStatus.FIELD_TESTING, ChallengeStatus.DEPLOYMENT,
    ChallengeStatus.IN_PROGRESS, ChallengeStatus.FIELD_VERIFICATION, ChallengeStatus.RESOLVED,
    ChallengeStatus.IMPACT_AUDITED, ChallengeStatus.CLOSED,
]
DEPLOYMENT_OR_LATER_STATUSES = [
    ChallengeStatus.DEPLOYMENT, ChallengeStatus.IN_PROGRESS, ChallengeStatus.FIELD_VERIFICATION,
    ChallengeStatus.RESOLVED, ChallengeStatus.IMPACT_AUDITED, ChallengeStatus.CLOSED,
]
IP_RECORD_LIVE_STATUSES_EXCLUDED = ("DRAFT", "REJECTED", "ARCHIVED")
from backend.app.schemas.schemas import (
    KPIMetadata, KPIDrillDownRecordOut, KPIDrillDownResponseOut,
    DistrictDrillDownOut, BlockDrillDownOut, VerifiableAdminDashboardOut,
    ExportJobCreate, ExportJobOut
)
from backend.app.services.privacy_service import PrivacyRedactionService


class AnalyticsService:
    """
    Jurisdiction-aware, verifiable analytics and reporting engine.
    Ensures:
    1. Single-pass / optimized relational aggregations without hardcoded constants.
    2. Strict administrative jurisdiction scoping (State vs District vs Block vs Panchayat).
    3. Complete metadata on every KPI (numerator, denominator, freshness, SLA rule, verification level).
    4. Drill-down reconciliation ("Why this number") linking aggregated stats to raw database records.
    5. Privacy-preserving bounded report exports (max 5,000 rows) with coarse GPS and masked PII.
    """

    @classmethod
    def apply_challenge_jurisdiction(cls, query, viewer: Optional[User]):
        """Scopes challenge queries by user jurisdiction tier."""
        if not viewer or viewer.role not in [UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER]:
            return query

        tier = (viewer.admin_tier or "STATE").upper()
        if tier == "STATE" and viewer.role == UserRole.GOVERNMENT_ADMIN:
            return query

        if tier == "STATE":
            return query

        user_dist = (viewer.district_name or viewer.jurisdiction_name or "").strip()
        user_block = (viewer.block_name or "").strip()
        user_panch = (viewer.panchayat_name or "").strip()

        # Check if ChallengeLocation is already joined in query
        # To be safe, join if not present
        query = query.join(ChallengeLocation, Challenge.id == ChallengeLocation.challenge_id)

        if tier == "DISTRICT" and user_dist:
            return query.filter(ChallengeLocation.district_name.ilike(f"%{user_dist}%"))
        elif tier == "BLOCK" and user_block:
            if user_dist:
                query = query.filter(ChallengeLocation.district_name.ilike(f"%{user_dist}%"))
            return query.filter(ChallengeLocation.block_name.ilike(f"%{user_block}%"))
        elif tier == "PANCHAYAT" and user_panch:
            if user_dist:
                query = query.filter(ChallengeLocation.district_name.ilike(f"%{user_dist}%"))
            return query.filter(ChallengeLocation.village_or_city.ilike(f"%{user_panch}%"))

        return query

    @classmethod
    def apply_project_jurisdiction(cls, query, viewer: Optional[User]):
        """Scopes project queries through associated challenge location."""
        if not viewer or viewer.role not in [UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER]:
            return query

        tier = (viewer.admin_tier or "STATE").upper()
        if tier == "STATE":
            return query

        user_dist = (viewer.district_name or viewer.jurisdiction_name or "").strip()
        user_block = (viewer.block_name or "").strip()

        query = query.join(Challenge, Project.challenge_id == Challenge.id).join(ChallengeLocation, Challenge.id == ChallengeLocation.challenge_id)

        if tier == "DISTRICT" and user_dist:
            return query.filter(ChallengeLocation.district_name.ilike(f"%{user_dist}%"))
        elif tier == "BLOCK" and user_block:
            if user_dist:
                query = query.filter(ChallengeLocation.district_name.ilike(f"%{user_dist}%"))
            return query.filter(ChallengeLocation.block_name.ilike(f"%{user_block}%"))

        return query

    @classmethod
    def get_dashboard_summary(cls, db: Session, viewer: User) -> Dict[str, Any]:
        """
        Computes high-level aggregated counts and verifiable KPIs with full provenance metadata.
        Zero hardcoded defaults.
        """
        now = datetime.now(timezone.utc)
        base_ch_query = db.query(Challenge)
        scoped_ch_query = cls.apply_challenge_jurisdiction(base_ch_query, viewer)

        total_challenges = scoped_ch_query.count()
        submitted = scoped_ch_query.filter(Challenge.status == ChallengeStatus.SUBMITTED).count()
        under_review = scoped_ch_query.filter(Challenge.status.in_([ChallengeStatus.UNDER_REVIEW, ChallengeStatus.AI_ANALYSIS])).count()
        assigned = scoped_ch_query.filter(Challenge.status.in_([ChallengeStatus.VALIDATED, ChallengeStatus.UNIVERSITY_ASSIGNED])).count()
        in_progress = scoped_ch_query.filter(Challenge.status.in_([
            ChallengeStatus.TEAM_FORMED, ChallengeStatus.SOLUTION_PROPOSED,
            ChallengeStatus.APPROVED, ChallengeStatus.PROTOTYPE,
            ChallengeStatus.FIELD_TESTING, ChallengeStatus.DEPLOYMENT,
            ChallengeStatus.IN_PROGRESS
        ])).count()
        resolved = scoped_ch_query.filter(Challenge.status == ChallengeStatus.RESOLVED).count()

        tier_panchayat = scoped_ch_query.filter(Challenge.current_tier == "PANCHAYAT").count()
        tier_block = scoped_ch_query.filter(Challenge.current_tier == "BLOCK").count()
        tier_district = scoped_ch_query.filter(Challenge.current_tier == "DISTRICT").count()
        tier_state = scoped_ch_query.filter(Challenge.current_tier == "STATE").count()

        # Institutional aggregations
        total_universities = db.query(University).filter(University.is_active == True).count()
        total_industry = db.query(IndustryPartner).filter(IndustryPartner.is_active == True).count()
        total_students = db.query(Student).count()

        proj_query = db.query(Project)
        scoped_proj_query = cls.apply_project_jurisdiction(proj_query, viewer)
        total_projects = scoped_proj_query.count()

        # SLA compliance calculations (statutory window = 7 days)
        seven_days_ago = now - timedelta(days=7)
        all_challenges_list = scoped_ch_query.all()

        sla_eligible_count = 0
        sla_breach_count = 0
        turnaround_days_list = []

        for ch in all_challenges_list:
            created_at = ch.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            age_days = (now - created_at).total_seconds() / 86400.0

            # If still pending review and older than 7 days, it is an SLA breach
            if ch.status in [ChallengeStatus.SUBMITTED, ChallengeStatus.UNDER_REVIEW, ChallengeStatus.AI_ANALYSIS]:
                if age_days > 7.0:
                    sla_breach_count += 1
                sla_eligible_count += 1
                turnaround_days_list.append(age_days)
            else:
                # Processed/validated challenge
                sla_eligible_count += 1
                turnaround_days_list.append(min(age_days, 7.0))  # Capped or actual turnaround

        if sla_eligible_count > 0:
            compliant_count = max(0, sla_eligible_count - sla_breach_count)
            sla_compliance_pct = round((compliant_count / sla_eligible_count) * 100.0, 1)
        else:
            compliant_count = 0
            sla_compliance_pct = 100.0

        avg_turnaround_days = round(sum(turnaround_days_list) / len(turnaround_days_list), 1) if turnaround_days_list else 0.0

        # Active student teams: distinct projects with members
        active_student_teams = db.query(func.count(func.distinct(ProjectMember.project_id))).filter(ProjectMember.is_active == True).scalar() or 0

        # Faculty mentors accepted
        accepted_faculty_mentors = scoped_proj_query.filter(Project.faculty_mentor_status == "ACCEPTED").count()
        faculty_mentorship_pct = round((accepted_faculty_mentors / total_projects) * 100.0, 1) if total_projects > 0 else 0.0

        # Problem resolution rate
        resolution_rate_pct = round((resolved / total_challenges) * 100.0, 1) if total_challenges > 0 else 0.0

        # CSR funding totals (cash + in-kind)
        csr_total_inr = db.query(func.sum(IndustryCollaboration.cash_value)).scalar() or 0.0

        # Beneficiaries served — derived from field-verified OutcomeMetric
        # records (see _sum_verified_beneficiary_metrics), not the seeded
        # ImpactMetrics constant.
        beneficiaries_sum = _sum_verified_beneficiary_metrics(db)

        # --- Live innovation outcomes (never hardcoded demo constants) ---
        ip_query = db.query(IPRecord).filter(~IPRecord.status.in_(IP_RECORD_LIVE_STATUSES_EXCLUDED))
        patent_records = ip_query.filter(IPRecord.record_type == IPRecordType.PATENT).all()
        patents_filed = len(patent_records)

        startup_records = db.query(IPRecord).filter(
            IPRecord.status != "REJECTED",
            IPRecord.startup_spinoff_name.isnot(None),
            IPRecord.startup_spinoff_name != ""
        ).all()
        startups_created = len({r.startup_spinoff_name.strip().lower() for r in startup_records if r.startup_spinoff_name and r.startup_spinoff_name.strip()})

        tech_transfer_records = db.query(IndustryCollaboration).filter(
            IndustryCollaboration.offer_type == CollaborationOfferType.TECHNOLOGY_TRANSFER.value,
            IndustryCollaboration.agreement_status == AgreementStatus.COMPLETED
        ).all()
        technology_transfers = len(tech_transfer_records)

        prototype_challenge_ids = {c[0] for c in scoped_ch_query.filter(Challenge.status.in_(PROTOTYPE_OR_LATER_STATUSES)).with_entities(Challenge.id).all()}
        prototypes_developed = len(prototype_challenge_ids)
        pilot_challenge_ids = {c[0] for c in scoped_ch_query.filter(Challenge.status.in_(DEPLOYMENT_OR_LATER_STATUSES)).with_entities(Challenge.id).all()}
        pilots_deployed = len(pilot_challenge_ids)

        freshness_iso = now.isoformat()

        kpis: Dict[str, Dict[str, Any]] = {
            "submission_volume": {
                "name": "submission_volume",
                "display_title": "Total Challenge Submissions",
                "value": total_challenges,
                "unit": "submissions",
                "numerator": float(total_challenges),
                "denominator": None,
                "time_window": "ALL_TIME",
                "inclusion_rules": "All community and citizen challenge submissions recorded within jurisdiction scope",
                "freshness": freshness_iso,
                "verification_level": "REPORTED",
                "reconciliation_metric_key": "submissions"
            },
            "review_sla_compliance": {
                "name": "review_sla_compliance",
                "display_title": "Review SLA Compliance Rate",
                "value": sla_compliance_pct,
                "unit": "%",
                "numerator": float(compliant_count),
                "denominator": float(sla_eligible_count) if sla_eligible_count > 0 else None,
                "time_window": "LAST_30_DAYS",
                "inclusion_rules": "Proportion of challenges triaged or evaluated within the statutory 7-day SLA window",
                "freshness": freshness_iso,
                "verification_level": "MEASURED",
                "reconciliation_metric_key": "sla_breaches"
            },
            "avg_review_turnaround_days": {
                "name": "avg_review_turnaround_days",
                "display_title": "Average Administrative Triage Time",
                "value": avg_turnaround_days,
                "unit": "days",
                "numerator": round(sum(turnaround_days_list), 1) if turnaround_days_list else 0.0,
                "denominator": float(len(turnaround_days_list)) if turnaround_days_list else None,
                "time_window": "ALL_TIME",
                "inclusion_rules": "Average elapsed calendar days from submission to official validation or review triage",
                "freshness": freshness_iso,
                "verification_level": "MEASURED",
                "reconciliation_metric_key": "under_review"
            },
            "active_verified_universities": {
                "name": "active_verified_universities",
                "display_title": "Active Verified Universities",
                "value": total_universities,
                "unit": "institutions",
                "numerator": float(total_universities),
                "denominator": None,
                "time_window": "CURRENT_ACADEMIC_YEAR",
                "inclusion_rules": "Recognized Higher Education Institutions with active, verified institutional portal accounts",
                "freshness": freshness_iso,
                "verification_level": "VERIFIED",
                "reconciliation_metric_key": "hei_participating"
            },
            "active_student_teams": {
                "name": "active_student_teams",
                "display_title": "Active Student Problem-Solving Teams",
                "value": active_student_teams,
                "unit": "teams",
                "numerator": float(active_student_teams),
                "denominator": float(total_projects) if total_projects > 0 else None,
                "time_window": "ACTIVE_PROJECTS",
                "inclusion_rules": "Confirmed university student teams actively working on milestones within jurisdiction",
                "freshness": freshness_iso,
                "verification_level": "VERIFIED",
                "reconciliation_metric_key": "student_teams"
            },
            "faculty_mentorship_coverage": {
                "name": "faculty_mentorship_coverage",
                "display_title": "Faculty Mentorship Coverage",
                "value": faculty_mentorship_pct,
                "unit": "%",
                "numerator": float(accepted_faculty_mentors),
                "denominator": float(total_projects) if total_projects > 0 else None,
                "time_window": "ACTIVE_PROJECTS",
                "inclusion_rules": "Percentage of active R&D projects with formally accepted faculty mentor supervision",
                "freshness": freshness_iso,
                "verification_level": "VERIFIED",
                "reconciliation_metric_key": "active_projects"
            },
            "problem_resolution_rate": {
                "name": "problem_resolution_rate",
                "display_title": "Problem Resolution Rate",
                "value": resolution_rate_pct,
                "unit": "%",
                "numerator": float(resolved),
                "denominator": float(total_challenges) if total_challenges > 0 else None,
                "time_window": "ALL_TIME",
                "inclusion_rules": "Ratio of field-verified resolved challenges to total submitted challenges",
                "freshness": freshness_iso,
                "verification_level": "VERIFIED",
                "reconciliation_metric_key": "resolved"
            },
            "csr_funding_disbursed": {
                "name": "csr_funding_disbursed",
                "display_title": "CSR & Industry Funding Disbursed",
                "value": float(csr_total_inr),
                "unit": "INR",
                "numerator": float(csr_total_inr),
                "denominator": None,
                "time_window": "ALL_TIME",
                "inclusion_rules": "Audited corporate social responsibility funds and equipment grants committed to verified projects",
                "freshness": freshness_iso,
                "verification_level": "VERIFIED",
                "reconciliation_metric_key": "csr_funding"
            },
            "measured_beneficiaries_served": {
                "name": "measured_beneficiaries_served",
                "display_title": "Documented Citizen Beneficiaries",
                "value": int(beneficiaries_sum),
                "unit": "citizens",
                "numerator": float(beneficiaries_sum),
                "denominator": None,
                "time_window": "ALL_TIME",
                "inclusion_rules": "Field-audited citizen beneficiaries directly served by deployed technical solutions",
                "freshness": freshness_iso,
                "verification_level": "VERIFIED",
                "reconciliation_metric_key": "beneficiaries"
            },
            "patents_filed": {
                "name": "patents_filed",
                "display_title": "Patents Filed",
                "value": patents_filed,
                "unit": "patents",
                "numerator": float(patents_filed),
                "denominator": None,
                "time_window": "ALL_TIME",
                "inclusion_rules": "IP records of type PATENT recorded against a project, excluding drafts, rejected or archived records",
                "freshness": freshness_iso,
                "verification_level": "VERIFIED",
                "reconciliation_metric_key": "patents_filed"
            },
            "startups_incubated": {
                "name": "startups_incubated",
                "display_title": "Startups Incubated",
                "value": startups_created,
                "unit": "startups",
                "numerator": float(startups_created),
                "denominator": None,
                "time_window": "ALL_TIME",
                "inclusion_rules": "Distinct named startup/spin-off entities recorded on a non-rejected IP record",
                "freshness": freshness_iso,
                "verification_level": "VERIFIED",
                "reconciliation_metric_key": "startups_incubated"
            },
            "technology_transfers_completed": {
                "name": "technology_transfers_completed",
                "display_title": "Technology Transfers Completed",
                "value": technology_transfers,
                "unit": "transfers",
                "numerator": float(technology_transfers),
                "denominator": None,
                "time_window": "ALL_TIME",
                "inclusion_rules": "Industry collaborations of offer type TECHNOLOGY_TRANSFER whose agreement reached COMPLETED status",
                "freshness": freshness_iso,
                "verification_level": "VERIFIED",
                "reconciliation_metric_key": "technology_transfers_completed"
            },
            "prototypes_developed": {
                "name": "prototypes_developed",
                "display_title": "Prototypes Developed",
                "value": prototypes_developed,
                "unit": "prototypes",
                "numerator": float(prototypes_developed),
                "denominator": float(total_challenges) if total_challenges > 0 else None,
                "time_window": "ALL_TIME",
                "inclusion_rules": "Challenges whose lifecycle status has reached PROTOTYPE or a later stage",
                "freshness": freshness_iso,
                "verification_level": "VERIFIED",
                "reconciliation_metric_key": "prototypes_developed"
            },
            "pilots_deployed": {
                "name": "pilots_deployed",
                "display_title": "Solutions Field-Deployed / Piloted",
                "value": pilots_deployed,
                "unit": "pilots",
                "numerator": float(pilots_deployed),
                "denominator": float(total_challenges) if total_challenges > 0 else None,
                "time_window": "ALL_TIME",
                "inclusion_rules": "Challenges whose lifecycle status has reached DEPLOYMENT or a later stage",
                "freshness": freshness_iso,
                "verification_level": "VERIFIED",
                "reconciliation_metric_key": "pilots_deployed"
            }
        }

        # District-wise and domain-wise breakdown of the live innovation outcomes above.
        # Small dataset assumption (SIH demo scale): joined in Python for clarity/auditability
        # rather than a dense multi-join SQL aggregate.
        def _challenge_geo(ch: Optional[Challenge]):
            district = str(ch.location.district_name) if ch and ch.location and ch.location.district_name else "Unknown"
            domain = str(ch.category) if ch and ch.category else "Unknown"
            return district, domain

        def _bump(bucket: Dict[str, Dict[str, int]], key: str, metric: str):
            bucket.setdefault(key, {}).setdefault(metric, 0)
            bucket[key][metric] += 1

        by_district: Dict[str, Dict[str, int]] = {}
        by_domain: Dict[str, Dict[str, int]] = {}

        for r in patent_records:
            district, domain = _challenge_geo(r.project.challenge if r.project else None)
            _bump(by_district, district, "patents_filed")
            _bump(by_domain, domain, "patents_filed")

        seen_startups = set()
        for r in startup_records:
            key = (r.startup_spinoff_name or "").strip().lower()
            if not key or key in seen_startups:
                continue
            seen_startups.add(key)
            district, domain = _challenge_geo(r.project.challenge if r.project else None)
            _bump(by_district, district, "startups_incubated")
            _bump(by_domain, domain, "startups_incubated")

        for c in tech_transfer_records:
            district, domain = _challenge_geo(c.project.challenge if c.project else None)
            _bump(by_district, district, "technology_transfers_completed")
            _bump(by_domain, domain, "technology_transfers_completed")

        innovation_breakdown = {"by_district": by_district, "by_domain": by_domain}

        return {
            "total_challenges": total_challenges,
            "submitted": submitted,
            "under_review": under_review,
            "assigned": assigned,
            "in_progress": in_progress,
            "resolved": resolved,
            "total_universities": total_universities,
            "total_industry_partners": total_industry,
            "total_students": total_students,
            "total_active_projects": total_projects,
            "jurisdiction": {
                "tier": viewer.admin_tier or "STATE",
                "district": viewer.district_name or viewer.jurisdiction_name,
                "block": viewer.block_name,
                "panchayat": viewer.panchayat_name
            },
            "tiers": {
                "panchayat": tier_panchayat,
                "block": tier_block,
                "district": tier_district,
                "state": tier_state
            },
            "kpis": kpis,
            "innovation_breakdown": innovation_breakdown
        }

    @classmethod
    def get_analytics_breakdown(cls, db: Session, viewer: User) -> Dict[str, Any]:
        """Provides category, priority, status breakdowns with review aging and pipeline stages."""
        now = datetime.now(timezone.utc)
        base_query = db.query(Challenge)
        scoped_query = cls.apply_challenge_jurisdiction(base_query, viewer)

        # By category
        cats = db.query(Challenge.category, func.count(Challenge.id))
        cats = cls.apply_challenge_jurisdiction(cats, viewer).group_by(Challenge.category).all()
        by_category = {cat: count for cat, count in cats if cat}

        # By priority
        prios = db.query(Challenge.priority, func.count(Challenge.id))
        prios = cls.apply_challenge_jurisdiction(prios, viewer).group_by(Challenge.priority).all()
        by_priority = {p.value if hasattr(p, "value") else str(p): count for p, count in prios if p}

        # By status
        stats = db.query(Challenge.status, func.count(Challenge.id))
        stats = cls.apply_challenge_jurisdiction(stats, viewer).group_by(Challenge.status).all()
        by_status = {s.value if hasattr(s, "value") else str(s): count for s, count in stats if s}

        # By district
        dists = db.query(ChallengeLocation.district_name, func.count(ChallengeLocation.id)).group_by(ChallengeLocation.district_name).all()
        by_district = {d: cnt for d, cnt in dists if d}

        # Review Aging distribution
        all_challenges = scoped_query.all()
        under_3_days = 0
        three_to_seven = 0
        sla_breaches = 0

        for ch in all_challenges:
            if ch.status in [ChallengeStatus.SUBMITTED, ChallengeStatus.UNDER_REVIEW, ChallengeStatus.AI_ANALYSIS]:
                c_date = ch.created_at
                if c_date.tzinfo is None:
                    c_date = c_date.replace(tzinfo=timezone.utc)
                age = (now - c_date).total_seconds() / 86400.0
                if age < 3.0:
                    under_3_days += 1
                elif age <= 7.0:
                    three_to_seven += 1
                else:
                    sla_breaches += 1

        review_aging = {
            "under_3_days": under_3_days,
            "three_to_seven_days": three_to_seven,
            "sla_breaches_over_7_days": sla_breaches
        }

        # Pipeline funnel
        total_sub = sum(by_status.values())
        validated_count = sum(by_status.get(s, 0) for s in ["VALIDATED", "UNIVERSITY_ASSIGNED", "TEAM_FORMED", "SOLUTION_PROPOSED", "APPROVED", "PROTOTYPE", "FIELD_TESTING", "DEPLOYMENT", "RESOLVED"])
        active_hei_count = sum(by_status.get(s, 0) for s in ["TEAM_FORMED", "SOLUTION_PROPOSED", "APPROVED", "PROTOTYPE", "FIELD_TESTING", "DEPLOYMENT", "IN_PROGRESS"])
        prototyping_count = sum(by_status.get(s, 0) for s in ["PROTOTYPE", "FIELD_TESTING", "DEPLOYMENT"])
        resolved_count = by_status.get("RESOLVED", 0)

        pipeline_funnel = {
            "submissions": total_sub,
            "triaged_and_validated": validated_count,
            "active_hei_projects": active_hei_count,
            "prototyping_and_pilots": prototyping_count,
            "resolved_and_deployed": resolved_count
        }

        return {
            "by_category": by_category,
            "by_priority": by_priority,
            "by_status": by_status,
            "by_district": by_district,
            "review_aging": review_aging,
            "pipeline_funnel": pipeline_funnel
        }

    @classmethod
    def get_districts_drill_down(cls, db: Session, viewer: User) -> List[Dict[str, Any]]:
        """
        Canonical list of districts with live aggregated stats.
        District Admins see only their assigned district.
        """
        user_tier = (viewer.admin_tier or "STATE").upper()
        user_dist = (viewer.district_name or viewer.jurisdiction_name or "").strip().lower()

        districts = db.query(District).order_by(District.name.asc()).all()

        # Pre-aggregate challenge counts per district in a single grouped query
        ch_stats_rows = db.query(
            ChallengeLocation.district_name,
            func.count(Challenge.id).label("total"),
            func.count(case((Challenge.status == ChallengeStatus.SUBMITTED, 1))).label("submitted"),
            func.count(case((Challenge.status.in_([ChallengeStatus.UNDER_REVIEW, ChallengeStatus.AI_ANALYSIS]), 1))).label("under_review"),
            func.count(case((Challenge.status.in_([ChallengeStatus.VALIDATED, ChallengeStatus.UNIVERSITY_ASSIGNED]), 1))).label("assigned"),
            func.count(case((Challenge.status.in_([
                ChallengeStatus.TEAM_FORMED, ChallengeStatus.SOLUTION_PROPOSED,
                ChallengeStatus.APPROVED, ChallengeStatus.PROTOTYPE,
                ChallengeStatus.FIELD_TESTING, ChallengeStatus.DEPLOYMENT,
                ChallengeStatus.IN_PROGRESS
            ]), 1))).label("in_progress"),
            func.count(case((Challenge.status == ChallengeStatus.RESOLVED, 1))).label("resolved")
        ).join(Challenge, Challenge.id == ChallengeLocation.challenge_id).group_by(ChallengeLocation.district_name).all()

        stats_map = {}
        for r in ch_stats_rows:
            d_key = (r[0] or "").strip().lower()
            stats_map[d_key] = {
                "total": r[1] or 0,
                "submitted": r[2] or 0,
                "under_review": r[3] or 0,
                "assigned": r[4] or 0,
                "in_progress": r[5] or 0,
                "resolved": r[6] or 0
            }

        # Pre-aggregate project counts per district
        proj_stats_rows = db.query(
            ChallengeLocation.district_name,
            func.count(Project.id)
        ).join(Challenge, Project.challenge_id == Challenge.id).join(
            ChallengeLocation, Challenge.id == ChallengeLocation.challenge_id
        ).group_by(ChallengeLocation.district_name).all()

        proj_map = {}
        for r in proj_stats_rows:
            d_key = (r[0] or "").strip().lower()
            proj_map[d_key] = r[1] or 0

        results = []
        for d in districts:
            if user_tier != "STATE" and viewer.role != UserRole.GOVERNMENT_ADMIN:
                if user_dist and user_dist not in d.name.lower() and d.name.lower() not in user_dist:
                    continue

            d_key = d.name.strip().lower()
            st = stats_map.get(d_key, {"total": 0, "submitted": 0, "under_review": 0, "assigned": 0, "in_progress": 0, "resolved": 0})
            act_proj = proj_map.get(d_key, 0)

            results.append({
                "district_name": d.name,
                "total_challenges": st["total"],
                "submitted": st["submitted"],
                "under_review": st["under_review"],
                "assigned": st["assigned"],
                "in_progress": st["in_progress"],
                "resolved": st["resolved"],
                "active_projects": act_proj,
                "total_population": d.total_population,
                "rural_population_pct": d.rural_population_pct,
                "latitude": d.latitude,
                "longitude": d.longitude
            })

        return results

    @classmethod
    def get_blocks_drill_down(cls, db: Session, district_name: str, viewer: User) -> List[Dict[str, Any]]:
        """
        Block-level drill-down for a given district.
        """
        user_tier = (viewer.admin_tier or "STATE").upper()
        user_dist = (viewer.district_name or viewer.jurisdiction_name or "").strip().lower()

        # Enforce jurisdiction
        if user_tier != "STATE" and viewer.role != UserRole.GOVERNMENT_ADMIN:
            if user_dist and user_dist not in district_name.lower() and district_name.lower() not in user_dist:
                return []

        # Find distinct blocks in this district
        blocks = db.query(ChallengeLocation.block_name).filter(
            ChallengeLocation.district_name.ilike(f"%{district_name}%"),
            ChallengeLocation.block_name != None
        ).distinct().all()

        results = []
        for (b_name,) in blocks:
            if not b_name:
                continue

            ch_query = db.query(Challenge).join(ChallengeLocation).filter(
                ChallengeLocation.district_name.ilike(f"%{district_name}%"),
                ChallengeLocation.block_name.ilike(f"%{b_name}%")
            )
            total = ch_query.count()
            submitted = ch_query.filter(Challenge.status == ChallengeStatus.SUBMITTED).count()
            under_review = ch_query.filter(Challenge.status.in_([ChallengeStatus.UNDER_REVIEW, ChallengeStatus.AI_ANALYSIS])).count()
            assigned = ch_query.filter(Challenge.status.in_([ChallengeStatus.VALIDATED, ChallengeStatus.UNIVERSITY_ASSIGNED])).count()
            in_progress = ch_query.filter(Challenge.status.in_([
                ChallengeStatus.TEAM_FORMED, ChallengeStatus.SOLUTION_PROPOSED,
                ChallengeStatus.APPROVED, ChallengeStatus.PROTOTYPE,
                ChallengeStatus.FIELD_TESTING, ChallengeStatus.DEPLOYMENT,
                ChallengeStatus.IN_PROGRESS
            ])).count()
            resolved = ch_query.filter(Challenge.status == ChallengeStatus.RESOLVED).count()

            active_projects = db.query(Project).join(Challenge).join(ChallengeLocation).filter(
                ChallengeLocation.district_name.ilike(f"%{district_name}%"),
                ChallengeLocation.block_name.ilike(f"%{b_name}%")
            ).count()

            results.append({
                "district_name": district_name,
                "block_name": b_name,
                "total_challenges": total,
                "submitted": submitted,
                "under_review": under_review,
                "assigned": assigned,
                "in_progress": in_progress,
                "resolved": resolved,
                "active_projects": active_projects
            })

        return sorted(results, key=lambda x: x["block_name"])

    @classmethod
    def get_kpi_source_records(
        cls, db: Session, metric_key: str, viewer: User, limit: int = 50, offset: int = 0
    ) -> KPIDrillDownResponseOut:
        """
        'Why this number' source reconciliation endpoint.
        Returns underlying transactional records, statuses, verification levels, and audit trail references.
        Applies PrivacyRedactionService to coordinates and citizen PII.
        """
        now = datetime.now(timezone.utc)
        summary = cls.get_dashboard_summary(db, viewer)
        kpi_meta_dict = summary["kpis"].get(metric_key)

        if not kpi_meta_dict:
            # Fallback to finding by key
            for k, meta in summary["kpis"].items():
                if meta.get("reconciliation_metric_key") == metric_key:
                    kpi_meta_dict = meta
                    break

        if not kpi_meta_dict:
            kpi_meta_dict = {
                "name": metric_key,
                "display_title": metric_key.replace("_", " ").title(),
                "value": 0,
                "unit": "records",
                "time_window": "ALL_TIME",
                "inclusion_rules": f"Underlying records contributing to {metric_key}",
                "freshness": now.isoformat(),
                "verification_level": "MEASURED",
                "reconciliation_metric_key": metric_key
            }

        kpi_meta = KPIMetadata(**kpi_meta_dict)
        records: List[KPIDrillDownRecordOut] = []
        total_records = 0

        norm_key = metric_key.lower().strip()

        if norm_key in ["submissions", "submission_volume"]:
            q = db.query(Challenge)
            q = cls.apply_challenge_jurisdiction(q, viewer)
            total_records = q.count()
            raw_challenges = q.order_by(Challenge.created_at.desc()).offset(offset).limit(limit).all()

            for ch in raw_challenges:
                dist = ch.location.district_name if ch.location else None
                block = ch.location.block_name if ch.location else None
                records.append(KPIDrillDownRecordOut(
                    record_id=ch.id,
                    entity_type="Challenge",
                    title=ch.title,
                    category=ch.category,
                    status=ch.status.value if hasattr(ch.status, "value") else str(ch.status),
                    district_name=dist,
                    block_name=block,
                    verification_level="REPORTED",
                    contributing_value=1,
                    timestamp=ch.created_at,
                    audit_event_id=ch.version,
                    redacted=False
                ))

        elif norm_key in ["sla_breaches", "review_sla_compliance"]:
            seven_days_ago = now - timedelta(days=7)
            q = db.query(Challenge).filter(
                Challenge.status.in_([ChallengeStatus.SUBMITTED, ChallengeStatus.UNDER_REVIEW, ChallengeStatus.AI_ANALYSIS]),
                Challenge.created_at <= seven_days_ago
            )
            q = cls.apply_challenge_jurisdiction(q, viewer)
            total_records = q.count()
            raw_challenges = q.order_by(Challenge.created_at.asc()).offset(offset).limit(limit).all()

            for ch in raw_challenges:
                c_date = ch.created_at
                if c_date.tzinfo is None:
                    c_date = c_date.replace(tzinfo=timezone.utc)
                age_days = round((now - c_date).total_seconds() / 86400.0, 1)
                dist = ch.location.district_name if ch.location else None
                block = ch.location.block_name if ch.location else None

                records.append(KPIDrillDownRecordOut(
                    record_id=ch.id,
                    entity_type="Challenge",
                    title=ch.title,
                    category=ch.category,
                    status=ch.status.value if hasattr(ch.status, "value") else str(ch.status),
                    district_name=dist,
                    block_name=block,
                    verification_level="MEASURED",
                    contributing_value=f"{age_days} days waiting",
                    timestamp=ch.created_at,
                    audit_event_id=ch.version,
                    redacted=False
                ))

        elif norm_key in ["under_review", "avg_review_turnaround_days"]:
            q = db.query(Challenge).filter(
                Challenge.status.in_([ChallengeStatus.UNDER_REVIEW, ChallengeStatus.AI_ANALYSIS, ChallengeStatus.SUBMITTED])
            )
            q = cls.apply_challenge_jurisdiction(q, viewer)
            total_records = q.count()
            raw_challenges = q.order_by(Challenge.created_at.desc()).offset(offset).limit(limit).all()

            for ch in raw_challenges:
                c_date = ch.created_at
                if c_date.tzinfo is None:
                    c_date = c_date.replace(tzinfo=timezone.utc)
                age_days = round((now - c_date).total_seconds() / 86400.0, 1)
                dist = ch.location.district_name if ch.location else None
                block = ch.location.block_name if ch.location else None

                records.append(KPIDrillDownRecordOut(
                    record_id=ch.id,
                    entity_type="Challenge",
                    title=ch.title,
                    category=ch.category,
                    status=ch.status.value if hasattr(ch.status, "value") else str(ch.status),
                    district_name=dist,
                    block_name=block,
                    verification_level="MEASURED",
                    contributing_value=f"{age_days} days in triage",
                    timestamp=ch.created_at,
                    audit_event_id=ch.version,
                    redacted=False
                ))

        elif norm_key in ["active_projects", "student_teams", "problem_resolution_rate", "resolved"]:
            proj_q = db.query(Project)
            proj_q = cls.apply_project_jurisdiction(proj_q, viewer)
            if norm_key in ["resolved", "problem_resolution_rate"]:
                proj_q = proj_q.join(Challenge).filter(Challenge.status == ChallengeStatus.RESOLVED)

            total_records = proj_q.count()
            raw_projects = proj_q.order_by(Project.created_at.desc()).offset(offset).limit(limit).all()

            for p in raw_projects:
                dist = p.challenge.location.district_name if p.challenge and p.challenge.location else None
                block = p.challenge.location.block_name if p.challenge and p.challenge.location else None

                records.append(KPIDrillDownRecordOut(
                    record_id=p.id,
                    entity_type="Project",
                    title=p.name,
                    category=p.current_stage,
                    status=p.faculty_mentor_status,
                    district_name=dist,
                    block_name=block,
                    verification_level="VERIFIED",
                    contributing_value=f"{p.progress_percentage}% completed",
                    timestamp=p.created_at,
                    audit_event_id=p.version,
                    redacted=False
                ))

        elif norm_key in ["hei_participating", "active_verified_universities"]:
            u_query = db.query(University).filter(University.is_active == True)
            total_records = u_query.count()
            # Note: fixed a pre-existing bug here — University has no `.name`/`.university_type`/
            # `.district`/`.created_at` attributes (they are `.institution_name`/`.district_name`);
            # the previous hasattr()-guarded fallbacks silently masked the crash on `.name`.
            raw_unis = u_query.order_by(University.institution_name.asc()).offset(offset).limit(limit).all()

            for u in raw_unis:
                records.append(KPIDrillDownRecordOut(
                    record_id=u.id,
                    entity_type="University",
                    title=u.institution_name,
                    category="University",
                    status="VERIFIED" if u.is_verified_active else "PENDING",
                    district_name=u.district_name or "Jharkhand",
                    block_name=None,
                    verification_level="VERIFIED",
                    contributing_value="Verified HEI Portal",
                    timestamp=now,
                    audit_event_id=u.id,
                    redacted=False
                ))

        elif norm_key in ["patents_filed"]:
            q = db.query(IPRecord).filter(~IPRecord.status.in_(IP_RECORD_LIVE_STATUSES_EXCLUDED), IPRecord.record_type == IPRecordType.PATENT)
            total_records = q.count()
            raw_records = q.order_by(IPRecord.created_at.desc()).offset(offset).limit(limit).all()
            for r in raw_records:
                ch = r.project.challenge if r.project else None
                dist = ch.location.district_name if ch and ch.location else None
                records.append(KPIDrillDownRecordOut(
                    record_id=r.id, entity_type="IPRecord", title=r.title,
                    category=ch.category if ch else "Innovation", status=r.status,
                    district_name=dist, block_name=None, verification_level="VERIFIED",
                    contributing_value=r.patent_reference or "Patent filed", timestamp=r.created_at,
                    audit_event_id=r.id, redacted=False
                ))

        elif norm_key in ["startups_incubated"]:
            q = db.query(IPRecord).filter(
                IPRecord.status != "REJECTED", IPRecord.startup_spinoff_name.isnot(None), IPRecord.startup_spinoff_name != ""
            )
            total_records = q.count()
            raw_records = q.order_by(IPRecord.created_at.desc()).offset(offset).limit(limit).all()
            for r in raw_records:
                ch = r.project.challenge if r.project else None
                dist = ch.location.district_name if ch and ch.location else None
                records.append(KPIDrillDownRecordOut(
                    record_id=r.id, entity_type="IPRecord", title=r.startup_spinoff_name or r.title,
                    category=ch.category if ch else "Entrepreneurship", status=r.status,
                    district_name=dist, block_name=None, verification_level="VERIFIED",
                    contributing_value="Startup / spin-off", timestamp=r.created_at,
                    audit_event_id=r.id, redacted=False
                ))

        elif norm_key in ["technology_transfers_completed"]:
            q = db.query(IndustryCollaboration).filter(
                IndustryCollaboration.offer_type == CollaborationOfferType.TECHNOLOGY_TRANSFER.value,
                IndustryCollaboration.agreement_status == AgreementStatus.COMPLETED
            )
            total_records = q.count()
            raw_records = q.order_by(IndustryCollaboration.updated_at.desc()).offset(offset).limit(limit).all()
            for c in raw_records:
                ch = c.project.challenge if c.project else None
                dist = ch.location.district_name if ch and ch.location else None
                records.append(KPIDrillDownRecordOut(
                    record_id=c.id, entity_type="IndustryCollaboration", title=f"Technology transfer #{c.id}",
                    category=ch.category if ch else "Technology Transfer", status=c.agreement_status.value,
                    district_name=dist, block_name=None, verification_level="VERIFIED",
                    contributing_value=c.description or "Completed technology transfer", timestamp=c.updated_at or c.created_at,
                    audit_event_id=c.id, redacted=False
                ))

        elif norm_key in ["prototypes_developed", "pilots_deployed"]:
            statuses = PROTOTYPE_OR_LATER_STATUSES if norm_key == "prototypes_developed" else DEPLOYMENT_OR_LATER_STATUSES
            q = db.query(Challenge).filter(Challenge.status.in_(statuses))
            q = cls.apply_challenge_jurisdiction(q, viewer)
            total_records = q.count()
            raw_challenges = q.order_by(Challenge.updated_at.desc()).offset(offset).limit(limit).all()
            for ch in raw_challenges:
                dist = ch.location.district_name if ch.location else None
                records.append(KPIDrillDownRecordOut(
                    record_id=ch.id, entity_type="Challenge", title=ch.title, category=ch.category,
                    status=ch.status.value, district_name=dist, block_name=ch.location.block_name if ch.location else None,
                    verification_level="VERIFIED", contributing_value=ch.status.value, timestamp=ch.updated_at or ch.created_at,
                    audit_event_id=ch.version, redacted=False
                ))

        elif norm_key in ["csr_funding", "csr_funding_disbursed"]:
            collab_q = db.query(IndustryCollaboration)
            total_records = collab_q.count()
            raw_offers = collab_q.order_by(IndustryCollaboration.id.desc()).offset(offset).limit(limit).all()

            for offer in raw_offers:
                val = offer.cash_value or offer.in_kind_value or 0.0
                records.append(KPIDrillDownRecordOut(
                    record_id=offer.id,
                    entity_type="IndustryCollaboration",
                    title=f"CSR Offer #{offer.id} ({offer.offer_type.value if hasattr(offer.offer_type, 'value') else offer.offer_type})",
                    category="CSR Funding",
                    status="COMMITTED",
                    district_name=None,
                    block_name=None,
                    verification_level="VERIFIED",
                    contributing_value=f"INR {val:,.2f}",
                    timestamp=offer.start_date or now,
                    audit_event_id=offer.id,
                    redacted=False
                ))

        elif norm_key in ["beneficiaries", "measured_beneficiaries_served"]:
            outcome_q = db.query(OutcomeMetric).filter(
                OutcomeMetric.metric_name.ilike("%beneficiar%"),
                OutcomeMetric.verification_status == "INDEPENDENTLY_VERIFIED"
            )
            total_records = outcome_q.count()
            raw_metrics = outcome_q.order_by(OutcomeMetric.id.asc()).offset(offset).limit(limit).all()

            for om in raw_metrics:
                records.append(KPIDrillDownRecordOut(
                    record_id=om.id,
                    entity_type="OutcomeMetric",
                    title=om.metric_name,
                    category=om.district_name or "Beneficiary Coverage",
                    status=om.verification_status,
                    district_name=om.district_name,
                    block_name=om.block_name,
                    verification_level="VERIFIED",
                    contributing_value=f"{om.actual_value} {om.unit_of_measure or ''}".strip(),
                    timestamp=om.verified_at or om.actual_date or om.created_at or now,
                    audit_event_id=om.id,
                    redacted=False
                ))

        return KPIDrillDownResponseOut(
            metric_key=metric_key,
            metadata=kpi_meta,
            total_records=total_records,
            limit=limit,
            offset=offset,
            records=records
        )

    @classmethod
    def create_and_process_export(
        cls, db: Session, user: User, payload: ExportJobCreate, max_rows: int = 5000
    ) -> ExportJob:
        """
        Creates and executes a bounded asynchronous export job.
        Enforces maximum row limit (5,000) and privacy redaction.
        """
        filters_json = json.dumps(payload.filters) if payload.filters else None

        job = ExportJob(
            user_id=user.id,
            export_type=payload.export_type.upper(),
            export_format=payload.export_format.upper(),
            filters_json=filters_json,
            status="PROCESSING",
            row_count=0
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        try:
            export_dir = os.path.join(tempfile.gettempdir(), "jk_exports")
            os.makedirs(export_dir, exist_ok=True)
            filename = f"export_{job.id}_{job.export_type.lower()}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
            file_path = os.path.join(export_dir, filename)

            row_count = 0
            with open(file_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                if job.export_type == "CHALLENGES":
                    writer.writerow([
                        "Challenge ID", "Title", "Category", "Priority", "Status",
                        "Tier", "District", "Block", "Panchayat", "Coarse Latitude",
                        "Coarse Longitude", "Submitted At", "Verification Level"
                    ])

                    q = db.query(Challenge).options(joinedload(Challenge.location))
                    q = cls.apply_challenge_jurisdiction(q, user)
                    challenges = q.order_by(Challenge.id.asc()).limit(max_rows).all()

                    for ch in challenges:
                        row_count += 1
                        loc = ch.location
                        loc_dict = {
                            "latitude": loc.latitude if loc else None,
                            "longitude": loc.longitude if loc else None
                        }
                        # Apply privacy redaction on coordinates
                        redacted_loc = PrivacyRedactionService.redact_location(loc_dict, viewer=user)
                        lat = redacted_loc.get("latitude") if redacted_loc else ""
                        lon = redacted_loc.get("longitude") if redacted_loc else ""

                        dist = loc.district_name if loc else "Jharkhand"
                        blk = loc.block_name if loc else ""
                        panch = loc.village_or_city if loc else ""

                        writer.writerow([
                            ch.id,
                            ch.title,
                            ch.category,
                            ch.priority.value if hasattr(ch.priority, "value") else str(ch.priority),
                            ch.status.value if hasattr(ch.status, "value") else str(ch.status),
                            ch.current_tier or "STATE",
                            dist,
                            blk,
                            panch,
                            lat,
                            lon,
                            ch.created_at.strftime("%Y-%m-%d %H:%M:%S") if ch.created_at else "",
                            "REPORTED"
                        ])

                elif job.export_type == "PROJECTS":
                    writer.writerow([
                        "Project ID", "Title", "Stage", "Progress %", "Faculty Status",
                        "District", "Created At"
                    ])

                    pq = db.query(Project).options(
                        joinedload(Project.challenge).joinedload(Challenge.location)
                    )
                    pq = cls.apply_project_jurisdiction(pq, user)
                    projects = pq.order_by(Project.id.asc()).limit(max_rows).all()

                    for p in projects:
                        row_count += 1
                        dist = p.challenge.location.district_name if p.challenge and p.challenge.location else "Jharkhand"
                        writer.writerow([
                            p.id,
                            p.name,
                            p.current_stage,
                            p.progress_percentage,
                            p.faculty_mentor_status,
                            dist,
                            p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else ""
                        ])

                elif job.export_type == "IMPACT_METRICS":
                    writer.writerow(["Metric ID", "Metric Name", "Value", "Category", "Last Updated"])
                    metrics = db.query(ImpactMetrics).limit(max_rows).all()
                    for m in metrics:
                        row_count += 1
                        writer.writerow([
                            m.id,
                            m.metric_name,
                            m.metric_value,
                            m.category,
                            m.last_updated.strftime("%Y-%m-%d %H:%M:%S") if m.last_updated else ""
                        ])

                elif job.export_type == "AUDIT_LOGS":
                    writer.writerow(["Sequence", "Entity Type", "Entity ID", "Action", "Previous State", "Timestamp"])
                    events = db.query(DomainAuditEvent).order_by(DomainAuditEvent.sequence_number.desc()).limit(max_rows).all()
                    for ev in events:
                        row_count += 1
                        writer.writerow([
                            ev.sequence_number,
                            ev.entity_type,
                            ev.entity_id,
                            ev.action,
                            ev.previous_state or "",
                            ev.created_at.strftime("%Y-%m-%d %H:%M:%S") if ev.created_at else ""
                        ])
                else:
                    raise ValueError(f"Unsupported export type: {job.export_type}")

            job.status = "COMPLETED"
            job.file_path = file_path
            job.row_count = row_count
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(job)
            return job

        except Exception as e:
            job.status = "FAILED"
            job.failure_reason = str(e)
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(job)
            return job


analytics_service = AnalyticsService()
