"""attachment_soft_delete_timestamp

Records when an attachment was soft-deleted, so files can be purged after the
retention window (StorageService.purge_expired_attachments, 30 days by
default). Soft-deleted attachments were previously kept forever.

Revision ID: a1c5e9d27b40
Revises: f7b3d2a91c6e
Create Date: 2026-10-06 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c5e9d27b40'
down_revision: Union[str, Sequence[str], None] = 'f7b3d2a91c6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEX = "ix_challenge_attachments_soft_deleted_at"


def upgrade() -> None:
    bind = op.get_bind()
    columns = {c["name"] for c in sa.inspect(bind).get_columns("challenge_attachments")}
    if "soft_deleted_at" in columns:
        return
    with op.batch_alter_table("challenge_attachments") as batch_op:
        batch_op.add_column(sa.Column("soft_deleted_at", sa.DateTime(), nullable=True))
        batch_op.create_index(INDEX, ["soft_deleted_at"])


def downgrade() -> None:
    with op.batch_alter_table("challenge_attachments") as batch_op:
        batch_op.drop_index(INDEX)
        batch_op.drop_column("soft_deleted_at")
