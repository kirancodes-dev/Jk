"""stage7_industry_csr_ip_workflow

Revision ID: c7f4e91b3a5d
Revises: a58f3d9c21e7
Create Date: 2026-09-23 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7f4e91b3a5d'
down_revision: Union[str, Sequence[str], None] = 'a58f3d9c21e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # 1. Industry partners: verified identity & capability profile
    if "industry_partners" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("industry_partners")]
        with op.batch_alter_table("industry_partners", schema=None) as batch_op:
            if "organization_profile_id" not in existing_cols:
                batch_op.add_column(sa.Column("organization_profile_id", sa.Integer(), sa.ForeignKey("organization_profiles.id", name="fk_industry_org_profile"), nullable=True))
            if "partner_type" not in existing_cols:
                batch_op.add_column(sa.Column("partner_type", sa.String(50), nullable=False, server_default="INDUSTRY"))
            if "legal_identity" not in existing_cols:
                batch_op.add_column(sa.Column("legal_identity", sa.String(255), nullable=True))
            if "registration_number" not in existing_cols:
                batch_op.add_column(sa.Column("registration_number", sa.String(100), nullable=True))
            if "csr_eligible" not in existing_cols:
                batch_op.add_column(sa.Column("csr_eligible", sa.Boolean(), nullable=False, server_default="false"))
            if "authorized_representative_name" not in existing_cols:
                batch_op.add_column(sa.Column("authorized_representative_name", sa.String(255), nullable=True))
            if "authorized_representative_designation" not in existing_cols:
                batch_op.add_column(sa.Column("authorized_representative_designation", sa.String(150), nullable=True))
            if "domains" not in existing_cols:
                batch_op.add_column(sa.Column("domains", sa.Text(), nullable=True))
            if "capacity_description" not in existing_cols:
                batch_op.add_column(sa.Column("capacity_description", sa.Text(), nullable=True))
            if "geographic_coverage" not in existing_cols:
                batch_op.add_column(sa.Column("geographic_coverage", sa.Text(), nullable=True))
            if "compliance_documents" not in existing_cols:
                batch_op.add_column(sa.Column("compliance_documents", sa.Text(), nullable=True))
            if "is_active" not in existing_cols:
                batch_op.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"))
            if "suspended_reason" not in existing_cols:
                batch_op.add_column(sa.Column("suspended_reason", sa.Text(), nullable=True))
            if "notification_preferences" not in existing_cols:
                batch_op.add_column(sa.Column("notification_preferences", sa.Text(), nullable=True))
            if "version" not in existing_cols:
                batch_op.add_column(sa.Column("version", sa.Integer(), nullable=False, server_default="1"))

        # Backfill linkage to existing organization profiles for already-registered partners
        if "organization_profiles" in existing_tables:
            op.execute(sa.text(
                "UPDATE industry_partners SET organization_profile_id = ("
                "  SELECT op.id FROM organization_profiles op "
                "  JOIN users u ON u.id = op.user_id "
                "  WHERE u.id = industry_partners.user_id LIMIT 1"
                ") WHERE organization_profile_id IS NULL"
            ))

    # 2. Industry collaborations: structured agreement workflow
    if "industry_collaborations" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("industry_collaborations")]
        with op.batch_alter_table("industry_collaborations", schema=None) as batch_op:
            if "agreement_status" not in existing_cols:
                batch_op.add_column(sa.Column("agreement_status", sa.String(50), nullable=False, server_default="OFFERED"))
            if "scope" not in existing_cols:
                batch_op.add_column(sa.Column("scope", sa.Text(), nullable=True))
            if "personnel" not in existing_cols:
                batch_op.add_column(sa.Column("personnel", sa.Text(), nullable=True))
            if "in_kind_value" not in existing_cols:
                batch_op.add_column(sa.Column("in_kind_value", sa.Float(), nullable=True))
            if "cash_value" not in existing_cols:
                batch_op.add_column(sa.Column("cash_value", sa.Float(), nullable=True))
            if "currency" not in existing_cols:
                batch_op.add_column(sa.Column("currency", sa.String(10), nullable=False, server_default="INR"))
            if "start_date" not in existing_cols:
                batch_op.add_column(sa.Column("start_date", sa.DateTime(), nullable=True))
            if "end_date" not in existing_cols:
                batch_op.add_column(sa.Column("end_date", sa.DateTime(), nullable=True))
            if "dependencies" not in existing_cols:
                batch_op.add_column(sa.Column("dependencies", sa.Text(), nullable=True))
            if "data_access_level" not in existing_cols:
                batch_op.add_column(sa.Column("data_access_level", sa.String(50), nullable=True, server_default="RESTRICTED"))
            if "safety_requirements" not in existing_cols:
                batch_op.add_column(sa.Column("safety_requirements", sa.Text(), nullable=True))
            if "deliverables" not in existing_cols:
                batch_op.add_column(sa.Column("deliverables", sa.Text(), nullable=True))
            if "milestone_id" not in existing_cols:
                batch_op.add_column(sa.Column("milestone_id", sa.Integer(), sa.ForeignKey("project_milestones.id", name="fk_collab_milestone"), nullable=True))
            if "reviewed_by_user_id" not in existing_cols:
                batch_op.add_column(sa.Column("reviewed_by_user_id", sa.Integer(), sa.ForeignKey("users.id", name="fk_collab_reviewed_by"), nullable=True))
            if "review_notes" not in existing_cols:
                batch_op.add_column(sa.Column("review_notes", sa.Text(), nullable=True))
            if "conflict_check_notes" not in existing_cols:
                batch_op.add_column(sa.Column("conflict_check_notes", sa.Text(), nullable=True))
            if "conflict_declared" not in existing_cols:
                batch_op.add_column(sa.Column("conflict_declared", sa.Boolean(), nullable=False, server_default="false"))
            if "mou_evidence_object_id" not in existing_cols:
                batch_op.add_column(sa.Column("mou_evidence_object_id", sa.String(64), nullable=True))
            if "accepted_at" not in existing_cols:
                batch_op.add_column(sa.Column("accepted_at", sa.DateTime(), nullable=True))
            if "terminated_reason" not in existing_cols:
                batch_op.add_column(sa.Column("terminated_reason", sa.Text(), nullable=True))
            if "version" not in existing_cols:
                batch_op.add_column(sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
            if "updated_at" not in existing_cols:
                batch_op.add_column(sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True))

        # Backfill agreement_status from legacy free-text status (dialect-portable: LOWER()+LIKE
        # works identically on PostgreSQL and SQLite, unlike PostgreSQL-only ILIKE).
        op.execute(sa.text(
            "UPDATE industry_collaborations SET agreement_status = CASE "
            "  WHEN LOWER(status) = 'active' THEN 'ACTIVE' "
            "  WHEN LOWER(status) = 'accepted' THEN 'ACCEPTED' "
            "  WHEN LOWER(status) = 'completed' THEN 'COMPLETED' "
            "  ELSE 'OFFERED' END "
            "WHERE agreement_status IS NULL OR agreement_status = 'OFFERED'"
        ))

    # 3. Funding records (CSR / funding governance ledger)
    if "funding_records" not in existing_tables:
        op.create_table(
            "funding_records",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column("collaboration_id", sa.Integer(), sa.ForeignKey("industry_collaborations.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False, index=True),
            sa.Column("industry_id", sa.Integer(), sa.ForeignKey("industry_partners.id"), nullable=False, index=True),
            sa.Column("milestone_id", sa.Integer(), sa.ForeignKey("project_milestones.id"), nullable=True),
            sa.Column("budget_line_item", sa.String(255), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False),
            sa.Column("currency", sa.String(10), nullable=False, server_default="INR"),
            sa.Column("sanction_authority", sa.String(255), nullable=True),
            sa.Column("agreement_reference", sa.String(255), nullable=True),
            sa.Column("disbursement_schedule", sa.Text(), nullable=True),
            sa.Column("hold_state", sa.String(50), nullable=False, server_default="PENDING", index=True),
            sa.Column("receipt_evidence_object_id", sa.String(64), nullable=True),
            sa.Column("utilization_notes", sa.Text(), nullable=True),
            sa.Column("payment_integration_reference", sa.String(255), nullable=True),
            sa.Column("settlement_status", sa.String(50), nullable=False, server_default="PENDING_EXTERNAL_CONFIRMATION"),
            sa.Column("payment_confirmed", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("approved_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("approved_at", sa.DateTime(), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        )

    # 4. IP & technology transfer records
    if "ip_records" not in existing_tables:
        op.create_table(
            "ip_records",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False, index=True),
            sa.Column("collaboration_id", sa.Integer(), sa.ForeignKey("industry_collaborations.id"), nullable=True),
            sa.Column("record_type", sa.String(50), nullable=False),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("background_ip_notes", sa.Text(), nullable=True),
            sa.Column("foreground_ip_notes", sa.Text(), nullable=True),
            sa.Column("ownership", sa.String(50), nullable=False, server_default="JOINT"),
            sa.Column("license_terms", sa.Text(), nullable=True),
            sa.Column("contributor_attributions", sa.Text(), nullable=True),
            sa.Column("publication_restrictions", sa.Text(), nullable=True),
            sa.Column("patent_reference", sa.String(255), nullable=True),
            sa.Column("software_repo_reference", sa.String(255), nullable=True),
            sa.Column("design_reference", sa.String(255), nullable=True),
            sa.Column("startup_spinoff_name", sa.String(255), nullable=True),
            sa.Column("open_source_decision", sa.Boolean(), nullable=True),
            sa.Column("government_benefit_terms", sa.Text(), nullable=True),
            sa.Column("status", sa.String(50), nullable=False, server_default="DRAFT", index=True),
            sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        )

    # 5. IP consent records (per-party consent required before final closure)
    if "ip_consent_records" not in existing_tables:
        op.create_table(
            "ip_consent_records",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column("ip_record_id", sa.Integer(), sa.ForeignKey("ip_records.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("party_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("party_role", sa.String(50), nullable=False),
            sa.Column("status", sa.String(50), nullable=False, server_default="PENDING", index=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("responded_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        )

    # 6. Review comments: moderation & retention
    if "review_comments" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("review_comments")]
        with op.batch_alter_table("review_comments", schema=None) as batch_op:
            if "is_flagged" not in existing_cols:
                batch_op.add_column(sa.Column("is_flagged", sa.Boolean(), nullable=False, server_default="false"))
            if "is_hidden" not in existing_cols:
                batch_op.add_column(sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default="false"))
            if "moderated_by_user_id" not in existing_cols:
                batch_op.add_column(sa.Column("moderated_by_user_id", sa.Integer(), sa.ForeignKey("users.id", name="fk_comments_moderated_by"), nullable=True))
            if "moderation_action" not in existing_cols:
                batch_op.add_column(sa.Column("moderation_action", sa.String(50), nullable=True))
            if "moderation_notes" not in existing_cols:
                batch_op.add_column(sa.Column("moderation_notes", sa.Text(), nullable=True))
            if "retention_state" not in existing_cols:
                batch_op.add_column(sa.Column("retention_state", sa.String(50), nullable=False, server_default="ACTIVE"))


def downgrade() -> None:
    with op.batch_alter_table("review_comments", schema=None) as batch_op:
        batch_op.drop_column("retention_state")
        batch_op.drop_column("moderation_notes")
        batch_op.drop_column("moderation_action")
        batch_op.drop_column("moderated_by_user_id")
        batch_op.drop_column("is_hidden")
        batch_op.drop_column("is_flagged")
    op.drop_table("ip_consent_records")
    op.drop_table("ip_records")
    op.drop_table("funding_records")
    with op.batch_alter_table("industry_collaborations", schema=None) as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("version")
        batch_op.drop_column("terminated_reason")
        batch_op.drop_column("accepted_at")
        batch_op.drop_column("mou_evidence_object_id")
        batch_op.drop_column("conflict_declared")
        batch_op.drop_column("conflict_check_notes")
        batch_op.drop_column("review_notes")
        batch_op.drop_column("reviewed_by_user_id")
        batch_op.drop_column("milestone_id")
        batch_op.drop_column("deliverables")
        batch_op.drop_column("safety_requirements")
        batch_op.drop_column("data_access_level")
        batch_op.drop_column("dependencies")
        batch_op.drop_column("end_date")
        batch_op.drop_column("start_date")
        batch_op.drop_column("currency")
        batch_op.drop_column("cash_value")
        batch_op.drop_column("in_kind_value")
        batch_op.drop_column("personnel")
        batch_op.drop_column("scope")
        batch_op.drop_column("agreement_status")
    with op.batch_alter_table("industry_partners", schema=None) as batch_op:
        batch_op.drop_column("version")
        batch_op.drop_column("notification_preferences")
        batch_op.drop_column("suspended_reason")
        batch_op.drop_column("is_active")
        batch_op.drop_column("compliance_documents")
        batch_op.drop_column("geographic_coverage")
        batch_op.drop_column("capacity_description")
        batch_op.drop_column("domains")
        batch_op.drop_column("authorized_representative_designation")
        batch_op.drop_column("authorized_representative_name")
        batch_op.drop_column("csr_eligible")
        batch_op.drop_column("registration_number")
        batch_op.drop_column("legal_identity")
        batch_op.drop_column("partner_type")
        batch_op.drop_column("organization_profile_id")
