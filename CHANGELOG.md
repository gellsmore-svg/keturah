# Changelog

## [Unreleased]
- **New `keturah.envelope`** — the shared capability-call contract
  (`SpecialistRequest`, `SpecialistResult`, `SPECIALIST_MODES`,
  `TERMINAL_REASONS`, validators). Extracted from two hand-maintained copies
  (`tirzah.coherence`, `milcah.contract`) that had already drifted: only the
  consumer carried `error`/`error_type`, so a provider could not represent its
  own failure. Both now import one definition.
- **New `Evidence` type** (`kind`/`ref`/`note`) plus `normalise_evidence()`.
  Evidence was `list[str]`, so "evidence-backed" could be asserted but never
  checked. `SpecialistResult.is_anchored` distinguishes evidence that points at
  something from prose. Bare strings still work — they upgrade to `kind="note"`,
  so no producer has to change first.
- `Registry.find_all()` now parses namespaced `product.tool` names the same way
  `find()` does — `find_all("milcah.coherence_check")` returned `[]` before (#10).
  It also takes the `product=` keyword for symmetry with `find()`.
- New federated `Registry.resources()` and `Registry.prompts()`, mirroring the
  per-manifest accessors across every product (#13).

## [0.3.0] - 2026-07-10
- Hanani handlers wired into the MCP server.
- `list only executable tools` — non-tool capabilities no longer surface as
  callable MCP tools.

## [0.2.0] - 2026-07-06
- Minimal stdio MCP server for family tools (Codex / Claude Code), with the
  Tirzah memory handlers wired in.
- `outputSchema` in the MCP projection, `schema_version` + stricter validation,
  namespaced `find`, `py.typed`, ruff enforced in CI.

## [0.1.0] - 2026-06-26
- Initial release: `Capability` / `Manifest` — a uniform, MCP-bridgeable manifest
  of a product's LLM-consumable interfaces (`build_manifest()`, `to_mcp()`).
  Adopted family-wide (Tirzah, Mahalath, Hoglah, Milcah, Cairn) with
  `GET /api/capabilities?format=mcp` served by Tirzah.
