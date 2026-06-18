"""Task Planner module."""

from __future__ import annotations

from ..core.plugin import Plugin
from .models import Milestone, Plan, Risk, Task
from .planner import TaskPlanner

plugin = Plugin(
    name=TaskPlanner.name,
    factory=TaskPlanner,
    summary=TaskPlanner.summary,
    version=TaskPlanner.version,
)

__all__ = ["Milestone", "Plan", "Risk", "Task", "TaskPlanner", "plugin"]
