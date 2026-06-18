"""Architecture Generator: design a stack from a high-level project description."""

from __future__ import annotations

from agent_essentials import ArchitectureGenerator, ProjectSpec


def main() -> None:
    spec = ProjectSpec(
        project_type="customer support",
        users=10_000,
        documents=50_000,
        countries=["US", "MX"],
        budget="balanced",
    )
    rec = ArchitectureGenerator().generate(spec)

    print(rec.summary)
    print("\nDecisions:")
    print(f"  RAG:          {rec.needs_rag}  ({rec.vector_store})")
    print(f"  Cache (Redis):{rec.needs_cache}")
    print(f"  Task queue:   {rec.needs_queue}")
    print(f"  Deployment:   {rec.deployment}")
    print(f"  Multi-region: {rec.multi_region}")
    print(f"  Models:       default={rec.recommended_models['default']}")

    cost = rec.estimated_monthly_cost_usd["total_per_month"]
    print(f"\nEstimated cost/month: ${cost['low']:,.0f} - ${cost['high']:,.0f}")

    print("\nMermaid diagram:\n")
    print(rec.diagram_mermaid)


if __name__ == "__main__":
    main()
