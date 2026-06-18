"""Hallucination Detector: score outputs for grounding and consistency."""

from __future__ import annotations

from agent_essentials import HallucinationDetector


def main() -> None:
    detector = HallucinationDetector()

    sources = [
        "The Eiffel Tower is located in Paris, France. It was completed in 1889 "
        "and stands about 330 metres tall."
    ]

    print("== Well-grounded answer ==")
    good = detector.analyze(
        "The Eiffel Tower is in Paris and was completed in 1889.", sources=sources
    )
    print(f"risk={good.risk_score} ({good.risk_level}), confidence={good.confidence}")

    print("\n== Hallucinated answer ==")
    bad = detector.analyze(
        "The Eiffel Tower opened in 1925 and is definitely 1,200 metres tall, "
        "according to (Smith, 2099).",
        sources=sources,
    )
    print(f"risk={bad.risk_score} ({bad.risk_level})")
    for warning in bad.warnings:
        print(f"  ! {warning.code}: {warning.message}")
    for rec in bad.recommendations:
        print(f"  -> {rec.title}")


if __name__ == "__main__":
    main()
