"""Tests for the Token Counter and pricing."""

from __future__ import annotations

import pytest

from agent_essentials.core.exceptions import ValidationError
from agent_essentials.optimization import TokenCounter, count_tokens, list_models, resolve_price


def test_resolve_price_canonical_alias_unknown():
    assert resolve_price("gpt-4.1").provider == "openai"
    assert resolve_price("opus").model == "claude-opus-4-8"
    assert resolve_price("HAIKU").model == "claude-haiku-4-5"
    with pytest.raises(ValidationError):
        resolve_price("nonexistent-model")
    assert "gpt-4.1" in list_models()


def test_count_tokens_fallback():
    assert count_tokens("") == 0
    assert count_tokens("hello world", "gpt-4o") > 0


def test_estimate_cost_basic_and_cached():
    tc = TokenCounter()
    est = tc.estimate_cost(model="claude-sonnet-4-6", input_tokens=1_000_000, output_tokens=0)
    assert est.input_cost == pytest.approx(3.0)
    cached = tc.estimate_cost(
        model="claude-sonnet-4-6", input_tokens=1_000_000, output_tokens=0, cached=True
    )
    assert cached.input_cost < est.input_cost
    assert est.suggestions
    with pytest.raises(ValidationError):
        tc.estimate_cost(model="gpt-4o", requests=0)


def test_estimate_cost_scales_with_requests():
    tc = TokenCounter()
    one = tc.estimate_cost(model="gpt-4o", input_tokens=1000, output_tokens=1000, requests=1)
    many = tc.estimate_cost(model="gpt-4o", input_tokens=1000, output_tokens=1000, requests=100)
    assert many.total_cost == pytest.approx(one.total_cost * 100)


def test_compare_orders_cheapest_first():
    tc = TokenCounter()
    cmp = tc.compare(input_tokens=1000, output_tokens=1000, requests=10)
    costs = [row["total_cost"] for row in cmp.ranked]
    assert costs == sorted(costs)
    assert cmp.ranked[0]["model"] == "local"  # free is cheapest


def test_run_ops():
    tc = TokenCounter()
    assert tc.run({"op": "count", "text": "hello", "model": "gpt-4o"})["tokens"] > 0
    assert "total_cost" in tc.run({"op": "estimate", "model": "gpt-4o", "input_tokens": 10})
    assert tc.run({"op": "compare", "input_tokens": 10, "output_tokens": 5})["ranked"]
    with pytest.raises(ValidationError):
        tc.run({"op": "bogus"})


def test_compare_validates_inputs():
    tc = TokenCounter()
    with pytest.raises(ValidationError):
        tc.compare(input_tokens=-5, output_tokens=10)
    with pytest.raises(ValidationError):
        tc.compare(input_tokens=5, output_tokens=10, requests=0)
