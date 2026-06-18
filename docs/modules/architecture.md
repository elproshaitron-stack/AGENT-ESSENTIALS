# Architecture Generator

Recommend a production architecture from a high-level project description.

## API

```python
from agent_essentials import ArchitectureGenerator, ProjectSpec

rec = ArchitectureGenerator().generate(ProjectSpec(
    project_type="customer support", users=10_000, documents=50_000, countries=["US", "MX"],
))
```

### `ProjectSpec`

| Field | Type | Default | Notes |
|---|---|---|---|
| `project_type` | str | `"general"` | e.g. `customer support`, `rag`, `research` |
| `users` | int | `0` | active users |
| `documents` | int | `0` | corpus size (drives RAG + vector store) |
| `countries` | list[str] | `[]` | ISO codes; EU/UK ⇒ residency notes |
| `requests_per_day` | int? | `None` | else assumed `users * 10` |
| `compliance` | list[str] | `[]` | e.g. `gdpr`, `hipaa` |
| `latency_sensitive` / `realtime` / `multi_agent` | bool | `False` | |
| `budget` | str | `"balanced"` | `economy` \| `balanced` \| `premium` |

### `ArchitectureRecommendation` (selected fields)

`needs_rag`, `vector_store`, `needs_cache`, `needs_queue`, `memory_strategy`,
`model_strategy`, `recommended_models`, `deployment`, `scaling_strategy`,
`multi_region`, `data_residency_notes`, `estimated_monthly_cost_usd`,
`components`, `patterns`, `findings`, `recommendations`, `diagram_mermaid`.

## Heuristics (tunable in `architecture/knowledge.py`)

- **RAG** when documents ≥ 50 or the project type is knowledge-grounded.
- **Vector store** tiers: pgvector (≤10k) → managed (≤1M) → distributed cluster.
- **Cache (Redis)** when latency-sensitive, ≥1k users, or ≥50k req/day.
- **Queue** for large ingestion, batch domains, multi-agent, or ≥100k req/day.
- **Deployment** scales serverless → containers → Kubernetes by user count.
- **Regions** flagged for EU/UK users, residency compliance, or multi-country.

## CLI

```bash
agent-essentials architecture --type "customer support" --users 10000 --documents 50000 --countries US,MX
```
