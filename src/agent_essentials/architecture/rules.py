"""Pure, individually-testable heuristic rules.

Each function takes a :class:`ProjectSpec` and returns a decision plus a
human-readable rationale. Keeping them pure (no I/O, no shared state) makes the
whole engine deterministic and trivial to unit test or override.
"""

from __future__ import annotations

from ..optimization.pricing import resolve_price
from .knowledge import (
    BATCH_ORIENTED_TYPES,
    CACHE_REQUESTS_FLOOR,
    EU_EEA_UK,
    HYPERSCALE_USER_FLOOR,
    KNOWLEDGE_GROUNDED_TYPES,
    MANAGED_VECTOR_DOCUMENT_CEILING,
    MAX_REPLICAS,
    MEDIUM_USER_CEILING,
    MODEL_TIERS,
    PGVECTOR_DOCUMENT_CEILING,
    QUEUE_REQUESTS_FLOOR,
    RAG_DOCUMENT_FLOOR,
    RESIDENCY_COMPLIANCE,
    SMALL_USER_CEILING,
    TIER_PRICING_KEYS,
)
from .models import ProjectSpec


def decide_rag(spec: ProjectSpec) -> tuple[bool, str]:
    if spec.documents >= RAG_DOCUMENT_FLOOR:
        return True, (
            f"{spec.documents:,} documents exceed the {RAG_DOCUMENT_FLOOR}-document floor "
            "where retrieval beats stuffing everything into the context window."
        )
    if spec.project_type in KNOWLEDGE_GROUNDED_TYPES:
        return True, (
            f"Project type {spec.project_type!r} is knowledge-grounded; answers should be "
            "grounded in and cited from a source corpus to stay accurate."
        )
    if spec.documents == 0:
        return False, "No document corpus provided, so RAG is unnecessary for now."
    return False, (
        f"Only {spec.documents} documents; a small static context or prompt template is "
        "simpler and cheaper than a full RAG pipeline."
    )


def decide_vector_store(spec: ProjectSpec, needs_rag: bool) -> tuple[str | None, str]:
    if not needs_rag:
        return None, "No vector store required without retrieval."
    if spec.documents <= PGVECTOR_DOCUMENT_CEILING:
        return "pgvector (PostgreSQL extension)", (
            "Small corpus: reuse your primary Postgres with pgvector to avoid running a "
            "separate datastore."
        )
    if spec.documents <= MANAGED_VECTOR_DOCUMENT_CEILING:
        return "Managed vector DB (Pinecone / Weaviate / Qdrant Cloud)", (
            "Mid-size corpus: a purpose-built vector DB gives better recall and latency than "
            "pgvector without the ops burden of self-hosting."
        )
    return "Distributed vector DB cluster (Qdrant / Milvus) with sharding", (
        "Very large corpus: shard across a clustered vector DB and add a re-ranking stage."
    )


def decide_cache(spec: ProjectSpec) -> tuple[bool, str]:
    reasons: list[str] = []
    if spec.latency_sensitive:
        reasons.append("latency-sensitive workload")
    if spec.users >= SMALL_USER_CEILING:
        reasons.append(f"{spec.users:,} users")
    if spec.effective_requests_per_day >= CACHE_REQUESTS_FLOOR:
        reasons.append(f"~{spec.effective_requests_per_day:,} requests/day")
    if reasons:
        return True, (
            "Add Redis for response + semantic caching, rate limiting and session state "
            f"({', '.join(reasons)}). A semantic cache alone can deflect 20-40% of LLM calls."
        )
    return False, (
        "Low volume: an in-process cache is enough. Introduce Redis once you pass ~1k users "
        "or need shared rate limiting."
    )


