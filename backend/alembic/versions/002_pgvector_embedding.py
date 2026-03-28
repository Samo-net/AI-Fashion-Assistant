"""Migrate clip_embedding from JSON text to native pgvector vector(512)

Revision ID: 002
Revises: 001
Create Date: 2026-03-28
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable the pgvector extension (safe to run even if already enabled)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Drop the old JSON text column and add a native vector(512) column.
    # Any embeddings stored as JSON text are discarded here — items will be
    # re-classified by CLIP on next access (clip_processed is reset to false).
    op.drop_column("wardrobe_items", "clip_embedding")
    op.add_column(
        "wardrobe_items",
        sa.Column("clip_embedding", Vector(512), nullable=True),
    )

    # Reset clip_processed so all items are re-classified with the new column
    op.execute("UPDATE wardrobe_items SET clip_processed = false")

    # IVFFlat index for fast approximate nearest-neighbour cosine search.
    # lists=100 is a good default for a wardrobe-scale dataset (<100k rows).
    op.execute(
        "CREATE INDEX ix_wardrobe_items_clip_embedding "
        "ON wardrobe_items USING ivfflat (clip_embedding vector_cosine_ops) "
        "WITH (lists = 100)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_wardrobe_items_clip_embedding")
    op.drop_column("wardrobe_items", "clip_embedding")
    op.add_column(
        "wardrobe_items",
        sa.Column("clip_embedding", sa.Text, nullable=True),
    )
