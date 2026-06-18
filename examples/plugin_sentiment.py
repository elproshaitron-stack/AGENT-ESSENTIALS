"""A minimal third-party plugin showing the extension contract.

Run this file directly to register the plugin at runtime and use it. To ship it
as an installable plugin, expose ``plugin`` via an entry point in the
``agent_essentials.plugins`` group (see docs/guides/plugins.md).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar

from agent_essentials import get_registry
from agent_essentials.core import Module, Plugin


class SentimentModule(Module):
    name = "sentiment"
    version = "0.1.0"
    summary = "Toy lexicon sentiment scorer (demonstrates the plugin contract)."

    _POSITIVE: ClassVar[frozenset[str]] = frozenset(
        {"good", "great", "love", "excellent", "happy", "fast"}
    )
    _NEGATIVE: ClassVar[frozenset[str]] = frozenset(
        {"bad", "terrible", "hate", "slow", "broken", "angry"}
    )

    def run(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        words = str(payload.get("text", "")).lower().split()
        score = sum(w in self._POSITIVE for w in words) - sum(w in self._NEGATIVE for w in words)
        label = "positive" if score > 0 else "negative" if score < 0 else "neutral"
        return {"score": score, "label": label}


plugin = Plugin(
    name=SentimentModule.name,
    factory=SentimentModule,
    summary=SentimentModule.summary,
)


if __name__ == "__main__":
    registry = get_registry()
    registry.register(plugin, replace=True)
    text = "the product is great and fast but the UI is broken"
    print(registry.create("sentiment").run({"text": text}))
