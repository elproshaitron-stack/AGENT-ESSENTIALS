"""Tests for the Hallucination Detector."""

from __future__ import annotations

import pytest

from agent_essentials.core.exceptions import ValidationError
from agent_essentials.validation import HallucinationDetector, checks, risk_level


def test_risk_level_bands():
    assert risk_level(0.1) == "low"
    assert risk_level(0.4) == "moderate"
    assert risk_level(0.6) == "high"
    assert risk_level(0.9) == "critical"


def test_support_and_unsupported():
    assert checks.support_for_claim("paris france", ["paris is in france"]) == pytest.approx(1.0)
    assert checks.support_for_claim("quantum tunnels", ["paris is in france"]) == 0.0
    unsup = checks.find_unsupported(["totally unrelated content"], ["paris france"], threshold=0.5)
    assert unsup and unsup[0][1] < 0.5


def test_fabricated_specifics():
    flagged = checks.fabricated_specifics(
        "Revenue was 999 and see https://fake.test/x", ["Revenue was 12"]
    )
    assert any("999" in f for f in flagged)
    assert any("fake.test" in f for f in flagged)


def test_detect_contradictions_negation_and_antonym():
    neg = checks.detect_contradictions("The api is stable. The api is not stable.")
    assert len(neg) == 1
    anto = checks.detect_contradictions(
        "Sales increase every single year. Sales decrease every single year."
    )
    assert len(anto) >= 1


def test_confidence_scoring():
    assert 0.0 <= checks.score_confidence("maybe perhaps possibly") <= 0.5
    assert checks.score_confidence("definitely certainly absolutely") > 0.5
    assert checks.count_overconfidence("always never definitely") == 3


def test_analyze_grounded_low_risk():
    hd = HallucinationDetector()
    report = hd.analyze(
        "The Eiffel Tower is in Paris and opened in 1889.",
        sources=["The Eiffel Tower, located in Paris, opened in 1889."],
    )
    assert report.risk_score < 0.25
    assert report.risk_level == "low"


def test_analyze_ungrounded_high_risk():
    hd = HallucinationDetector()
    report = hd.analyze(
        "The product cured the disease in 100% of cases according to study 12345.",
        sources=["The product is a herbal tea with no proven medical effect."],
    )
    assert report.risk_score > 0.4
    assert 0.0 <= report.risk_score <= 1.0
    assert report.warnings


def test_analyze_without_sources_flags_no_sources():
    hd = HallucinationDetector()
    report = hd.analyze("It will rain exactly 42mm tomorrow at noon.")
    assert any(w.code == "no_sources" for w in report.warnings)


def test_analyze_empty_and_run():
    hd = HallucinationDetector()
    with pytest.raises(ValidationError):
        hd.analyze("  ")
    with pytest.raises(ValidationError):
        hd.run({"nope": 1})
    out = hd.run({"output": "X is true.", "sources": ["X is true."]})
    assert "risk_score" in out


def test_grounding_polarity_conflict_flips_meaning():
    """A claim that reuses source vocabulary but flips polarity must be flagged."""
    hd = HallucinationDetector()
    report = hd.analyze(
        "The medication is completely safe for children.",
        sources=["The medication is not safe for children."],
    )
    assert report.checks["contradicts_source"] == 1
    assert report.risk_score >= 0.5
    assert report.risk_level in {"high", "critical"}
    assert any(w.code == "contradicts_source" for w in report.warnings)


def test_grounding_polarity_no_false_positive_on_added_negation():
    """A negation about unrelated, added content must NOT be flagged as a conflict."""
    hd = HallucinationDetector()
    report = hd.analyze("The system is fast and does not crash.", sources=["The system is fast."])
    assert report.checks["contradicts_source"] == 0
    assert report.risk_level == "low"


def test_grounding_analysis_and_negation_helpers():
    unsupported, conflicts = checks.grounding_analysis(
        ["The drug is safe."], ["The drug is not safe."]
    )
    assert conflicts and not unsupported
    assert checks.has_negation("this is not true")
    assert not checks.has_negation("this is true")


def test_numeric_mismatch_detected():
    """A figure that disagrees with the best-matching source sentence is flagged,
    even if the wrong number appears elsewhere in the sources."""
    hd = HallucinationDetector()
    report = hd.analyze(
        "The tower opened in 1925.",
        sources=["The tower opened in 1889. A nearby museum opened in 1925."],
    )
    assert report.checks["numeric_mismatch"] == 1
    assert any(w.code == "numeric_mismatch" for w in report.warnings)
    # correct figures must not be flagged
    ok = hd.analyze("The tower opened in 1889.", sources=["The tower opened in 1889."])
    assert ok.checks["numeric_mismatch"] == 0


def test_numeric_conflicts_helper():
    conflicts = checks.numeric_conflicts(
        ["Revenue was 999 last year."], ["Revenue was 12 last year."]
    )
    assert conflicts
