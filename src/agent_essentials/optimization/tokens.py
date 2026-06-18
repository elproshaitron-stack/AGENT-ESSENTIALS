"""The Token Counter module."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..core.base import Module
from ..core.exceptions import ValidationError
from ..core.result import Priority, Recommendation
from .models import CostEstimate, ModelComparison
from .pricing import DEFAULT_MODEL, PRICING, PRICING_AS_OF, ModelPrice, resolve_price
from .tokenizers import count_tokens


class TokenCounter(Module):
    """Estimate token usage and cost, and suggest ways to spend less."""

    name = "optimization"
    version = "0.1.0"
    summary = "Count tokens and estimate cost across OpenAI/Anthropic/Gemini/local models."

    def count(self, text: str, model: str = DEFAULT_MODEL) -> int:
        return count_tokens(text, model)

    def estimate_cost(
        self,
        *,
        model: str = DEFAULT_MODEL,
        input_text: str | None = None,
        output_text: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        requests: int = 1,
        cached: bool = False,
    ) -> CostEstimate:
        if requests < 1:
            raise ValidationError("requests must be >= 1")
        price = resolve_price(model)

        in_tokens = (
            input_tokens
            if input_tokens is not None
            else (self.count(input_text, model) if input_text else 0)
        )
        out_tokens = (
            output_tokens
            if output_tokens is not None
            else (self.count(output_text, model) if output_text else 0)
        )
        if in_tokens < 0 or out_tokens < 0:
            raise ValidationError("token counts must be >= 0")

        input_rate = (
            price.cached_input_per_1m
            if cached and price.cached_input_per_1m is not None
            else price.input_per_1m
        )
        input_cost = in_tokens / 1e6 * input_rate * requests
        output_cost = out_tokens / 1e6 * price.output_per_1m * requests
        total_cost = input_cost + output_cost

        return CostEstimate(
            provider=price.provider,
            model=price.model,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            total_tokens=in_tokens + out_tokens,
            input_cost=round(input_cost, 6),
            output_cost=round(output_cost, 6),
            total_cost=round(total_cost, 6),
            requests=requests,
            cached=cached,
            pricing_as_of=PRICING_AS_OF,
            suggestions=self._suggest(price, in_tokens, out_tokens, requests),
        )

    def compare(
        self, *, input_tokens: int, output_tokens: int, requests: int = 1
    ) -> ModelComparison:
        """Cost of the same workload across every priced model, cheapest first."""
        if input_tokens < 0 or output_tokens < 0:
            raise ValidationError("token counts must be >= 0")
        if requests < 1:
            raise ValidationError("requests must be >= 1")
        ranked: list[dict[str, object]] = []
        for key, price in PRICING.items():
            cost = (
                input_tokens / 1e6 * price.input_per_1m + output_tokens / 1e6 * price.output_per_1m
            ) * requests
            ranked.append({"model": key, "provider": price.provider, "total_cost": round(cost, 6)})
        ranked.sort(key=lambda row: (row["total_cost"], row["model"]))
        return ModelComparison(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            requests=requests,
            ranked=ranked,
        )

    @staticmethod
    def _suggest(
        price: ModelPrice, in_tokens: int, out_tokens: int, requests: int
    ) -> list[Recommendation]:
        suggestions: list[Recommendation] = []
        if price.input_per_1m >= 5.0:
            suggestions.append(
                Recommendation(
                    "Default to a cheaper tier",
                    f"{price.model} is a premium model; route easy queries to a mini/flash "
                    "model and escalate only when needed.",
                    Priority.HIGH,
                )
            )
        if in_tokens >= 4_000:
            suggestions.append(
                Recommendation(
                    "Compress the prompt / context",
                    "Use the Memory Engine's optimize_context to keep only relevant context; "
                    "long prompts dominate input cost.",
                    Priority.MEDIUM,
                )
            )
        if requests > 1 and price.cached_input_per_1m is not None and in_tokens >= 1_000:
            saving = (price.input_per_1m - price.cached_input_per_1m) / price.input_per_1m
            suggestions.append(
                Recommendation(
                    "Enable prompt caching",
                    f"A stable prefix can use cached input pricing (~{saving:.0%} cheaper) "
                    "across repeated requests.",
                    Priority.MEDIUM,
                )
            )
        if requests >= 1_000:
            suggestions.append(
                Recommendation(
                    "Use the Batch API",
                    "Non-interactive workloads are typically ~50% cheaper when batched.",
                    Priority.MEDIUM,
                )
            )
        if out_tokens >= 1_500:
            suggestions.append(
                Recommendation(
                    "Cap output length",
                    "Output tokens cost 4-5x input; set max_tokens and request concise answers.",
                    Priority.LOW,
                )
            )
        if not suggestions:
            suggestions.append(
                Recommendation(
                    "Spend looks efficient",
                    "Small payload on an economical model; revisit if volume grows.",
                    Priority.LOW,
                )
            )
        return suggestions

    # -- Module API ---------------------------------------------------------
    def run(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        op = payload.get("op", "estimate")
        model = payload.get("model", DEFAULT_MODEL)
        if op == "count":
            text = payload.get("text", "")
            if not isinstance(text, str):
                raise ValidationError("payload 'text' must be a string")
            return {"model": model, "tokens": self.count(text, model)}
        if op == "compare":
            comparison = self.compare(
                input_tokens=int(payload.get("input_tokens", 0)),
                output_tokens=int(payload.get("output_tokens", 0)),
                requests=int(payload.get("requests", 1)),
            )
            return comparison.to_dict()
        if op == "estimate":
            return self.estimate_cost(
                model=model,
                input_text=payload.get("input_text"),
                output_text=payload.get("output_text"),
                input_tokens=payload.get("input_tokens"),
                output_tokens=payload.get("output_tokens"),
                requests=int(payload.get("requests", 1)),
                cached=bool(payload.get("cached", False)),
            ).to_dict()
        raise ValidationError(f"Unknown optimization op {op!r}; expected count|estimate|compare")


__all__ = ["TokenCounter"]
