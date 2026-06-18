# Memory Engine

Design and operate an agent's memory: save, recall, summarize and pack context.

## API

```python
from agent_essentials import MemoryEngine

mem = MemoryEngine()                       # defaults: in-memory store, hashing embedder
mem.save_memory("User prefers dark mode.", importance=0.8)
hits = mem.retrieve_memory("preferences", k=3)         # hybrid semantic + lexical
summary = mem.summarize_memory(max_sentences=3)
ctx = mem.optimize_context("preferences", token_budget=512)
```

| Method | Returns | Notes |
|---|---|---|
| `save_memory(content, *, kind, metadata, importance)` | `MemoryRecord` | importance ∈ [0,1] |
| `retrieve_memory(query, *, k, kind, alpha)` | `list[MemoryRecord]` | `alpha` blends semantic vs lexical (default 0.7) |
| `summarize_memory(*, kind, max_sentences)` | `str` | extractive summary |
| `optimize_context(query, *, token_budget, k, kind)` | `ContextResult` | greedily fills budget, summarizes overflow |

## Pluggable backends

- `MemoryStore` (default `InMemoryStore`) — implement for Redis/Postgres/vector DB.
- `Embedder` (default `HashingEmbedder`, deterministic & offline) — swap for a
  real embedding model.
- `Summarizer` (default `ExtractiveSummarizer`).

```python
MemoryEngine(store=MyVectorStore(), embedder=MyEmbedder(), summarizer=MySummarizer())
```

## CLI

```bash
agent-essentials run memory --json '{"op":"retrieve","query":"prefs","memories":["user likes dark mode"]}'
```
