"""Minimal stdio MCP server for Keturah manifests.

Implements enough of the Model Context Protocol (stdio transport) for coding
agents (Codex CLI, Claude Code, Cursor, etc.) to discover and call family tools.

See the plan in Noa/docs/codex-integration-plan.md:
- Keturah is the linchpin: serves manifests as MCP tools.
- Thin adapter: the server uses Registry.to_mcp() for discovery and a dispatch
  table of handlers for execution.
- Reusable: the same server can back Codex, Claude Code, etc.

This module is pure stdlib + the existing keturah types. No extra dependencies.

Usage (example):
    from keturah import Registry, manifest, capability
    from keturah.mcp import run_stdio_server

    m = manifest("demo", capabilities=[capability("echo", "Echo back", input_schema=...)])
    reg = Registry([m])

    def echo_handler(text: str) -> dict:
        return {"echo": text}

    run_stdio_server(reg, handlers={"echo": echo_handler})
"""

from __future__ import annotations

import json
import sys
from typing import Any, Callable, Mapping

from .registry import Registry


def _write_json(obj: dict[str, Any]) -> None:
    """Write a single JSON-RPC message (one line, flushed)."""
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _error_response(req_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": code, "message": message},
    }


def _callable_tools_result(result: dict[str, Any], handlers: Mapping[str, Callable[..., Any]]) -> dict[str, Any]:
    """Restrict MCP tools/list to tools this server can actually execute."""
    handler_names = set(handlers)
    tools = [
        tool for tool in result.get("tools", [])
        if isinstance(tool, dict) and tool.get("name") in handler_names
    ]
    return {**result, "tools": tools}


def run_stdio_server(
    registry: Registry,
    *,
    handlers: Mapping[str, Callable[..., Any]] | None = None,
    server_name: str = "keturah-mcp",
    server_version: str = "0.1.0",
) -> None:
    """Run a blocking stdio MCP server.

    - Listens on stdin for JSON-RPC requests (one per line).
    - Responds on stdout.
    - Uses the provided Registry for ``tools/list`` (namespaced by default).
    - Dispatches ``tools/call`` to the matching handler (keyed by the MCP tool name).

    handlers: mapping from tool name (as exposed by registry.to_mcp(), usually
              "product.name" when using Registry) to a callable that accepts
              **kwargs from the tool arguments and returns a JSON-serializable result.

    The server is intentionally minimal and synchronous. It is suitable for
    local stdio MCP clients. For production use, wrap in a small process manager.
    """
    handlers = dict(handlers or {})
    initialized = False

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        if not isinstance(req, dict):
            continue

        method = req.get("method")
        req_id = req.get("id")
        params = req.get("params") or {}

        # Notifications (no id) are fire-and-forget
        if req_id is None:
            if method == "notifications/initialized":
                initialized = True
            continue

        if method == "initialize":
            _write_json(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {"listChanged": False},
                        },
                        "serverInfo": {
                            "name": server_name,
                            "version": server_version,
                        },
                    },
                }
            )
            continue

        if method == "tools/list":
            # Always return the current view from the registry
            result = _callable_tools_result(registry.to_mcp(namespaced=True), handlers)
            _write_json({"jsonrpc": "2.0", "id": req_id, "result": result})
            continue

        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}

            if not name:
                _write_json(_error_response(req_id, -32602, "Missing tool name"))
                continue

            handler = handlers.get(name)
            if handler is None:
                _write_json(
                    _error_response(req_id, -32601, f"Tool not found or no handler: {name}")
                )
                continue

            try:
                # Call the handler. Handlers are expected to be **kwargs friendly
                # or accept a single dict. We prefer ** unpacking for MCP style.
                if callable(handler):
                    raw_result = handler(**arguments) if arguments else handler()
                else:
                    raw_result = handler

                # MCP expects content blocks for the result.
                # We support both plain return values and already-structured content.
                if isinstance(raw_result, dict) and "content" in raw_result:
                    content = raw_result["content"]
                else:
                    # Default: serialize as text block (clients can parse JSON inside)
                    text = json.dumps(raw_result, ensure_ascii=False, default=str)
                    content = [{"type": "text", "text": text}]

                _write_json(
                    {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {"content": content},
                    }
                )
            except Exception as exc:
                _write_json(
                    _error_response(req_id, -32603, f"Tool execution failed: {exc}")
                )
            continue

        # Unknown method
        if req_id is not None:
            _write_json(_error_response(req_id, -32601, f"Method not found: {method}"))


