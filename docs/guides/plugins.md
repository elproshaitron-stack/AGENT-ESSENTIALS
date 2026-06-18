# Plugin guide

Agent Essentials is plugin-first: built-in modules and your own extensions use
the same mechanism. A plugin is a `Plugin` descriptor that can build a `Module`.

## 1. Implement a Module

```python
from collections.abc import Mapping
from typing import Any
from agent_essentials.core import Module, Plugin

class SentimentModule(Module):
    name = "sentiment"
    version = "1.0.0"
    summary = "Lexicon sentiment scorer."

    def run(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        words = str(payload.get("text", "")).lower().split()
        score = sum(w in {"good", "great"} for w in words) - sum(w in {"bad"} for w in words)
        return {"score": score}

plugin = Plugin(name="sentiment", factory=SentimentModule, summary=SentimentModule.summary)
```

## 2a. Register at runtime (no packaging)

```python
from agent_essentials import get_registry
get_registry().register(plugin)
get_registry().create("sentiment").run({"text": "good great bad"})  # {"score": 1}
```

## 2b. Ship it as an installable plugin (auto-discovered)

Expose `plugin` through the `agent_essentials.plugins` entry-point group:

```toml
# your plugin package's pyproject.toml
[project.entry-points."agent_essentials.plugins"]
sentiment = "my_pkg.sentiment:plugin"
```

Once installed, `get_registry()` discovers it automatically — no core changes.

## What the registry accepts

`load_entry_points` and `register` accept any of:

- a `Plugin` instance (preferred),
- a `Module` **subclass** (wrapped into a `Plugin` using its `name`),
- a zero-argument callable returning a `Module`.

A factory that returns a non-`Module` raises `PluginError`.

## Dependency injection

Modules that need swappable backends should accept them in `__init__` and/or
resolve them from a `Container`:

```python
from agent_essentials.core import Container
c = Container()
c.register("store", lambda _c: MyRedisStore())
engine = MemoryEngine(store=c.resolve("store"))
```

## Conventions for good plugins

- Keep the core logic deterministic; put LLM/network behavior behind a flag.
- Validate inputs and raise `ValidationError` with a helpful message.
- Return JSON-serializable dicts from `run` (use `Serializable` models).
- Ship tests and a one-line `summary`.

## Injecting an LLM scorer (deterministic core, optional intelligence)

Some modules expose a callable *seam* so you can upgrade their core logic without
changing the module. The `EntailmentValidator` takes a `Scorer`
(`Callable[[premise, hypothesis], tuple[EntailmentLabel, float]]`): the default is
deterministic and offline, but you can inject an LLM- or transformers-backed
scorer (the `llm` extra) for real semantic judgement. This is the toolkit's
recommended pattern for adding intelligence: keep a cheap, testable default and
let callers opt into a model. See [`examples/plugin_entailment_llm.py`](../../examples/plugin_entailment_llm.py).
