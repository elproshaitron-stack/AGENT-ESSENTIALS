"""The Memory Engine module."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from ..core.base import Module
from ..core.exceptions import ValidationError
from ..utilities.text import approx_token_count, cosine, keyword_overlap, truncate_to_tokens
from .embeddings import Embedder, HashingEmbedder
from .models import ContextResult, MemoryRecord
from .stores import InMemoryStore, MemoryStore
from .summarizers import ExtractiveSummarizer, Summarizer


class MemoryEngine(Module):
    """Design and operate an agent's memory: save, retrieve, summarize, optimize."""

    name = "memory"
    version = "0.1.0"
    summary = "Short/long-term memory with retrieval, summarization and context packing."

    def __init__(
        self,
        store: MemoryStore | None = None,
        embedder: Embedder | None = None,
        summarizer: Summarizer | None = None,
    ) -> None:
        self.store = store or InMemoryStore()
        self.embedder = embedder or HashingEmbedder()
        self.summarizer = summarizer or ExtractiveSummarizer()

    # -- core operations ----------------------------------------------------
    def save_memory(
        self,
        content: str,
        *,
        kind: str = "episodic",
        metadata: Mapping[str, Any] | None = None,
        importance: float = 0.5,
    ) -> MemoryRecord:
        if not content or not content.strip():
            raise ValidationError("Cannot save empty memory content")
        if not 0.0 <= importance <= 1.0:
            raise ValidationError("importance must be in [0, 1]")
        record = MemoryRecord(
            content=content.strip(),
            kind=kind,
            metadata=dict(metadata or {}),
            importance=importance,
        )
        self.store.add(record, self.embedder.embed(record.content))
        return record

    def retrieve_memory(
        self,
        query: str,
        *,
        k: int = 5,
        kind: str | None = None,
        alpha: float = 0.7,
    ) -> list[MemoryRecord]:
        """Hybrid retrieval: ``alpha`` blends semantic similarity with keyword overlap."""
        if k <= 0:
            raise ValidationError("k must be positive")
        if not 0.0 <= alpha <= 1.0:
            raise ValidationError("alpha must be in [0, 1]")
        query_embedding = self.embedder.embed(query)
        scored: list[tuple[float, MemoryRecord]] = []
        for record, embedding in self.store.items(kind):
            semantic = cosine(query_embedding, embedding) if embedding else 0.0
            lexical = keyword_overlap(query, record.content)
            base = alpha * semantic + (1.0 - alpha) * lexical
            score = base * (0.85 + 0.15 * record.importance)
            scored.append((score, record))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [replace(record, score=round(score, 4)) for score, record in scored[:k]]

    def summarize_memory(self, *, kind: str | None = None, max_sentences: int = 3) -> str:
        texts = [record.content for record in self.store.all(kind)]
        return self.summarizer.summarize(texts, max_sentences=max_sentences)

    def optimize_context(
        self,
        query: str,
        *,
        token_budget: int = 1_000,
        k: int = 20,
        kind: str | None = None,
    ) -> ContextResult:
        """Pack the most relevant memories into ``token_budget`` tokens.

        Greedily includes top-ranked memories that fit, then compresses the
        overflow into a single summary line if any budget remains.
        """
        if token_budget <= 0:
            raise ValidationError("token_budget must be positive")
        candidates = self.retrieve_memory(query, k=k, kind=kind)
        included: list[MemoryRecord] = []
        overflow: list[MemoryRecord] = []
        used = 0
        for record in candidates:
            cost = approx_token_count(record.content)
            if used + cost <= token_budget:
                included.append(record)
                used += cost
            else:
                overflow.append(record)

        # If no whole memory fit the budget, include a truncated fragment of the
        # most relevant one so the returned context is never empty.
        if overflow and not included:
            top = overflow[0]
            fragment = truncate_to_tokens(top.content, token_budget)
            if fragment:
                included.append(
                    replace(
                        top,
                        content=fragment + " \u2026",
                        metadata={**top.metadata, "truncated": True},
                    )
                )
                used += approx_token_count(included[0].content)
                overflow = overflow[1:]

        pieces = [r.content for r in included]
        dropped = 0
        if overflow:
            remaining = token_budget - used
            if remaining > 10:
                summary = self.summarizer.summarize([r.content for r in overflow], max_sentences=2)
                if approx_token_count(summary) <= remaining:
                    pieces.append(f"[summary of {len(overflow)} older memories] {summary}")
                    used += approx_token_count(summary)
                else:
                    dropped = len(overflow)
            else:
                dropped = len(overflow)

        return ContextResult(
            context="\n".join(pieces),
            used_tokens=used,
            token_budget=token_budget,
            included=included,
            summarized_count=len(overflow) - dropped,
            dropped_count=dropped,
        )

    # -- Module API ---------------------------------------------------------
    def run(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        # Optionally seed the store so the operation is usable statelessly (CLI).
        for item in payload.get("memories", []):
            if isinstance(item, str):
                self.save_memory(item)
            elif isinstance(item, Mapping):
                self.save_memory(
                    item["content"],
                    kind=item.get("kind", "episodic"),
                    metadata=item.get("metadata"),
                    importance=item.get("importance", 0.5),
                )

        op = payload.get("op", "retrieve")
        if op == "save":
            record = self.save_memory(
                payload["content"],
                kind=payload.get("kind", "episodic"),
                metadata=payload.get("metadata"),
                importance=payload.get("importance", 0.5),
            )
            return {"record": record.to_dict()}
        if op == "retrieve":
            results = self.retrieve_memory(
                payload["query"],
                k=int(payload.get("k", 5)),
                kind=payload.get("kind"),
                alpha=float(payload.get("alpha", 0.7)),
            )
            return {"results": [r.to_dict() for r in results]}
        if op == "summarize":
            return {
                "summary": self.summarize_memory(
                    kind=payload.get("kind"),
                    max_sentences=int(payload.get("max_sentences", 3)),
                )
            }
        if op == "optimize_context":
            result = self.optimize_context(
                payload["query"],
                token_budget=int(payload.get("token_budget", 1_000)),
                k=int(payload.get("k", 20)),
                kind=payload.get("kind"),
            )
            return result.to_dict()
        raise ValidationError(
            f"Unknown memory op {op!r}; expected save|retrieve|summarize|optimize_context"
        )


__all__ = ["MemoryEngine"]
