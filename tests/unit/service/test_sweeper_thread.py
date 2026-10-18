import threading

from src.environment import EnvVar
from src.service.sweeper_thread import THREAD_NAME, start_sweeper

CONFIGURED = {
    EnvVar.EMBEDDER_URL: "http://duly-embedder:8100",
    EnvVar.EMBEDDER_KEY: "embedder-key",
    EnvVar.DATABASE_URL: "postgresql+psycopg2://admin:password@localhost:5432/unused",
}

RELOADING = {**CONFIGURED, EnvVar.FLASK_DEBUG: "1"}


def running_sweepers() -> list[str]:
    return [
        thread.name for thread in threading.enumerate() if thread.name == THREAD_NAME
    ]


def test_no_sweeper_runs_without_an_embedder_url():
    # The test suite and anyone running the app without the embedding service
    # must not get a background thread polling the database.
    config = {EnvVar.DATABASE_URL: CONFIGURED[EnvVar.DATABASE_URL]}

    assert start_sweeper(config) is None
    assert running_sweepers() == []


def test_no_sweeper_runs_in_the_reloader_parent():
    # The parent only watches files, but it imports the app too, so without
    # the check the sweeper would run in both processes.
    assert start_sweeper(RELOADING) is None
    assert running_sweepers() == []


def test_the_sweeper_runs_in_the_reloader_child():
    # Stopped before it starts, so the loop exits without reaching the
    # database. Only the thread's creation is under test here.
    stop = threading.Event()
    stop.set()

    thread = start_sweeper({**RELOADING, EnvVar.WERKZEUG_RUN_MAIN: "true"}, stop=stop)

    assert thread is not None
    assert thread.name == THREAD_NAME
    # A daemon, so a running sweep cannot hold up shutdown.
    assert thread.daemon

    thread.join(timeout=5)

    assert not thread.is_alive()
