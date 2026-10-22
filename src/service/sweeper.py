"""The sweeper fills in missing note embeddings, a batch at a time."""

import threading
import time
from contextlib import closing

from sqlalchemy.orm import sessionmaker

from src.adapters.embedding import Embedder
from src.adapters.repository.note_embeddings import fetch_pending_notes, store_embedding
from src.logs import get_logger

logger = get_logger(__name__)

BATCH_SIZE = 32
PERIOD_SECONDS = 30.0


def sweep_once(
    session_factory: sessionmaker, embedder: Embedder, limit: int = BATCH_SIZE
) -> int:
    """Embed one batch of notes. Returns how many were stored.

    The gap that opens between reading and writing is what store()'s version
    guard is for.
    """
    with closing(session_factory()) as session:
        notes = fetch_pending_notes(session, limit)

    if not notes:
        return 0

    if not embedder.is_ready():
        logger.info(
            "embedder is unavailable, so the sweep stands down",
            extra={"pending": len(notes)},
        )

        return 0

    embeddings = embedder.embed([note.text for note in notes])

    with closing(session_factory()) as session:
        results = [
            store_embedding(session, note.id, note.version, embedding)
            for note, embedding in zip(notes, embeddings, strict=True)
        ]
        session.commit()

    return results.count(True)


def run_sweeper(
    session_factory: sessionmaker,
    embedder: Embedder,
    period: float = PERIOD_SECONDS,
    stop: threading.Event | None = None,
) -> None:
    stopping = stop or threading.Event()

    while not stopping.is_set():
        started = time.monotonic()

        try:
            stored = sweep_once(session_factory, embedder)

            if stored:
                logger.info("embedded %d notes", stored)
        except Exception:
            logger.exception("sweep failed")

        stopping.wait(max(0.0, period - (time.monotonic() - started)))
