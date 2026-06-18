"""Tests for the Memory Engine."""

from __future__ import annotations

import pytest

from agent_essentials.core.exceptions import ValidationError
from agent_essentials.memory import (
    ExtractiveSummarizer,
    HashingEmbedder,
    InMemoryStore,
    MemoryEngine,
    MemoryRecord,
)


def test_hashing_embedder_deterministic_and_normalized():
    emb = HashingEmbedder(dim=64)
    v1 = emb.embed("the quick brown fox")
    v2 = emb.embed("the quick brown fox")
    assert v1 == v2
    assert len(v1) == 64
    assert sum(x * x for x in v1) == pytest.approx(1.0, abs=1e-9)
    assert emb.embed("") == [0.0] * 64
    assert emb.embed("totally different text here") != v1


def test_extractive_summarizer():
    s = ExtractiveSummarizer()
    assert s.summarize([]) == ""
    text = (
        "Cats are great pets. Cats are independent and clean. "
        "Dogs are loyal companions. The weather today is sunny and warm. "
        "Many people enjoy keeping cats as pets in apartments."
    )
    summary = s.summarize([text], max_sentences=2)
    assert summary
    assert len(summary) < len(text)


def test_inmemory_store_crud():
    store = InMemoryStore()
    r = MemoryRecord(content="hello", kind="fact")
    store.add(r, [0.0])
    assert store.get(r.id) is r
    assert store.count() == 1
    assert store.count(kind="other") == 0
    assert store.all(kind="fact") == [r]
    assert store.delete(r.id) is True
    assert store.delete(r.id) is False
    store.add(r)
    store.clear()
    assert store.count() == 0


def test_save_validation():
    mem = MemoryEngine()
    with pytest.raises(ValidationError):
        mem.save_memory("   ")
    with pytest.raises(ValidationError):
        mem.save_memory("ok", importance=2.0)


def test_retrieve_ranks_relevant_first():
    mem = MemoryEngine()
    mem.save_memory("The user loves hiking in the mountains.")
    mem.save_memory("Database migrations run nightly at 2am.")
    hits = mem.retrieve_memory("outdoor hiking activities", k=2)
    assert hits[0].content.lower().find("hiking") >= 0
    assert hits[0].score is not None
    with pytest.raises(ValidationError):
        mem.retrieve_memory("x", k=0)


def test_optimize_context_respects_budget():
    mem = MemoryEngine()
    for i in range(10):
        mem.save_memory(f"Fact number {i} about the project and its many details here.")
    result = mem.optimize_context("project facts", token_budget=30, k=10)
    assert result.used_tokens <= 30
    assert result.token_budget == 30
    assert result.summarized_count + result.dropped_count + len(result.included) >= 1
    with pytest.raises(ValidationError):
        mem.optimize_context("x", token_budget=0)


def test_run_dispatch():
    mem = MemoryEngine()
    saved = mem.run({"op": "save", "content": "remember me"})
    assert saved["record"]["content"] == "remember me"
    got = mem.run({"op": "retrieve", "query": "remember", "k": 1})
    assert got["results"]
    summ = mem.run({"op": "summarize"})
    assert "summary" in summ
    ctx = mem.run({"op": "optimize_context", "query": "remember", "token_budget": 50})
    assert "context" in ctx
    # seeding + unknown op
    seeded = MemoryEngine().run(
        {"op": "retrieve", "query": "blue", "memories": ["the sky is blue"]}
    )
    assert seeded["results"]
    with pytest.raises(ValidationError):
        mem.run({"op": "nonsense"})


def test_subword_ngrams_match_morphological_variants():
    from agent_essentials.memory import HashingEmbedder
    from agent_essentials.utilities.text import cosine

    emb = HashingEmbedder()
    # morphological variants share subword n-grams => non-trivial similarity
    assert cosine(emb.embed("running"), emb.embed("runner")) > 0.1
    # disabling subwords removes the morphological signal entirely
    plain = HashingEmbedder(subword_ngrams=0)
    assert cosine(plain.embed("running"), plain.embed("runner")) == 0.0


def test_retrieve_validates_alpha():
    mem = MemoryEngine()
    mem.save_memory("hello world")
    with pytest.raises(ValidationError):
        mem.retrieve_memory("hello", alpha=5.0)


def test_optimize_context_never_empty_with_oversized_memory():
    mem = MemoryEngine()
    mem.save_memory("This is a very long memory entry " * 20)
    result = mem.optimize_context("memory entry", token_budget=20)
    assert result.context  # not empty
    assert len(result.included) == 1
    assert result.included[0].metadata.get("truncated") is True
    assert result.used_tokens <= 20
