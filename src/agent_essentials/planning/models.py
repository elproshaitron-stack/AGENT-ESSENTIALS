"""Typed models for the Task Planner."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..core.result import Severity
from ..core.types import Serializable


@dataclass(slots=True)
class Task(Serializable):
    """A single unit of work in a plan."""

    id: str
    title: str
    description: str = ""
    milestone: str = ""
    depends_on: list[str] = field(default_factory=list)
    effort: str = "medium"  # small | medium | large
    category: str = "build"


@dataclass(slots=True)
class Milestone(Serializable):
    """A phase grouping related tasks toward an objective."""

    id: str
    name: str
    objective: str
    task_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Risk(Serializable):
    """An identified delivery risk and how to mitigate it."""

    title: str
    description: str
    severity: Severity
    likelihood: str  # low | medium | high
    mitigation: str


@dataclass(slots=True)
class Plan(Serializable):
    """A full executable plan derived from a goal."""

    goal: str
    domain: str
    summary: str
    tasks: list[Task]
    milestones: list[Milestone]
    risks: list[Risk]
    execution_order: list[str]
    parallel_groups: list[list[str]]
    detected_features: list[str]


__all__ = ["Milestone", "Plan", "Risk", "Task"]
