"""add white_list_level column

Revision ID: 004
Revises: 003
Create Date: 2026-04-05
"""

from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "articles",
        sa.Column("white_list_level", sa.Integer, nullable=True),
    )
    op.create_index(
        "idx_articles_white_list_level",
        "articles",
        ["white_list_level"],
    )


def downgrade() -> None:
    op.drop_index("idx_articles_white_list_level")
    op.drop_column("articles", "white_list_level")
