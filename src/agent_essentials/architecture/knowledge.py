"""Static knowledge used by the architecture rules.

Centralizing thresholds and catalogs keeps the rule functions readable and makes
it trivial to tune the heuristics (or override them in a plugin).
"""

from __future__ import annotations

# Scale thresholds ----------------------------------------------------------
SMALL_USER_CEILING = 1_000
MEDIUM_USER_CEILING = 100_000

# Document-count thresholds that change the retrieval/storage strategy.
RAG_DOCUMENT_FLOOR = 50
PGVECTOR_DOCUMENT_CEILING = 10_000
MANAGED_VECTOR_DOCUMENT_CEILING = 1_000_000

# Hyperscale guardrails: above these, a single fleet stops scaling linearly and
# the design must shard into cells / regions.
MAX_REPLICAS = 500
HYPERSCALE_USER_FLOOR = 10_000_000

# Request-volume thresholds.
CACHE_REQUESTS_FLOOR = 50_000
QUEUE_REQUESTS_FLOOR = 100_000

# Project types that are inherently knowledge-grounded and benefit from RAG.
KNOWLEDGE_GROUNDED_TYPES = frozenset(
    {
        "customer support",
        "support",
        "research",
        "knowledge base",
        "documentation",
        "legal",
        "qa",
        "question answering",
        "search",
    }
)

# Project types that tend to fan out into background / long-running work.
BATCH_ORIENTED_TYPES = frozenset(
    {"research", "data analysis", "etl", "batch", "ingestion", "analytics"}
)

# Model tiers with current (2026-06) representative models per provider.
MODEL_TIERS: dict[str, list[str]] = {
    "frontier": ["Claude Opus 4.8", "GPT-5", "Gemini 2.5 Pro"],
    "balanced": ["Claude Sonnet 4.6", "GPT-4.1", "Gemini 2.5 Pro"],
    "economy": ["Claude Haiku 4.5", "GPT-4.1-mini", "Gemini 2.5 Flash"],
}

VALID_BUDGETS = frozenset({"economy", "balanced", "premium"})

# Canonical optimization.pricing keys for each tier, used to derive cost bands
# from the real pricing catalog (keeps cost consistent with the chosen tier).
TIER_PRICING_KEYS: dict[str, list[str]] = {
    "frontier": ["claude-opus-4-8", "gpt-5", "gemini-2.5-pro"],
    "balanced": ["claude-sonnet-4-6", "gpt-4.1", "gemini-2.5-pro"],
    "economy": ["claude-haiku-4-5", "gpt-4.1-mini", "gemini-2.5-flash"],
}


# Countries in scope for GDPR-style data-residency considerations (EU/EEA + UK).
EU_EEA_UK = frozenset(
    {
        "AT",
        "BE",
        "BG",
        "HR",
        "CY",
        "CZ",
        "DK",
        "EE",
        "FI",
        "FR",
        "DE",
        "GR",
        "HU",
        "IE",
        "IT",
        "LV",
        "LT",
        "LU",
        "MT",
        "NL",
        "PL",
        "PT",
        "RO",
        "SK",
        "SI",
        "ES",
        "SE",
        "IS",
        "LI",
        "NO",
        "GB",
        "UK",
    }
)

# Compliance regimes that imply regional data residency.
RESIDENCY_COMPLIANCE = frozenset({"gdpr", "hipaa", "ccpa", "lgpd", "pipeda"})

__all__ = [name for name in dir() if name.isupper()]
