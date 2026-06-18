"""The Hallucination Detector module."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ..core.base import Module
from ..core.exceptions import ValidationError
from ..core.result import Finding, Priority, Recommendation, Severity
from . import checks
from .models import ValidationReport, risk_level, severity_for_risk


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


class HallucinationDetector(Module):
    """Score a model output for hallucination risk using explainable heuristics."""

    name = "validation"
    version = "0.1.0"
    summary = "Confidence, source-grounding, polarity, consistency and contradiction analysis."

    def analyze(
        self,
        output: str,
        sources: Sequence[str] | None = None,
        *,
        support_threshold: float = 0.5,
    ) -> ValidationReport:
        if not output or not output.strip():
            raise ValidationError("output must be a non-empty string")
        source_list = [s for s in (sources or []) if s and s.strip()]
        has_sources = bool(source_list)

        claims = checks.extract_claims(output)
        contradictions = checks.detect_contradictions(output)
        overconfidence = checks.count_overconfidence(output)
        confidence = checks.score_confidence(output)

        warnings: list[Finding] = []
        risk = 0.0
        polarity_conflicts: list[tuple[str, str]] = []

        if has_sources:
            unsupported, polarity_conflicts = checks.grounding_analysis(
                claims, source_list, threshold=support_threshold
            )
            unsupported_ratio = len(unsupported) / max(1, len(claims))
            fabricated = checks.fabricated_specifics(output, source_list)
            numeric = checks.numeric_conflicts(claims, source_list, threshold=support_threshold)
            risk += 0.45 * unsupported_ratio
            risk += 0.25 * min(1.0, len(fabricated) / 3)
            risk += min(0.5, 0.3 * len(numeric))
            # A claim that reuses the source's words but flips its polarity is
            # asserting the opposite of the evidence: a strong hallucination.
            if polarity_conflicts:
                risk += min(0.6, 0.5 * len(polarity_conflicts))
            for claim, support in unsupported[:5]:
                warnings.append(
                    Finding(
                        "unsupported_claim",
                        f"Claim not grounded in sources (support={support}): {claim}",
                        Severity.HIGH if support < 0.25 else Severity.MEDIUM,
                        {"support": support},
                    )
                )
            for claim, sentence in polarity_conflicts[:5]:
                warnings.append(
                    Finding(
                        "contradicts_source",
                        f"Claim contradicts its source (polarity flip). "
                        f"claim={claim!r} source={sentence!r}",
                        Severity.HIGH,
                    )
                )
            for detail in fabricated[:5]:
                warnings.append(Finding("fabricated_detail", detail, Severity.HIGH))
            for claim, sentence in numeric[:5]:
                warnings.append(
                    Finding(
                        "numeric_mismatch",
                        f"Claim's figures disagree with the source. "
                        f"claim={claim!r} source={sentence!r}",
                        Severity.HIGH,
                    )
                )
            if unsupported_ratio > 0.3 and overconfidence > 0:
                risk += 0.10  # confident + unsupported is the classic failure mode
        else:
            unsupported = []
            unsupported_ratio = 0.0
            fabricated = []
            numeric = []
            specifics = checks.extract_specifics(output)
            specific_count = sum(len(v) for v in specifics.values())
            risk += 0.20  # cannot verify grounding at all
            risk += 0.15 * min(1.0, specific_count / 4)
            warnings.append(
                Finding(
                    "no_sources",
                    "No reference sources supplied; grounding could not be verified.",
                    Severity.MEDIUM,
                    {"specifics_detected": specific_count},
                )
            )

        risk += 0.25 * min(1.0, len(contradictions) / 2)
        risk += 0.10 * min(1.0, overconfidence / 3)
        for contradiction in contradictions[:5]:
            warnings.append(
                Finding(
                    "contradiction",
                    f"Possible contradiction ({contradiction['reason']}): "
                    f'"{contradiction["a"]}" vs "{contradiction["b"]}"',
                    Severity.HIGH,
                )
            )
        if overconfidence >= 2:
            warnings.append(
                Finding(
                    "overconfident_language",
                    f"{overconfidence} absolute/overconfident terms detected.",
                    Severity.LOW,
                    {"count": overconfidence},
                )
            )

        risk = round(_clamp(risk), 3)
        level = risk_level(risk)
        recommendations = self._recommend(
            has_sources=has_sources,
            unsupported=bool(unsupported),
            fabricated=bool(fabricated),
            contradictions=bool(contradictions),
            contradicts_source=bool(polarity_conflicts),
            risk=risk,
        )

        return ValidationReport(
            risk_score=risk,
            risk_level=level,
            confidence=confidence,
            warnings=warnings,
            recommendations=recommendations,
            checks={
                "claims": len(claims),
                "has_sources": has_sources,
                "unsupported_claims": len(unsupported),
                "unsupported_ratio": round(unsupported_ratio, 3),
                "contradicts_source": len(polarity_conflicts),
                "fabricated_specifics": len(fabricated),
                "numeric_mismatch": len(numeric),
                "contradictions": len(contradictions),
                "overconfident_terms": overconfidence,
                "severity": severity_for_risk(risk).value,
            },
        )

    @staticmethod
    def _recommend(
        *,
        has_sources: bool,
        unsupported: bool,
        fabricated: bool,
        contradictions: bool,
        contradicts_source: bool,
        risk: float,
    ) -> list[Recommendation]:
        recs: list[Recommendation] = []
        if contradicts_source:
            recs.append(
                Recommendation(
                    "Answer contradicts the source",
                    "The response flips the polarity of the evidence. Regenerate and "
                    "require it to agree with the cited source.",
                    Priority.HIGH,
                )
            )
        if not has_sources:
            recs.append(
                Recommendation(
                    "Supply reference sources",
                    "Pass the retrieved documents so grounding can be verified.",
                    Priority.HIGH,
                )
            )
        if unsupported:
            recs.append(
                Recommendation(
                    "Ground or remove unsupported claims",
                    "Require citations for each claim or drop those not in the sources.",
                    Priority.HIGH,
                )
            )
        if fabricated:
            recs.append(
                Recommendation(
                    "Verify specific figures, links and citations",
                    "Numbers, URLs and citations absent from sources are likely fabricated.",
                    Priority.HIGH,
                )
            )
        if contradictions:
            recs.append(
                Recommendation(
                    "Resolve internal contradictions",
                    "Reconcile statements that negate one another before returning the answer.",
                    Priority.MEDIUM,
                )
            )
        if risk >= 0.5:
            recs.append(
                Recommendation(
                    "Route to human review or a stronger model",
                    "High risk: escalate, regenerate with retrieval, or require approval.",
                    Priority.HIGH,
                )
            )
        if not recs:
            recs.append(
                Recommendation(
                    "Looks well-grounded",
                    "Low risk. Keep logging risk scores to catch regressions.",
                    Priority.LOW,
                )
            )
        return recs

    # -- Module API ---------------------------------------------------------
    def run(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        output = payload.get("output")
        if not isinstance(output, str):
            raise ValidationError("payload must include a string 'output'")
        sources = payload.get("sources")
        return self.analyze(
            output,
            sources=sources,
            support_threshold=float(payload.get("support_threshold", 0.5)),
        ).to_dict()


__all__ = ["HallucinationDetector"]
