"""Pure heuristic checks for hallucination detection.

Each check is independent and explainable. None require network access or model
internals, so the detector is deterministic and cheap to run in CI on every
generated response.
"""

from __future__ import annotations

import re

from ..utilities.text import STOPWORDS, content_tokens, split_sentences, tokenize

# Specific, easy-to-fabricate tokens.
_NUMBER_RE = re.compile(r"\b\d[\d,]*\.?\d*%?\b")
_URL_RE = re.compile(r"https?://[^\s)>\]]+")
_YEAR_RE = re.compile(r"\b(1[89]\d{2}|20\d{2})\b")
# Crude academic-style citation, e.g. "(Smith, 2021)" or "[12]".
_CITATION_RE = re.compile(r"\([A-Z][A-Za-z]+(?:\s+et\s+al\.?)?,?\s+\d{4}\)|\[\d+\]")

_NEGATIONS = frozenset(
    {
        "not",
        "never",
        "no",
        "cannot",
        "cant",
        "isnt",
        "arent",
        "wasnt",
        "werent",
        "dont",
        "doesnt",
        "didnt",
        "wont",
        "without",
        "none",
        "neither",
        "nor",
        "fails",
        "lacks",
        "fail",
        "failed",
        "denies",
        "denied",
    }
)

_ANTONYMS: tuple[tuple[str, str], ...] = (
    ("increase", "decrease"),
    ("increases", "decreases"),
    ("rise", "fall"),
    ("higher", "lower"),
    ("more", "less"),
    ("true", "false"),
    ("always", "never"),
    ("positive", "negative"),
    ("gain", "loss"),
    ("enabled", "disabled"),
    ("success", "failure"),
    ("safe", "dangerous"),
    ("legal", "illegal"),
    ("included", "excluded"),
    ("supported", "unsupported"),
    ("possible", "impossible"),
    ("present", "absent"),
    ("compliant", "noncompliant"),
)

_OVERCONFIDENT = frozenset(
    {
        "definitely",
        "certainly",
        "guaranteed",
        "always",
        "never",
        "undoubtedly",
        "absolutely",
        "unquestionably",
        "obviously",
        "clearly",
        "everyone",
        "proven",
        "impossible",
        "100",
    }
)

_HEDGES = frozenset(
    {
        "maybe",
        "perhaps",
        "possibly",
        "probably",
        "might",
        "likely",
        "apparently",
        "seems",
        "seem",
        "reportedly",
        "presumably",
        "allegedly",
        "roughly",
        "approximately",
        "unclear",
    }
)


def has_negation(text: str) -> bool:
    """True if the text contains a negation cue (used for polarity comparison)."""
    return bool(set(tokenize(text)) & _NEGATIONS)


def extract_claims(text: str) -> list[str]:
    """Sentences that carry content (i.e. assertions worth checking)."""
    return [s for s in split_sentences(text) if content_tokens(s)]


def support_for_claim(claim: str, sources: list[str]) -> float:
    """Fraction of the claim's content words covered by the best-matching source."""
    claim_tokens = set(content_tokens(claim))
    if not claim_tokens:
        return 1.0  # nothing to verify
    best = 0.0
    for source in sources:
        source_tokens = set(content_tokens(source))
        if not source_tokens:
            continue
        covered = len(claim_tokens & source_tokens) / len(claim_tokens)
        best = max(best, covered)
    return best


def find_unsupported(
    claims: list[str], sources: list[str], *, threshold: float = 0.5
) -> list[tuple[str, float]]:
    unsupported: list[tuple[str, float]] = []
    for claim in claims:
        support = support_for_claim(claim, sources)
        if support < threshold:
            unsupported.append((claim, round(support, 3)))
    return unsupported


def _source_sentences(sources: list[str]) -> list[str]:
    out: list[str] = []
    for source in sources:
        sentences = split_sentences(source)
        out.extend(sentences if sentences else [source])
    return out


def negation_targets(sentence: str, *, window: int = 4) -> set[str]:
    """Content words that fall within ``window`` tokens after a negation cue.

    A crude approximation of negation *scope*: it tells us what is actually being
    negated, so we don't flag a claim that merely adds an unrelated negation.
    """
    tokens = tokenize(sentence)
    targets: set[str] = set()
    for i, token in enumerate(tokens):
        if token in _NEGATIONS:
            for following in tokens[i + 1 : i + 1 + window]:
                if following not in STOPWORDS:
                    targets.add(following)
    return targets


def grounding_analysis(
    claims: list[str], sources: list[str], *, threshold: float = 0.5
) -> tuple[list[tuple[str, float]], list[tuple[str, str]]]:
    """Sentence-level grounding with negation-scope-aware polarity checking.

    Returns ``(unsupported, polarity_conflicts)``:

    - **unsupported**: claims whose vocabulary is not covered by any source
      sentence (coverage below ``threshold``).
    - **polarity_conflicts**: claims whose vocabulary *is* well covered by a
      source sentence, but where exactly one side negates a *shared* word -- i.e.
      the answer asserts the reverse of the source ("X is safe" vs "X is not
      safe"). Plain token-overlap grounding wrongly marks these as supported, so
      we surface them: they are a strong hallucination signal. Requiring the
      negation to target a shared word avoids flagging claims that merely add an
      unrelated negation ("...and does not crash").
    """
    sentences = _source_sentences(sources)
    unsupported: list[tuple[str, float]] = []
    conflicts: list[tuple[str, str]] = []
    for claim in claims:
        claim_tokens = set(content_tokens(claim))
        if not claim_tokens:
            continue
        best_cov = 0.0
        best_sentence = ""
        for sentence in sentences:
            sentence_tokens = set(content_tokens(sentence))
            if not sentence_tokens:
                continue
            cov = len(claim_tokens & sentence_tokens) / len(claim_tokens)
            if cov > best_cov:
                best_cov, best_sentence = cov, sentence
        if best_cov < threshold:
            unsupported.append((claim, round(best_cov, 3)))
            continue
        if not best_sentence or has_negation(claim) == has_negation(best_sentence):
            continue
        # Exactly one side negates. Confirm the negation targets a shared word.
        shared = claim_tokens & set(content_tokens(best_sentence))
        negated = claim if has_negation(claim) else best_sentence
        if negation_targets(negated) & shared:
            conflicts.append((claim, best_sentence))
    return unsupported, conflicts


