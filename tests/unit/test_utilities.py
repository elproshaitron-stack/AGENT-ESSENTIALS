"""Tests for shared text utilities."""

from __future__ import annotations

import pytest

from agent_essentials.utilities import text


def test_tokenize_and_content_tokens():
    assert text.tokenize("Hello, World! 42") == ["hello", "world", "42"]
    # stopwords removed
    assert "the" not in text.content_tokens("the quick brown fox")


def test_split_sentences_and_normalize():
    assert text.split_sentences("One. Two! Three?") == ["One.", "Two!", "Three?"]
    assert text.split_sentences("") == []
    assert text.normalize_whitespace("a   b\n c") == "a b c"


def test_approx_token_count():
    assert text.approx_token_count("") == 0
    assert text.approx_token_count("   ") == 0
    short = text.approx_token_count("hello world")
    longer = text.approx_token_count("hello world " * 50)
    assert 0 < short < longer


def test_jaccard():
    assert text.jaccard([], []) == 0.0
    assert text.jaccard(["a", "b"], ["a", "b"]) == 1.0
    assert text.jaccard(["a"], ["b"]) == 0.0


def test_cosine():
    assert text.cosine([1, 0], [0, 1]) == 0.0
    assert text.cosine([1, 1], [1, 1]) == pytest.approx(1.0)
    assert text.cosine([0, 0], [1, 1]) == 0.0
    with pytest.raises(ValueError):
        text.cosine([1], [1, 2])


def test_keyword_overlap():
    assert text.keyword_overlap("the cat sat", "the cat sat") == 1.0
    assert text.keyword_overlap("apples", "oranges") == 0.0


def test_approx_token_count_cjk_not_underestimated():
    # char/4 would give ~3 for this; CJK-aware counting must be much higher.
    zh = "人工智能正在改变软件行业"
    assert text.approx_token_count(zh) >= len(zh)
    # Latin text stays in the heuristic's normal range.
    assert 8 <= text.approx_token_count("The quick brown fox jumps over the lazy dog.") <= 16
