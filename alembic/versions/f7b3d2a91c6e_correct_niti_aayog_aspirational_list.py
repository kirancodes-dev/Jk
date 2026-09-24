"""correct_niti_aayog_aspirational_list

Corrects District.is_aspirational to NITI Aayog's actual 19 Jharkhand
Aspirational Districts. The prior migration (c9a1e7f4b2d5) used an inaccurate
list (included Deoghar, Jamtara, Koderma, Saraikela Kharsawan; omitted
Bokaro, East Singhbhum, Ramgarh, Ranchi). This migration does not hand-edit
that prior revision — it re-derives the flag from the corrected list here,
matching the corrected `JHARKHAND_ASPIRATIONAL_DISTRICTS` constant in
backend/app/services/ai/priority_service.py.

Revision ID: f7b3d2a91c6e
Revises: e2c7b9a4d3f8
Create Date: 2026-09-25 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7b3d2a91c6e'
down_revision: Union[str, Sequence[str], None] = 'e2c7b9a4d3f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CORRECTED_ASPIRATIONAL_DISTRICT_NAMES = [
    "Bokaro", "Chatra", "Dumka", "Garhwa", "Giridih", "Godda", "Gumla",
    "Hazaribagh", "Khunti", "Latehar", "Lohardaga", "Pakur", "Palamu",
    "West Singhbhum", "East Singhbhum", "Ramgarh", "Ranchi", "Sahebganj", "Simdega",
]


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "districts" not in inspector.get_table_names():
        return
    existing_cols = {c["name"] for c in inspector.get_columns("districts")}
    if "is_aspirational" not in existing_cols:
        return

    districts = sa.table(
        "districts",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("is_aspirational", sa.Boolean),
    )
    bind.execute(districts.update().values(is_aspirational=False))
    for name in CORRECTED_ASPIRATIONAL_DISTRICT_NAMES:
        bind.execute(
            districts.update()
            .where(districts.c.name.ilike(name))
            .values(is_aspirational=True)
        )


def downgrade() -> None:
    # Reverts to the previous (inaccurate) list from c9a1e7f4b2d5, for symmetry.
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "districts" not in inspector.get_table_names():
        return
    existing_cols = {c["name"] for c in inspector.get_columns("districts")}
    if "is_aspirational" not in existing_cols:
        return

    previous_list = [
        "Khunti", "Dumka", "Pakur", "Sahebganj", "Simdega", "West Singhbhum", "Latehar",
        "Hazaribagh", "Palamu", "Garhwa", "Godda", "Gumla", "Lohardaga",
        "Chatra", "Deoghar", "Giridih", "Jamtara", "Koderma", "Saraikela Kharsawan",
    ]
    districts = sa.table(
        "districts",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("is_aspirational", sa.Boolean),
    )
    bind.execute(districts.update().values(is_aspirational=False))
    for name in previous_list:
        bind.execute(
            districts.update()
            .where(districts.c.name.ilike(name))
            .values(is_aspirational=True)
        )
