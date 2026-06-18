"""Embedders.

The default :class:`HashingEmbedder` is fully deterministic and dependency-free
(stable feature hashing), which makes retrieval reproducible and unit-testable
offline. It augments whole-word features with character n-gram (subword) features
so morphological variants (``hike``/``hiking``/``hiker``) and typos still match.

It remains a *lexical* embedder, not a semantic one: unrelated synonyms
(``car``/``automobile``) will not match. Swap in a real embedding model via the
``Embedder`` interface and the optional ``llm`` extra when you need semantics.
"""

from __future__ import annotations

import abc
import hashlib
import math
from collections.abc import Sequence

from ..utilities.text import tokenize


class Embedder(abc.ABC):
    """Turn text into a fixed-length dense vector."""

    dim: int

    @abc.abstractmethod
    def embed(self, text: str) -> list[float]: ...

    def embed_many(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


class HashingEmbedder(Embedder):
    """Signed feature-hashing embedder with subword n-grams.

    Python's built-in ``hash`` is salted per process, so we use BLAKE2b to keep
    vectors identical across runs and machines.
    """

    def __init__(
        self, dim: int = 256, *, subword_ngrams: int = 3, subword_weight: float = 0.5
    ) -> None:
        if dim <= 0:
            raise ValueError("dim must be positive")
        if subword_weight < 0:
            raise ValueError("subword_weight must be >= 0")
        self.dim = dim
        self.subword_ngrams = subword_ngrams
        self.subword_weight = subword_weight

    @staticmethod
    def _bucket_sign(feature: str) -> tuple[int, float]:
        digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, "big")
        return value % 1_000_003, (1.0 if (value >> 1) & 1 else -1.0)

    def _char_ngrams(self, token: str) -> list[str]:
        if self.subword_ngrams <= 0:
            return []
        marked = f"<{token}>"  # boundary markers capture prefixes/suffixes
        n = self.subword_ngrams
        if len(marked) < n:
            return []
        return [marked[i : i + n] for i in range(len(marked) - n + 1)]

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for token in tokenize(text):
            bucket, sign = self._bucket_sign(token)
            vec[bucket % self.dim] += sign
            if self.subword_weight:
                for ngram in self._char_ngrams(token):
                    b, s = self._bucket_sign("#" + ngram)
                    vec[b % self.dim] += s * self.subword_weight
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0.0:
            return vec
        return [v / norm for v in vec]


__all__ = ["Embedder", "HashingEmbedder"]
