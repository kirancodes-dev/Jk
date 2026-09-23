"""stage8_verification_metrics_closure

Revision ID: f593b7e3b1c4
Revises: c7f4e91b3a5d
Create Date: 2026-09-23 15:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f593b7e3b1c4'
down_revision: Union[str, Sequence[str], None] = 'c7f4e91b3a5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # 1. Extend verification_records
    if "verification_records" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("verification_records")]
        with op.batch_alter_table("verification_records", schema=None) as batch_op:
            if "inspector_user_id" not in existing_cols:
                batch_op.add_column(sa.Column("inspector_user_id", sa.Integer(), sa.ForeignKey("users.id", name="fk_verification_inspector_user"), nullable=True))
            if "inspector_organization_id" not in existing_cols:
                batch_op.add_column(sa.Column("inspector_organization_id", sa.Integer(), sa.ForeignKey("organization_profiles.id", name="fk_verification_inspector_org"), nullable=True))
            if "assignment_id" not in existing_cols:
                batch_op.add_column(sa.Column("assignment_id", sa.String(100), nullable=True))
            if "checklist_responses" not in existing_cols:
                batch_op.add_column(sa.Column("checklist_responses", sa.Text(), nullable=True))
            if "visit_timestamp" not in existing_cols:
                batch_op.add_column(sa.Column("visit_timestamp", sa.DateTime(), nullable=True))
            if "device_metadata" not in existing_cols:
                batch_op.add_column(sa.Column("device_metadata", sa.Text(), nullable=True))
            if "before_media_urls" not in existing_cols:
                batch_op.add_column(sa.Column("before_media_urls", sa.Text(), nullable=True))
            if "after_media_urls" not in existing_cols:
                batch_op.add_column(sa.Column("after_media_urls", sa.Text(), nullable=True))
            if "lab_report_references" not in existing_cols:
                batch_op.add_column(sa.Column("lab_report_references", sa.Text(), nullable=True))
            if "beneficiary_sample_size" not in existing_cols:
                batch_op.add_column(sa.Column("beneficiary_sample_size", sa.Integer(), nullable=True))
            if "beneficiary_feedback_summary" not in existing_cols:
                batch_op.add_column(sa.Column("beneficiary_feedback_summary", sa.Text(), nullable=True))
            if "reviewed_by_user_id" not in existing_cols:
                batch_op.add_column(sa.Column("reviewed_by_user_id", sa.Integer(), sa.ForeignKey("users.id", name="fk_verification_reviewed_by_user"), nullable=True))
            if "review_decision" not in existing_cols:
                batch_op.add_column(sa.Column("review_decision", sa.String(50), nullable=True))
            if "review_notes" not in existing_cols:
                batch_op.add_column(sa.Column("review_notes", sa.Text(), nullable=True))

    # 2. Create outcome_metrics table
    if "outcome_metrics" not in existing_tables:
        op.create_table(
            "outcome_metrics",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, index=True),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", name="fk_outcome_metrics_project_id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("challenge_id", sa.Integer(), sa.ForeignKey("challenges.id", name="fk_outcome_metrics_challenge_id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("metric_name", sa.String(255), nullable=False, index=True),
            sa.Column("metric_definition", sa.Text(), nullable=False),
            sa.Column("metric_type", sa.String(50), server_default="QUANTITATIVE", nullable=False),
            sa.Column("unit_of_measure", sa.String(50), nullable=True),
            sa.Column("baseline_value", sa.String(100), nullable=False),
            sa.Column("baseline_date", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("baseline_source", sa.String(255), nullable=False),
            sa.Column("target_value", sa.String(100), nullable=False),
            sa.Column("target_date", sa.DateTime(), nullable=True),
            sa.Column("actual_value", sa.String(100), nullable=True),
            sa.Column("actual_date", sa.DateTime(), nullable=True),
            sa.Column("actual_source", sa.String(255), nullable=True),
            sa.Column("collection_method", sa.String(100), nullable=True),
            sa.Column("sample_size", sa.Integer(), nullable=True),
            sa.Column("uncertainty_margin", sa.String(50), nullable=True),
            sa.Column("responsible_org_name", sa.String(255), nullable=True),
            sa.Column("responsible_user_id", sa.Integer(), sa.ForeignKey("users.id", name="fk_outcome_metrics_responsible_user"), nullable=True),
            sa.Column("evidence_references", sa.Text(), nullable=True),
            sa.Column("district_name", sa.String(100), nullable=True),
            sa.Column("block_name", sa.String(100), nullable=True),
            sa.Column("verification_status", sa.String(50), server_default="REPORTED", nullable=False),
            sa.Column("verified_by_user_id", sa.Integer(), sa.ForeignKey("users.id", name="fk_outcome_metrics_verified_by_user"), nullable=True),
            sa.Column("verified_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False)
        )

    # 3. Extend citizen_feedback
    if "citizen_feedback" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("citizen_feedback")]
        with op.batch_alter_table("citizen_feedback", schema=None) as batch_op:
            if "challenge_version" not in existing_cols:
                batch_op.add_column(sa.Column("challenge_version", sa.Integer(), server_default="1", nullable=False))
            if "user_id" not in existing_cols:
                batch_op.add_column(sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", name="fk_citizen_feedback_user_id"), nullable=True))
            if "beneficiary_verification_type" not in existing_cols:
                batch_op.add_column(sa.Column("beneficiary_verification_type", sa.String(50), server_default="ORIGINAL_REPORTER", nullable=False))
            if "invitation_token" not in existing_cols:
                batch_op.add_column(sa.Column("invitation_token", sa.String(100), nullable=True))
            if "moderation_status" not in existing_cols:
                batch_op.add_column(sa.Column("moderation_status", sa.String(50), server_default="APPROVED", nullable=False))
            if "moderated_by_user_id" not in existing_cols:
                batch_op.add_column(sa.Column("moderated_by_user_id", sa.Integer(), sa.ForeignKey("users.id", name="fk_citizen_feedback_moderated_by"), nullable=True))
            if "moderation_reason" not in existing_cols:
                batch_op.add_column(sa.Column("moderation_reason", sa.Text(), nullable=True))
            if "original_comments" not in existing_cols:
                batch_op.add_column(sa.Column("original_comments", sa.Text(), nullable=True))
            if "is_public" not in existing_cols:
                batch_op.add_column(sa.Column("is_public", sa.Boolean(), server_default="true", nullable=False))
            if "appeal_status" not in existing_cols:
                batch_op.add_column(sa.Column("appeal_status", sa.String(50), server_default="NONE", nullable=False))
            if "appeal_reason" not in existing_cols:
                batch_op.add_column(sa.Column("appeal_reason", sa.Text(), nullable=True))
            if "accessibility_needs" not in existing_cols:
                batch_op.add_column(sa.Column("accessibility_needs", sa.String(100), nullable=True))
            if "language" not in existing_cols:
                batch_op.add_column(sa.Column("language", sa.String(20), server_default="en", nullable=False))

    # 4. Create project_closure_records table
    if "project_closure_records" not in existing_tables:
        op.create_table(
            "project_closure_records",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, index=True),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", name="fk_closure_project_id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("challenge_id", sa.Integer(), sa.ForeignKey("challenges.id", name="fk_closure_challenge_id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("closed_by_user_id", sa.Integer(), sa.ForeignKey("users.id", name="fk_closure_closed_by_user"), nullable=False, index=True),
            sa.Column("closure_decision", sa.String(50), nullable=False),
            sa.Column("preconditions_snapshot_json", sa.Text(), nullable=False),
            sa.Column("ip_cleared", sa.Boolean(), server_default="true", nullable=False),
            sa.Column("ip_handover_details", sa.Text(), nullable=True),
            sa.Column("maintenance_handover_plan", sa.Text(), nullable=False),
            sa.Column("handover_recipient_org", sa.String(255), nullable=False),
            sa.Column("closure_remarks", sa.Text(), nullable=False),
            sa.Column("closed_at", sa.DateTime(), server_default=sa.func.now(), nullable=False)
        )


def downgrade() -> None:
    op.drop_table("project_closure_records")
    op.drop_table("outcome_metrics")
