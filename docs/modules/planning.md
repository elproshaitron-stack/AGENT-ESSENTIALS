# Task Planner

Turn a goal into milestones, tasks, dependencies, risks and an execution order.

## API

```python
from agent_essentials import TaskPlanner

plan = TaskPlanner().plan("Build a sports league SaaS platform with payments")
plan.milestones        # phases (Discovery → … → Launch)
plan.tasks             # Task(id, title, milestone, depends_on, effort, category)
plan.execution_order   # topologically sorted task ids
plan.parallel_groups   # tasks grouped by dependency level (what can run together)
plan.risks             # Risk(title, severity, likelihood, mitigation)
plan.detected_features # e.g. ["auth", "payments", "scheduling"]
```

## How it works

- **Domain & features** are detected from goal keywords (`templates.py`).
- A stable **SDLC skeleton** (6 milestones) expands with **feature-gated tasks**
  (auth, payments, realtime, AI, mobile, analytics, scheduling, multitenancy).
- Dependencies form a DAG; `execution_order` is a deterministic topological sort
  and `parallel_groups` layers tasks that can run concurrently.
- **Risks** combine always-on risks (scope creep, testing) with feature risks
  (payments/PCI, AI reliability, tenant isolation, scheduling complexity).

## CLI

```bash
agent-essentials plan "Build a sports league SaaS platform"
```
