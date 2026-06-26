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
contracts a product already enforces** (Cairn's plan schema, Milcah's
specialist request/result, Mahalath's match, Galeed's events) so the manifest and
the contract never drift.

```python
from keturah import manifest, capability

m = manifest("tirzah", version="1.3.0", capabilities=[
    capability(
        "ask",
        "Answer a question over Tirzah's memory.",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
    ),
])
m.to_dict()   # the full manifest (descriptions + schemas)
m.to_mcp()    # {"tools": [{"name": "ask", "description": ..., "inputSchema": ...}]}
```

A product typically exposes this as `capabilities()` and, where it is a service, a
`GET /api/capabilities` endpoint (with `?format=mcp` for the MCP view).

## Develop

```bash
pip install -e ".[dev]" && pytest
```
