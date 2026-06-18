# Hallucination Detector

Score a model output for hallucination risk with explainable, offline heuristics.

## API

```python
from agent_essentials import HallucinationDetector

report = HallucinationDetector().analyze(
    "The Eiffel Tower opened in 1925.",
    sources=["The Eiffel Tower opened in 1889."],
)
report.risk_score        # 0..1
report.risk_level        # low | moderate | high | critical
report.confidence        # apparent stated confidence (language-based)
report.warnings          # list[Finding]
report.recommendations   # list[Recommendation]
report.checks            # raw sub-scores
```

## Checks (in `validation/checks.py`)

- **Source grounding** — fraction of each claim's content words covered by the
  best-matching source; low coverage ⇒ unsupported claim.
- **Fabricated specifics** — numbers, URLs and citations present in the answer but
  absent from the sources.
- **Contradictions** — sentence pairs that negate one another or use antonyms over
  an overlapping subject.
- **Overconfidence** — absolute language (`always`, `definitely`, `100%`) that
  compounds risk when claims are unsupported.

If no sources are supplied, the detector cannot verify grounding and applies a
moderate baseline plus a `no_sources` warning.

## CLI

```bash
agent-essentials validate --output "Revenue grew 240%." --source "Revenue grew 12%."
```
