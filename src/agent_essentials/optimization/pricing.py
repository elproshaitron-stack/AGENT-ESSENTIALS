"""Model pricing catalog.

Prices are USD per 1,000,000 tokens and reflect public list prices as of
2026-06. They are intentionally in one editable place so updating them (or
overriding via a plugin) is a one-line change. Verify against the provider's
pricing page before relying on these for billing.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..core.exceptions import ValidationError
from ..core.types import Serializable

PRICING_AS_OF = "2026-06"


@dataclass(frozen=True, slots=True)
class ModelPrice(Serializable):
    provider: str
    model: str
    input_per_1m: float
    output_per_1m: float
    cached_input_per_1m: float | None = None
    context_window: int | None = None


PRICING: dict[str, ModelPrice] = {
    # OpenAI -----------------------------------------------------------------
    "gpt-5": ModelPrice("openai", "gpt-5", 1.25, 10.00, 0.125, 400_000),
    "gpt-4.1": ModelPrice("openai", "gpt-4.1", 2.00, 8.00, 0.50, 1_000_000),
    "gpt-4.1-mini": ModelPrice("openai", "gpt-4.1-mini", 0.40, 1.60, 0.10, 1_000_000),
    "gpt-4.1-nano": ModelPrice("openai", "gpt-4.1-nano", 0.10, 0.40, 0.025, 1_000_000),
    "gpt-4o": ModelPrice("openai", "gpt-4o", 2.50, 10.00, 1.25, 128_000),
    # Anthropic --------------------------------------------------------------
    "claude-opus-4-8": ModelPrice("anthropic", "claude-opus-4-8", 5.00, 25.00, 0.50, 200_000),
    "claude-sonnet-4-6": ModelPrice("anthropic", "claude-sonnet-4-6", 3.00, 15.00, 0.30, 1_000_000),
    "claude-haiku-4-5": ModelPrice("anthropic", "claude-haiku-4-5", 1.00, 5.00, 0.10, 200_000),
    # Google Gemini ----------------------------------------------------------
    "gemini-2.5-pro": ModelPrice("google", "gemini-2.5-pro", 1.25, 10.00, 0.31, 1_000_000),
    "gemini-2.5-flash": ModelPrice("google", "gemini-2.5-flash", 0.30, 2.50, 0.075, 1_000_000),
    # Local / self-hosted ----------------------------------------------------
    "local": ModelPrice("local", "local", 0.00, 0.00, 0.00, None),
}

# Friendly aliases -> canonical key.
ALIASES: dict[str, str] = {
    "gpt5": "gpt-5",
    "gpt-4.1-turbo": "gpt-4.1",
    "gpt41": "gpt-4.1",
    "gpt4o": "gpt-4o",
    "opus": "claude-opus-4-8",
    "claude-opus": "claude-opus-4-8",
    "sonnet": "claude-sonnet-4-6",
    "claude-sonnet": "claude-sonnet-4-6",
    "haiku": "claude-haiku-4-5",
    "claude-haiku": "claude-haiku-4-5",
    "gemini-pro": "gemini-2.5-pro",
    "gemini-flash": "gemini-2.5-flash",
    "self-hosted": "local",
    "ollama": "local",
}

DEFAULT_MODEL = "gpt-4.1-mini"


def resolve_price(model: str) -> ModelPrice:
    key = model.strip().lower()
    if key in PRICING:
        return PRICING[key]
    if key in ALIASES:
        return PRICING[ALIASES[key]]
    raise ValidationError(
        f"Unknown model {model!r}. Known models: {sorted(PRICING)} (aliases: {sorted(ALIASES)})"
    )


def list_models() -> list[str]:
    return sorted(PRICING)


__all__ = [
    "ALIASES",
    "DEFAULT_MODEL",
    "PRICING",
    "PRICING_AS_OF",
    "ModelPrice",
    "list_models",
    "resolve_price",
]
