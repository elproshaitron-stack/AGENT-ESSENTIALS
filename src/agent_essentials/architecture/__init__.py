"""Architecture Generator module."""

from __future__ import annotations

from ..core.plugin import Plugin
from .generator import ArchitectureGenerator
from .models import ArchitectureRecommendation, Component, ProjectSpec

plugin = Plugin(
    name=ArchitectureGenerator.name,
    factory=ArchitectureGenerator,
    summary=ArchitectureGenerator.summary,
    version=ArchitectureGenerator.version,
)

__all__ = [
    "ArchitectureGenerator",
    "ArchitectureRecommendation",
    "Component",
    "ProjectSpec",
    "plugin",
]
