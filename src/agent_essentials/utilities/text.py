"""Small, dependency-free text helpers shared across modules."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Sequence

_WORD_RE = re.compile(r"[A-Za-z0-9']+")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")

# A compact, intentionally small stopword list. Kept tiny on purpose: the goal
# is lightweight keyword extraction, not linguistic perfection.
STOPWORDS: frozenset[str] = frozenset(
    [
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "if",
        "then",
        "else",
        "for",
        "to",
        "of",
        "in",
        "on",
        "at",
        "by",
        "with",
        "from",
        "as",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "do",
        "does",
        "did",
        "have",
        "has",
        "had",
        "will",
        "would",
        "can",
        "could",
        "should",
        "may",
        "might",
        "must",
        "not",
        "no",
        "nor",
        "so",
        "than",
        "too",
        "very",
        "into",
        "your",
        "you",
        "we",
        "our",
        "they",
        "them",
        "their",
        "he",
        "she",
        "his",
        "her",
        "i",
        "me",
        "my",
        "mine",
        "ours",
        "yours",
    ]
)


def tokenize(text: str) -> list[str]:
    """Lowercased word tokens."""
    return [m.group(0).lower() for m in _WORD_RE.finditer(text)]


def content_tokens(text: str) -> list[str]:
    """Word tokens with stopwords removed."""
    return [t for t in tokenize(text) if t not in STOPWORDS]


def split_sentences(text: str) -> list[str]:
    """Naive but robust sentence splitter."""
    text = normalize_whitespace(text)
    if not text:
        return []
    return [s.strip() for s in _SENTENCE_RE.split(text) if s.strip()]


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _is_cjk(char: str) -> bool:
    """True for CJK ideographs and Japanese/Korean syllabaries.

    These scripts tokenize at roughly one token per character (often more), so a
    ``chars / 4`` rule of thumb badly underestimates them.
    """
    code = ord(char)
    return (
        0x4E00 <= code <= 0x9FFF  # CJK Unified Ideographs
        or 0x3400 <= code <= 0x4DBF  # CJK Extension A
        or 0x3040 <= code <= 0x30FF  # Hiragana + Katakana
        or 0xAC00 <= code <= 0xD7A3  # Hangul syllables
        or 0xF900 <= code <= 0xFAFF  # CJK compatibility ideographs
    )


def approx_token_count(text: str) -> int:
    """Provider-agnostic token estimate.

    For Latin-script text it blends the two rules of thumb that bracket real
    tokenizers (~4 chars/token and ~1.33 tokens/word). CJK characters are counted
    separately at ~1.5 tokens each, since ``chars / 4`` underestimates them by an
    order of magnitude. The optimization module offers exact counts via tiktoken.
    """
    if not text.strip():
        return 0
    cjk = sum(1 for ch in text if _is_cjk(ch))
    latin_chars = len(text) - cjk
    words = len(tokenize(text))
    latin_estimate = 0.5 * (latin_chars / 4.0) + 0.5 * (words * 1.333)
    cjk_estimate = cjk * 1.5
    return max(1, round(latin_estimate + cjk_estimate))


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Trim ``text`` to fit within ``max_tokens`` (word-boundary, never empty)."""
    if max_tokens <= 0:
        return ""
    words = text.split()
    kept: list[str] = []
    for word in words:
        if approx_token_count(" ".join([*kept, word])) > max_tokens:
            break
        kept.append(word)
    if not kept and words:
        kept = [words[0]]
    return " ".join(kept)


def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    """Jaccard similarity between two token sets in ``[0, 1]``."""
    set_a, set_b = set(a), set(b)
    if not set_a and not set_b:
        return 0.0
    union = set_a | set_b
    return len(set_a & set_b) / len(union)


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity between two equal-length dense vectors."""
    if len(a) != len(b):
        raise ValueError("Vectors must have equal length")
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def keyword_overlap(text_a: str, text_b: str) -> float:
    """Jaccard similarity over content (stopword-filtered) tokens."""
    return jaccard(content_tokens(text_a), content_tokens(text_b))


__all__ = [
    "STOPWORDS",
    "approx_token_count",
    "content_tokens",
    "cosine",
    "jaccard",
    "keyword_overlap",
    "normalize_whitespace",
    "split_sentences",
    "tokenize",
    "truncate_to_tokens",
]
