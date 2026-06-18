"""Token counting.

Uses ``tiktoken`` for exact counts when it is installed (the optional
``tokenizers`` extra); otherwise falls back to a provider-agnostic heuristic so
the toolkit always works with zero dependencies.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from ..utilities.text import approx_token_count
from .pricing import resolve_price


@lru_cache(maxsize=1)
def _tiktoken_module() -> Any:
    """Return the imported ``tiktoken`` module, or ``None`` if unavailable."""
    try:
        import tiktoken  # type: ignore[import-not-found]
    except Exception:
        return None
    return tiktoken


def tiktoken_available() -> bool:
    return _tiktoken_module() is not None


def count_tokens(text: str, model: str | None = None, *, prefer_exact: bool = True) -> int:
    """Count tokens in ``text``.

    For OpenAI models with ``tiktoken`` installed this is exact; for other
    providers it is a close estimate; with no ``tiktoken`` it is heuristic.
    """
    if not text:
        return 0
    if prefer_exact:
        tiktoken = _tiktoken_module()
        if tiktoken is not None:
            try:
                encoding = None
                if model is not None and resolve_price(model).provider == "openai":
                    try:
                        encoding = tiktoken.encoding_for_model(model)
                    except Exception:
                        encoding = None
                if encoding is None:
                    encoding = tiktoken.get_encoding("o200k_base")
                count: int = len(encoding.encode(text))
                return count
            except Exception:
                pass
    return approx_token_count(text)


__all__ = ["count_tokens", "tiktoken_available"]
