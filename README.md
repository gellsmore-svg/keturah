# Keturah

**Keturah describes what an LLM can call in your product, once, in a form
that is also MCP.** Each interface is a `Capability` (name, description,
JSON-Schema input and output); a `Manifest` bundles a product's capabilities
with its name and version; a `Registry` lets agents discover capabilities
across many products. `to_mcp()` turns any of them into the Model Context
Protocol `tools/list` shape, so an MCP server becomes a thin adapter over the
manifest rather than a second definition that can drift.

It is pure stdlib with no dependencies. The name means "incense, that which is
offered up": the catalogue of what each product **offers**.

## Is it for you?

**Good fit:** you have several libraries or services, not just MCP servers,
and want one description of their LLM-callable interfaces that drives
discovery, validation and MCP from the same source. In this family the
manifests are built from contracts each product already enforces (Deborah's
plan schema, Milcah's specialist request and result, Galeed's events).

**Not a fit:** you only need a single MCP server. Use an MCP SDK directly.
Keturah's own server is minimal and implements tools only (see below).

## Try it

```bash
pip install keturah
keturah-mcp --demo        # a stdio MCP server with two demo tools
```

Register it with an MCP client, for example
`claude mcp add keturah -- keturah-mcp --demo`, and the client can list and
call `demo.echo`.

Describe your own product:

```python
from keturah import manifest, capability, Registry

m = manifest(
    "tirzah",
    version="1.3.0",
    capabilities=[
        capability(
            "ask",
            "Answer a question over Tirzah's memory.",
            input_schema={"type": "object",
                          "properties": {"query": {"type": "string"}},
                          "required": ["query"]},
            output_schema={"type": "object",
                           "properties": {"answer": {"type": "string"}}},
            tags=["qa", "memory"],
        ),
        capability("system_prompt", "Default system prompt for agents.", kind="prompt"),
    ],
)

m.to_dict()        # the full manifest, with descriptions and schemas
m.to_mcp()         # MCP tools/list: tools only, including outputSchema
m.prompts()        # kind="prompt" capabilities (also: m.resources())
```

A product usually exposes this as `capabilities()` and, if it is a service, as
`GET /api/capabilities` (`?format=mcp` for the MCP view).

## Discovery across products

```python
reg = Registry([m, other_manifest])

reg.find("tirzah.ask")             # namespaced, the form to_mcp() emits
reg.find("ask", product="tirzah")  # or by explicit product
reg.find_all("ask")                # every product exposing that name
reg.with_tag("planner")            # also: tools(), resources(), prompts()
reg.to_mcp()                       # union tools/list, named product.tool
```

## Mapping to MCP

| Keturah | MCP `tools/list` |
|---|---|
| `name` | `name` (a Registry emits `product.tool`) |
| `description` | `description` |
| `input_schema` | `inputSchema` |
| `output_schema` | `outputSchema` (omitted when unset) |

Only `kind="tool"` capabilities are projected. Resources and prompts stay on
the Keturah surface (`resources()` / `prompts()`).

## Serving over MCP

`keturah.mcp.run_stdio_server(registry, handlers={...})` runs a minimal,
synchronous stdio MCP server. It implements `initialize`, `tools/list` and
`tools/call`. It lists only tools that have a handler, and does not serve MCP
resources or prompts.

`keturah-mcp` with no flags serves the family registry from an installed
Tirzah, with whichever handlers Tirzah and Hanani provide; `--demo` needs
nothing installed.

## Calling a capability: the envelope

`keturah.envelope` defines the shape of one call and its result:
`SpecialistRequest`, `SpecialistResult`, `Confidence` and `Evidence`, with
`validate_request` / `validate_result`. Evidence has a `kind` and a `ref`, so a
validator can check that it points at something. `normalise_evidence` upgrades
older free-text evidence lists, so existing producers keep working.

## Versioning

Manifests carry `schema_version`, and validation requires it to equal
`MANIFEST_SCHEMA_VERSION` (currently `"1.0"`), so consumers can version-gate.

## Develop

Stdlib-only, so it behaves the same on Linux and WSL.

```bash
pip install -e ".[dev]" && pytest
```

[CHANGELOG](CHANGELOG.md) · [2026-08-08 review](docs/review-2026-08-08.md) ·
Apache 2.0, see [LICENSE](LICENSE).
