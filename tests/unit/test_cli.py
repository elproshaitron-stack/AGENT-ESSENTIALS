"""Tests for the command-line interface."""

from __future__ import annotations

import json

import pytest

from agent_essentials.cli import main


def test_version_exits_zero():
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0


def test_modules_lists_builtins(capsys):
    assert main(["modules"]) == 0
    out = json.loads(capsys.readouterr().out)
    names = {m["name"] for m in out}
    assert {"architecture", "memory", "planning", "validation", "optimization"} <= names


def test_architecture_command(capsys):
    assert (
        main(
            [
                "architecture",
                "--type",
                "customer support",
                "--users",
                "10000",
                "--documents",
                "50000",
                "--countries",
                "US,MX",
            ]
        )
        == 0
    )
    out = json.loads(capsys.readouterr().out)
    assert out["needs_rag"] is True


def test_plan_command(capsys):
    assert main(["plan", "Build a sports league SaaS platform"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["domain"] == "saas"


def test_validate_command(capsys):
    assert (
        main(["validate", "--output", "Revenue grew 240%.", "--source", "Revenue grew 12%."]) == 0
    )
    out = json.loads(capsys.readouterr().out)
    assert 0.0 <= out["risk_score"] <= 1.0


def test_tokens_command(capsys):
    assert (
        main(
            [
                "tokens",
                "--op",
                "estimate",
                "--model",
                "gpt-4.1",
                "--input-tokens",
                "1500",
                "--output-tokens",
                "500",
                "--requests",
                "1000",
            ]
        )
        == 0
    )
    out = json.loads(capsys.readouterr().out)
    assert out["total_cost"] > 0


def test_run_generic_and_errors(capsys):
    assert (
        main(["run", "optimization", "--json", '{"op":"count","text":"hi","model":"gpt-4o"}']) == 0
    )
    assert json.loads(capsys.readouterr().out)["tokens"] > 0
    # unknown module -> error exit code
    assert main(["run", "does-not-exist", "--json", "{}"]) == 2
    # malformed json -> error exit code
    assert main(["run", "optimization", "--json", "{not json"]) == 2
