"""A tiny, dependency-free service container.

Just enough dependency injection to wire stores, embedders and summarizers into
modules without a heavyweight framework. Factories receive the container so they
can resolve their own dependencies.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from .exceptions import ConfigurationError

T = TypeVar("T")

Factory = Callable[["Container"], Any]


class Container:
    """Resolve named services lazily, with optional singleton caching."""

    def __init__(self) -> None:
        self._factories: dict[str, tuple[Factory, bool]] = {}
        self._singletons: dict[str, Any] = {}

    def register(self, key: str, factory: Factory, *, singleton: bool = True) -> None:
        """Register a factory callable for ``key``."""
        self._factories[key] = (factory, singleton)
        self._singletons.pop(key, None)

    def register_instance(self, key: str, instance: Any) -> None:
        """Register an already-built instance as a singleton."""
        self._factories[key] = ((lambda _c: instance), True)
        self._singletons[key] = instance

    def has(self, key: str) -> bool:
        return key in self._factories

    def resolve(self, key: str) -> Any:
        if key in self._singletons:
            return self._singletons[key]
        if key not in self._factories:
            raise ConfigurationError(
                f"No service registered for {key!r}. Known: {sorted(self._factories)}"
            )
        factory, singleton = self._factories[key]
        instance = factory(self)
        if singleton:
            self._singletons[key] = instance
        return instance

    def override(self, key: str, instance: Any) -> None:
        """Force a value for ``key`` (handy in tests)."""
        self.register_instance(key, instance)


__all__ = ["Container", "Factory"]
