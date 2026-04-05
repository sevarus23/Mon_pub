"""add in_scopus boolean column

Revision ID: 006
Revises: 005
Create Date: 2026-04-05
"""

from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "articles",
        sa.Column("in_scopus", sa.Boolean, nullable=False, server_default=sa.false()),
    )
    op.create_index("idx_articles_in_scopus", "articles", ["in_scopus"])


def downgrade() -> None:
    op.drop_index("idx_articles_in_scopus")
    op.drop_column("articles", "in_scopus")
