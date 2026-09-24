"""stage3_district_aspirational_flag

Adds District.is_aspirational and backfills it for the 19 (of 24) Jharkhand
districts under NITI Aayog's Aspirational Districts Programme, correcting the
priority_service.py module constant which previously listed only 13 districts
(and misspelled "Sahebganj" as "sahibganj", which never matched the seeded
district name).

Revision ID: c9a1e7f4b2d5
Revises: b4d6f0a3c8e1
Create Date: 2026-09-24 00:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9a1e7f4b2d5'
down_revision: Union[str, Sequence[str], None] = 'b4d6f0a3c8e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ASPIRATIONAL_DISTRICT_NAMES = [
    "Khunti", "Dumka", "Pakur", "Sahebganj", "Simdega", "West Singhbhum", "Latehar",
    "Hazaribagh", "Palamu", "Garhwa", "Godda", "Gumla", "Lohardaga",
    "Chatra", "Deoghar", "Giridih", "Jamtara", "Koderma", "Saraikela Kharsawan",
]


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "districts" not in inspector.get_table_names():
        return
    existing_cols = {c["name"] for c in inspector.get_columns("districts")}

    if "is_aspirational" not in existing_cols:
        with op.batch_alter_table("districts", schema=None) as batch_op:
            batch_op.add_column(
                sa.Column("is_aspirational", sa.Boolean(), server_default=sa.false(), nullable=False)
            )

    districts = sa.table(
        "districts",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("is_aspirational", sa.Boolean),
    )
    bind.execute(districts.update().values(is_aspirational=False))
    for name in ASPIRATIONAL_DISTRICT_NAMES:
        bind.execute(
            districts.update()
            .where(districts.c.name.ilike(name))
            .values(is_aspirational=True)
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "districts" not in inspector.get_table_names():
        return
    existing_cols = {c["name"] for c in inspector.get_columns("districts")}
    if "is_aspirational" in existing_cols:
        with op.batch_alter_table("districts", schema=None) as batch_op:
            batch_op.drop_column("is_aspirational")
