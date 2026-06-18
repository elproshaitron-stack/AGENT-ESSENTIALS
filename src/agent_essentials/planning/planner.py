"""The Task Planner module."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from typing import Any

from ..core.base import Module
from ..core.exceptions import ValidationError
from . import templates
from .models import Milestone, Plan, Risk, Task

_CATEGORY_BY_PHASE = {
    "m1": "discovery",
    "m2": "design",
    "m3": "build",
    "m4": "integration",
    "m5": "test",
    "m6": "launch",
}


def _task_key(task_id: str) -> int:
    return int(task_id[1:])


class TaskPlanner(Module):
    """Decompose a goal into a hierarchical, dependency-aware execution plan."""

    name = "planning"
    version = "0.1.0"
    summary = "Turn a goal into milestones, tasks, dependencies, risks and an order."

    def plan(self, goal: str) -> Plan:
        goal = goal.strip()
        if not goal:
            raise ValidationError("goal must be a non-empty string")

        domain = templates.detect_domain(goal)
        features = templates.detect_features(goal)

        tasks: list[Task] = []
        milestones: list[Milestone] = []
        counter = 0
        previous_phase_lead: str | None = None

        for phase_id, phase_name, objective, specs in templates.PHASES:
            selected = [s for s in specs if s[3] is None or s[3] in features]
            phase_task_ids: list[str] = []
            phase_lead: str | None = None

            for title, description, effort, _gate in selected:
                counter += 1
                task_id = f"t{counter}"
                if phase_lead is None:
                    depends_on = [previous_phase_lead] if previous_phase_lead else []
                    phase_lead = task_id
                else:
                    depends_on = [phase_lead]
                tasks.append(
                    Task(
                        id=task_id,
                        title=title,
                        description=description,
                        milestone=phase_name,
                        depends_on=depends_on,
                        effort=effort,
                        category=_CATEGORY_BY_PHASE[phase_id],
                    )
                )
                phase_task_ids.append(task_id)

            milestones.append(
                Milestone(
                    id=phase_id, name=phase_name, objective=objective, task_ids=phase_task_ids
                )
            )
            if phase_lead is not None:
                previous_phase_lead = phase_lead

        order = self._topological_order(tasks)
        groups = self._parallel_groups(tasks, order)
        risks = self._build_risks(features)
        summary = (
            f"{domain} project decomposed into {len(tasks)} tasks across "
            f"{len(milestones)} milestones; {len(groups)} dependency levels, "
            f"{len(risks)} tracked risks. Detected features: "
            f"{', '.join(features) if features else 'none'}."
        )
        return Plan(
            goal=goal,
            domain=domain,
            summary=summary,
            tasks=tasks,
            milestones=milestones,
            risks=risks,
            execution_order=order,
            parallel_groups=groups,
            detected_features=features,
        )

    # -- graph helpers ------------------------------------------------------
    @staticmethod
    def _topological_order(tasks: list[Task]) -> list[str]:
        by_id = {t.id: t for t in tasks}
        indegree = {t.id: 0 for t in tasks}
        adjacency: dict[str, list[str]] = defaultdict(list)
        for task in tasks:
            for dependency in task.depends_on:
                if dependency not in by_id:
                    raise ValidationError(f"Task {task.id} depends on unknown task {dependency!r}")
                adjacency[dependency].append(task.id)
                indegree[task.id] += 1

        ready = sorted([tid for tid, deg in indegree.items() if deg == 0], key=_task_key)
        order: list[str] = []
        while ready:
            node = ready.pop(0)
            order.append(node)
            for nxt in adjacency[node]:
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    ready.append(nxt)
            ready.sort(key=_task_key)

        if len(order) != len(tasks):
            raise ValidationError("Cycle detected in task dependencies")
        return order

    @staticmethod
    def _parallel_groups(tasks: list[Task], order: list[str]) -> list[list[str]]:
        by_id = {t.id: t for t in tasks}
        level: dict[str, int] = {}
        for task_id in order:
            deps = by_id[task_id].depends_on
            level[task_id] = 0 if not deps else 1 + max(level[d] for d in deps)
        grouped: dict[int, list[str]] = defaultdict(list)
        for task_id, lvl in level.items():
            grouped[lvl].append(task_id)
        return [sorted(grouped[lvl], key=_task_key) for lvl in sorted(grouped)]

    @staticmethod
    def _build_risks(features: list[str]) -> list[Risk]:
        risks = [
            Risk(title=t[0], description=t[1], severity=t[2], likelihood=t[3], mitigation=t[4])
            for t in templates.BASELINE_RISKS
        ]
        for feature in features:
            template = templates.RISK_TEMPLATES.get(feature)
            if template:
                risks.append(
                    Risk(
                        title=template[0],
                        description=template[1],
                        severity=template[2],
                        likelihood=template[3],
                        mitigation=template[4],
                    )
                )
        return risks

    # -- Module API ---------------------------------------------------------
    def run(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        goal = payload.get("goal")
        if not isinstance(goal, str):
            raise ValidationError("payload must include a string 'goal'")
        return self.plan(goal).to_dict()


__all__ = ["TaskPlanner"]
