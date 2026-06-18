# Token Counter

Estimate token usage and cost, compare models, and get optimization suggestions.

## API

```python
from agent_essentials import TokenCounter

tc = TokenCounter()
tc.count("hello world", model="gpt-4.1")                       # token count
est = tc.estimate_cost(model="claude-sonnet-4-6",
                       input_tokens=1500, output_tokens=500, requests=10_000)
cmp = tc.compare(input_tokens=1500, output_tokens=500, requests=10_000)  # cheapest first
```

| Method | Returns |
|---|---|
| `count(text, model)` | `int` |
| `estimate_cost(*, model, input_text/input_tokens, output_text/output_tokens, requests, cached)` | `CostEstimate` |
| `compare(*, input_tokens, output_tokens, requests)` | `ModelComparison` |

## Token counting

Exact via `tiktoken` when the `tokenizers` extra is installed; otherwise a
provider-agnostic heuristic (`~4 chars/token` blended with `~1.33 tokens/word`).

## Pricing

`optimization/pricing.py` holds list prices (USD / 1M tokens) **as of 2026-06**
for OpenAI (GPT-5, GPT-4.1 family, GPT-4o), Anthropic (Opus 4.8, Sonnet 4.6,
Haiku 4.5), Google (Gemini 2.5 Pro/Flash) and `local` (self-hosted, $0). Friendly
aliases (`opus`, `sonnet`, `haiku`, `gemini-pro`, …) resolve to canonical models.
Verify against the provider's pricing page before billing.

## Suggestions

Estimates include recommendations: default to a cheaper tier, compress context,
enable prompt caching, use the Batch API, and cap output length.

## CLI

```bash
agent-essentials tokens --op estimate --model gpt-4.1 --input-tokens 1500 --output-tokens 500 --requests 1000
```
