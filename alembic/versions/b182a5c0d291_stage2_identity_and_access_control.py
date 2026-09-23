"""stage2_identity_and_access_control

Revision ID: b182a5c0d291
Revises: f48420fc1dd0
Create Date: 2026-09-22 18:32:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b182a5c0d291'
down_revision: Union[str, Sequence[str], None] = 'f48420fc1dd0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # Add new values to postgres enum if on postgresql
    if dialect == "postgresql":
        new_roles = [
            "COMMUNITY_ORG", "PRI", "ULB", "GOVERNMENT_OFFICER",
            "RESEARCH_LAB", "INNOVATION_HUB"
        ]
        for role in new_roles:
            try:
                op.execute(f"ALTER TYPE userrole ADD VALUE IF NOT EXISTS '{role}'")
            except Exception:
                pass

    # Add Stage 2 columns to users table if not already present
    if 'users' in existing_tables:
        existing_user_cols = [c["name"] for c in inspector.get_columns('users')]
        with op.batch_alter_table('users', schema=None) as batch_op:
            if 'account_status' not in existing_user_cols:
                batch_op.add_column(sa.Column('account_status', sa.String(length=50), nullable=False, server_default='ACTIVE'))
                batch_op.create_index('ix_users_account_status', ['account_status'])
            if 'password_changed_at' not in existing_user_cols:
                batch_op.add_column(sa.Column('password_changed_at', sa.DateTime(), nullable=False, server_default=sa.func.now()))
            if 'district_name' not in existing_user_cols:
                batch_op.add_column(sa.Column('district_name', sa.String(length=100), nullable=True))
                batch_op.create_index('ix_users_district_name', ['district_name'])
            if 'block_name' not in existing_user_cols:
                batch_op.add_column(sa.Column('block_name', sa.String(length=100), nullable=True))
                batch_op.create_index('ix_users_block_name', ['block_name'])
            if 'panchayat_name' not in existing_user_cols:
                batch_op.add_column(sa.Column('panchayat_name', sa.String(length=100), nullable=True))
                batch_op.create_index('ix_users_panchayat_name', ['panchayat_name'])
            if 'department_id' not in existing_user_cols:
                batch_op.add_column(sa.Column('department_id', sa.Integer(), nullable=True))
            if 'mfa_enabled' not in existing_user_cols:
                batch_op.add_column(sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default='0'))
            if 'mfa_secret' not in existing_user_cols:
                batch_op.add_column(sa.Column('mfa_secret', sa.String(length=255), nullable=True))
            if 'id_provider' not in existing_user_cols:
                batch_op.add_column(sa.Column('id_provider', sa.String(length=50), nullable=False, server_default='LOCAL'))
            if 'id_provider_subject' not in existing_user_cols:
                batch_op.add_column(sa.Column('id_provider_subject', sa.String(length=255), nullable=True))

    # Create user_sessions table if not exists
    if 'user_sessions' not in existing_tables:
        op.create_table(
            'user_sessions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('session_id', sa.String(length=64), nullable=False),
            sa.Column('refresh_token_hash', sa.String(length=64), nullable=False),
            sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('revoked_reason', sa.String(length=255), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('user_agent', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('last_used_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_user_sessions_id', 'user_sessions', ['id'])
        op.create_index('ix_user_sessions_user_id', 'user_sessions', ['user_id'])
        op.create_index('ix_user_sessions_session_id', 'user_sessions', ['session_id'], unique=True)
        op.create_index('ix_user_sessions_refresh_token_hash', 'user_sessions', ['refresh_token_hash'])
        op.create_index('ix_user_sessions_is_revoked', 'user_sessions', ['is_revoked'])
        op.create_index('ix_user_sessions_expires_at', 'user_sessions', ['expires_at'])

    # Create otp_challenges table if not exists
    if 'otp_challenges' not in existing_tables:
        op.create_table(
            'otp_challenges',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('account_identifier', sa.String(length=255), nullable=False),
            sa.Column('otp_hash', sa.String(length=64), nullable=False),
            sa.Column('purpose', sa.String(length=50), nullable=False, server_default='PASSWORD_RESET'),
            sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='3'),
            sa.Column('delivery_status', sa.String(length=50), nullable=False, server_default='PENDING'),
            sa.Column('is_used', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_otp_challenges_id', 'otp_challenges', ['id'])
        op.create_index('ix_otp_challenges_account_identifier', 'otp_challenges', ['account_identifier'])
        op.create_index('ix_otp_challenges_expires_at', 'otp_challenges', ['expires_at'])
        op.create_index('ix_otp_challenges_is_used', 'otp_challenges', ['is_used'])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if 'otp_challenges' in existing_tables:
        op.drop_table('otp_challenges')

    if 'user_sessions' in existing_tables:
        op.drop_table('user_sessions')

    if 'users' in existing_tables:
        existing_user_indexes = [idx["name"] for idx in inspector.get_indexes('users')]
        existing_user_cols = [c["name"] for c in inspector.get_columns('users')]
        with op.batch_alter_table('users', schema=None) as batch_op:
            for idx in ['ix_users_panchayat_name', 'ix_users_block_name', 'ix_users_district_name', 'ix_users_account_status']:
                if idx in existing_user_indexes:
                    batch_op.drop_index(idx)
            cols_to_drop = [
                'id_provider_subject', 'id_provider', 'mfa_secret', 'mfa_enabled',
                'department_id', 'panchayat_name', 'block_name', 'district_name',
                'password_changed_at', 'account_status'
            ]
            for col in cols_to_drop:
                if col in existing_user_cols:
                    batch_op.drop_column(col)
