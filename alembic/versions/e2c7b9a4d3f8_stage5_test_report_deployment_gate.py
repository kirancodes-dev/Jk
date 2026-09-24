"""stage5_test_report_deployment_gate

Adds the test_reports table (structured field/lab/user-trial testing outcomes,
modeled as OutcomeReport in code — named to avoid pytest's Test* collection
convention). A challenge may no longer transition into DEPLOYMENT on
milestone/status alone — WorkflowService.transition_challenge now requires at
least one PASS or PARTIAL OutcomeReport across the challenge's project(s) first.

Revision ID: e2c7b9a4d3f8
Revises: d1f5a8c3e6b7
Create Date: 2026-09-24 00:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2c7b9a4d3f8'
down_revision: Union[str, Sequence[str], None] = 'd1f5a8c3e6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "test_reports" in inspector.get_table_names():
        return

    op.create_table(
        "test_reports",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("reported_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("test_type", sa.String(20), nullable=False),
        sa.Column("outcome", sa.String(20), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("tested_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "test_reports" in inspector.get_table_names():
        op.drop_table("test_reports")
