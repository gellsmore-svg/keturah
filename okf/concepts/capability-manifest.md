---
type: Concept
title: Capability manifests
description: Each LLM-consumable interface is a Capability (name, description, schemas); a Manifest collects them and renders to MCP tools/list — built FROM the seam contracts so it cannot drift.
resource: https://github.com/gellsmore-svg/keturah
tags: [keturah, capability, manifest, mcp]
timestamp: 2026-07-05T00:00:00Z
---

# Capability manifests

A `Capability` describes one LLM-callable interface: name, human description,
input/output schema. A `Manifest` collects a product's capabilities and
answers in two dialects: the family's own (`to_dict()`) and MCP
(`to_mcp()` → `tools/list`, names namespaced `product.tool` when federated).

The discipline: manifests are **built from the executable seam contracts**
(each sibling's `<pkg>.manifest.build_manifest()`), not hand-maintained — so
what a manifest advertises is what the tests enforce. Tirzah serves its own at
`/api/capabilities` and the federated family registry at `/api/registry`
(every importable sibling's manifest, lazily and fail-soft); its planner
advertises specialist tools FROM the manifest rather than from prose.
