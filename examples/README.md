# Examples

Runnable scripts for each MVP module. With the package installed (`pip install -e .`)
or `src` on `PYTHONPATH`, run any of them:

```bash
python examples/01_architecture.py
python examples/02_memory.py
python examples/03_planning.py
python examples/04_validation.py
python examples/05_tokens.py
python examples/06_end_to_end.py
python examples/plugin_sentiment.py   # custom plugin registration
```

| File | Module | Shows |
|---|---|---|
| `01_architecture.py` | Architecture Generator | Stack/RAG/cache/cost decisions + Mermaid diagram |
| `02_memory.py` | Memory Engine | Save, hybrid retrieval, summarize, budgeted context |
| `03_planning.py` | Task Planner | Milestones, dependencies, execution order, risks |
| `04_validation.py` | Hallucination Detector | Grounded vs hallucinated outputs, warnings |
| `05_tokens.py` | Token Counter | Cost estimate + cheapest-model comparison |
| `06_end_to_end.py` | All | Design → price → plan → validate, then the registry |
| `plugin_sentiment.py` | Plugin system | Implementing `Module` and registering a `Plugin` |