def decide_queue(spec: ProjectSpec) -> tuple[bool, str]:
    reasons: list[str] = []
    if spec.documents >= PGVECTOR_DOCUMENT_CEILING:
        reasons.append("large ingestion/embedding pipeline")
    if spec.project_type in BATCH_ORIENTED_TYPES:
        reasons.append(f"{spec.project_type!r} implies background jobs")
    if spec.multi_agent:
        reasons.append("multi-agent orchestration with long-running steps")
    if spec.effective_requests_per_day >= QUEUE_REQUESTS_FLOOR:
        reasons.append(f"~{spec.effective_requests_per_day:,} requests/day")
    if reasons:
        return True, (
            "Use an async task queue (Celery / RQ / Arq + broker) to decouple long-running "
            f"work from request handling ({', '.join(reasons)})."
        )
    return False, "Synchronous request handling is sufficient at this scale."


def decide_memory(spec: ProjectSpec) -> str:
    parts = ["Short-term: rolling conversation buffer with token-budgeted truncation."]
    if (
        spec.documents
        or spec.project_type in KNOWLEDGE_GROUNDED_TYPES
        or spec.users >= SMALL_USER_CEILING
    ):
        parts.append(
            "Long-term: vector-backed episodic memory keyed by user/session for "
            "cross-session recall."
        )
    parts.append("Summarization: compress older turns into a running summary to cap context cost.")
    if spec.multi_agent:
        parts.append("Shared blackboard memory for inter-agent coordination.")
    return " ".join(parts)


_BUDGET_TIERS: dict[str, tuple[str, str]] = {
    "economy": ("economy", "balanced"),
    "balanced": ("economy", "frontier"),
    "premium": ("balanced", "frontier"),
}


def decide_tiers(spec: ProjectSpec) -> tuple[str, str]:
    """Return (default_tier, escalation_tier) for the model router.

    ``economy`` keeps both routing tiers cheap; ``balanced`` keeps a cheap default
    but allows escalation to a frontier model; ``premium`` raises the default tier.
    """
    return _BUDGET_TIERS[spec.budget]


def decide_model_strategy(spec: ProjectSpec) -> tuple[str, dict[str, list[str]]]:
    default_tier, escalation_tier = decide_tiers(spec)
    models = {
        "default": MODEL_TIERS[default_tier],
        "escalation": MODEL_TIERS[escalation_tier],
    }
    strategy = (
        f"Model router: serve most traffic with a {default_tier}-tier model and escalate hard "
        f"or low-confidence queries to a {escalation_tier}-tier model. Gate escalation on the "
        "Hallucination Detector's risk score and task complexity."
    )
    return strategy, models


def _raw_replicas(spec: ProjectSpec) -> int:
    rps_peak = spec.effective_requests_per_day / 86_400 * 5  # assume 5x peak factor
    return max(2, int(rps_peak / 5) + 1)  # ~5 req/s per replica budget


def estimate_replicas(spec: ProjectSpec) -> int:
    """Stateless-replica count from peak load, capped at MAX_REPLICAS.

    Above the cap a single fleet no longer scales linearly; see is_hyperscale.
    """
    return min(_raw_replicas(spec), MAX_REPLICAS)


def is_hyperscale(spec: ProjectSpec) -> bool:
    """True when the system needs cell-based / multi-region scaling."""
    return spec.users >= HYPERSCALE_USER_FLOOR or _raw_replicas(spec) > MAX_REPLICAS


def decide_deployment(spec: ProjectSpec) -> tuple[str, str]:
    replicas = estimate_replicas(spec)
    if spec.users < SMALL_USER_CEILING and not spec.realtime:
        deployment = "Serverless functions (AWS Lambda / Google Cloud Run) behind an API gateway"
        scaling = (
            "Scale-to-zero between bursts; cold starts are acceptable. Keep the function "
            "stateless and push all state to managed services."
        )
    elif spec.users < MEDIUM_USER_CEILING:
        deployment = "Containerized services with autoscaling (ECS Fargate / Cloud Run / Fly.io)"
        scaling = (
            f"Run stateless replicas (start ~{replicas}) behind a load balancer with CPU/RPS "
            "autoscaling. Use connection pooling to the DB and a shared Redis."
        )
    else:
        deployment = "Kubernetes with horizontal pod autoscaling and a managed ingress"
        scaling = (
            f"Horizontal pod autoscaling (start ~{replicas} replicas), separate node pools for "
            "API vs. background workers, and a CDN in front of static assets."
        )
    return deployment, scaling


