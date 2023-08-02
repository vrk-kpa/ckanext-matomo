"""Add events field for resource_stats

Revision ID: ec140de715f6
Revises: c2aea25862a9
Create Date: 2023-07-05 14:14:07.852722

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ec140de715f6'
down_revision = 'c2aea25862a9'
branch_labels = None
depends_on = None


def upgrade():
    if not column_exists('resource_stats', 'events'):
        op.add_column('resource_stats', sa.Column('events', sa.Integer, default=0))
    pass


def downgrade():
    op.drop_column('resource_stats', 'events')
    pass


def column_exists(table_name, column_name):
    bind = op.get_context().bind
    insp = sa.inspect(bind)
    columns = insp.get_columns(table_name)
    return any(c["name"] == column_name for c in columns)
    pass
