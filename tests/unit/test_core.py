"""Tests for core foundations: serialization, results, DI, plugins."""

from __future__ import annotations

import json

import pytest

from agent_essentials.core import (
    Container,
    Finding,
    Module,
    Plugin,
    PluginRegistry,
    Severity,
)
from agent_essentials.core.exceptions import ConfigurationError, PluginError
from agent_essentials.core.types import to_serializable


class _Echo(Module):
    name = "echo"
    summary = "echoes payload"

    def run(self, payload):
        return {"echo": dict(payload)}


def test_severity_ordering():
    assert Severity.CRITICAL.weight > Severity.HIGH.weight > Severity.INFO.weight


def test_serializable_roundtrip_handles_enums_and_nested():
    finding = Finding("c1", "msg", Severity.HIGH, {"k": [1, 2]})
    data = finding.to_dict()
    assert data["severity"] == "high"
    assert data["detail"] == {"k": [1, 2]}
    # to_json is valid JSON
    assert json.loads(finding.to_json())["code"] == "c1"


def test_to_serializable_passthrough_scalar():
    assert to_serializable(5) == 5
    assert to_serializable({"a": (1, 2)}) == {"a": [1, 2]}


def test_module_is_abstract():
    with pytest.raises(TypeError):
        Module()  # type: ignore[abstract]
    assert _Echo().run({"a": 1}) == {"echo": {"a": 1}}
    assert _Echo.describe()["name"] == "echo"


def test_container_singleton_and_transient():
    c = Container()
    calls = {"n": 0}

    def factory(_c):
        calls["n"] += 1
        return object()

    c.register("singleton", factory, singleton=True)
    c.register("transient", factory, singleton=False)
    assert c.resolve("singleton") is c.resolve("singleton")
    assert c.resolve("transient") is not c.resolve("transient")
    assert c.has("singleton")


def test_container_instance_and_override_and_missing():
    c = Container()
    sentinel = object()
    c.register_instance("x", sentinel)
    assert c.resolve("x") is sentinel
    new = object()
    c.override("x", new)
    assert c.resolve("x") is new
    with pytest.raises(ConfigurationError):
        c.resolve("missing")


def test_plugin_registry_register_get_create():
    reg = PluginRegistry()
    reg.register(Plugin("echo", _Echo, summary="s"))
    assert "echo" in reg
    assert reg.names() == ["echo"]
    assert len(reg) == 1
    module = reg.create("echo")
    assert isinstance(module, _Echo)
    assert [p.name for p in reg] == ["echo"]


def test_plugin_registry_duplicate_and_replace():
    reg = PluginRegistry()
    reg.register(Plugin("echo", _Echo))
    with pytest.raises(PluginError):
        reg.register(Plugin("echo", _Echo))
    reg.register(Plugin("echo", _Echo), replace=True)  # ok
    reg.unregister("echo")
    assert "echo" not in reg


def test_plugin_registry_get_missing_raises():
    reg = PluginRegistry()
    with pytest.raises(PluginError):
        reg.get("nope")


def test_plugin_factory_returning_non_module_raises():
    bad = Plugin("bad", lambda: "not a module")  # type: ignore[arg-type,return-value]
    with pytest.raises(PluginError):
        bad.create()
