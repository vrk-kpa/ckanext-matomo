"""add indexes to date columns

Revision ID: e325f57c80b5
Revises: 299beffac30a
Create Date: 2024-02-13 07:46:25.846061

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e325f57c80b5'
down_revision = '299beffac30a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_package_stats_visit_date', 'package_stats', ['visit_date'], if_not_exists=True)
    op.create_index('ix_resource_stats_visit_date', 'resource_stats', ['visit_date'], if_not_exists=True)
    pass


def downgrade():
    op.drop_index('ix_package_stats_visit_date', 'package_stats')
    op.drop_index('ix_resource_stats_visit_date', 'resource_stats')
    pass
