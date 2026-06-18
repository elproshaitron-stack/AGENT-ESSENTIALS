# Roadmap

Agent Essentials ships an MVP today and grows into a full pre-production toolkit.
Versioning follows [SemVer](https://semver.org/); minor releases add modules,
patch releases fix bugs, and breaking changes wait for a major bump.

## Status legend

✅ shipped · 🚧 in progress · 🗓️ planned

## Suites

### Architecture
- ✅ Architecture Generator
- 🗓️ Pattern Recommender, Workflow Designer, RAG Designer, Scaling Advisor,
  Architecture Validator, Multi-Agent Designer

### Memory
- ✅ Memory Engine (with pluggable store/embedder/summarizer)
- 🗓️ Context Optimizer (standalone), Knowledge Graph, Memory Router

### Planning
- ✅ Task Planner
- 🗓️ Goal Decomposer, Decision Analyzer, Project Planner

### Validation
- ✅ Hallucination Detector
- 🗓️ Fact Checker, Response Validator, Self Critic

### Optimization
- ✅ Token Counter (+ pricing, model comparison)
- 🗓️ Cost Analyzer, Model Selector, Inference Optimizer

### Research
- 🗓️ Web Extractor, Metadata Extractor, Website Analyzer, Article Summarizer

### Integration
- 🗓️ Universal API Connector, OpenAPI Parser, Workflow Builder, Webhook Manager

## Development priorities

1. **v0.1 (now): MVP.** Five modules, plugin system, CLI, tests, docs, CI.
2. **v0.2: Optimization & Validation depth.** Model Selector and Cost Analyzer
   (build on the pricing catalog); Response Validator and Fact Checker.
3. **v0.3: Architecture suite.** RAG Designer, Scaling Advisor, Architecture
   Validator, Multi-Agent Designer.
4. **v0.4: Memory & Planning depth.** Knowledge Graph, Memory Router; Decision
   Analyzer, Project Planner.
5. **v0.5: Research & Integration.** Web/metadata extraction, API connectors.
6. **v1.0:** Stable public API, full suite coverage, optional LLM-backed plugins,
   adapters for popular runtimes (LangChain, CrewAI, OpenAI Agents) — as
   *advisors*, never executors.

## Release strategy

- `main` is always green (lint + types + tests + build).
- Tag `vMAJOR.MINOR.PATCH` → the Release workflow builds and publishes to PyPI via
  OIDC trusted publishing.
- Each release updates `CHANGELOG.md` (Keep a Changelog format).
- Deprecations are announced one minor version before removal.
