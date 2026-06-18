"""Integration tests: registry discovery and cross-module JSON contracts."""

from __future__ import annotations

import json

from agent_essentials import (
    ArchitectureGenerator,
    HallucinationDetector,
    MemoryEngine,
    ProjectSpec,
    TaskPlanner,
    TokenCounter,
    get_registry,
)
from agent_essentials.core.plugin import PluginRegistry


def test_registry_discovers_all_modules():
    names = set(get_registry().names())
    assert {"architecture", "memory", "planning", "validation", "optimization"} <= names


def test_register_builtins_is_idempotent():
    from agent_essentials import _register_builtins

    reg = PluginRegistry()
    _register_builtins(reg)
    _register_builtins(reg)  # must not raise on second call
    assert len(reg) == 6


def test_every_module_run_output_is_json_serializable():
    payloads = {
        "architecture": {"project_type": "customer support", "users": 1000, "documents": 100},
        "memory": {"op": "summarize", "memories": ["a b c. d e f. g h i. j k l."]},
        "planning": {"goal": "Build a SaaS with payments and analytics"},
        "validation": {"output": "X is true.", "sources": ["X is true."]},
        "optimization": {
            "op": "estimate",
            "model": "gpt-4.1",
            "input_tokens": 100,
            "output_tokens": 50,
        },
    }
    reg = get_registry()
    for name, payload in payloads.items():
        result = reg.create(name).run(payload)
        # round-trips through JSON without error
        json.dumps(result)


def test_design_to_cost_workflow():
    """A realistic flow: design an architecture, then price its assumed traffic."""
    spec = ProjectSpec(project_type="customer support", users=10_000, documents=50_000)
    rec = ArchitectureGenerator().generate(spec)
    assert rec.needs_rag

    # Use the architecture's traffic assumption to estimate monthly LLM cost.
    requests = rec.estimated_monthly_cost_usd["assumptions"]["requests_per_month"]
    est = TokenCounter().estimate_cost(
        model="claude-haiku-4-5", input_tokens=1500, output_tokens=500, requests=requests
    )
    assert est.total_cost > 0

    # Plan the build, remember a decision, and validate a generated answer.
    plan = TaskPlanner().plan("Build a customer support agent with RAG")
    assert plan.tasks
    mem = MemoryEngine()
    mem.save_memory("Chose managed vector DB for 50k docs.", importance=0.9)
    assert mem.retrieve_memory("vector database choice", k=1)[0].score is not None
    report = HallucinationDetector().analyze(
        "We use a vector DB.", sources=["We use a managed vector DB."]
    )
    assert report.risk_level in {"low", "moderate", "high", "critical"}