def decide_regions(spec: ProjectSpec) -> tuple[bool, str]:
    eu = [c for c in spec.countries if c in EU_EEA_UK]
    residency = [c for c in spec.compliance if c in RESIDENCY_COMPLIANCE]
    multi = len(set(spec.countries)) > 1
    if eu or residency or multi:
        notes: list[str] = []
        if eu:
            notes.append(
                f"EU/UK users ({', '.join(sorted(set(eu)))}) imply GDPR data residency; keep "
                "PII in-region."
            )
        if residency:
            notes.append(
                f"Compliance {sorted(set(residency))} requires regional storage, audit logging "
                "and a DPA/BAA with model providers."
            )
        if multi:
            notes.append(
                "Multiple countries: deploy regional replicas and route by geography to cut "
                "latency."
            )
        return True, " ".join(notes)
    return False, (
        "A single region is fine; add regions when you expand geographically or face "
        "data-residency rules."
    )


def _tier_rates(tier: str) -> tuple[float, float]:
    """Average input/output price (USD per 1M tokens) across a tier's models."""
    prices = [resolve_price(key) for key in TIER_PRICING_KEYS[tier]]
    avg_in = sum(p.input_per_1m for p in prices) / len(prices)
    avg_out = sum(p.output_per_1m for p in prices) / len(prices)
    return avg_in, avg_out


def estimate_cost(
    spec: ProjectSpec,
    *,
    needs_cache: bool,
    needs_queue: bool,
    vector_store: str | None,
    default_tier: str = "economy",
    escalation_tier: str = "balanced",
) -> dict[str, object]:
    requests_per_month = spec.effective_requests_per_day * 30
    input_tokens, output_tokens = 1_500, 500

    def cost_for(tier: str) -> float:
        rate_in, rate_out = _tier_rates(tier)
        per_request = input_tokens / 1e6 * rate_in + output_tokens / 1e6 * rate_out
        return requests_per_month * per_request

    # low = default (cheap) routing tier, high = escalation tier.
    low = cost_for(default_tier)
    high = cost_for(escalation_tier)

    infra = 0.0
    if needs_cache:
        infra += 25.0
    if needs_queue:
        infra += 30.0
    if vector_store and "Managed" in vector_store:
        infra += 70.0
    elif vector_store and "Distributed" in vector_store:
        infra += 300.0
    infra += 50.0 * estimate_replicas(spec) if spec.users >= SMALL_USER_CEILING else 0.0

    return {
        "currency": "USD",
        "assumptions": {
            "requests_per_month": requests_per_month,
            "input_tokens_per_request": input_tokens,
            "output_tokens_per_request": output_tokens,
            "default_tier": default_tier,
            "escalation_tier": escalation_tier,
            "pricing_as_of": "2026-06",
        },
        "llm_per_month": {"low": round(low, 2), "high": round(high, 2)},
        "infra_per_month": round(infra, 2),
        "total_per_month": {
            "low": round(low + infra, 2),
            "high": round(high + infra, 2),
        },
        "notes": (
            "Rough planning estimate only. Bands span the default routing tier (low) to the "
            "escalation tier (high), priced from the live catalog. Semantic caching, batching "
            "and prompt compression typically cut the LLM line item by 30-80%."
            + (
                " At this scale the infra figure is a floor: a single fleet does not scale "
                "linearly, so model cost per cell/region instead."
                if is_hyperscale(spec)
                else ""
            )
        ),
    }


__all__ = [
    "decide_cache",
    "decide_deployment",
    "decide_memory",
    "decide_model_strategy",
    "decide_queue",
    "decide_rag",
    "decide_regions",
    "decide_tiers",
    "decide_vector_store",
    "estimate_cost",
    "estimate_replicas",
    "is_hyperscale",
]
