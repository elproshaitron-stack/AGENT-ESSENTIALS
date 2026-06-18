"""Memory stores. Ships with an in-memory backend; implement ``MemoryStore`` to
add Redis, Postgres/pgvector, or a managed vector DB.
"""

from __future__ import annotations

import abc

from .models import MemoryRecord

Embedding = list[float]


class MemoryStore(abc.ABC):
    """Persistence interface for memories and their embeddings."""

    @abc.abstractmethod
    def add(self, record: MemoryRecord, embedding: Embedding | None = None) -> None: ...

    @abc.abstractmethod
    def get(self, record_id: str) -> MemoryRecord | None: ...

    @abc.abstractmethod
    def delete(self, record_id: str) -> bool: ...

    @abc.abstractmethod
    def items(self, kind: str | None = None) -> list[tuple[MemoryRecord, Embedding | None]]: ...

    @abc.abstractmethod
    def clear(self) -> None: ...

    def all(self, kind: str | None = None) -> list[MemoryRecord]:
        return [record for record, _ in self.items(kind)]

    def count(self, kind: str | None = None) -> int:
        return len(self.items(kind))


class InMemoryStore(MemoryStore):
    """Simple dict-backed store. Insertion order is preserved."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[MemoryRecord, Embedding | None]] = {}

    def add(self, record: MemoryRecord, embedding: Embedding | None = None) -> None:
        self._data[record.id] = (record, embedding)

    def get(self, record_id: str) -> MemoryRecord | None:
        entry = self._data.get(record_id)
        return entry[0] if entry else None

    def delete(self, record_id: str) -> bool:
        return self._data.pop(record_id, None) is not None

    def items(self, kind: str | None = None) -> list[tuple[MemoryRecord, Embedding | None]]:
        if kind is None:
            return list(self._data.values())
        return [pair for pair in self._data.values() if pair[0].kind == kind]

    def clear(self) -> None:
        self._data.clear()


__all__ = ["Embedding", "InMemoryStore", "MemoryStore"]
