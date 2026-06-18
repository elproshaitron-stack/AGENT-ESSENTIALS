"""Abstract base class every module implements.

A :class:`Module` exposes a uniform ``run(payload) -> dict`` entry point so the
CLI, the plugin registry and remote callers can invoke any module generically.
Concrete modules additionally provide richer, fully-typed methods (for example
``ArchitectureGenerator.generate(spec)``) for direct use from Python.
"""

from __future__ import annotations

import abc
from collections.abc import Mapping
from typing import Any, ClassVar


class Module(abc.ABC):
    """Base class for all Agent Essentials modules."""

    #: Stable identifier, also used as the plugin name.
    name: ClassVar[str] = "module"
    #: Semantic version of the module implementation.
    version: ClassVar[str] = "0.1.0"
    #: One-line human-readable summary.
    summary: ClassVar[str] = ""

    @abc.abstractmethod
    def run(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Execute the module from a plain mapping and return a plain dict.

        This is the framework-agnostic seam: anything that can build a dict can
        drive any module, and the output is always JSON-serializable.
        """

    @classmethod
    def describe(cls) -> dict[str, Any]:
        """Return machine-readable metadata describing this module."""
        return {"name": cls.name, "version": cls.version, "summary": cls.summary}


__all__ = ["Module"]
