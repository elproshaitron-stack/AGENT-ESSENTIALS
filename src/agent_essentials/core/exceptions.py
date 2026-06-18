"""Exception hierarchy for Agent Essentials.

All exceptions raised by the toolkit derive from :class:`AgentEssentialsError`,
so callers can catch everything from the library with a single ``except``.
"""

from __future__ import annotations


class AgentEssentialsError(Exception):
    """Base class for every error raised by the toolkit."""


class ConfigurationError(AgentEssentialsError):
    """Raised when a component is configured with invalid options."""


class ValidationError(AgentEssentialsError):
    """Raised when user-supplied input fails validation."""


class PluginError(AgentEssentialsError):
    """Raised when a plugin cannot be registered, found, or instantiated."""


class MemoryStoreError(AgentEssentialsError):
    """Raised when a memory store backend fails."""


__all__ = [
    "AgentEssentialsError",
    "ConfigurationError",
    "MemoryStoreError",
    "PluginError",
    "ValidationError",
]
