"""stage4_workflow_state_machine

Revision ID: d381b7e2a0f1
Revises: c293b6e1f0a2
Create Date: 2026-09-23 08:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd381b7e2a0f1'
down_revision: Union[str, Sequence[str], None] = 'c293b6e1f0a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # 1. Expand PostgreSQL enum challengestatus if applicable
    if dialect == "postgresql":
        for val in ['PAUSED', 'REOPENED', 'IMPACT_AUDITED']:
            try:
                op.execute(sa.text(f"ALTER TYPE challengestatus ADD VALUE IF NOT EXISTS '{val}'"))
            except Exception:
                pass

    # 2. Add optimistic locking 'version' column to core tables
    if "challenges" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("challenges")]
        if "version" not in existing_cols:
            with op.batch_alter_table("challenges", schema=None) as batch_op:
                batch_op.add_column(sa.Column("version", sa.Integer(), nullable=False, server_default="1"))

    if "projects" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("projects")]
        if "version" not in existing_cols:
            with op.batch_alter_table("projects", schema=None) as batch_op:
                batch_op.add_column(sa.Column("version", sa.Integer(), nullable=False, server_default="1"))

    if "project_milestones" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("project_milestones")]
        if "version" not in existing_cols:
            with op.batch_alter_table("project_milestones", schema=None) as batch_op:
                batch_op.add_column(sa.Column("version", sa.Integer(), nullable=False, server_default="1"))

    if "verification_records" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("verification_records")]
        if "version" not in existing_cols:
            with op.batch_alter_table("verification_records", schema=None) as batch_op:
                batch_op.add_column(sa.Column("version", sa.Integer(), nullable=False, server_default="1"))

    # 3. Create challenge_allocations table
    if "challenge_allocations" not in existing_tables:
        op.create_table(
            "challenge_allocations",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("challenge_id", sa.Integer(), nullable=False),
            sa.Column("assigned_by_user_id", sa.Integer(), nullable=False),
            sa.Column("assigned_to_org_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=False, server_default="OFFERED"),
            sa.Column("allocated_at", sa.DateTime(), nullable=False),
            sa.Column("deadline_at", sa.DateTime(), nullable=True),
            sa.Column("responded_at", sa.DateTime(), nullable=True),
            sa.Column("response_notes", sa.Text(), nullable=True),
            sa.Column("capacity_assessment", sa.Text(), nullable=True),
            sa.Column("coi_declared", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("reassigned_from_allocation_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["assigned_to_org_id"], ["organization_profiles.id"]),
            sa.ForeignKeyConstraint(["challenge_id"], ["challenges.id"]),
            sa.ForeignKeyConstraint(["reassigned_from_allocation_id"], ["challenge_allocations.id"]),
            sa.PrimaryKeyConstraint("id")
        )
        op.create_index("ix_challenge_allocations_id", "challenge_allocations", ["id"])
        op.create_index("ix_challenge_allocations_challenge_id", "challenge_allocations", ["challenge_id"])
        op.create_index("ix_challenge_allocations_assigned_by_user_id", "challenge_allocations", ["assigned_by_user_id"])
        op.create_index("ix_challenge_allocations_assigned_to_org_id", "challenge_allocations", ["assigned_to_org_id"])
        op.create_index("ix_challenge_allocations_status", "challenge_allocations", ["status"])

    # 4. Create domain_audit_events table
    if "domain_audit_events" not in existing_tables:
        op.create_table(
            "domain_audit_events",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("sequence_number", sa.BigInteger(), nullable=False),
            sa.Column("entity_type", sa.String(length=64), nullable=False),
            sa.Column("entity_id", sa.Integer(), nullable=False),
            sa.Column("action", sa.String(length=64), nullable=False),
            sa.Column("previous_state", sa.String(length=64), nullable=True),
            sa.Column("new_state", sa.String(length=64), nullable=True),
            sa.Column("actor_id", sa.Integer(), nullable=True),
            sa.Column("actor_role", sa.String(length=64), nullable=True),
            sa.Column("jurisdiction_level", sa.String(length=64), nullable=True),
            sa.Column("jurisdiction_value", sa.String(length=128), nullable=True),
            sa.Column("reason_code", sa.String(length=64), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("payload_json", sa.Text(), nullable=False),
            sa.Column("payload_hash", sa.String(length=64), nullable=False),
            sa.Column("prev_event_hash", sa.String(length=64), nullable=True),
            sa.Column("event_hash", sa.String(length=64), nullable=False),
            sa.Column("is_internal", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("sequence_number")
        )
        op.create_index("ix_domain_audit_events_id", "domain_audit_events", ["id"])
        op.create_index("ix_domain_audit_events_sequence_number", "domain_audit_events", ["sequence_number"])
        op.create_index("ix_domain_audit_events_entity_type", "domain_audit_events", ["entity_type"])
        op.create_index("ix_domain_audit_events_entity_id", "domain_audit_events", ["entity_id"])
        op.create_index("ix_domain_audit_events_action", "domain_audit_events", ["action"])
        op.create_index("ix_domain_audit_events_actor_id", "domain_audit_events", ["actor_id"])
        op.create_index("ix_domain_audit_events_event_hash", "domain_audit_events", ["event_hash"])
        op.create_index("ix_domain_audit_events_created_at", "domain_audit_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("domain_audit_events")
    op.drop_table("challenge_allocations")
    with op.batch_alter_table("verification_records", schema=None) as batch_op:
        batch_op.drop_column("version")
    with op.batch_alter_table("project_milestones", schema=None) as batch_op:
        batch_op.drop_column("version")
    with op.batch_alter_table("projects", schema=None) as batch_op:
        batch_op.drop_column("version")
    with op.batch_alter_table("challenges", schema=None) as batch_op:
        batch_op.drop_column("version")
