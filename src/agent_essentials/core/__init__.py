"""Core foundations shared by every Agent Essentials module."""

from __future__ import annotations

from .base import Module
from .di import Container, Factory
from .exceptions import (
    AgentEssentialsError,
    ConfigurationError,
    MemoryStoreError,
    PluginError,
    ValidationError,
)
from .plugin import (
    ENTRY_POINT_GROUP,
    Plugin,
    PluginRegistry,
    get_registry,
    reset_registry,
)
from .result import Finding, Priority, Recommendation, Severity
from .types import Serializable, to_serializable

__all__ = [
    "ENTRY_POINT_GROUP",
    "AgentEssentialsError",
    "ConfigurationError",
    "Container",
    "Factory",
    "Finding",
    "MemoryStoreError",
    "Module",
    "Plugin",
    "PluginError",
    "PluginRegistry",
    "Priority",
    "Recommendation",
    "Serializable",
    "Severity",
    "ValidationError",
    "get_registry",
    "reset_registry",
    "to_serializable",
]
