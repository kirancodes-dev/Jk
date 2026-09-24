"""stage6_source_type_vocabulary

Redefines Challenge.source_type from a mixed identity/channel vocabulary
(CITIZEN_MOBILE, PRI_PORTAL, ULB_DESK, GOVERNMENT_FIELD, ...) to a pure
submission-CHANNEL vocabulary (MOBILE_APP, WEB_PORTAL, FIELD_VISIT,
COMMUNITY_SURVEY). WHO submitted is tracked separately and exclusively by
Challenge.submitter_role, derived server-side from the authenticated user's
role. This migration remaps existing rows' source_type values and backfills
submitter_role for legacy rows where it was never populated.

Revision ID: b4d6f0a3c8e1
Revises: 7a8e91d0f2a4
Create Date: 2026-09-24 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4d6f0a3c8e1'
down_revision: Union[str, Sequence[str], None] = '7a8e91d0f2a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Maps every historical / ad-hoc value observed (backend defaults, the old
# ChallengeSourceType enum, and previously-unvalidated Flutter client values)
# to the new pure-channel vocabulary.
_SOURCE_TYPE_REMAP = {
    "CITIZEN_MOBILE": "MOBILE_APP",
    "DIRECT_CITIZEN": "MOBILE_APP",
    "COMMUNITY_GROUP": "COMMUNITY_SURVEY",
    "PRI_PORTAL": "WEB_PORTAL",
    "PRI": "WEB_PORTAL",
    "ULB_DESK": "WEB_PORTAL",
    "ULB": "WEB_PORTAL",
    "GOVERNMENT_FIELD": "FIELD_VISIT",
    "GOVERNMENT_AGENCY": "WEB_PORTAL",
}
_NEW_CHANNEL_VALUES = {"MOBILE_APP", "WEB_PORTAL", "FIELD_VISIT", "COMMUNITY_SURVEY"}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "challenges" not in inspector.get_table_names():
        return
    existing_cols = {c["name"] for c in inspector.get_columns("challenges")}
    if "source_type" not in existing_cols:
        return

    challenges = sa.table(
        "challenges",
        sa.column("id", sa.Integer),
        sa.column("source_type", sa.String),
        sa.column("submitter_role", sa.String),
        sa.column("submitted_by_user_id", sa.Integer),
    )

    for old_value, new_value in _SOURCE_TYPE_REMAP.items():
        bind.execute(
            challenges.update()
            .where(challenges.c.source_type == old_value)
            .values(source_type=new_value)
        )

    # Anything left over (NULL, or a value we've never seen) becomes the safe default.
    bind.execute(
        sa.text(
            "UPDATE challenges SET source_type = 'WEB_PORTAL' "
            "WHERE source_type IS NULL OR source_type NOT IN :valid"
        ).bindparams(sa.bindparam("valid", expanding=True)),
        {"valid": list(_NEW_CHANNEL_VALUES)},
    )

    # Backfill submitter_role for legacy rows from the submitting user's role,
    # where it was never populated (submitter_role predates some early rows).
    if "users" in inspector.get_table_names():
        bind.execute(
            sa.text(
                "UPDATE challenges SET submitter_role = users.role "
                "FROM users WHERE challenges.submitted_by_user_id = users.id "
                "AND challenges.submitter_role IS NULL"
            )
        )

    with op.batch_alter_table("challenges", schema=None) as batch_op:
        batch_op.alter_column(
            "source_type",
            existing_type=sa.String(50),
            server_default="WEB_PORTAL",
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "challenges" not in inspector.get_table_names():
        return
    existing_cols = {c["name"] for c in inspector.get_columns("challenges")}
    if "source_type" not in existing_cols:
        return

    with op.batch_alter_table("challenges", schema=None) as batch_op:
        batch_op.alter_column(
            "source_type",
            existing_type=sa.String(50),
            server_default="CITIZEN_MOBILE",
        )

    # Best-effort reverse mapping (lossy: several old values collapsed to WEB_PORTAL).
    reverse_map = {
        "MOBILE_APP": "CITIZEN_MOBILE",
        "FIELD_VISIT": "GOVERNMENT_FIELD",
    }
    challenges = sa.table(
        "challenges",
        sa.column("id", sa.Integer),
        sa.column("source_type", sa.String),
    )
    for new_value, old_value in reverse_map.items():
        bind.execute(
            challenges.update()
            .where(challenges.c.source_type == new_value)
            .values(source_type=old_value)
        )
