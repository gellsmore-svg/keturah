"""Tests for the minimal Keturah stdio MCP server."""

from __future__ import annotations

import io
import json
import sys
from typing import Any

import pytest

from keturah import Registry, capability, manifest, run_stdio_server


def _make_demo_manifest() -> Registry:
    m = manifest(
        "demo",
        version="0.0.1",
        description="demo product",
        capabilities=[
            capability(
                "echo",
                "Return the message",
                input_schema={
                    "type": "object",
                    "properties": {"message": {"type": "string"}},
                    "required": ["message"],
                },
            )
        ],
    )
    return Registry([m])


def _capture_stdio(run_callable, inputs: list[str]) -> list[dict]:
    """Run a function that reads stdin / writes stdout and capture the JSON lines written."""
    old_stdin = sys.stdin
    old_stdout = sys.stdout
    try:
        sys.stdin = io.StringIO("\n".join(inputs) + "\n")
        out = io.StringIO()
        sys.stdout = out
        run_callable()
        raw = out.getvalue().strip()
        if not raw:
            return []
        return [json.loads(line) for line in raw.splitlines() if line.strip()]
    finally:
        sys.stdin = old_stdin
        sys.stdout = old_stdout


def test_tools_list_from_registry(monkeypatch):
    reg = _make_demo_manifest()

    # Send initialize + tools/list
    responses = _capture_stdio(
        lambda: run_stdio_server(reg, handlers={"demo.echo": lambda **k: k}),
        [
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
        ],
    )

    # We should have at least the tools/list response
    list_resp = next((r for r in responses if r.get("id") == 2), None)
    assert list_resp is not None
    tools = list_resp["result"]["tools"]
    names = [t["name"] for t in tools]
    assert "demo.echo" in names
    assert any(t["name"] == "demo.echo" for t in tools)


def test_tools_list_hides_tools_without_handlers():
    reg = Registry([
        manifest(
            "demo",
            capabilities=[
                capability("echo", "Return the message"),
                capability("planned", "Declared but not executable yet"),
            ],
        )
    ])

    responses = _capture_stdio(
        lambda: run_stdio_server(reg, handlers={"demo.echo": lambda **k: k}),
        [
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}),
        ],
    )

    tools = responses[-1]["result"]["tools"]
    assert [tool["name"] for tool in tools] == ["demo.echo"]


def test_tool_call_executes_handler():
    reg = _make_demo_manifest()

    def echo_handler(message: str = "") -> dict[str, Any]:
        return {"received": message, "ok": True}

    responses = _capture_stdio(
        lambda: run_stdio_server(reg, handlers={"demo.echo": echo_handler}),
        [
            json.dumps({"jsonrpc": "2.0", "id": 10, "method": "initialize"}),
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 11,
                    "method": "tools/call",
                    "params": {"name": "demo.echo", "arguments": {"message": "hello from test"}},
                }
            ),
        ],
    )

    call_resp = next((r for r in responses if r.get("id") == 11), None)
    assert call_resp is not None
    assert "result" in call_resp
    content = call_resp["result"]["content"][0]
    assert content["type"] == "text"
    parsed = json.loads(content["text"])
    assert parsed["received"] == "hello from test"
    assert parsed["ok"] is True


def test_unknown_tool_returns_error():
    reg = _make_demo_manifest()

    responses = _capture_stdio(
        lambda: run_stdio_server(reg, handlers={}),
        [
            json.dumps({"jsonrpc": "2.0", "id": 99, "method": "tools/call", "params": {"name": "no.such.tool"}}),
        ],
    )

    err = responses[-1]
    assert "error" in err
    assert "not found" in err["error"]["message"].lower() or "Tool not found" in err["error"]["message"]
