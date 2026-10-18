"""Running the sweeper beside the web app."""

import logging
import threading

from src.adapters.embedding import HTTPEmbedder
from src.db import create_session_factory
from src.environment import EnvVar
from src.service.sweeper import run_sweeper

logger = logging.getLogger(__name__)

THREAD_NAME = "note-embedding-sweeper"


def start_sweeper(
    config: dict[EnvVar, str], stop: threading.Event | None = None
) -> threading.Thread | None:
    """Start the sweeper in a daemon thread, if this process should run one."""
    if not config.get(EnvVar.EMBEDDER_URL):
        logger.info("EMBEDDER_URL is not set, so the sweeper will not run")

        return None

    if not _is_serving_process(config):
        return None

    thread = threading.Thread(
        target=run_sweeper,
        args=(
            create_session_factory(config[EnvVar.DATABASE_URL]),
            HTTPEmbedder(
                config[EnvVar.EMBEDDER_URL], config.get(EnvVar.EMBEDDER_KEY, "")
            ),
        ),
        kwargs={"stop": stop},
        name=THREAD_NAME,
        daemon=True,
    )
    thread.start()

    logger.info("sweeper started")

    return thread


def _is_serving_process(config: dict[EnvVar, str]) -> bool:
    """Whether this process is the one serving requests.

    Under the Flask reloader there are two: a parent that only watches files
    and a child that serves. Both import the app, so without this check the
    sweeper would run twice. Werkzeug marks the child.
    """
    if config.get(EnvVar.FLASK_DEBUG) != "1":
        return True

    return config.get(EnvVar.WERKZEUG_RUN_MAIN) == "true"
