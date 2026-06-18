"""Serialization helpers shared by every result model.

The toolkit returns rich, typed dataclasses but every result is trivially
convertible to plain ``dict``/JSON so it can cross process or network
boundaries (CLI, HTTP, message queues) without coupling callers to our types.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any


def to_serializable(obj: Any) -> Any:
    """Recursively convert dataclasses, enums and containers to JSON-safe types."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: to_serializable(getattr(obj, f.name)) for f in fields(obj)}
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, Mapping):
        return {str(k): to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set, frozenset)):
        return [to_serializable(v) for v in obj]
    return obj


class Serializable:
    """Mixin that gives dataclass result models ``to_dict`` / ``to_json``."""

    def to_dict(self) -> dict[str, Any]:
        result = to_serializable(self)
        if not isinstance(result, dict):  # pragma: no cover - defensive
            raise TypeError("Serializable must be mixed into a dataclass")
        return result

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


__all__ = ["Serializable", "to_serializable"]
