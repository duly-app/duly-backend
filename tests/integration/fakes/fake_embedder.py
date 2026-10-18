from collections.abc import Sequence

from src.adapters.embedding import Embedder, Embedding
from src.adapters.orm.notes import EMBEDDING_DIMENSIONS


def vector(fill: float) -> Embedding:
    """A whole vector of one value, so a test can name what it expects."""
    return [fill] * EMBEDDING_DIMENSIONS


class FakeEmbedder(Embedder):
    _vectors: dict[str, Embedding]
    _default: Embedding
    calls: list[list[str]]

    def __init__(
        self,
        vectors: dict[str, Embedding] | None = None,
        default: Embedding | None = None,
    ):
        self._vectors = vectors or {}
        self._default = default if default is not None else vector(0.0)
        self.calls = []

    def embed(self, texts: Sequence[str]) -> list[Embedding]:
        self.calls.append(list(texts))

        return [self._vectors.get(text, self._default) for text in texts]
