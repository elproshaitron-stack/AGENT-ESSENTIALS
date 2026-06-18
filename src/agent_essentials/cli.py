"""Command-line interface for Agent Essentials.

Every command runs a module through the same plugin registry the Python API
uses, so the CLI is a thin, faithful wrapper. Output is always JSON on stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from typing import Any

from .__about__ import __version__
from .core import get_registry
from .core.exceptions import AgentEssentialsError


def _print_json(data: Any) -> None:
    json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def _load_payload(args: argparse.Namespace) -> dict[str, Any]:
    raw: str | None = None
    if getattr(args, "json", None):
        raw = args.json
    elif getattr(args, "file", None):
        if args.file == "-":
            raw = sys.stdin.read()
        else:
            with open(args.file, encoding="utf-8") as handle:
                raw = handle.read()
    if raw is None:
        return {}
    payload = json.loads(raw)
    if not isinstance(payload, Mapping):
        raise AgentEssentialsError("JSON payload must be an object")
    return dict(payload)


def _run_module(name: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    return get_registry().create(name).run(payload)


def _cmd_modules(_args: argparse.Namespace) -> int:
    registry = get_registry()
    _print_json(
        [
            {"name": p.name, "version": p.version, "summary": p.summary}
            for p in sorted(registry, key=lambda p: p.name)
        ]
    )
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    _print_json(_run_module(args.name, _load_payload(args)))
    return 0


def _cmd_architecture(args: argparse.Namespace) -> int:
    if args.json or args.file:
        payload = _load_payload(args)
    else:
        payload = {
            "project_type": args.type,
            "users": args.users,
            "documents": args.documents,
            "countries": _split_csv(args.countries),
            "budget": args.budget,
            "multi_agent": args.multi_agent,
            "realtime": args.realtime,
            "latency_sensitive": args.latency_sensitive,
            "languages": _split_csv(args.languages),
            "compliance": _split_csv(args.compliance),
        }
        if args.requests_per_day is not None:
            payload["requests_per_day"] = args.requests_per_day
    _print_json(_run_module("architecture", payload))
    return 0


def _cmd_plan(args: argparse.Namespace) -> int:
    _print_json(_run_module("planning", {"goal": args.goal}))
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {"output": args.output}
    if args.source:
        payload["sources"] = list(args.source)
    _print_json(_run_module("validation", payload))
    return 0


def _cmd_tokens(args: argparse.Namespace) -> int:
    if args.op == "count":
        payload: dict[str, Any] = {"op": "count", "model": args.model, "text": args.text or ""}
    else:
        payload = {
            "op": "estimate",
            "model": args.model,
            "requests": args.requests,
            "cached": args.cached,
        }
        if args.text is not None:
            payload["input_text"] = args.text
        if args.input_tokens is not None:
            payload["input_tokens"] = args.input_tokens
        if args.output_tokens is not None:
            payload["output_tokens"] = args.output_tokens
    _print_json(_run_module("optimization", payload))
    return 0


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-essentials",
        description="The missing toolkit for AI agents.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("modules", help="List registered modules").set_defaults(func=_cmd_modules)

    run_p = sub.add_parser("run", help="Run any module with a JSON payload")
    run_p.add_argument("name", help="Module name (see `modules`)")
    run_p.add_argument("--json", help="Inline JSON payload")
    run_p.add_argument("--file", help="Path to a JSON file, or '-' for stdin")
    run_p.set_defaults(func=_cmd_run)

    arch_p = sub.add_parser("architecture", help="Recommend an architecture")
    arch_p.add_argument("--type", default="general", help="Project type")
    arch_p.add_argument("--users", type=int, default=0)
    arch_p.add_argument("--documents", type=int, default=0)
    arch_p.add_argument("--countries", default="", help="Comma-separated ISO codes")
    arch_p.add_argument("--languages", default="")
    arch_p.add_argument("--compliance", default="", help="e.g. gdpr,hipaa")
    arch_p.add_argument("--budget", default="balanced", choices=["economy", "balanced", "premium"])
    arch_p.add_argument("--requests-per-day", type=int, default=None)
    arch_p.add_argument("--multi-agent", action="store_true")
    arch_p.add_argument("--realtime", action="store_true")
    arch_p.add_argument("--latency-sensitive", action="store_true")
    arch_p.add_argument("--json", help="Inline JSON ProjectSpec (overrides flags)")
    arch_p.add_argument("--file", help="Path to a JSON ProjectSpec, or '-' for stdin")
    arch_p.set_defaults(func=_cmd_architecture)

    plan_p = sub.add_parser("plan", help="Decompose a goal into a plan")
    plan_p.add_argument("goal", help="The goal to plan")
    plan_p.set_defaults(func=_cmd_plan)

    val_p = sub.add_parser("validate", help="Score an output for hallucination risk")
    val_p.add_argument("--output", required=True, help="The model output to check")
    val_p.add_argument("--source", action="append", help="A reference source (repeatable)")
    val_p.set_defaults(func=_cmd_validate)

    tok_p = sub.add_parser("tokens", help="Count tokens / estimate cost")
    tok_p.add_argument("--op", default="estimate", choices=["count", "estimate"])
    tok_p.add_argument("--model", default="gpt-4.1-mini")
    tok_p.add_argument("--text", help="Text to count / use as input")
    tok_p.add_argument("--input-tokens", type=int, default=None)
    tok_p.add_argument("--output-tokens", type=int, default=None)
    tok_p.add_argument("--requests", type=int, default=1)
    tok_p.add_argument("--cached", action="store_true")
    tok_p.set_defaults(func=_cmd_tokens)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result: int = args.func(args)
        return result
    except AgentEssentialsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except (json.JSONDecodeError, FileNotFoundError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
