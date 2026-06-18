"""The Architecture Generator module."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..core.base import Module
from ..core.result import Finding, Priority, Recommendation, Severity
from . import rules
from .models import ArchitectureRecommendation, Component, ProjectSpec


class ArchitectureGenerator(Module):
    """Turn a high-level project description into a recommended architecture."""

    name = "architecture"
    version = "0.1.0"
    summary = "Recommend stack, infra, RAG, memory, scaling and cost for an agent system."

    def generate(self, spec: ProjectSpec) -> ArchitectureRecommendation:
        needs_rag, rag_reason = rules.decide_rag(spec)
        vector_store, vector_reason = rules.decide_vector_store(spec, needs_rag)
        needs_cache, cache_reason = rules.decide_cache(spec)
        needs_queue, queue_reason = rules.decide_queue(spec)
        memory_strategy = rules.decide_memory(spec)
        default_tier, escalation_tier = rules.decide_tiers(spec)
        model_strategy, recommended_models = rules.decide_model_strategy(spec)
        deployment, scaling = rules.decide_deployment(spec)
        multi_region, residency = rules.decide_regions(spec)
        cost = rules.estimate_cost(
            spec,
            needs_cache=needs_cache,
            needs_queue=needs_queue,
            vector_store=vector_store,
            default_tier=default_tier,
            escalation_tier=escalation_tier,
        )

        components = self._build_components(
            spec,
            needs_rag=needs_rag,
            vector_store=vector_store,
            needs_cache=needs_cache,
            needs_queue=needs_queue,
        )
        patterns = self._build_patterns(spec, needs_rag=needs_rag)
        findings = self._build_findings(
            rag_reason=rag_reason,
            vector_reason=vector_reason,
            cache_reason=cache_reason,
            queue_reason=queue_reason,
            residency=residency,
            multi_region=multi_region,
        )
        recommendations = self._build_recommendations(spec, needs_rag=needs_rag)
        diagram = self._build_diagram(
            needs_rag=needs_rag,
            needs_cache=needs_cache,
            needs_queue=needs_queue,
            multi_agent=spec.multi_agent,
        )

        if rules.is_hyperscale(spec):
            patterns.extend(
                [
                    "Cell-based architecture (shard users into independent cells)",
                    "Multi-region active-active",
                ]
            )
            findings.append(
                Finding(
                    "hyperscale",
                    "At this scale a single fleet does not scale linearly; the replica and "
                    "infra figures are a floor. Shard into cells and go multi-region.",
                    Severity.HIGH,
                    {"users": spec.users},
                )
            )
            recommendations.insert(
                0,
                Recommendation(
                    "Design a cell-based, multi-region architecture",
                    "Shard users into independent cells (each a full stack) and route by cell; "
                    "scale by adding cells, not by growing one fleet.",
                    Priority.HIGH,
                ),
            )

        summary = (
            f"For a {spec.project_type!r} system with {spec.users:,} users and "
            f"{spec.documents:,} documents: "
            f"{'use RAG' if needs_rag else 'no RAG'}, "
            f"{'add Redis' if needs_cache else 'no cache yet'}, "
            f"{'add a task queue' if needs_queue else 'sync handling'}, "
            f"deploy via {deployment.split('(')[0].strip().lower()}."
        )

        return ArchitectureRecommendation(
            summary=summary,
            needs_rag=needs_rag,
            vector_store=vector_store,
            needs_cache=needs_cache,
            needs_queue=needs_queue,
            memory_strategy=memory_strategy,
            model_strategy=model_strategy,
            recommended_models=recommended_models,
            deployment=deployment,
            scaling_strategy=scaling,
            multi_region=multi_region,
            data_residency_notes=residency,
            estimated_monthly_cost_usd=cost,
            components=components,
            patterns=patterns,
            findings=findings,
            recommendations=recommendations,
            diagram_mermaid=diagram,
            spec=spec,
        )

    # -- Module API ---------------------------------------------------------
    def run(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        spec = ProjectSpec.from_dict(payload)
        return self.generate(spec).to_dict()

    # -- assembly helpers ---------------------------------------------------
    def _build_components(
        self,
        spec: ProjectSpec,
        *,
        needs_rag: bool,
        vector_store: str | None,
        needs_cache: bool,
        needs_queue: bool,
    ) -> list[Component]:
        components = [
            Component(
                "API Gateway",
                "edge",
                "Authenticate, rate-limit and route incoming requests.",
                "Single entry point keeps auth and quotas out of the agent code.",
            ),
            Component(
                "Agent Service",
                "compute",
                "Orchestrate the agent loop: prompt, tools, validation, response.",
                "Stateless service so it can scale horizontally.",
            ),
            Component(
                "LLM Router",
                "model",
                "Pick the cheapest model that can handle each request; escalate on risk.",
                "Tiered routing controls cost without sacrificing hard-query quality.",
            ),
            Component(
                "Memory Engine",
                "memory",
                "Short-term buffer, long-term recall and summarization.",
                "Keeps context relevant and bounded.",
            ),
            Component(
                "Primary Database",
                "data",
                "Store users, sessions, audit logs and structured app data.",
                "System of record separate from ephemeral agent state.",
            ),
            Component(
                "Validation Layer",
                "reliability",
                "Score outputs for hallucination risk before returning them.",
                "Catches unsupported claims and gates model escalation.",
            ),
        ]
        if needs_rag and vector_store:
            components.append(
                Component(
                    "Vector Store",
                    "retrieval",
                    f"Embed and retrieve from {spec.documents:,} documents.",
                    vector_store,
                )
            )
            components.append(
                Component(
                    "Ingestion Pipeline",
                    "retrieval",
                    "Chunk, embed and index source documents.",
                    "Keeps the knowledge base fresh and de-duplicated.",
                )
            )
        if needs_cache:
            components.append(
                Component(
                    "Redis",
                    "cache",
                    "Response/semantic cache, rate limiting and session store.",
                    "Cuts latency and deflects repeat LLM calls.",
                )
            )
        if needs_queue:
            components.append(
                Component(
                    "Task Queue",
                    "async",
                    "Run ingestion, long agent tasks and webhooks in the background.",
                    "Decouples slow work from the request path.",
                )
            )
        if spec.multi_agent:
            components.append(
                Component(
                    "Orchestrator",
                    "coordination",
                    "Coordinate multiple specialized agents and shared memory.",
                    "Needed once a single agent loop is insufficient.",
                )
            )
        return components

    def _build_patterns(self, spec: ProjectSpec, *, needs_rag: bool) -> list[str]:
        patterns = [
            "Stateless service + managed state",
            "Tiered model routing",
            "Guardrails / output validation",
        ]
        if needs_rag:
            patterns.append("Retrieval-Augmented Generation (RAG)")
            patterns.append("Re-ranking + citation enforcement")
        if spec.multi_agent:
            patterns.append("Orchestrator-worker multi-agent")
            patterns.append("Blackboard shared memory")
        if spec.realtime:
            patterns.append("Streaming responses (SSE/WebSocket)")
        return patterns

    def _build_findings(
        self,
        *,
        rag_reason: str,
        vector_reason: str,
        cache_reason: str,
        queue_reason: str,
        residency: str,
        multi_region: bool,
    ) -> list[Finding]:
        findings = [
            Finding("rag", rag_reason, Severity.INFO),
            Finding("vector_store", vector_reason, Severity.INFO),
            Finding("cache", cache_reason, Severity.INFO),
            Finding("queue", queue_reason, Severity.INFO),
        ]
        if multi_region:
            findings.append(
                Finding("data_residency", residency, Severity.HIGH, {"multi_region": True})
            )
        return findings

    def _build_recommendations(self, spec: ProjectSpec, *, needs_rag: bool) -> list[Recommendation]:
        recs = [
            Recommendation(
                "Start with the smallest model that passes your evals",
                "Route by default to an economy-tier model and escalate only on low confidence.",
                Priority.HIGH,
            ),
            Recommendation(
                "Add output validation before you ship",
                "Wire the Hallucination Detector into the response path and log risk scores.",
                Priority.HIGH,
            ),
        ]
        if needs_rag:
            recs.append(
                Recommendation(
                    "Enforce citations in RAG answers",
                    "Reject or flag answers whose claims are not supported by retrieved sources.",
                    Priority.HIGH,
                )
            )
        if spec.users >= 100_000:
            recs.append(
                Recommendation(
                    "Load-test before launch",
                    "Validate autoscaling and DB connection limits at projected peak traffic.",
                    Priority.MEDIUM,
                )
            )
        return recs

    def _build_diagram(
        self,
        *,
        needs_rag: bool,
        needs_cache: bool,
        needs_queue: bool,
        multi_agent: bool,
    ) -> str:
        lines = [
            "flowchart LR",
            "    U[Users] --> GW[API Gateway]",
            "    GW --> APP[Agent Service]",
            "    APP --> ROUTER[LLM Router]",
            "    ROUTER --> M1[Default model]",
            "    ROUTER --> M2[Escalation model]",
            "    APP --> MEM[Memory Engine]",
            "    APP --> VAL[Validation Layer]",
            "    APP --> DB[(Primary DB)]",
        ]
        if needs_rag:
            lines.append("    APP --> VDB[(Vector Store)]")
            lines.append("    ING[Ingestion Pipeline] --> VDB")
        if needs_cache:
            lines.append("    APP --> CACHE[(Redis)]")
        if needs_queue:
            lines.append("    APP --> Q[[Task Queue]]")
            lines.append("    Q --> WORKER[Background Workers]")
        if multi_agent:
            lines.append("    APP --> ORCH[Orchestrator]")
            lines.append("    ORCH --> AG1[Agent A]")
            lines.append("    ORCH --> AG2[Agent B]")
        return "\n".join(lines)


__all__ = ["ArchitectureGenerator"]
