"""stage3_challenge_ingestion

Revision ID: c293b6e1f0a2
Revises: b182a5c0d291
Create Date: 2026-09-23 07:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c293b6e1f0a2'
down_revision: Union[str, Sequence[str], None] = 'b182a5c0d291'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # 1. Update challenges table with submitter, consent, privacy, and idempotency fields
    if "challenges" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("challenges")]
        with op.batch_alter_table("challenges", schema=None) as batch_op:
            if "submitted_by_user_id" not in existing_cols:
                batch_op.add_column(sa.Column("submitted_by_user_id", sa.Integer(), nullable=True))
                batch_op.create_foreign_key("fk_challenges_submitted_by_user_id", "users", ["submitted_by_user_id"], ["id"])
                batch_op.create_index("ix_challenges_submitted_by_user_id", ["submitted_by_user_id"])
            if "organization_id" not in existing_cols:
                batch_op.add_column(sa.Column("organization_id", sa.Integer(), nullable=True))
                batch_op.create_foreign_key("fk_challenges_organization_id", "organization_profiles", ["organization_id"], ["id"])
                batch_op.create_index("ix_challenges_organization_id", ["organization_id"])
            if "submitter_role" not in existing_cols:
                batch_op.add_column(sa.Column("submitter_role", sa.String(50), nullable=True))
            if "source_type" not in existing_cols:
                batch_op.add_column(sa.Column("source_type", sa.String(50), server_default="CITIZEN_MOBILE", nullable=True))
            if "contact_preference" not in existing_cols:
                batch_op.add_column(sa.Column("contact_preference", sa.String(50), server_default="SMS", nullable=True))
            if "consent_version" not in existing_cols:
                batch_op.add_column(sa.Column("consent_version", sa.String(20), server_default="v1.0", nullable=True))
            if "consent_given" not in existing_cols:
                batch_op.add_column(sa.Column("consent_given", sa.Boolean(), server_default=sa.true(), nullable=True))
            if "data_sharing_choice" not in existing_cols:
                batch_op.add_column(sa.Column("data_sharing_choice", sa.String(50), server_default="PUBLIC", nullable=True))
            if "accessibility_needs" not in existing_cols:
                batch_op.add_column(sa.Column("accessibility_needs", sa.Text(), nullable=True))
            if "submission_language" not in existing_cols:
                batch_op.add_column(sa.Column("submission_language", sa.String(10), server_default="en", nullable=True))
            if "original_title" not in existing_cols:
                batch_op.add_column(sa.Column("original_title", sa.String(255), nullable=True))
            if "original_description" not in existing_cols:
                batch_op.add_column(sa.Column("original_description", sa.Text(), nullable=True))
            if "translation_status" not in existing_cols:
                batch_op.add_column(sa.Column("translation_status", sa.String(50), server_default="NONE", nullable=True))
            if "is_anonymous_public" not in existing_cols:
                batch_op.add_column(sa.Column("is_anonymous_public", sa.Boolean(), server_default=sa.false(), nullable=True))
            if "idempotency_key" not in existing_cols:
                batch_op.add_column(sa.Column("idempotency_key", sa.String(128), nullable=True))
                batch_op.create_index("ix_challenges_idempotency_key", ["idempotency_key"], unique=True)

    # 2. Create challenge_attachments table
    if "challenge_attachments" not in existing_tables:
        op.create_table(
            "challenge_attachments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("object_id", sa.String(64), nullable=False),
            sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("challenge_id", sa.Integer(), sa.ForeignKey("challenges.id"), nullable=True),
            sa.Column("original_filename", sa.String(255), nullable=False),
            sa.Column("detected_mime", sa.String(100), nullable=False),
            sa.Column("size_bytes", sa.Integer(), nullable=False),
            sa.Column("sha256_checksum", sa.String(64), nullable=False),
            sa.Column("storage_key", sa.String(500), nullable=False),
            sa.Column("scan_status", sa.String(50), server_default="CLEAN", nullable=False),
            sa.Column("access_classification", sa.String(50), server_default="RESTRICTED", nullable=False),
            sa.Column("retention_state", sa.String(50), server_default="ACTIVE", nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False)
        )
        op.create_index("ix_challenge_attachments_id", "challenge_attachments", ["id"])
        op.create_index("ix_challenge_attachments_object_id", "challenge_attachments", ["object_id"], unique=True)
        op.create_index("ix_challenge_attachments_owner_id", "challenge_attachments", ["owner_id"])
        op.create_index("ix_challenge_attachments_challenge_id", "challenge_attachments", ["challenge_id"])

    # 3. Create challenge_drafts table
    if "challenge_drafts" not in existing_tables:
        op.create_table(
            "challenge_drafts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("draft_id", sa.String(64), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("idempotency_key", sa.String(128), nullable=True),
            sa.Column("payload_json", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False)
        )
        op.create_index("ix_challenge_drafts_id", "challenge_drafts", ["id"])
        op.create_index("ix_challenge_drafts_draft_id", "challenge_drafts", ["draft_id"], unique=True)
        op.create_index("ix_challenge_drafts_user_id", "challenge_drafts", ["user_id"])
        op.create_index("ix_challenge_drafts_idempotency_key", "challenge_drafts", ["idempotency_key"])

    # 4. Create taxonomy_domains table
    if "taxonomy_domains" not in existing_tables:
        op.create_table(
            "taxonomy_domains",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("code", sa.String(100), nullable=False),
            sa.Column("name", sa.String(150), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("icon_name", sa.String(50), server_default="category", nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False)
        )
        op.create_index("ix_taxonomy_domains_id", "taxonomy_domains", ["id"])
        op.create_index("ix_taxonomy_domains_code", "taxonomy_domains", ["code"], unique=True)

    # 5. Create taxonomy_subdomains table
    if "taxonomy_subdomains" not in existing_tables:
        op.create_table(
            "taxonomy_subdomains",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("domain_id", sa.Integer(), sa.ForeignKey("taxonomy_domains.id"), nullable=False),
            sa.Column("code", sa.String(100), nullable=False),
            sa.Column("name", sa.String(150), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False)
        )
        op.create_index("ix_taxonomy_subdomains_id", "taxonomy_subdomains", ["id"])
        op.create_index("ix_taxonomy_subdomains_domain_id", "taxonomy_subdomains", ["domain_id"])
        op.create_index("ix_taxonomy_subdomains_code", "taxonomy_subdomains", ["code"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "taxonomy_subdomains" in existing_tables:
        op.drop_table("taxonomy_subdomains")

    if "taxonomy_domains" in existing_tables:
        op.drop_table("taxonomy_domains")

    if "challenge_drafts" in existing_tables:
        op.drop_table("challenge_drafts")

    if "challenge_attachments" in existing_tables:
        op.drop_table("challenge_attachments")

    if "challenges" in existing_tables:
        with op.batch_alter_table("challenges", schema=None) as batch_op:
            batch_op.drop_index("ix_challenges_idempotency_key")
            batch_op.drop_index("ix_challenges_organization_id")
            batch_op.drop_index("ix_challenges_submitted_by_user_id")
            for col in [
                "submitted_by_user_id", "organization_id", "submitter_role",
                "source_type", "contact_preference", "consent_version",
                "consent_given", "data_sharing_choice", "accessibility_needs",
                "submission_language", "original_title", "original_description",
                "translation_status", "is_anonymous_public", "idempotency_key"
            ]:
                batch_op.drop_column(col)
