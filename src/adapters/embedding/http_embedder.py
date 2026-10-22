import time
from collections.abc import Callable, Sequence

import requests

from src.adapters.embedding.embedder import Embedder, Embedding
from src.adapters.embedding.http_client import HTTPClient
from src.logs import get_logger

logger = get_logger(__name__)

DEFAULT_TIMEOUT_SECONDS = 30.0
DOCUMENTS_PATH = "/embed/documents"
HEALTH_PATH = "/health"

HEALTH_TIMEOUT_SECONDS = 2.0
HEALTH_ATTEMPTS = 3
HEALTH_DELAY_SECONDS = 1.0


class HTTPEmbedder(Embedder):
    """Calls the embedding service over the internal network."""

    _base_url: str
    _secret: str
    _timeout: float
    _client: HTTPClient
    _sleep: Callable[[float], None]

    def __init__(
        self,
        base_url: str,
        secret: str,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        client: HTTPClient | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self._base_url = base_url.rstrip("/")
        self._secret = secret
        self._timeout = timeout
        self._client = client if client is not None else requests.Session()
        self._sleep = sleep

    def is_ready(self) -> bool:
        """Poll the service's health endpoint, giving it a moment to come up.

        A pod that is rolling, restarting or still loading its model refuses
        connections. Retrying rides out a short gap; past that the caller is
        better off waiting for its next turn than embedding into a void.
        """
        for attempt in range(1, HEALTH_ATTEMPTS + 1):
            if self._healthy():
                return True

            logger.debug(
                "embedder is not ready (attempt %d of %d)", attempt, HEALTH_ATTEMPTS
            )

            if attempt < HEALTH_ATTEMPTS:
                self._sleep(HEALTH_DELAY_SECONDS)

        return False

    def _healthy(self) -> bool:
        try:
            response = self._client.get(
                f"{self._base_url}{HEALTH_PATH}", timeout=HEALTH_TIMEOUT_SECONDS
            )
        except requests.RequestException:
            return False

        return response.ok

    def embed(self, texts: Sequence[str]) -> list[Embedding]:
        response = self._client.post(
            f"{self._base_url}{DOCUMENTS_PATH}",
            json={"texts": list(texts)},
            headers={"Authorization": f"Bearer {self._secret}"},
            timeout=self._timeout,
        )
        response.raise_for_status()

        embeddings: list[Embedding] = response.json()["embeddings"]

        if len(embeddings) != len(texts):
            raise ValueError(
                f"asked for {len(texts)} embeddings, got {len(embeddings)}"
            )

        return embeddings
