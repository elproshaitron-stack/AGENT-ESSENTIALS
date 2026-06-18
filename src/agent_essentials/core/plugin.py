"""Plugin system.

Built-in modules and third-party extensions register through the same
mechanism: a :class:`Plugin` descriptor placed behind the
``agent_essentials.plugins`` entry-point group, or registered imperatively on a
:class:`PluginRegistry`.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from importlib import metadata

from .base import Module
from .exceptions import PluginError

ENTRY_POINT_GROUP = "agent_essentials.plugins"


@dataclass(frozen=True, slots=True)
class Plugin:
    """Descriptor that knows how to create a :class:`Module` on demand."""

    name: str
    factory: Callable[[], Module]
    summary: str = ""
    version: str = "0.1.0"

    def create(self) -> Module:
        try:
            instance = self.factory()
        except Exception as exc:
            raise PluginError(f"Failed to instantiate plugin {self.name!r}: {exc}") from exc
        if not isinstance(instance, Module):
            raise PluginError(
                f"Plugin {self.name!r} factory returned {type(instance)!r}, "
                "which is not a Module subclass"
            )
        return instance


def _coerce_plugin(name: str, obj: object) -> Plugin:
    """Accept a Plugin, a Module subclass, or a zero-arg factory."""
    if isinstance(obj, Plugin):
        return obj
    if isinstance(obj, type) and issubclass(obj, Module):
        return Plugin(name=name, factory=obj, summary=obj.summary, version=obj.version)
    if callable(obj):
        return Plugin(name=name, factory=obj)
    raise PluginError(f"Entry point {name!r} is not a Plugin, Module, or callable")


class PluginRegistry:
    """An in-memory registry mapping names to :class:`Plugin` descriptors."""

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin, *, replace: bool = False) -> None:
        if plugin.name in self._plugins and not replace:
            raise PluginError(f"Plugin {plugin.name!r} is already registered")
        self._plugins[plugin.name] = plugin

    def unregister(self, name: str) -> None:
        self._plugins.pop(name, None)

    def get(self, name: str) -> Plugin:
        try:
            return self._plugins[name]
        except KeyError:
            raise PluginError(
                f"No plugin named {name!r}. Available: {sorted(self._plugins)}"
            ) from None

    def create(self, name: str) -> Module:
        """Instantiate the module registered under ``name``."""
        return self.get(name).create()

    def names(self) -> list[str]:
        return sorted(self._plugins)

    def load_entry_points(
        self, group: str = ENTRY_POINT_GROUP, *, replace: bool = False
    ) -> list[str]:
        """Discover and register plugins published via entry points."""
        loaded: list[str] = []
        for ep in metadata.entry_points(group=group):
            try:
                obj = ep.load()
            except Exception as exc:
                raise PluginError(f"Failed to load entry point {ep.name!r}: {exc}") from exc
            plugin = _coerce_plugin(ep.name, obj)
            if plugin.name in self._plugins and not replace:
                continue
            self.register(plugin, replace=replace)
            loaded.append(plugin.name)
        return loaded

    def __iter__(self) -> Iterator[Plugin]:
        return iter(self._plugins.values())

    def __len__(self) -> int:
        return len(self._plugins)

    def __contains__(self, name: object) -> bool:
        return name in self._plugins


_DEFAULT_REGISTRY: PluginRegistry | None = None


def get_registry() -> PluginRegistry:
    """Return the process-wide default registry, building it on first use."""
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        registry = PluginRegistry()
        registry.load_entry_points()
        # Fallback so the toolkit also works when run straight from a source
        # checkout that has not been pip-installed (no entry-point metadata).
        try:
            from agent_essentials import _register_builtins

            _register_builtins(registry)
        except Exception:
            pass
        _DEFAULT_REGISTRY = registry
    return _DEFAULT_REGISTRY


def reset_registry() -> None:
    """Reset the default registry (primarily for tests)."""
    global _DEFAULT_REGISTRY
    _DEFAULT_REGISTRY = None


__all__ = [
    "ENTRY_POINT_GROUP",
    "Plugin",
    "PluginRegistry",
    "get_registry",
    "reset_registry",
]
