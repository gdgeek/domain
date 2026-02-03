"""Initial migration - create domains and configs tables.

Revision ID: 001
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create domains table
    op.create_table(
        'domains',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_domains_name', 'domains', ['name'])
    op.create_index('idx_domains_active', 'domains', ['is_active'])
    
    # Create configs table
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
    op.create_index('idx_configs_domain', 'configs', ['domain_id'])
    op.create_index('idx_configs_language', 'configs', ['language'])
    op.create_index('idx_configs_domain_language', 'configs', ['domain_id', 'language'])


def downgrade():
    op.drop_table('configs')
    op.drop_table('domains')
