from collections.abc import Sequence

from src.adapters.embedding.embedder import Embedder, Embedding

DEFAULT_TIMEOUT_SECONDS = 30.0


class HTTPEmbedder(Embedder):
    _base_url: str
    _secret: str
    _timeout: float

    def __init__(
        self,
        base_url: str,
        secret: str,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ):
        self._base_url = base_url.rstrip("/")
        self._secret = secret
        self._timeout = timeout

    def embed(self, texts: Sequence[str]) -> list[Embedding]:
        return NotImplemented  # type: ignore[return-value]
