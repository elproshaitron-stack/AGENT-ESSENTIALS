"""Optimization suite: Token Counter and pricing."""

from __future__ import annotations

from ..core.plugin import Plugin
from .models import CostEstimate, ModelComparison
from .pricing import DEFAULT_MODEL, PRICING, ModelPrice, list_models, resolve_price
from .tokenizers import count_tokens, tiktoken_available
from .tokens import TokenCounter

plugin = Plugin(
    name=TokenCounter.name,
    factory=TokenCounter,
    summary=TokenCounter.summary,
    version=TokenCounter.version,
)

__all__ = [
    "DEFAULT_MODEL",
    "PRICING",
    "CostEstimate",
    "ModelComparison",
    "ModelPrice",
    "TokenCounter",
    "count_tokens",
    "list_models",
    "plugin",
    "resolve_price",
    "tiktoken_available",
]
