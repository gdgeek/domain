"""Add default_config field to domains.

Revision ID: 002
Revises: 001
Create Date: 2026-02-20
"""
from alembic import op
import sqlalchemy as sa


revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col['name'] for col in inspector.get_columns('domains')}

    if 'default_config' not in columns:
        op.add_column('domains', sa.Column('default_config', sa.JSON(), nullable=True))

    op.execute("UPDATE domains SET default_config = '{}' WHERE default_config IS NULL")
    with op.batch_alter_table('domains') as batch_op:
        batch_op.alter_column('default_config', nullable=False)


def downgrade():
    with op.batch_alter_table('domains') as batch_op:
        batch_op.drop_column('default_config')
