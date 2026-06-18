"""Agent Essentials — the missing toolkit for AI agents.

Design, validate, optimize and scale agents *before* production. This package
is framework-agnostic: it helps you make decisions, it does not run your agents.

Quick start::

    from agent_essentials import ArchitectureGenerator, ProjectSpec

    rec = ArchitectureGenerator().generate(
        ProjectSpec(project_type="customer support", users=10_000, documents=50_000)
    )
    print(rec.summary)
"""

from __future__ import annotations

from .__about__ import __version__
from .architecture import ArchitectureGenerator, ProjectSpec
from .architecture import plugin as _architecture_plugin
from .core import (
    Container,
    Finding,
    Module,
    Plugin,
    PluginRegistry,
    Priority,
    Recommendation,
    Severity,
    get_registry,
)
from .memory import MemoryEngine
from .memory import plugin as _memory_plugin
from .optimization import TokenCounter
from .optimization import plugin as _optimization_plugin
from .planning import TaskPlanner
from .planning import plugin as _planning_plugin
from .validation import EntailmentValidator, HallucinationDetector
from .validation import entailment_plugin as _entailment_plugin
from .validation import plugin as _validation_plugin

_BUILTIN_PLUGINS = (
    _architecture_plugin,
    _memory_plugin,
    _planning_plugin,
    _validation_plugin,
    _entailment_plugin,
    _optimization_plugin,
)


def _register_builtins(registry: PluginRegistry) -> None:
    """Register built-in modules that aren't already present.

    Lets the toolkit work from a source checkout with no installed entry-point
    metadata, without clobbering anything discovered via entry points.
    """
    for plugin in _BUILTIN_PLUGINS:
        if plugin.name not in registry:
            registry.register(plugin)


__all__ = [
    # modules
    "ArchitectureGenerator",
    "Container",
    "EntailmentValidator",
    "Finding",
    "HallucinationDetector",
    "MemoryEngine",
    # core
    "Module",
    "Plugin",
    "PluginRegistry",
    "Priority",
    "ProjectSpec",
    "Recommendation",
    "Severity",
    "TaskPlanner",
    "TokenCounter",
    "__version__",
    "get_registry",
]
