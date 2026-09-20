"""initial_production_schema

Revision ID: f48420fc1dd0
Revises: 
Create Date: 2026-09-19 10:17:18.466750

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f48420fc1dd0'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create all 33 production relational tables, foreign keys, and indexes."""
    from backend.app.core.database import Base
    import backend.app.models.models  # noqa: F401 - ensures all models are registered
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    """Downgrade schema: drop all production tables."""
    from backend.app.core.database import Base
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)

