"""Tests for the Task Planner."""

from __future__ import annotations

import pytest

from agent_essentials.core.exceptions import ValidationError
from agent_essentials.planning import Task, TaskPlanner, templates


def test_detect_domain_and_features():
    assert templates.detect_domain("Build a SaaS platform") == "saas"
    assert templates.detect_domain("Train an ML recommendation model") == "ml_ai"
    assert templates.detect_domain("write a poem") == "general"
    feats = templates.detect_features("a platform with user login and payments")
    assert "auth" in feats and "payments" in feats


def test_plan_empty_goal_raises():
    with pytest.raises(ValidationError):
        TaskPlanner().plan("   ")


def test_plan_structure_and_topological_validity():
    plan = TaskPlanner().plan("Build a sports league SaaS with payments and live scores")
    ids = [t.id for t in plan.tasks]
    assert len(ids) == len(set(ids))  # unique
    # every milestone task id exists
    milestone_ids = {tid for m in plan.milestones for tid in m.task_ids}
    assert milestone_ids == set(ids)
    # execution order is a valid topological order
    position = {tid: i for i, tid in enumerate(plan.execution_order)}
    {t.id: t for t in plan.tasks}
    for task in plan.tasks:
        for dep in task.depends_on:
            assert position[dep] < position[task.id]
    # parallel groups partition all tasks
    grouped = [tid for group in plan.parallel_groups for tid in group]
    assert sorted(grouped) == sorted(ids)
    assert "payments" in plan.detected_features


def test_cycle_detection():
    tasks = [
        Task(id="t1", title="a", depends_on=["t2"]),
        Task(id="t2", title="b", depends_on=["t1"]),
    ]
    with pytest.raises(ValidationError):
        TaskPlanner._topological_order(tasks)


def test_unknown_dependency_raises():
    tasks = [Task(id="t1", title="a", depends_on=["tX"])]
    with pytest.raises(ValidationError):
        TaskPlanner._topological_order(tasks)


def test_risks_include_baseline_and_feature():
    plan = TaskPlanner().plan("Build a SaaS with payments")
    titles = {r.title for r in plan.risks}
    assert "Scope creep" in titles
    assert any("Payment" in t for t in titles)


def test_run_requires_goal():
    with pytest.raises(ValidationError):
        TaskPlanner().run({"not_goal": 1})
    out = TaskPlanner().run({"goal": "build an api service"})
    assert out["domain"] == "api"


def test_detects_spanish_goals():
    """Spanish goals must detect the same features as their English equivalents."""
    es = set(templates.detect_features("plataforma SaaS de ligas deportivas con pagos y usuarios"))
    assert {"auth", "payments", "scheduling", "multitenant"} <= es
    assert templates.detect_domain("plataforma de análisis de datos") in {"saas", "data"}
