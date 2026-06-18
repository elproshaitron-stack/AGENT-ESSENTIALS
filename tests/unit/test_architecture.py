"""Tests for the Architecture Generator."""

from __future__ import annotations

import pytest

from agent_essentials.architecture import ArchitectureGenerator, ProjectSpec, rules
from agent_essentials.core.exceptions import ValidationError


def test_projectspec_validation_and_normalization():
    spec = ProjectSpec(project_type="Customer Support", users=10, countries=["us", "mx"])
    assert spec.project_type == "customer support"
    assert spec.countries == ["US", "MX"]
    with pytest.raises(ValidationError):
        ProjectSpec(users=-1)
    with pytest.raises(ValidationError):
        ProjectSpec(budget="lavish")


def test_projectspec_from_dict_rejects_unknown():
    with pytest.raises(ValidationError):
        ProjectSpec.from_dict({"users": 1, "bogus": True})


def test_effective_requests_per_day():
    assert ProjectSpec(users=100).effective_requests_per_day == 1000
    assert ProjectSpec(users=100, requests_per_day=5).effective_requests_per_day == 5


def test_decide_rag():
    assert rules.decide_rag(ProjectSpec(documents=100))[0] is True
    assert rules.decide_rag(ProjectSpec(project_type="customer support"))[0] is True
    assert rules.decide_rag(ProjectSpec(documents=0))[0] is False
    assert rules.decide_rag(ProjectSpec(documents=5, project_type="game"))[0] is False


def test_decide_vector_store_tiers():
    assert rules.decide_vector_store(ProjectSpec(), False)[0] is None
    assert "pgvector" in rules.decide_vector_store(ProjectSpec(documents=500), True)[0]
    assert "Managed" in rules.decide_vector_store(ProjectSpec(documents=50_000), True)[0]
    assert "Distributed" in rules.decide_vector_store(ProjectSpec(documents=5_000_000), True)[0]


def test_decide_cache_and_queue():
    assert rules.decide_cache(ProjectSpec(latency_sensitive=True))[0] is True
    assert rules.decide_cache(ProjectSpec(users=5000))[0] is True
    assert rules.decide_cache(ProjectSpec(users=10))[0] is False
    assert rules.decide_queue(ProjectSpec(documents=20_000))[0] is True
    assert rules.decide_queue(ProjectSpec(multi_agent=True))[0] is True
    assert rules.decide_queue(ProjectSpec(users=10))[0] is False


def test_decide_regions():
    assert rules.decide_regions(ProjectSpec(countries=["DE"]))[0] is True
    assert rules.decide_regions(ProjectSpec(countries=["US", "MX"]))[0] is True
    assert rules.decide_regions(ProjectSpec(compliance=["gdpr"]))[0] is True
    assert rules.decide_regions(ProjectSpec(countries=["US"]))[0] is False


def test_estimate_cost_scales_with_requests():
    low = rules.estimate_cost(
        ProjectSpec(users=100), needs_cache=False, needs_queue=False, vector_store=None
    )
    high = rules.estimate_cost(
        ProjectSpec(users=10000),
        needs_cache=True,
        needs_queue=True,
        vector_store="Managed vector DB",
    )
    assert high["total_per_month"]["low"] > low["total_per_month"]["low"]
    assert low["currency"] == "USD"


def test_generate_full_recommendation():
    gen = ArchitectureGenerator()
    rec = gen.generate(
        ProjectSpec(
            project_type="customer support", users=10_000, documents=50_000, countries=["US", "MX"]
        )
    )
    assert rec.needs_rag is True
    assert rec.needs_cache is True
    assert rec.vector_store is not None
    assert "flowchart" in rec.diagram_mermaid
    assert "VDB" in rec.diagram_mermaid  # RAG node present
    assert rec.recommended_models["default"]
    assert any(c.category == "retrieval" for c in rec.components)
    assert rec.summary


def test_run_returns_serializable_dict():
    out = ArchitectureGenerator().run({"project_type": "rag", "users": 500, "documents": 200})
    assert {"summary", "needs_rag", "diagram_mermaid"}.issubset(out)
    assert isinstance(out["components"], list)


def test_cost_bands_reflect_budget_tier():
    """Cost must change with budget: premium routes to pricier tiers than economy."""
    gen = ArchitectureGenerator()
    spec_kwargs = {"project_type": "chat", "users": 10_000}
    eco = gen.generate(ProjectSpec(budget="economy", **spec_kwargs)).estimated_monthly_cost_usd
    prem = gen.generate(ProjectSpec(budget="premium", **spec_kwargs)).estimated_monthly_cost_usd
    assert prem["total_per_month"]["low"] > eco["total_per_month"]["low"]
    assert eco["assumptions"]["default_tier"] == "economy"
    assert prem["assumptions"]["default_tier"] == "balanced"


def test_hyperscale_caps_replicas_and_flags():
    from agent_essentials.architecture import rules

    spec = ProjectSpec(project_type="chat", users=200_000_000)
    assert rules.is_hyperscale(spec) is True
    assert rules.estimate_replicas(spec) == 500  # capped
    rec = ArchitectureGenerator().generate(spec)
    assert any(f.code == "hyperscale" for f in rec.findings)
    assert any("cell" in p.lower() for p in rec.patterns)


def test_small_scale_is_not_hyperscale():
    from agent_essentials.architecture import rules

    assert rules.is_hyperscale(ProjectSpec(users=10_000)) is False
    assert rules.estimate_replicas(ProjectSpec(users=10_000)) < 500
