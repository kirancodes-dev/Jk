"""stage5_taxonomy_alignment_and_review_flag

Adds AIAnalysis.requires_human_review (set when the classifier found no keyword
signal and no resolvable category hint, instead of silently guessing a domain).

Also aligns the classifier's internal taxonomy key from the legacy "Water
Management" to the canonical PS 26043 domain name "Water Resources" (matching
taxonomy_service.CANONICAL_DOMAINS). "Water Management" remains a resolvable
alias for any NEW input via TaxonomyService.LEGACY_ALIASES; this migration
remaps that one specific, known legacy literal on existing rows so stored data
matches the same canonical wording new submissions now produce.

Revision ID: d1f5a8c3e6b7
Revises: c9a1e7f4b2d5
Create Date: 2026-09-24 00:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1f5a8c3e6b7'
down_revision: Union[str, Sequence[str], None] = 'c9a1e7f4b2d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "ai_analysis" in existing_tables:
        existing_cols = {c["name"] for c in inspector.get_columns("ai_analysis")}
        if "requires_human_review" not in existing_cols:
            with op.batch_alter_table("ai_analysis", schema=None) as batch_op:
                batch_op.add_column(
                    sa.Column("requires_human_review", sa.Boolean(), server_default=sa.false(), nullable=False)
                )

        ai_analysis = sa.table(
            "ai_analysis",
            sa.column("id", sa.Integer),
            sa.column("classified_domain", sa.String),
        )
        bind.execute(
            ai_analysis.update()
            .where(ai_analysis.c.classified_domain == "Water Management")
            .values(classified_domain="Water Resources")
        )

    if "challenges" in existing_tables:
        existing_cols = {c["name"] for c in inspector.get_columns("challenges")}
        if "category" in existing_cols:
            challenges = sa.table(
                "challenges",
                sa.column("id", sa.Integer),
                sa.column("category", sa.String),
            )
            bind.execute(
                challenges.update()
                .where(challenges.c.category == "Water Management")
                .values(category="Water Resources")
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "ai_analysis" in existing_tables:
        existing_cols = {c["name"] for c in inspector.get_columns("ai_analysis")}
        if "requires_human_review" in existing_cols:
            with op.batch_alter_table("ai_analysis", schema=None) as batch_op:
                batch_op.drop_column("requires_human_review")
    # Note: the "Water Management" -> "Water Resources" data remap is not reversed,
    # since it is a one-way alignment to canonical PS wording, not a rollback-able
    # schema change.
