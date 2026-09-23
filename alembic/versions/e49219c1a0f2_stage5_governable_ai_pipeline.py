"""stage5_governable_ai_pipeline

Revision ID: e49219c1a0f2
Revises: d381b7e2a0f1
Create Date: 2026-09-23 09:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e49219c1a0f2'
down_revision: Union[str, Sequence[str], None] = 'd381b7e2a0f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # 1. Add governance columns to ai_analysis
    if "ai_analysis" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("ai_analysis")]
        with op.batch_alter_table("ai_analysis", schema=None) as batch_op:
            if "model_name" not in existing_cols:
                batch_op.add_column(sa.Column("model_name", sa.String(100), nullable=False, server_default="JHARKHAND_TAXONOMY_CLASSIFIER_V2"))
            if "model_version" not in existing_cols:
                batch_op.add_column(sa.Column("model_version", sa.String(50), nullable=False, server_default="2.2.0"))
            if "provider_name" not in existing_cols:
                batch_op.add_column(sa.Column("provider_name", sa.String(100), nullable=False, server_default="LOCAL_DETERMINISTIC_ENGINE"))
            if "execution_time_ms" not in existing_cols:
                batch_op.add_column(sa.Column("execution_time_ms", sa.Integer(), nullable=False, server_default="0"))
            if "input_snapshot_hash" not in existing_cols:
                batch_op.add_column(sa.Column("input_snapshot_hash", sa.String(64), nullable=True))
            if "detected_language" not in existing_cols:
                batch_op.add_column(sa.Column("detected_language", sa.String(20), nullable=False, server_default="en"))
            if "language_confidence" not in existing_cols:
                batch_op.add_column(sa.Column("language_confidence", sa.Float(), nullable=False, server_default="1.0"))
            if "calibration_status" not in existing_cols:
                batch_op.add_column(sa.Column("calibration_status", sa.String(50), nullable=False, server_default="CALIBRATED_FALLBACK"))
            if "is_fallback" not in existing_cols:
                batch_op.add_column(sa.Column("is_fallback", sa.Boolean(), nullable=False, server_default="true"))
            if "fallback_reason" not in existing_cols:
                batch_op.add_column(sa.Column("fallback_reason", sa.String(255), nullable=True))
            if "policy_version" not in existing_cols:
                batch_op.add_column(sa.Column("policy_version", sa.String(50), nullable=False, server_default="v2026.1"))
            if "explanation" not in existing_cols:
                batch_op.add_column(sa.Column("explanation", sa.Text(), nullable=True))
            if "features_json" not in existing_cols:
                batch_op.add_column(sa.Column("features_json", sa.Text(), nullable=True))
            if "priority_breakdown_json" not in existing_cols:
                batch_op.add_column(sa.Column("priority_breakdown_json", sa.Text(), nullable=True))
            if "translated_title" not in existing_cols:
                batch_op.add_column(sa.Column("translated_title", sa.Text(), nullable=True))
            if "translated_description" not in existing_cols:
                batch_op.add_column(sa.Column("translated_description", sa.Text(), nullable=True))

    # 3. Add decomposed signals to challenge_similarity
    if "challenge_similarity" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("challenge_similarity")]
        with op.batch_alter_table("challenge_similarity", schema=None) as batch_op:
            if "text_similarity" not in existing_cols:
                batch_op.add_column(sa.Column("text_similarity", sa.Float(), nullable=False, server_default="0.0"))
            if "geographic_similarity" not in existing_cols:
                batch_op.add_column(sa.Column("geographic_similarity", sa.Float(), nullable=False, server_default="0.0"))
            if "temporal_similarity" not in existing_cols:
                batch_op.add_column(sa.Column("temporal_similarity", sa.Float(), nullable=False, server_default="0.0"))
            if "category_similarity" not in existing_cols:
                batch_op.add_column(sa.Column("category_similarity", sa.Float(), nullable=False, server_default="0.0"))
            if "explanation" not in existing_cols:
                batch_op.add_column(sa.Column("explanation", sa.Text(), nullable=True))
            if "dismissed" not in existing_cols:
                batch_op.add_column(sa.Column("dismissed", sa.Boolean(), nullable=False, server_default="false"))
            if "dismissed_by_user_id" not in existing_cols:
                batch_op.add_column(sa.Column("dismissed_by_user_id", sa.Integer(), sa.ForeignKey("users.id", name="fk_challenge_similarity_dismissed_by"), nullable=True))
            if "dismissal_reason" not in existing_cols:
                batch_op.add_column(sa.Column("dismissal_reason", sa.Text(), nullable=True))

    # 4. Create ai_jobs table (Durable Outbox Queue)
    if "ai_jobs" not in existing_tables:
        op.create_table(
            "ai_jobs",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, index=True),
            sa.Column("challenge_id", sa.Integer(), sa.ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("idempotency_key", sa.String(128), unique=True, nullable=False, index=True),
            sa.Column("job_type", sa.String(50), server_default="FULL_ANALYSIS", nullable=False),
            sa.Column("status", sa.String(50), server_default="PENDING", nullable=False, index=True),
            sa.Column("payload_json", sa.Text(), nullable=True),
            sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
            sa.Column("max_retries", sa.Integer(), server_default="3", nullable=False),
            sa.Column("backoff_seconds", sa.Integer(), server_default="5", nullable=False),
            sa.Column("next_run_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, index=True),
            sa.Column("timeout_seconds", sa.Integer(), server_default="60", nullable=False),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("completed_at", sa.DateTime(), nullable=True)
        )

    # 5. Create ai_human_overrides table
    if "ai_human_overrides" not in existing_tables:
        op.create_table(
            "ai_human_overrides",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column("challenge_id", sa.Integer(), sa.ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("analysis_id", sa.Integer(), sa.ForeignKey("ai_analysis.id", ondelete="SET NULL"), nullable=True),
            sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("decision_type", sa.String(50), nullable=False),
            sa.Column("original_value", sa.Text(), nullable=False),
            sa.Column("override_value", sa.Text(), nullable=False),
            sa.Column("mandatory_reason", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False)
        )

    # 6. Create ai_priority_configs table
    if "ai_priority_configs" not in existing_tables:
        op.create_table(
            "ai_priority_configs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column("config_version", sa.String(50), unique=True, nullable=False, index=True),
            sa.Column("weights_json", sa.Text(), nullable=False),
            sa.Column("thresholds_json", sa.Text(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False, index=True),
            sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False)
        )

    # 7. Create ai_model_governance table
    if "ai_model_governance" not in existing_tables:
        op.create_table(
            "ai_model_governance",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column("model_name", sa.String(100), nullable=False, index=True),
            sa.Column("model_version", sa.String(50), nullable=False),
            sa.Column("provider_name", sa.String(100), nullable=False),
            sa.Column("task_type", sa.String(50), nullable=False),
            sa.Column("approval_status", sa.String(50), server_default="STAGING", nullable=False),
            sa.Column("benchmark_metrics_json", sa.Text(), nullable=True),
            sa.Column("changelog", sa.Text(), nullable=True),
            sa.Column("approved_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("approved_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False)
        )


def downgrade() -> None:
    op.drop_table("ai_model_governance")
    op.drop_table("ai_priority_configs")
    op.drop_table("ai_human_overrides")
    op.drop_table("ai_jobs")
