"""Memory Engine module."""

from __future__ import annotations

from ..core.plugin import Plugin
from .embeddings import Embedder, HashingEmbedder
from .engine import MemoryEngine
from .models import ContextResult, MemoryRecord
from .stores import InMemoryStore, MemoryStore
from .summarizers import ExtractiveSummarizer, Summarizer

plugin = Plugin(
    name=MemoryEngine.name,
    factory=MemoryEngine,
    summary=MemoryEngine.summary,
    version=MemoryEngine.version,
)

__all__ = [
    "ContextResult",
    "Embedder",
    "ExtractiveSummarizer",
    "HashingEmbedder",
    "InMemoryStore",
    "MemoryEngine",
    "MemoryRecord",
    "MemoryStore",
    "Summarizer",
    "plugin",
]
