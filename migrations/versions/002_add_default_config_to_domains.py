"""Add default_config field to domains.

Revision ID: 002
Revises: 001
Create Date: 2026-02-20
"""
from alembic import op
import sqlalchemy as sa
from alembic import context


revision = '002'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def _column_exists(table_name, column_name, bind):
    """Check if column exists, safe for both online and offline mode."""
    if context.is_offline_mode():
        return False
    inspector = sa.inspect(bind)
    columns = {col['name'] for col in inspector.get_columns(table_name)}
    return column_name in columns


def upgrade():
    bind = op.get_bind()

    if not _column_exists('domains', 'default_config', bind):
        op.add_column('domains', sa.Column('default_config', sa.JSON(), nullable=True))

    op.execute("UPDATE domains SET default_config = '{}' WHERE default_config IS NULL")

    if not context.is_offline_mode() and bind.dialect.name == 'mysql':
        op.execute("ALTER TABLE domains MODIFY default_config JSON NOT NULL")
    else:
        with op.batch_alter_table('domains') as batch_op:
            batch_op.alter_column('default_config', nullable=False)


def downgrade():
    with op.batch_alter_table('domains') as batch_op:
        batch_op.drop_column('default_config')
