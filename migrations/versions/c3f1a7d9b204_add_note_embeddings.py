"""add note embeddings

Revision ID: c3f1a7d9b204
Revises: 7b1c9d4e2a10
Create Date: 2026-10-18 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "c3f1a7d9b204"
down_revision: Union[str, Sequence[str], None] = "7b1c9d4e2a10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIMENSIONS = 384


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "note_embeddings",
        sa.Column("note_id", sa.Uuid(), nullable=False),
        sa.Column("note_version", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSIONS), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("note_id"),
    )

    # NOTE: no vector index yet. An exact scan over a few hundred rows
    # beats an approximate index, which can only lose recall at this size.


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("note_embeddings")
    op.execute("DROP EXTENSION IF EXISTS vector")
