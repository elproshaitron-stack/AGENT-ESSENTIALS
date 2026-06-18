"""Inject a custom (e.g. LLM-backed) entailment scorer.

The default scorer is deterministic and offline. In production you would pass a
``Scorer`` backed by an LLM or a transformers NLI model (the ``llm`` extra). Here
we inject a tiny stand-in to show the seam without needing API keys: the
EntailmentValidator does not change, only the scorer does.
"""

from __future__ import annotations

from agent_essentials import EntailmentValidator
from agent_essentials.validation import EntailmentLabel


def fake_llm_scorer(premise: str, hypothesis: str) -> tuple[EntailmentLabel, float]:
    """Stand-in for an LLM/NLI call. A real one would prompt a model with
    ``premise`` and ``hypothesis`` and parse the label."""
    p, h = premise.lower(), hypothesis.lower()
    shared = [w for w in h.split() if len(w) > 3 and w in p]
    if "not" in p and "not" not in h and shared:
        return EntailmentLabel.CONTRADICTION, 0.95
    if len(shared) >= max(1, len([w for w in h.split() if len(w) > 3]) // 2):
        return EntailmentLabel.ENTAILMENT, 0.9
    return EntailmentLabel.NEUTRAL, 0.6


def main() -> None:
    validator = EntailmentValidator(scorer=fake_llm_scorer)
    report = validator.validate(
        "The Eiffel Tower is in Paris. It is not in Berlin.",
        sources=["The Eiffel Tower, a landmark in Paris, opened in 1889."],
    )
    print(
        f"risk={report.risk_score} ({report.risk_level}) "
        f"entailed={report.entailed} contradicted={report.contradicted} neutral={report.neutral}"
    )
    for j in report.judgements:
        print(f"  {j.label.value:13} (score={j.score}) <- {j.claim}")


if __name__ == "__main__":
    main()
