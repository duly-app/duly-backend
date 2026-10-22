from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TypeAlias

Embedding: TypeAlias = list[float]


class Embedder(ABC):
    """Turns text into vectors."""

    @abstractmethod
    def is_ready(self) -> bool:
        """Whether it can embed right now, so a caller can hold off."""

    @abstractmethod
    def embed(self, texts: Sequence[str]) -> list[Embedding]:
        """One vector per text, in the order given."""
