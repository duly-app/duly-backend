from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Computed,
    DateTime,
    Index,
    Integer,
    String,
    Table,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR

from src.adapters.orm.base import metadata

note_event_table = Table(
    "note_events",
    metadata,
    Column("seq", BigInteger, primary_key=True, autoincrement=True),
    Column("id", Uuid, nullable=False, unique=True),
    Column("note_id", Uuid, nullable=False, index=True),
    Column("event_type", String(20), nullable=False),
    Column("timestamp", DateTime(timezone=True), nullable=False),
    Column("author_id", Uuid, nullable=False),
    Column("author_type", String(20), nullable=False),
    Column("payload", JSONB, nullable=False),
)


note_table = Table(
    "notes",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("title", Text, nullable=False),
    Column("content", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("last_updated", DateTime(timezone=True), nullable=False),
    Column("updated_by", Uuid, nullable=False),
    Column("last_author_type", String(20), nullable=False),
    Column("owner", Uuid, nullable=False, index=True),
    Column("deleted", Boolean, nullable=False, default=False),
    Column("version", Integer, nullable=False),
    Column(
        "search_vector",
        TSVECTOR,
        Computed("to_tsvector('english', title || ' ' || content)", persisted=True),
    ),
)

Index("ix_notes_search_vector", note_table.c.search_vector, postgresql_using="gin")
