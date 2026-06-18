"""Task Planner: decompose a goal into milestones, tasks, deps and risks."""

from __future__ import annotations

from agent_essentials import TaskPlanner


def main() -> None:
    plan = TaskPlanner().plan("Build a sports league SaaS platform with payments and live scores")

    print(plan.summary)
    print(f"\nDomain: {plan.domain}  |  Features: {', '.join(plan.detected_features)}")

    print("\nMilestones & tasks:")
    by_id = {t.id: t for t in plan.tasks}
    for milestone in plan.milestones:
        print(f"\n  {milestone.name} — {milestone.objective}")
        for task_id in milestone.task_ids:
            task = by_id[task_id]
            deps = f" (after {', '.join(task.depends_on)})" if task.depends_on else ""
            print(f"    - [{task.id}] {task.title} [{task.effort}]{deps}")

    print("\nExecution order:", " -> ".join(plan.execution_order))
    print("\nParallelizable groups:")
    for i, group in enumerate(plan.parallel_groups):
        print(f"  level {i}: {', '.join(group)}")

    print("\nTop risks:")
    for risk in plan.risks:
        print(f"  - [{risk.severity.value}/{risk.likelihood}] {risk.title}: {risk.mitigation}")


if __name__ == "__main__":
    main()
