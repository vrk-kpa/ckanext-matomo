"""Create ckanext-matomo tables

Revision ID: 5a2342a4f2e8
Revises:
Create Date: 2026-01-09 09:01:51.454009

"""
from alembic import op
import sqlalchemy as sa
import datetime


# revision identifiers, used by Alembic.
revision = '5a2342a4f2e8'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    inspector = sa.inspect(engine)
    tables = inspector.get_table_names()

    if "search_terms" not in tables:
        op.create_table(
            "search_terms",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True, unique=True),
            sa.Column("search_term", sa.UnicodeText, nullable=False, primary_key=True),
            sa.Column("date", sa.DateTime, default=datetime.datetime.now, primary_key=True),
            sa.Column("count", sa.Integer, default=0),
        )

    if "package_stats" not in tables:
        op.create_table(
            "package_stats",
            sa.Column("package_id", sa.UnicodeText, nullable=False, index=True, primary_key=True),
            sa.Column("visit_date", sa.DateTime, default=datetime.datetime.now, primary_key=True),
            sa.Column("visits", sa.Integer, default=0),
            sa.Column("entrances", sa.Integer, default=0),
            sa.Column("downloads", sa.Integer, default=0),
            sa.Column("events", sa.Integer, default=0)
        )

    if "resource_stats" not in tables:
        op.create_table(
            "resource_stats",
            sa.Column("resource_id", sa.UnicodeText, nullable=False, index=True, primary_key=True),
            sa.Column("visit_date", sa.DateTime, default=datetime.datetime.now, primary_key=True),
            sa.Column("visits", sa.Integer, default=0),
            sa.Column("downloads", sa.Integer, default=0),
            sa.Column("events", sa.Integer, default=0),
        )

    if "audience_location" not in tables:
        op.create_table(
            "audience_location",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True, unique=True),
            sa.Column("location_name", sa.UnicodeText, nullable=False, primary_key=True),
        )

    if "audience_location_date" not in tables:
        op.create_table(
            "audience_location_date",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True, unique=True),
            sa.Column("date", sa.DateTime, default=datetime.datetime.now, primary_key=True),
            sa.Column("visits", sa.Integer, default=0),
            sa.Column("location_id", sa.Integer, sa.ForeignKey("audience_location.id")),
            sa.ForeignKey("audience_location.id", ondelete="CASCADE", onupdate="CASCADE"),
        )


def downgrade():
    op.drop_table("search_terms")
    op.drop_table("package_stats")
    op.drop_table("resource_stats")
    op.drop_table("audience_location")
    op.drop_table("audience_location_date")
