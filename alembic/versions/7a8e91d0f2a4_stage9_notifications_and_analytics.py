"""stage9_notifications_and_analytics

Revision ID: 7a8e91d0f2a4
Revises: f593b7e3b1c4
Create Date: 2026-09-23 16:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a8e91d0f2a4'
down_revision: Union[str, Sequence[str], None] = 'f593b7e3b1c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # 1. Extend notifications table
    if "notifications" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("notifications")]
        with op.batch_alter_table("notifications", schema=None) as batch_op:
            if "category" not in existing_cols:
                batch_op.add_column(sa.Column("category", sa.String(50), server_default="GENERAL", nullable=False))
            if "deep_link" not in existing_cols:
                batch_op.add_column(sa.Column("deep_link", sa.String(255), nullable=True))
            if "retention_days" not in existing_cols:
                batch_op.add_column(sa.Column("retention_days", sa.Integer(), server_default="90", nullable=False))
            if "is_archived" not in existing_cols:
                batch_op.add_column(sa.Column("is_archived", sa.Boolean(), server_default=sa.false(), nullable=False))

    # 2. Create notification_outbox table
    if "notification_outbox" not in existing_tables:
        op.create_table(
            "notification_outbox",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("notification_id", sa.Integer(), sa.ForeignKey("notifications.id", ondelete="SET NULL"), nullable=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("channel", sa.String(30), nullable=False),
            sa.Column("provider", sa.String(100), nullable=False),
            sa.Column("recipient", sa.String(255), nullable=False),
            sa.Column("template_id", sa.String(100), nullable=True),
            sa.Column("template_version", sa.String(20), nullable=True),
            sa.Column("locale", sa.String(10), server_default="en", nullable=False),
            sa.Column("delivery_status", sa.String(30), server_default="PENDING", nullable=False, index=True),
            sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
            sa.Column("max_retries", sa.Integer(), server_default="3", nullable=False),
            sa.Column("failure_reason", sa.Text(), nullable=True),
            sa.Column("payload_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("sent_at", sa.DateTime(), nullable=True),
            sa.Column("last_attempt_at", sa.DateTime(), nullable=True),
        )

    # 3. Create user_notification_preferences table
    if "user_notification_preferences" not in existing_tables:
        op.create_table(
            "user_notification_preferences",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True),
            sa.Column("email_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
            sa.Column("sms_enabled", sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column("push_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
            sa.Column("whatsapp_enabled", sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column("preferred_locale", sa.String(10), server_default="en", nullable=False),
            sa.Column("categories_json", sa.Text(), nullable=True),
            sa.Column("consent_given", sa.Boolean(), server_default=sa.true(), nullable=False),
            sa.Column("consent_timestamp", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("consent_version", sa.String(20), server_default="v1.0", nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        )

    # 4. Create export_jobs table (for Stage 10 bounded async exports)
    if "export_jobs" not in existing_tables:
        op.create_table(
            "export_jobs",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("export_type", sa.String(50), nullable=False),
            sa.Column("export_format", sa.String(20), server_default="CSV", nullable=False),
            sa.Column("filters_json", sa.Text(), nullable=True),
            sa.Column("status", sa.String(30), server_default="PENDING", nullable=False, index=True),
            sa.Column("file_path", sa.String(500), nullable=True),
            sa.Column("row_count", sa.Integer(), server_default="0", nullable=False),
            sa.Column("failure_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "export_jobs" in existing_tables:
        op.drop_table("export_jobs")

    if "user_notification_preferences" in existing_tables:
        op.drop_table("user_notification_preferences")

    if "notification_outbox" in existing_tables:
        op.drop_table("notification_outbox")

    if "notifications" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("notifications")]
        with op.batch_alter_table("notifications", schema=None) as batch_op:
            if "is_archived" in existing_cols:
                batch_op.drop_column("is_archived")
            if "retention_days" in existing_cols:
                batch_op.drop_column("retention_days")
            if "deep_link" in existing_cols:
                batch_op.drop_column("deep_link")
            if "category" in existing_cols:
                batch_op.drop_column("category")
