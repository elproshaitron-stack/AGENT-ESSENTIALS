"""Summarizers used for memory compression."""

from __future__ import annotations

import abc
from collections import Counter
from collections.abc import Sequence

from ..utilities.text import content_tokens, split_sentences


class Summarizer(abc.ABC):
    @abc.abstractmethod
    def summarize(self, texts: Sequence[str], *, max_sentences: int = 3) -> str: ...


class ExtractiveSummarizer(Summarizer):
    """Frequency-based extractive summarizer (TextRank-lite, no dependencies).

    Scores each sentence by the summed frequency of its content words and keeps
    the highest-scoring ones in their original order.
    """

    def summarize(self, texts: Sequence[str], *, max_sentences: int = 3) -> str:
        combined = " ".join(t.strip() for t in texts if t.strip())
        sentences = split_sentences(combined)
        if len(sentences) <= max_sentences:
            return combined.strip()

        freq = Counter(content_tokens(combined))
        if not freq:
            return " ".join(sentences[:max_sentences])

        peak = max(freq.values())
        scored: list[tuple[int, float, str]] = []
        for index, sentence in enumerate(sentences):
            words = content_tokens(sentence)
            if not words:
                continue
            score = sum(freq[w] for w in words) / (len(words) * peak)
            scored.append((index, score, sentence))

        top = sorted(scored, key=lambda item: item[1], reverse=True)[:max_sentences]
        top.sort(key=lambda item: item[0])  # restore reading order
        return " ".join(sentence for _, _, sentence in top)


__all__ = ["ExtractiveSummarizer", "Summarizer"]
