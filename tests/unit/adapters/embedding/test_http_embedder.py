import pytest
import requests

from src.adapters.embedding import HTTPEmbedder
from src.adapters.embedding.http_embedder import HEALTH_ATTEMPTS
from tests.unit.adapters.embedding.fake_http_client import FakeHTTPClient, response

BASE_URL = "http://embedder-qa:8000"
SECRET = "embedder-key"

TWO_EMBEDDINGS = response(payload={"embeddings": [[0.1, 0.2], [0.3, 0.4]]})
HEALTHY = response(payload={"status": "ok"})
REFUSED = requests.ConnectionError("connection refused")


class Waits:
    """Stands in for time.sleep, recording instead of waiting."""

    def __init__(self) -> None:
        self.taken: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.taken.append(seconds)


@pytest.fixture
def waits() -> Waits:
    return Waits()


def embedder(client: FakeHTTPClient, waits: Waits, **kwargs) -> HTTPEmbedder:
    return HTTPEmbedder(BASE_URL, SECRET, client=client, sleep=waits, **kwargs)


class TestReadiness:
    def test_ready_on_the_first_answer(self, waits: Waits):
        client = FakeHTTPClient(gets=HEALTHY)

        assert embedder(client, waits).is_ready()
        assert client.get_calls[0]["url"] == f"{BASE_URL}/health"
        assert waits.taken == []

    def test_ready_once_the_service_comes_up(self, waits: Waits):
        # Startup race: the pod refuses connections while it loads the
        # model, then answers. Retrying rides that out.
        client = FakeHTTPClient(gets=[REFUSED, HEALTHY])

        assert embedder(client, waits).is_ready()
        assert len(client.get_calls) == 2
        assert len(waits.taken) == 1

    def test_gives_up_after_the_last_attempt(self, waits: Waits):
        client = FakeHTTPClient(gets=REFUSED)

        assert not embedder(client, waits).is_ready()
        assert len(client.get_calls) == HEALTH_ATTEMPTS
        assert len(waits.taken) == HEALTH_ATTEMPTS - 1

    def test_an_error_status_is_not_ready(self, waits: Waits):
        client = FakeHTTPClient(gets=response(status_code=503))

        assert not embedder(client, waits).is_ready()

    def test_the_readiness_check_does_not_wait_as_long_as_an_embedding(
        self, waits: Waits
    ):
        client = FakeHTTPClient(gets=HEALTHY)

        embedder(client, waits, timeout=30.0).is_ready()

        assert client.get_calls[0]["timeout"] < 30.0


class TestEmbedding:
    def test_returns_one_embedding_per_text(self, waits: Waits):
        client = FakeHTTPClient(posts=TWO_EMBEDDINGS)

        assert embedder(client, waits).embed(["first", "second"]) == [
            [0.1, 0.2],
            [0.3, 0.4],
        ]

    def test_asks_the_document_side_of_the_service(self, waits: Waits):
        # Notes are passages, not queries. The two sides are separate
        # endpoints because an asymmetric model treats them differently.
        client = FakeHTTPClient(posts=TWO_EMBEDDINGS)

        embedder(client, waits).embed(["first", "second"])

        assert client.post_calls[0]["url"] == f"{BASE_URL}/embed/documents"
        assert client.post_calls[0]["json"] == {"texts": ["first", "second"]}

    def test_presents_the_shared_secret(self, waits: Waits):
        client = FakeHTTPClient(posts=TWO_EMBEDDINGS)

        embedder(client, waits).embed(["first", "second"])

        assert client.post_calls[0]["headers"] == {"Authorization": f"Bearer {SECRET}"}

    def test_bounds_the_wait(self, waits: Waits):
        # Without a timeout a stalled embedder would hold the sweeper's
        # thread forever, and no further note would ever be embedded.
        client = FakeHTTPClient(posts=TWO_EMBEDDINGS)

        embedder(client, waits, timeout=5.0).embed(["first", "second"])

        assert client.post_calls[0]["timeout"] == 5.0

    def test_does_not_double_up_the_slash(self, waits: Waits):
        client = FakeHTTPClient(posts=TWO_EMBEDDINGS)

        HTTPEmbedder(f"{BASE_URL}/", SECRET, client=client, sleep=waits).embed(
            ["first", "second"]
        )

        assert client.post_calls[0]["url"] == f"{BASE_URL}/embed/documents"

    def test_raises_when_the_secret_is_rejected(self, waits: Waits):
        client = FakeHTTPClient(posts=response(status_code=401))

        with pytest.raises(requests.HTTPError):
            embedder(client, waits).embed(["first"])

    def test_raises_when_the_service_returns_too_few_embeddings(self, waits: Waits):
        # The caller pairs embeddings with notes by position, so a short
        # response must fail rather than embed the wrong note.
        client = FakeHTTPClient(posts=response(payload={"embeddings": [[0.1, 0.2]]}))

        with pytest.raises(ValueError):
            embedder(client, waits).embed(["first", "second"])
