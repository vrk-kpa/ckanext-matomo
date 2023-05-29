"""Add events field for package_stats

Revision ID: c2aea25862a9
Revises: f492c1786c97
Create Date: 2023-05-25 16:39:32.237859

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2aea25862a9'
down_revision = 'f492c1786c97'
branch_labels = None
depends_on = None


def upgrade():
    if not column_exists('package_stats', 'events'):
        op.add_column('package_stats', sa.Column('events', sa.Integer, default=0))
    pass


def downgrade():
    op.drop_column('package_stats', 'events')
    pass


def column_exists(table_name, column_name):
    bind = op.get_context().bind
    insp = sa.inspect(bind)
    columns = insp.get_columns(table_name)
    return any(c["name"] == column_name for c in columns)
    pass
