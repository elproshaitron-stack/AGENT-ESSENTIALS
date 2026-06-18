"""Typed input/output models for the Architecture Generator."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ..core.exceptions import ValidationError
from ..core.result import Finding, Recommendation
from ..core.types import Serializable
from .knowledge import VALID_BUDGETS


@dataclass(slots=True)
class ProjectSpec(Serializable):
    """Description of the agent system to be designed."""

    project_type: str = "general"
    users: int = 0
    documents: int = 0
    countries: list[str] = field(default_factory=list)
    requests_per_day: int | None = None
    languages: list[str] = field(default_factory=list)
    compliance: list[str] = field(default_factory=list)
    latency_sensitive: bool = False
    realtime: bool = False
    multi_agent: bool = False
    budget: str = "balanced"

    def __post_init__(self) -> None:
        if self.users < 0:
            raise ValidationError("users must be >= 0")
        if self.documents < 0:
            raise ValidationError("documents must be >= 0")
        if self.requests_per_day is not None and self.requests_per_day < 0:
            raise ValidationError("requests_per_day must be >= 0")
        if self.budget not in VALID_BUDGETS:
            raise ValidationError(
                f"budget must be one of {sorted(VALID_BUDGETS)}, got {self.budget!r}"
            )
        self.project_type = self.project_type.strip().lower()
        self.countries = [c.strip().upper() for c in self.countries]
        self.compliance = [c.strip().lower() for c in self.compliance]

    @property
    def effective_requests_per_day(self) -> int:
        """Use the explicit value, else assume ~10 requests/user/day."""
        if self.requests_per_day is not None:
            return self.requests_per_day
        return self.users * 10

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ProjectSpec:
        allowed = set(cls.__dataclass_fields__)
        unknown = set(data) - allowed
        if unknown:
            raise ValidationError(f"Unknown ProjectSpec fields: {sorted(unknown)}")
        return cls(**dict(data))


@dataclass(slots=True)
class Component(Serializable):
    """One building block of the recommended architecture."""

    name: str
    category: str
    purpose: str
    rationale: str = ""


@dataclass(slots=True)
class ArchitectureRecommendation(Serializable):
    """Full recommended architecture for a :class:`ProjectSpec`."""

    summary: str
    needs_rag: bool
    vector_store: str | None
    needs_cache: bool
    needs_queue: bool
    memory_strategy: str
    model_strategy: str
    recommended_models: dict[str, list[str]]
    deployment: str
    scaling_strategy: str
    multi_region: bool
    data_residency_notes: str
    estimated_monthly_cost_usd: dict[str, Any]
    components: list[Component]
    patterns: list[str]
    findings: list[Finding]
    recommendations: list[Recommendation]
    diagram_mermaid: str
    spec: ProjectSpec


__all__ = ["ArchitectureRecommendation", "Component", "ProjectSpec"]
