"""Research suite (roadmap).

Planned modules: Web Extractor, Metadata Extractor, Website Analyzer and
Article Summarizer. These are intentionally not implemented in the MVP; the
interfaces in ``agent_essentials.core`` (Module, Plugin) define the contract a
contribution should follow. See ROADMAP.md.
"""

from __future__ import annotations

__roadmap__ = [
    "web_extractor",
    "metadata_extractor",
    "website_analyzer",
    "article_summarizer",
]

__all__ = ["__roadmap__"]
