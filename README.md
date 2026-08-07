# Keturah

**A uniform, MCP-bridgeable manifest of a product's LLM-consumable interfaces.**

Keturah lets any family product — library *or* service — answer one question:
*what can an LLM call here, and how?* Each interface is a `Capability` (name,
description, JSON-Schema input/output); a `Manifest` bundles them with the product
and version. The name is biblical ("incense / that which is offered up") — the
catalog of what each product **offers**.

There is already a standard for this — **Model Context Protocol (MCP)** — and
Keturah does not replace it. `Manifest.to_mcp()` projects a manifest onto MCP's
`tools/list` shape, so a real MCP server is a thin adapter over a Keturah manifest
rather than a parallel definition. Keturah exists because the family is a mix of
libraries and services, and because manifests should be **built from the seam
contracts a product already enforces** (Deborah's plan schema, Milcah's
specialist request/result, Mahalath's match, Galeed's events) so the manifest and
the contract never drift.

```python
from keturah import manifest, capability, Registry, MANIFEST_SCHEMA_VERSION

m = manifest(
    "tirzah",
    version="1.3.0",
    capabilities=[
        capability(
            "ask",
            "Answer a question over Tirzah's memory.",
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "answer": {"type": "string"},
                    "traceId": {"type": "string"},
                },
            },
            tags=["qa", "memory"],
        ),
        capability(
            "capabilities",
            "List this product's interfaces.",
            kind="resource",
            tags=["discovery"],
        ),
        capability(
            "system_prompt",
            "Default system prompt for agents using this product.",
            kind="prompt",
        ),
    ],
)

m.schema_version          # MANIFEST_SCHEMA_VERSION ("1.0")
m.to_dict()               # full manifest (descriptions + schemas)
m.to_mcp()                # MCP tools/list — tools only; includes outputSchema
m.resources()             # kind="resource" capabilities
m.prompts()               # kind="prompt" capabilities
```

A product typically exposes this as `capabilities()` and, where it is a service, a
`GET /api/capabilities` endpoint (with `?format=mcp` for the MCP view).

## Registry (federated discovery)

```python
reg = Registry([m, other_product_manifest])

reg.find("ask")                    # first (product, capability) match
reg.find("tirzah.ask")             # namespaced — same form to_mcp() emits
reg.find("ask", product="tirzah")  # explicit product wins
reg.find_all("ask")                # every product exposing that tool name

reg.tools()                        # all kind="tool"
reg.resources()                    # all kind="resource"
reg.prompts()                      # all kind="prompt"
reg.with_tag("planner")

reg.to_mcp()                       # union tools/list; names are product.tool
```

## MCP projection

`Capability.to_mcp_tool()` / `Manifest.to_mcp()` / `Registry.to_mcp()` emit the
MCP `tools/list` shape:

| Keturah field | MCP field |
|---|---|
| `name` | `name` (Registry namespaces as `product.tool`) |
| `description` | `description` |
| `input_schema` | `inputSchema` |
| `output_schema` | `outputSchema` (omitted when unset) |

Only `kind="tool"` entries appear in `to_mcp()`. Resources and prompts stay on
the Keturah surface (`resources()` / `prompts()`); a real MCP server can map them
to MCP prompts/resources resources separately via `keturah.mcp.run_stdio_server`.

Manifest validation requires `schema_version` equal to
`MANIFEST_SCHEMA_VERSION` so consumers can version-gate.

## Develop

Works the same on native Linux and WSL — stdlib-only, no platform-specific steps.

```bash
pip install -e ".[dev]" && pytest
```
