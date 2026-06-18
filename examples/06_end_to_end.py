"""End-to-end: design -> price -> plan -> validate, then drive via the registry."""

from __future__ import annotations

from agent_essentials import (
    ArchitectureGenerator,
    HallucinationDetector,
    ProjectSpec,
    TaskPlanner,
    TokenCounter,
    get_registry,
)


def main() -> None:
    # 1. Design
    rec = ArchitectureGenerator().generate(
        ProjectSpec(project_type="customer support", users=10_000, documents=50_000)
    )
    print("1. Architecture:", rec.summary)

    # 2. Price the assumed traffic
    requests = rec.estimated_monthly_cost_usd["assumptions"]["requests_per_month"]
    est = TokenCounter().estimate_cost(
        model="claude-haiku-4-5", input_tokens=1500, output_tokens=500, requests=requests
    )
    print(f"2. Cost: ${est.total_cost:,.0f}/month on {est.model} for {requests:,} requests")

    # 3. Plan the build
    plan = TaskPlanner().plan("Build a customer support agent with RAG and analytics")
    print(f"3. Plan: {len(plan.tasks)} tasks across {len(plan.milestones)} milestones")

    # 4. Validate a generated answer
    report = HallucinationDetector().analyze(
        "We store embeddings in a managed vector database.",
        sources=["The system uses a managed vector database for retrieval."],
    )
    print(f"4. Validation: risk={report.risk_score} ({report.risk_level})")

    # Everything is also reachable generically through the plugin registry:
    print("\nRegistered modules:", get_registry().names())


if __name__ == "__main__":
    main()
