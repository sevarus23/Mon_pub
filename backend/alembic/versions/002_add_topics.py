"""add topics column

Revision ID: 002
Revises: 001
Create Date: 2026-04-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "articles",
        sa.Column("topics", ARRAY(sa.String), server_default="{}", nullable=False),
    )
    op.create_index(
        "idx_articles_topics",
        "articles",
        ["topics"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("idx_articles_topics")
    op.drop_column("articles", "topics")
