from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TypeAlias

Embedding: TypeAlias = list[float]


class EmbedderError(RuntimeError):
    """The embedding service could not be reached or did not answer usably."""


class Embedder(ABC):
    """Turns text into vectors."""

    @abstractmethod
    def is_ready(self) -> bool:
        """Whether it can embed right now, so a caller can hold off."""

    @abstractmethod
    def embed_documents(self, texts: Sequence[str]) -> list[Embedding]:
        """One vector per text, in the order given."""

    def embed_query(self, texts: Sequence[str]) -> list[Embedding]:
        """Symmetric by default: one space, so a query embeds like a passage."""
        return self.embed_documents(texts)
