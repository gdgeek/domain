"""Initial migration - create domains and configs tables.

Revision ID: 001
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa
from alembic import context


# revision identifiers
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def _table_exists(table_name, bind):
    """Check if table exists, safe for both online and offline mode."""
    if context.is_offline_mode():
        return False
    inspector = sa.inspect(bind)
    return table_name in set(inspector.get_table_names())


def _index_exists(index_name, table_name, bind):
    """Check if index exists, safe for both online and offline mode."""
    if context.is_offline_mode():
        return False
    inspector = sa.inspect(bind)
    existing = {idx['name'] for idx in inspector.get_indexes(table_name)}
    return index_name in existing


def _create_index_if_not_exists(bind, index_name, table_name, columns):
    """Create index only if it doesn't already exist."""
    if not _index_exists(index_name, table_name, bind):
        op.create_index(index_name, table_name, columns)


def upgrade():
    bind = op.get_bind()

    # Create domains table (idempotent)
    if not _table_exists('domains', bind):
        op.create_table(
            'domains',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
            sa.Column('fallback_domain_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name'),
            sa.ForeignKeyConstraint(['fallback_domain_id'], ['domains.id'], ondelete='SET NULL')
        )
    _create_index_if_not_exists(bind, 'idx_domains_name', 'domains', ['name'])
    _create_index_if_not_exists(bind, 'idx_domains_active', 'domains', ['is_active'])

    # Create configs table (idempotent)
    if not _table_exists('configs', bind):
        op.create_table(
            'configs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('domain_id', sa.Integer(), nullable=False),
            sa.Column('language', sa.String(length=10), nullable=False, default='zh-CN'),
            sa.Column('data', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['domain_id'], ['domains.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('domain_id', 'language', name='uq_config_domain_language')
        )
    _create_index_if_not_exists(bind, 'idx_configs_domain', 'configs', ['domain_id'])
    _create_index_if_not_exists(bind, 'idx_configs_language', 'configs', ['language'])
    _create_index_if_not_exists(bind, 'idx_configs_domain_language', 'configs', ['domain_id', 'language'])


def downgrade():
    op.drop_table('configs')
    op.drop_table('domains')