def numeric_conflicts(
    claims: list[str], sources: list[str], *, threshold: float = 0.5
) -> list[tuple[str, str]]:
    """Claims whose numbers disagree with their best-matching source sentence.

    Catches mis-attributed figures ("opened in 1925" when the matching source
    says "opened in 1889") even when the wrong number appears elsewhere in the
    sources, which the global fabricated-specifics check would miss. Heuristic:
    only flags when *none* of the claim's numbers appear in the best sentence.
    """
    sentences = _source_sentences(sources)
    conflicts: list[tuple[str, str]] = []
    for claim in claims:
        claim_numbers = set(_NUMBER_RE.findall(claim))
        claim_tokens = set(content_tokens(claim))
        if not claim_numbers or not claim_tokens:
            continue
        best_cov = 0.0
        best_sentence = ""
        for sentence in sentences:
            sentence_tokens = set(content_tokens(sentence))
            if not sentence_tokens:
                continue
            cov = len(claim_tokens & sentence_tokens) / len(claim_tokens)
            if cov > best_cov:
                best_cov, best_sentence = cov, sentence
        if best_cov < threshold or not best_sentence:
            continue
        source_numbers = set(_NUMBER_RE.findall(best_sentence))
        if source_numbers and claim_numbers.isdisjoint(source_numbers):
            conflicts.append((claim, best_sentence))
    return conflicts


def extract_specifics(text: str) -> dict[str, list[str]]:
    return {
        "numbers": _NUMBER_RE.findall(text),
        "urls": _URL_RE.findall(text),
        "years": _YEAR_RE.findall(text),
        "citations": _CITATION_RE.findall(text),
    }


def fabricated_specifics(answer: str, sources: list[str]) -> list[str]:
    """Specific numbers/URLs/citations in the answer absent from every source."""
    joined = " ".join(sources)
    source_numbers = set(_NUMBER_RE.findall(joined))
    source_urls = set(_URL_RE.findall(joined))
    flagged: list[str] = []
    for number in set(_NUMBER_RE.findall(answer)):
        if number not in source_numbers:
            flagged.append(f"number {number!r} not found in sources")
    for url in set(_URL_RE.findall(answer)):
        if url not in source_urls:
            flagged.append(f"URL {url!r} not found in sources")
    for citation in set(_CITATION_RE.findall(answer)):
        if citation not in joined:
            flagged.append(f"citation {citation!r} not found in sources")
    return flagged


def detect_contradictions(
    text: str, *, overlap_threshold: float = 0.5, cap: int = 10
) -> list[dict[str, str]]:
    """Find sentence pairs that appear to contradict each other."""
    sentences = [s for s in split_sentences(text) if content_tokens(s)]
    found: list[dict[str, str]] = []
    for i in range(len(sentences)):
        tokens_i = set(content_tokens(sentences[i]))
        raw_i = set(tokenize(sentences[i]))
        for j in range(i + 1, len(sentences)):
            tokens_j = set(content_tokens(sentences[j]))
            if not tokens_i or not tokens_j:
                continue
            overlap = len(tokens_i & tokens_j) / len(tokens_i | tokens_j)
            if overlap < overlap_threshold:
                continue
            raw_j = set(tokenize(sentences[j]))
            neg_i = bool(raw_i & _NEGATIONS)
            neg_j = bool(raw_j & _NEGATIONS)
            reason = ""
            if neg_i != neg_j:
                reason = "one statement negates the other"
            else:
                for a, b in _ANTONYMS:
                    if (a in raw_i and b in raw_j) or (b in raw_i and a in raw_j):
                        reason = f"antonyms {a!r}/{b!r} on overlapping subject"
                        break
            if reason:
                found.append({"a": sentences[i], "b": sentences[j], "reason": reason})
                if len(found) >= cap:
                    return found
    return found


def count_overconfidence(text: str) -> int:
    tokens = tokenize(text)
    return sum(1 for t in tokens if t in _OVERCONFIDENT)


def count_hedges(text: str) -> int:
    tokens = tokenize(text)
    return sum(1 for t in tokens if t in _HEDGES)


def score_confidence(text: str) -> float:
    """Apparent stated confidence in ``[0, 1]`` from assertive vs hedging language."""
    confidence = 0.5 + 0.08 * count_overconfidence(text) - 0.08 * count_hedges(text)
    return round(max(0.0, min(1.0, confidence)), 3)


__all__ = [
    "count_hedges",
    "count_overconfidence",
    "detect_contradictions",
    "extract_claims",
    "extract_specifics",
    "fabricated_specifics",
    "find_unsupported",
    "grounding_analysis",
    "has_negation",
    "negation_targets",
    "numeric_conflicts",
    "score_confidence",
    "support_for_claim",
]
