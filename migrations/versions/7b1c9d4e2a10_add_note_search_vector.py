"""add note search vector

Revision ID: 7b1c9d4e2a10
Revises: 0294a00df047
Create Date: 2026-10-12 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "7b1c9d4e2a10"
down_revision: Union[str, Sequence[str], None] = "0294a00df047"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "notes",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "to_tsvector('english', title || ' ' || content)", persisted=True
            ),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_notes_search_vector",
        "notes",
        ["search_vector"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_notes_search_vector", table_name="notes")
    op.drop_column("notes", "search_vector")
