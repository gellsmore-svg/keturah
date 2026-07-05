---
type: Project
title: Keturah
description: A uniform, MCP-bridgeable manifest of a product's LLM-consumable interfaces — each interface is a Capability; a Manifest renders to MCP tools/list.
resource: https://github.com/gellsmore-svg/keturah
tags: [keturah, mcp, manifest, capabilities, llm-interfaces]
timestamp: 2026-07-05T00:00:00Z
---

# Keturah

Keturah lets any family product — library *or* service — answer one question:
*what can an LLM call here, and how?* Each interface is a `Capability` (name,
description, input/output schema); a `Manifest` collects them and bridges to MCP
(`to_mcp()` → `tools/list`). Built FROM the executable seam contracts so the
manifest cannot drift from the code.

## Map

- **manifest** — `Capability`, `Manifest`, `build_manifest()` conventions.
- Family adoption: every sibling exposes `<pkg>.manifest.build_manifest()`;
  Tirzah serves the federated registry at `/api/registry` and its own at
  `/api/capabilities` (`?format=mcp`).
