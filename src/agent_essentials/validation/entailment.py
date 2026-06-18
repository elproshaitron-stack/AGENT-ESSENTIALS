"""Entailment / NLI-style validator (plugin).

This is the principled answer to the limits of the heuristic Hallucination
Detector: instead of a single risk score, it classifies *each claim* against its
best-matching source sentence as ``entailment``, ``contradiction`` or
``neutral``.

The default scorer is **deterministic and offline** (reuses the validation
checks), so it runs in CI with no API keys. For real semantic judgement, inject
any callable ``Scorer`` — e.g. an LLM or a transformers NLI model behind the
``llm`` extra — without changing the module. This is the toolkit's core pattern:
deterministic core, optional intelligence via a plugin seam.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..core.base import Module
from ..core.exceptions import ValidationError
from ..core.result import Priority, Recommendation
from ..core.types import Serializable
from ..utilities.text import content_tokens, split_sentences
from . import checks
from .models import risk_level


class EntailmentLabel(str, Enum):
    ENTAILMENT = "entailment"
    CONTRADICTION = "contradiction"
    NEUTRAL = "neutral"


#: A scorer maps (premise, hypothesis) -> (label, confidence in [0, 1]).
Scorer = Callable[[str, str], tuple[EntailmentLabel, float]]


@dataclass(slots=True)
class EntailmentJudgement(Serializable):
    claim: str
    label: EntailmentLabel
    score: float
    premise: str


@dataclass(slots=True)
class EntailmentReport(Serializable):
    risk_score: float
    risk_level: str
    entailed: int
    contradicted: int
    neutral: int
    judgements: list[EntailmentJudgement]
    recommendations: list[Recommendation] = field(default_factory=list)


class HeuristicEntailmentScorer:
    """Deterministic NLI-style scorer built from the validation checks.

    Logic: if the hypothesis is not covered by the premise -> NEUTRAL; if exactly
    one side negates a shared word, or their numbers disagree -> CONTRADICTION;
    otherwise -> ENTAILMENT.
    """

    def __init__(self, *, support_threshold: float = 0.5) -> None:
        self.support_threshold = support_threshold

    def __call__(self, premise: str, hypothesis: str) -> tuple[EntailmentLabel, float]:
        hyp = set(content_tokens(hypothesis))
        prem = set(content_tokens(premise))
        if not hyp:
            return EntailmentLabel.NEUTRAL, 0.0
        coverage = len(hyp & prem) / len(hyp)
        if coverage < self.support_threshold:
            return EntailmentLabel.NEUTRAL, round(1.0 - coverage, 3)
        shared = hyp & prem
        if checks.has_negation(hypothesis) != checks.has_negation(premise):
            negated = hypothesis if checks.has_negation(hypothesis) else premise
            if checks.negation_targets(negated) & shared:
                return EntailmentLabel.CONTRADICTION, round(coverage, 3)
        hyp_numbers = set(checks.extract_specifics(hypothesis)["numbers"])
        prem_numbers = set(checks.extract_specifics(premise)["numbers"])
        if hyp_numbers and prem_numbers and hyp_numbers.isdisjoint(prem_numbers):
            return EntailmentLabel.CONTRADICTION, round(coverage, 3)
        return EntailmentLabel.ENTAILMENT, round(coverage, 3)


class EntailmentValidator(Module):
    """Per-claim entailment check against sources, with a pluggable scorer."""

    name = "entailment"
    version = "0.1.0"
    summary = "NLI-style per-claim entailment/contradiction check (pluggable scorer)."

    def __init__(self, scorer: Scorer | None = None, *, support_threshold: float = 0.5) -> None:
        self.support_threshold = support_threshold
        self.scorer: Scorer = scorer or HeuristicEntailmentScorer(
            support_threshold=support_threshold
        )

    def _source_sentences(self, sources: list[str]) -> list[str]:
        out: list[str] = []
        for source in sources:
            sentences = split_sentences(source)
            out.extend(sentences if sentences else [source])
        return out

    def _best_premise(self, claim: str, sentences: list[str]) -> str:
        claim_tokens = set(content_tokens(claim))
        if not claim_tokens:
            return sentences[0] if sentences else ""
        best, best_cov = "", -1.0
        for sentence in sentences:
            sentence_tokens = set(content_tokens(sentence))
            if not sentence_tokens:
                continue
            cov = len(claim_tokens & sentence_tokens) / len(claim_tokens)
            if cov > best_cov:
                best, best_cov = sentence, cov
        return best

    def validate(self, output: str, sources: Sequence[str] | None) -> EntailmentReport:
        if not output or not output.strip():
            raise ValidationError("output must be a non-empty string")
        source_list = [s for s in (sources or []) if s and s.strip()]
        if not source_list:
            raise ValidationError("entailment validation requires at least one source")

        sentences = self._source_sentences(source_list)
        claims = checks.extract_claims(output)
        judgements: list[EntailmentJudgement] = []
        for claim in claims:
            premise = self._best_premise(claim, sentences)
            label, score = self.scorer(premise, claim)
            judgements.append(EntailmentJudgement(claim, label, score, premise))

        total = max(1, len(judgements))
        contradicted = sum(j.label is EntailmentLabel.CONTRADICTION for j in judgements)
        neutral = sum(j.label is EntailmentLabel.NEUTRAL for j in judgements)
        entailed = sum(j.label is EntailmentLabel.ENTAILMENT for j in judgements)
        risk = min(1.0, 0.7 * contradicted / total + 0.25 * neutral / total)

        return EntailmentReport(
            risk_score=round(risk, 3),
            risk_level=risk_level(risk),
            entailed=entailed,
            contradicted=contradicted,
            neutral=neutral,
            judgements=judgements,
            recommendations=self._recommend(contradicted, neutral),
        )

    @staticmethod
    def _recommend(contradicted: int, neutral: int) -> list[Recommendation]:
        recs: list[Recommendation] = []
        if contradicted:
            recs.append(
                Recommendation(
                    "Resolve claims that contradict the sources",
                    "Regenerate or correct the claims classified as contradiction.",
                    Priority.HIGH,
                )
            )
        if neutral:
            recs.append(
                Recommendation(
                    "Ground the unsupported claims",
                    "Claims classified neutral are not entailed by any source; "
                    "cite or remove them.",
                    Priority.MEDIUM,
                )
            )
        if not recs:
            recs.append(
                Recommendation(
                    "All claims entailed by the sources",
                    "Every claim is supported. Keep logging for regressions.",
                    Priority.LOW,
                )
            )
        return recs

    def run(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        output = payload.get("output")
        if not isinstance(output, str):
            raise ValidationError("payload must include a string 'output'")
        return self.validate(output, payload.get("sources")).to_dict()


__all__ = [
    "EntailmentJudgement",
    "EntailmentLabel",
    "EntailmentReport",
    "EntailmentValidator",
    "HeuristicEntailmentScorer",
    "Scorer",
]
