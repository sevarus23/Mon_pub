"""initial

Revision ID: 001
Revises:
Create Date: 2026-03-24
"""

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "articles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("num_id", sa.String(100), unique=True, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("authors", sa.Text, nullable=False),
        sa.Column("doi", sa.String(255), unique=True, nullable=True),
        sa.Column("published_at", sa.Date, nullable=True),
        sa.Column("journal_name", sa.String(500), nullable=True),
        sa.Column("issn", sa.String(50), nullable=True),
        sa.Column("type", sa.String(50), nullable=True),
        sa.Column("quartile", sa.String(2), nullable=True),
        sa.Column("publisher", sa.String(500), nullable=True),
        sa.Column("cited_by_count", sa.Integer, nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_index("idx_articles_title_trgm", "articles", ["title"], postgresql_using="gin", postgresql_ops={"title": "gin_trgm_ops"})
    op.create_index("idx_articles_authors_trgm", "articles", ["authors"], postgresql_using="gin", postgresql_ops={"authors": "gin_trgm_ops"})
    op.create_index("idx_articles_journal_trgm", "articles", ["journal_name"], postgresql_using="gin", postgresql_ops={"journal_name": "gin_trgm_ops"})
    op.create_index("idx_articles_doi", "articles", ["doi"])
    op.create_index("idx_articles_issn", "articles", ["issn"])
    op.create_index("idx_articles_published_at", "articles", ["published_at"])


def downgrade() -> None:
    op.drop_table("articles")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
