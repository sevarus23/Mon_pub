"""add full-text search vector

Revision ID: 003
Revises: 002
Create Date: 2026-04-05
"""

from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add generated tsvector column for full-text search with stemming
    op.execute(
        "ALTER TABLE articles ADD COLUMN search_vector tsvector "
        "GENERATED ALWAYS AS ("
        "to_tsvector('english', coalesce(title, '') || ' ' || coalesce(authors, ''))"
        ") STORED"
    )
    op.create_index(
        "idx_articles_fts",
        "articles",
        ["search_vector"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("idx_articles_fts")
    op.execute("ALTER TABLE articles DROP COLUMN search_vector")
