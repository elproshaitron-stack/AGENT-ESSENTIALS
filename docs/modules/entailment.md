# Entailment Validator (NLI plugin)

A per-claim entailment checker — the principled complement to the heuristic
[Hallucination Detector](validation.md). It classifies each claim against its
best-matching source sentence as **entailment**, **contradiction** or **neutral**.

It is registered as the `entailment` plugin (not part of the 5-module MVP core).

## API

```python
from agent_essentials import EntailmentValidator

report = EntailmentValidator().validate(
    "The medication is safe. Revenue was 999.",
    sources=["The medication is not safe.", "Revenue was 12."],
)
print(report.risk_score, report.risk_level)        # 0.7 high
for j in report.judgements:
    print(j.label.value, "<-", j.claim)             # contradiction / contradiction
```

`EntailmentReport`: `risk_score`, `risk_level`, `entailed`, `contradicted`,
`neutral`, `judgements` (list of `EntailmentJudgement`), `recommendations`.

## Pluggable scorer (deterministic core, optional LLM)

The default `HeuristicEntailmentScorer` is deterministic and offline (reuses the
validation checks: negation-scope polarity + numeric disagreement + coverage).
Inject any callable to use real semantic judgement — no module changes:

```python
from agent_essentials.validation import EntailmentLabel

def my_scorer(premise: str, hypothesis: str) -> tuple[EntailmentLabel, float]:
    # Call an LLM or a transformers NLI model here (the `llm` extra).
    ...

EntailmentValidator(scorer=my_scorer).validate(output, sources=[...])
```

A `Scorer` is `Callable[[premise, hypothesis], tuple[EntailmentLabel, float]]`.
See [`examples/plugin_entailment_llm.py`](../../examples/plugin_entailment_llm.py).

## CLI

```bash
agent-essentials run entailment --json '{"output":"Paris is in France.","sources":["Paris is the capital of France."]}'
```

## When to use which validator

| | Hallucination Detector | Entailment Validator |
|---|---|---|
| Output | single risk score + warnings | per-claim labels |
| Sources | optional | required |
| Default cost | zero (heuristic) | zero (heuristic) |
| Upgrade path | — | inject an LLM/NLI scorer |
