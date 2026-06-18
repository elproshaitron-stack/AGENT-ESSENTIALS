"""Common result primitives reused across modules.

These give every module a shared vocabulary for findings, severities and
recommendations so that downstream tooling (dashboards, CI gates, reports)
can treat heterogeneous module output uniformly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .types import Serializable


class Severity(str, Enum):
    """Ordered severity levels. ``str`` mixin keeps JSON output human-readable."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def weight(self) -> int:
        return _SEVERITY_WEIGHTS[self]


_SEVERITY_WEIGHTS: dict[Severity, int] = {
    Severity.INFO: 0,
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}


class Priority(str, Enum):
    """Recommendation priority."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(slots=True)
class Finding(Serializable):
    """A single observation produced by an analyzer."""

    code: str
    message: str
    severity: Severity = Severity.INFO
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Recommendation(Serializable):
    """An actionable suggestion produced by a module."""

    title: str
    detail: str = ""
    priority: Priority = Priority.MEDIUM


__all__ = ["Finding", "Priority", "Recommendation", "Severity"]
