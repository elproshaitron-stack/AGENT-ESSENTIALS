"""Tests for the Entailment Validator plugin."""

from __future__ import annotations

import pytest

from agent_essentials import EntailmentValidator
from agent_essentials.core.exceptions import ValidationError
from agent_essentials.validation import EntailmentLabel, HeuristicEntailmentScorer


def test_heuristic_scorer_labels():
    s = HeuristicEntailmentScorer()
    assert s("The drug is safe.", "The drug is safe.")[0] is EntailmentLabel.ENTAILMENT
    assert s("The drug is not safe.", "The drug is safe.")[0] is EntailmentLabel.CONTRADICTION
    assert (
        s("Revenue was 12 last year.", "Revenue was 999 last year.")[0]
        is EntailmentLabel.CONTRADICTION
    )
    assert s("The sky is blue.", "Quantum chromodynamics is complex.")[0] is EntailmentLabel.NEUTRAL


def test_validator_contradiction_high_risk():
    report = EntailmentValidator().validate(
        "The medication is safe.", sources=["The medication is not safe."]
    )
    assert report.contradicted == 1
    assert report.risk_score >= 0.5
    assert report.risk_level in {"high", "critical"}


def test_validator_all_entailed_low_risk():
    report = EntailmentValidator().validate(
        "Paris is in France.", sources=["Paris is the capital of France."]
    )
    assert report.contradicted == 0
    assert report.risk_level == "low"


def test_validator_requires_sources_and_output():
    v = EntailmentValidator()
    with pytest.raises(ValidationError):
        v.validate("something", sources=[])
    with pytest.raises(ValidationError):
        v.validate("   ", sources=["x"])


def test_injected_scorer_overrides_default():
    def always_contradiction(premise: str, hypothesis: str):
        return EntailmentLabel.CONTRADICTION, 1.0

    report = EntailmentValidator(scorer=always_contradiction).validate(
        "Anything at all goes here.", sources=["Some unrelated source text."]
    )
    assert report.contradicted == 1
    assert report.entailed == 0


def test_run_path_and_errors():
    v = EntailmentValidator()
    out = v.run({"output": "Paris is in France.", "sources": ["Paris is the capital of France."]})
    assert "risk_score" in out and "judgements" in out
    with pytest.raises(ValidationError):
        v.run({"sources": ["x"]})
