"""add core_rank column

Revision ID: 005
Revises: 004
Create Date: 2026-04-05
"""

from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "articles",
        sa.Column("core_rank", sa.String(10), nullable=True),
    )
    op.create_index("idx_articles_core_rank", "articles", ["core_rank"])


def downgrade() -> None:
    op.drop_index("idx_articles_core_rank")
    op.drop_column("articles", "core_rank")