def main(argv: list[str] | None = None) -> None:
    """Entry point for the Keturah MCP stdio server.

    Run as:
        keturah-mcp                 # uses family tools if available
        keturah-mcp --demo          # self-contained demo only

    The server speaks Model Context Protocol over stdio so that Codex CLI,
    Claude Code, Cursor, etc. can discover (tools/list) and invoke family
    capabilities.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Keturah MCP stdio server")
    parser.add_argument("--demo", action="store_true", help="Use only the built-in demo manifest (no real product imports)")
    parser.add_argument("--name", default="keturah-mcp", help="Server name reported to clients")
    args = parser.parse_args(argv)

    handlers: dict[str, Callable[..., Any]] = {}
    reg: Registry

    if not args.demo:
        try:
            from tirzah.manifest import family_registry

            reg = family_registry()

            # Tirzah's own MCP handlers (the "memory in" seam: search_memory, …).
            # Defensive by construction — no live DB needed to register.
            try:
                from tirzah.mcp_handlers import build_handlers as _tirzah_handlers

                handlers.update(_tirzah_handlers())
            except Exception:
                pass  # tirzah memory handlers not available

            # Hanani's reasoning-slice handlers (ingest_and_assess, corpus_summary).
            try:
                from hanani.mcp_handlers import build_handlers as _hanani_handlers

                handlers.update(_hanani_handlers())
            except Exception:
                pass  # hanani handlers not available

            # Try to provide real(ish) handlers for tools that can be called safely
            # Note: full "tirzah.ask" needs a configured Tirzah runtime + DB.
            # We wire the ones that are importable with minimal state.
            try:
                from tirzah.semantic import annotate as tirzah_annotate
                from tirzah.semantic import make_resolver  # may exist for default

                def semantic_handler(terms: list[str] | None = None, **_kw) -> dict[str, Any]:
                    terms = terms or []
                    # Best-effort default resolver (Mahalath if present)
                    try:
                        resolver = make_resolver()
                    except Exception:
                        # Fallback no-op resolver for demo environments
                        class _Noop:
                            def resolve(self, t):
                                return []
                        resolver = _Noop()
                    labels = tirzah_annotate("", " ".join(terms) if terms else "", resolver) or []
                    return {
                        "labels": [
                            {
                                "term": getattr(l, "term", ""),
                                "mpl_label": getattr(l, "mpl_label", ""),
                                "canonical_term": getattr(l, "canonical_term", ""),
                                "match_kind": getattr(l, "match_kind", ""),
                            }
                            for l in labels
                        ]
                    }

                # Register under both namespaced and short forms
                handlers["tirzah.semantic_annotate"] = semantic_handler
                handlers["semantic_annotate"] = semantic_handler
            except Exception:
                pass  # semantic not available

            # Placeholder / future: coherence_check, ask, etc. would be added here
            # with proper dependency injection (config, db, adapters).

        except Exception:
            reg = None  # fall through to demo

    if args.demo or reg is None:
        from . import capability, manifest, Registry

        demo = manifest(
            "demo",
            version="0.0.0+demo",
            description="Keturah demo MCP server (no real siblings loaded)",
            capabilities=[
                capability(
                    "echo",
                    "Echo the input (demo tool for testing MCP clients)",
                    input_schema={
                        "type": "object",
                        "properties": {"message": {"type": "string"}},
                        "required": ["message"],
                    },
                ),
                capability(
                    "list_tools",
                    "List tools known to this server (demo)",
                    input_schema={"type": "object"},
                ),
            ],
        )
        reg = Registry([demo])

        def demo_echo(message: str = "") -> dict[str, Any]:
            return {"echo": message, "note": "demo handler from keturah.mcp"}

        def demo_list_tools() -> dict[str, Any]:
            return {"tools": [t["name"] for t in reg.to_mcp()["tools"]]}

        handlers.update(
            {
                "echo": demo_echo,
                "demo.echo": demo_echo,
                "list_tools": demo_list_tools,
                "demo.list_tools": demo_list_tools,
            }
        )

    run_stdio_server(reg, handlers=handlers, server_name=args.name)


if __name__ == "__main__":
    main()
