"""Integration suite (roadmap).

Planned modules: Universal API Connector, OpenAPI Parser, Workflow Builder and
Webhook Manager. Not implemented in the MVP; implement ``core.Module`` and
register a ``Plugin`` to contribute one. See ROADMAP.md.
"""

from __future__ import annotations

__roadmap__ = [
    "universal_api_connector",
    "openapi_parser",
    "workflow_builder",
    "webhook_manager",
]

__all__ = ["__roadmap__"]
