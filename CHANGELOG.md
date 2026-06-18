# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Entailment Validator (`entailment` plugin).** A per-claim NLI-style check that
  classifies each claim against its best-matching source sentence as
  entailment/contradiction/neutral. Ships a deterministic, offline default scorer
  and accepts an injectable `Scorer` (LLM or transformers NLI via the `llm`
  extra) — the toolkit's "deterministic core, optional intelligence" pattern.
- **Project hygiene.** `SECURITY.md`, `CODE_OF_CONDUCT.md`, `.editorconfig`,
  Dependabot config, and a MkDocs site config (`mkdocs.yml`) for the `docs` extra.

### Improved
- **Hallucination Detector — negation/polarity-aware grounding.** A claim that
  reuses a source's vocabulary but flips its meaning ("X is safe" vs source "X is
  *not* safe") was previously scored `risk=0.0` (low) — a dangerous false
  negative. Grounding is now sentence-level and negation-scope aware: such claims
  are flagged `contradicts_source` and scored high risk, while claims that merely
  *add* an unrelated negation are not falsely flagged.
- **Memory Engine — subword n-gram embedder.** `HashingEmbedder` now adds
  character n-gram (subword) features, so morphological variants
  (`running`/`runner`) and typos match. `cosine('running','runner')` went from
  `0.00` to `~0.35`. Still lexical (no synonyms); configurable via
  `subword_ngrams` / `subword_weight`.
- **Token Counter — CJK-aware estimation.** The dependency-free heuristic counted
  CJK text at `chars/4`, underestimating Chinese/Japanese/Korean by ~10x
  (14-char Chinese string ⇒ 2 tokens). It now counts CJK characters at ~1.5
  tokens each; Latin estimation is unchanged.
- **Architecture Generator — cost coherent with the chosen tier.** The monthly
  cost band was identical for `economy`/`balanced`/`premium` because it used
  fixed rates. It now derives the low/high bands from the live pricing catalog
  according to the recommended default/escalation tiers, so premium correctly
  costs more than economy.
- **Task Planner — bilingual (EN+ES), accent-insensitive detection.** Spanish
  goals previously detected far fewer features ("plataforma SaaS con pagos y
  usuarios" found 1 of 4). Domain/feature detection now matches English and
  Spanish keywords and strips accents.
- **Memory Engine — input hardening.** `retrieve_memory` validates `alpha ∈
  [0,1]`; `optimize_context` now returns a truncated fragment of the top memory
  instead of an empty context when no whole memory fits the budget.
- **Hallucination Detector — numeric mismatch detection.** Flags a claim whose
  figures disagree with its best-matching source sentence ("opened in 1925" vs a
  source that says 1889), even when the wrong number appears elsewhere.
- **Token Counter — `compare` validates inputs** (non-negative tokens, ≥1 request).
- **Architecture Generator — hyperscale guardrails.** Replica estimates are now
  capped (a single fleet does not scale to tens of thousands of replicas), and
  above ~10M users the recommendation flags `hyperscale` and advises a
  cell-based, multi-region architecture instead of a linear cost projection.


## [0.1.0] - 2026-06-18

Initial public release — the MVP toolkit.

### Added
- **Core foundations**: `Module` ABC, `Plugin`/`PluginRegistry` with entry-point
  discovery, a lightweight `Container` (DI), shared `Finding`/`Recommendation`/
  `Severity` result types, and JSON-serializable result models.
- **Architecture Generator**: turns a `ProjectSpec` into a recommended stack,
  RAG/cache/queue decisions, memory & scaling strategy, cost estimate and a
  generated Mermaid diagram.
- **Memory Engine**: `save_memory`, `retrieve_memory` (hybrid semantic + lexical),
  `summarize_memory`, `optimize_context`; pluggable `MemoryStore`, `Embedder`
  (deterministic hashing default) and `Summarizer`.
- **Task Planner**: decomposes a goal into milestones, tasks, dependencies,
  risks, a topologically-sorted execution order and parallelizable groups.
- **Hallucination Detector**: confidence scoring, source grounding, fabricated-
  specifics and contradiction checks, returning a risk score and recommendations.
- **Token Counter**: token estimation (exact with optional `tiktoken`), a 2026-06
  pricing catalog for OpenAI/Anthropic/Gemini/local, cost estimates, model
  comparison and optimization suggestions.
- **CLI** (`agent-essentials` / `ae`) exposing every module over a uniform JSON I/O.
- Test suite (66 tests, 91% coverage), strict mypy, ruff lint/format, CI/CD,
  examples and documentation.

[Unreleased]: https://github.com/agent-essentials/agent-essentials/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/agent-essentials/agent-essentials/releases/tag/v0.1.0
