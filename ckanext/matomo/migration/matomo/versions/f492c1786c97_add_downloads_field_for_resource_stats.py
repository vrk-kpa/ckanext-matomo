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
    if not column_exists('resource_stats', 'downloads'):
        op.add_column('resource_stats', sa.Column('downloads', sa.Integer, default=0))
    pass


def downgrade():
    op.drop_column('resource_stats', 'downloads')
    pass


def column_exists(table_name, column_name):
    bind = op.get_context().bind
    insp = sa.inspect(bind)
    columns = insp.get_columns(table_name)
    return any(c["name"] == column_name for c in columns)
