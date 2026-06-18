# Contributing to Agent Essentials

Thanks for helping build the toolkit engineers reach for *before* shipping agents.

## Principles

- **Decide, don't execute.** Modules help engineers make decisions; they do not
  run agents. Keep that boundary.
- **Deterministic core, optional intelligence.** Core engines must work offline
  with no API keys and be unit-testable. LLM-powered behavior belongs behind the
  `llm` extra or in a plugin.
- **Minimal dependencies.** The core stays stdlib-only. New runtime dependencies
  need a strong justification and usually belong in an optional extra.

## Dev setup

```bash
git clone https://github.com/agent-essentials/agent-essentials
cd agent-essentials
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install   # optional but recommended
```

## Quality gates (all enforced in CI)

```bash
ruff check .            # lint
ruff format .           # format
mypy                    # strict type checking
pytest --cov=agent_essentials --cov-report=term-missing
coverage report --fail-under=80
```

Every PR must keep coverage at 80%+ and pass lint, format and mypy.

## Adding a module

1. Create a package under `src/agent_essentials/<suite>/`.
2. Implement a class that subclasses `agent_essentials.core.Module` and provides
   `run(payload: Mapping[str, Any]) -> dict[str, Any]` plus a rich typed API.
3. Put input/output models in `models.py` (dataclasses mixing in `Serializable`).
4. Keep heuristics as pure functions in `rules.py`/`checks.py` so they're testable.
5. Expose a module-level `plugin = Plugin(...)` in the package `__init__.py`.
6. Register it in `pyproject.toml` under
   `[project.entry-points."agent_essentials.plugins"]` and in
   `agent_essentials/__init__.py:_register_builtins`.
7. Add unit tests, an example in `examples/`, and a page in `docs/modules/`.

See [`docs/guides/plugins.md`](docs/guides/plugins.md) for the third-party path
(no core changes required).

## Commit & PR

- Use clear, present-tense commit messages.
- Reference the issue you're addressing.
- Fill out the PR checklist.

## Code of Conduct

Be respectful and constructive. We follow the
[Contributor Covenant](https://www.contributor-covenant.org/).
