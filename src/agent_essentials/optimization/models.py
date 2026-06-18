"""Typed models for the Optimization suite."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..core.result import Recommendation
from ..core.types import Serializable


@dataclass(slots=True)
class CostEstimate(Serializable):
    """Token usage and projected cost for a call (optionally x N requests)."""

    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    requests: int = 1
    currency: str = "USD"
    cached: bool = False
    pricing_as_of: str = ""
    suggestions: list[Recommendation] = field(default_factory=list)


@dataclass(slots=True)
class ModelComparison(Serializable):
    """Cost of the same workload across all known models, cheapest first."""

    input_tokens: int
    output_tokens: int
    requests: int
    ranked: list[dict[str, object]]


__all__ = ["CostEstimate", "ModelComparison"]
