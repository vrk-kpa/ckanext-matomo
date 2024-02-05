"""Add indexes to search terms table

Revision ID: 299beffac30a
Revises: ec140de715f6
Create Date: 2024-02-01 13:13:27.201693

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '299beffac30a'
down_revision = 'ec140de715f6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_search_terms_id', 'search_terms', ['id'], unique=True, if_not_exists=True)
    op.create_index('ix_search_terms_date', 'search_terms', ['date'], if_not_exists=True)
    pass


def downgrade():
    op.drop_index('ix_search_terms_id', 'search_terms')
    op.drop_index('ix_search_terms_date', 'search_terms')
    pass
