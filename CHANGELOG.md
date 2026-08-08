# Changelog

## [Unreleased]

## [0.5.0] — 2026-08-08

Review action for `docs/review-2026-08-08.md` (0.4.0 baseline).

### Fixed
- **H1 / F1**: Stage 0 fields fully enforced — `negotiable` bool, `cost.budget` /
  `cost.budget_class` ∈ `BUDGET_CLASSES`, `evidence.confidence` /
  `evidence.confidence_mode` ∈ `CONFIDENCE_MODES`, `failure_modes` list of
  strings. `capability()` raises `TypeError` on wrong types instead of
  silently coercing (`bool("yes")`, `list("times out")`).
- **H2 / F2**: capability names may not contain `.` (Registry `product.tool`
  separator).
- **M1**: `Registry.to_mcp(namespaced=False)` raises on duplicate tool names.
- **M2**: stdio MCP emits JSON-RPC `-32700` / `-32600` for malformed frames
  instead of silence.
- **M3**: wrong-typed `semantics` / related builder args name the field.
- **M4**: empty product `version` fails `validate_manifest`.
- **L1**: `band_for` maps non-finite values (`nan`, `±inf`) to `unassessed`.

## [0.4.0] — 2026-08-07

### Added
- Stage 0 contract extensions on `Capability` (all optional, additive):
  `negotiable`, `semantics`, `evidence`, `cost`, `failure_modes`
- MCP tools carry these under `_meta.keturah` when present (round-trip safe)
- `BUDGET_CLASSES` / `CONFIDENCE_MODES` vocabularies for validation
- **Layered confidence in `keturah.envelope`**, adopted from `deborah.contracts`
  so the estate has one vocabulary: three dimensions (`evidence`, `inference`,
  `execution`) with ordinal bands (`high`/`medium`/`low`/`unassessed`).
  `SpecialistResult.confidence_bands` carries the decomposition;
  `confidence_layered()` derives it from the legacy scalar when unset. The
  scalar is **never** back-computed from bands — that would manufacture the
  precision the model exists to avoid. `band_for()` matches
  `milcah.deborah.confidence_band` exactly, verified by test.
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
