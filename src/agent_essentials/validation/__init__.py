"""Validation suite: Hallucination Detector."""

from __future__ import annotations

from ..core.plugin import Plugin
from .entailment import (
    EntailmentJudgement,
    EntailmentLabel,
    EntailmentReport,
    EntailmentValidator,
    HeuristicEntailmentScorer,
)
from .hallucination import HallucinationDetector
from .models import ValidationReport, risk_level, severity_for_risk

plugin = Plugin(
    name=HallucinationDetector.name,
    factory=HallucinationDetector,
    summary=HallucinationDetector.summary,
    version=HallucinationDetector.version,
)

entailment_plugin = Plugin(
    name=EntailmentValidator.name,
    factory=EntailmentValidator,
    summary=EntailmentValidator.summary,
    version=EntailmentValidator.version,
)

__all__ = [
    "EntailmentJudgement",
    "EntailmentLabel",
    "EntailmentReport",
    "EntailmentValidator",
    "HallucinationDetector",
    "HeuristicEntailmentScorer",
    "ValidationReport",
    "entailment_plugin",
    "plugin",
    "risk_level",
    "severity_for_risk",
]
