# Public API design

## Conventions

- **Import surface.** Common classes are re-exported at the top level:
  `from agent_essentials import ArchitectureGenerator, MemoryEngine, TaskPlanner,
  HallucinationDetector, TokenCounter, ProjectSpec, get_registry`.
- **Two ways to call every module:**
  - *Typed* (recommended in Python): `ArchitectureGenerator().generate(spec)`.
  - *Generic* (CLI / plugins / transport): `module.run({...}) -> dict`.
- **Results are dataclasses** mixing in `Serializable`: call `.to_dict()` or
  `.to_json()` to serialize. Enums serialize to their string value.
- **Errors** derive from `agent_essentials.core.AgentEssentialsError`
  (`ValidationError`, `PluginError`, `ConfigurationError`, `MemoryStoreError`).

## Core types

```python
from agent_essentials.core import (
    Module,            # ABC: run(payload) -> dict ; classmethod describe()
    Plugin,            # descriptor: name, factory, summary, version ; create()
    PluginRegistry,    # register / get / create / names / load_entry_points
    get_registry,      # process-wide registry (entry points + builtins)
    Container,          # DI: register / register_instance / resolve / override
    Finding, Recommendation, Severity, Priority,
    Serializable,
)
```

## Module entry points (typed API)

| Module | Constructor | Primary method | Returns |
|---|---|---|---|
| `ArchitectureGenerator` | `()` | `generate(spec: ProjectSpec)` | `ArchitectureRecommendation` |
| `MemoryEngine` | `(store?, embedder?, summarizer?)` | `save_memory` / `retrieve_memory` / `summarize_memory` / `optimize_context` | records / `ContextResult` |
| `TaskPlanner` | `()` | `plan(goal: str)` | `Plan` |
| `HallucinationDetector` | `()` | `analyze(output, sources=None)` | `ValidationReport` |
| `TokenCounter` | `()` | `count` / `estimate_cost` / `compare` | `int` / `CostEstimate` / `ModelComparison` |

## Generic `run` payloads

```jsonc
// architecture
{ "project_type": "customer support", "users": 10000, "documents": 50000, "countries": ["US","MX"] }
// memory
{ "op": "retrieve", "query": "prefs", "k": 3, "memories": ["user likes dark mode"] }
// planning
{ "goal": "Build a sports league SaaS platform" }
// validation
{ "output": "…", "sources": ["…"] }
// optimization
{ "op": "estimate", "model": "gpt-4.1", "input_tokens": 1500, "output_tokens": 500, "requests": 1000 }
```

## Stability

Pre-1.0, minor versions may adjust APIs; breaking changes are called out in
`CHANGELOG.md`. The `Module.run(dict) -> dict` seam is the most stable contract
and is the safest thing to build automation against.
