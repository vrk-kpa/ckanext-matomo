"""Add downloads field for resource_stats

Revision ID: f492c1786c97
Revises: 
Create Date: 2022-11-14 07:43:25.308276

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f492c1786c97'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('resource_stats', sa.Column('downloads', sa.Integer))
    pass


def downgrade():
    op.drop_column('resource_stats', 'downloads')
    pass
