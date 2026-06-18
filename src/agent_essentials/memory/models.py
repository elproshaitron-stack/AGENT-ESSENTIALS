"""Typed models for the Memory Engine."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ..core.types import Serializable


@dataclass(slots=True)
class MemoryRecord(Serializable):
    """A single stored memory."""

    content: str
    kind: str = "episodic"  # episodic | fact | summary | <custom>
    metadata: dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5  # 0..1, nudges retrieval ranking
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: float = field(default_factory=time.time)
    score: float | None = None  # similarity score, populated on retrieval


@dataclass(slots=True)
class ContextResult(Serializable):
    """Result of packing memories into a bounded context window."""

    context: str
    used_tokens: int
    token_budget: int
    included: list[MemoryRecord]
    summarized_count: int
    dropped_count: int


__all__ = ["ContextResult", "MemoryRecord"]
