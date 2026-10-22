from collections.abc import Sequence

from src.adapters.embedding import Embedder, Embedding
from src.adapters.orm.notes import EMBEDDING_DIMENSIONS


def vector(fill: float) -> Embedding:
    """A whole vector of one value, so a test can name what it expects."""
    return [fill] * EMBEDDING_DIMENSIONS


class FakeEmbedder(Embedder):
    _vectors: dict[str, Embedding]
    _default: Embedding
    _ready: bool
    _error: Exception | None
    calls: list[list[str]]
    queries: list[list[str]]

    def __init__(
        self,
        vectors: dict[str, Embedding] | None = None,
        default: Embedding | None = None,
        ready: bool = True,
        error: Exception | None = None,
    ):
        self._vectors = vectors or {}
        self._default = default if default is not None else vector(0.0)
        self._ready = ready
        self._error = error
        self.calls = []
        self.queries = []

    def is_ready(self) -> bool:
        return self._ready

    def embed_documents(self, texts: Sequence[str]) -> list[Embedding]:
        self.calls.append(list(texts))

        return self._embed(texts)

    def embed_query(self, texts: Sequence[str]) -> list[Embedding]:
        self.queries.append(list(texts))

        return self._embed(texts)

    def _embed(self, texts: Sequence[str]) -> list[Embedding]:
        if self._error is not None:
            raise self._error

        return [self._vectors.get(text, self._default) for text in texts]
