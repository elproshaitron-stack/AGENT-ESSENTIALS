"""Typed models for the Validation suite."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core.result import Finding, Recommendation, Severity
from ..core.types import Serializable


def risk_level(score: float) -> str:
    if score < 0.25:
        return "low"
    if score < 0.5:
        return "moderate"
    if score < 0.75:
        return "high"
    return "critical"


def severity_for_risk(score: float) -> Severity:
    return {
        "low": Severity.LOW,
        "moderate": Severity.MEDIUM,
        "high": Severity.HIGH,
        "critical": Severity.CRITICAL,
    }[risk_level(score)]


@dataclass(slots=True)
class ValidationReport(Serializable):
    """Result of analyzing an output for hallucination risk."""

    risk_score: float
    risk_level: str
    confidence: float
    warnings: list[Finding] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    checks: dict[str, Any] = field(default_factory=dict)


__all__ = ["ValidationReport", "risk_level", "severity_for_risk"]
