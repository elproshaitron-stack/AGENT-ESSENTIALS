# Agent Essentials

**The missing toolkit for AI agents.**

Design, validate, optimize and scale AI agents **before** you ship them to production.

[![CI](https://github.com/agent-essentials/agent-essentials/actions/workflows/ci.yml/badge.svg)](https://github.com/agent-essentials/agent-essentials/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Typed](https://img.shields.io/badge/typing-strict-informational.svg)](https://peps.python.org/pep-0561/)

---

## What this is (and isn't)

Agent Essentials is **not another agent framework.** It does not run your agents, and it does not compete with LangChain, CrewAI, AutoGen, or the OpenAI Agents SDK. Those frameworks *execute* agents.

Agent Essentials helps you make the **decisions that come before execution** — and that determine whether your agent survives production:

> *What architecture should I use? Do I need RAG? Do I need Redis? How should memory work? How much will this cost? Will it scale? Is it reliable? How do I optimize it?*

It is **framework-agnostic** — use it alongside whatever runtime you already have.

## Core philosophy

```
Design before coding. Validate before deployment.
Optimize before scaling. Measure before spending.
```

## Highlights

- **Zero required dependencies.** The entire core runs on the Python standard library. Heavy things (`tiktoken`, provider SDKs) are optional extras.
- **Deterministic & offline.** Every core engine is rule-based and reproducible — no API keys, no network, fully unit-testable. LLM-powered enhancements are opt-in plugins.
- **Typed end to end.** Strict type hints and a shipped `py.typed` marker.
- **Plugin-first.** Built-in modules register through the *same* entry-point system third-party plugins use.
- **One uniform seam.** Every module implements `run(dict) -> dict`, so the CLI, plugins and remote callers drive any module the same way — while a rich typed API is available for direct Python use.

## Install

```bash
pip install agent-essentials            # core, zero dependencies
pip install "agent-essentials[tokenizers]"   # + exact tiktoken counting
pip install "agent-essentials[llm]"     # + OpenAI/Anthropic SDKs for LLM plugins
pip install "agent-essentials[dev]"     # + pytest, ruff, mypy
```

Requires Python 3.12+.

## The five MVP modules

| Module | Class | What it answers |
|---|---|---|
| Architecture Generator | `ArchitectureGenerator` | What stack, infra, RAG, memory, scaling & cost do I need? |
| Memory Engine | `MemoryEngine` | How should my agent remember, recall and compress context? |
| Task Planner | `TaskPlanner` | How do I turn a goal into milestones, tasks, deps & risks? |
| Hallucination Detector | `HallucinationDetector` | How risky / ungrounded is this output? |
| Token Counter | `TokenCounter` | How many tokens, how much money, how do I spend less? |

Plus an included **`entailment` plugin** (NLI-style per-claim validator with an injectable LLM scorer) — see [`docs/modules/entailment.md`](docs/modules/entailment.md).

---

## Quick start

### 1. Architecture Generator

```python
from agent_essentials import ArchitectureGenerator, ProjectSpec

rec = ArchitectureGenerator().generate(
    ProjectSpec(
        project_type="customer support",
        users=10_000,
        documents=50_000,
        countries=["US", "MX"],
    )
)

print(rec.summary)
print("RAG:", rec.needs_rag, "| Vector store:", rec.vector_store)
print("Cache:", rec.needs_cache, "| Queue:", rec.needs_queue)
print("Cost/mo:", rec.estimated_monthly_cost_usd["total_per_month"])
print(rec.diagram_mermaid)   # a ready-to-paste Mermaid diagram
```

### 2. Memory Engine

```python
from agent_essentials import MemoryEngine

mem = MemoryEngine()
mem.save_memory("User prefers dark mode and concise answers.", importance=0.8)
mem.save_memory("User is building a sports-league SaaS in Mexico.", importance=0.9)

hits = mem.retrieve_memory("what does the user like?", k=2)
ctx = mem.optimize_context("user preferences", token_budget=512)
print(ctx.context, ctx.used_tokens)
```

### 3. Task Planner

```python
from agent_essentials import TaskPlanner

plan = TaskPlanner().plan("Build a sports league SaaS platform with payments and live scores")
print(plan.domain, plan.detected_features)
for m in plan.milestones:
    print(m.name, "->", m.task_ids)
print("Execution order:", plan.execution_order)
print("Parallelizable groups:", plan.parallel_groups)
```

### 4. Hallucination Detector

```python
from agent_essentials import HallucinationDetector

report = HallucinationDetector().analyze(
    "The Eiffel Tower opened in 1925 and is 1,200m tall.",
    sources=["The Eiffel Tower opened in 1889 and is about 330 metres tall."],
)
print(report.risk_score, report.risk_level)
for w in report.warnings:
    print("-", w.code, w.message)
```

### 5. Token Counter

```python
from agent_essentials import TokenCounter

tc = TokenCounter()
est = tc.estimate_cost(model="claude-sonnet-4-6", input_tokens=1500, output_tokens=500, requests=10_000)
print(f"${est.total_cost:,.2f}/run-batch")
for s in est.suggestions:
    print("-", s.title)

# Compare the same workload across every known model, cheapest first:
print(tc.compare(input_tokens=1500, output_tokens=500, requests=10_000).ranked[:3])
```

---

## CLI

Every command runs through the same plugin registry as the Python API.

```bash
agent-essentials modules                       # list registered modules
agent-essentials architecture --type "customer support" --users 10000 --documents 50000 --countries US,MX
agent-essentials plan "Build a sports league SaaS platform"
agent-essentials validate --output "Revenue grew 240%." --source "Revenue grew 12%."
agent-essentials tokens --op estimate --model gpt-4.1 --input-tokens 1500 --output-tokens 500 --requests 1000
agent-essentials run memory --json '{"op":"retrieve","query":"prefs","memories":["user likes dark mode"]}'
```

`ae` is installed as a short alias for `agent-essentials`.

---

## Plugin system

Add a module without touching the core. Implement `Module` and expose a `Plugin`:

```python
from agent_essentials.core import Module, Plugin

class SentimentModule(Module):
    name = "sentiment"
    summary = "Toy sentiment scorer."

    def run(self, payload):
        text = payload["text"].lower()
        score = text.count("good") - text.count("bad")
        return {"sentiment": score}

plugin = Plugin(name="sentiment", factory=SentimentModule, summary=SentimentModule.summary)
```

Publish it via an entry point and it is auto-discovered:

```toml
# pyproject.toml of your plugin package
[project.entry-points."agent_essentials.plugins"]
sentiment = "my_pkg.sentiment:plugin"
```

```python
from agent_essentials import get_registry
get_registry().create("sentiment").run({"text": "good good bad"})  # -> {"sentiment": 1}
```

See [`docs/guides/plugins.md`](docs/guides/plugins.md) and [`examples/plugin_sentiment.py`](examples/plugin_sentiment.py).

---

## Repository layout

```
agent-essentials/
├── src/agent_essentials/
│   ├── core/           # ABCs, Result types, plugin registry, DI container
│   ├── architecture/   # Architecture Generator
│   ├── memory/         # Memory Engine
│   ├── planning/       # Task Planner
│   ├── validation/     # Hallucination Detector + Entailment plugin
│   ├── optimization/   # Token Counter + pricing
│   ├── research/       # roadmap (Web Extractor, …)
│   ├── integration/    # roadmap (API Connector, …)
│   ├── utilities/      # shared text helpers
│   └── cli.py
├── tests/{unit,integration}/
├── examples/
├── docs/{modules,guides,diagrams}/
└── pyproject.toml
```

## Documentation

- [Architecture overview](docs/architecture.md)
- [Public API design](docs/api.md)
- [Plugin guide](docs/guides/plugins.md)
- Module references: [architecture](docs/modules/architecture.md) · [memory](docs/modules/memory.md) · [planning](docs/modules/planning.md) · [validation](docs/modules/validation.md) · [optimization](docs/modules/optimization.md) · [entailment](docs/modules/entailment.md)
- [Technical study — adversarial probes, findings & improvements (ES)](docs/estudio-tecnico.md)
- [Roadmap](ROADMAP.md) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md) · [Security](SECURITY.md) · [Code of Conduct](CODE_OF_CONDUCT.md)

## Development

```bash
pip install -e ".[dev]"
pytest --cov=agent_essentials      # tests + coverage
ruff check . && ruff format --check .
mypy
```

## Pricing note

Model prices in `agent_essentials/optimization/pricing.py` reflect public list prices as of **2026-06**. Verify against the provider's pricing page before using them for billing.

## License

[MIT](LICENSE) © Agent Essentials Contributors
