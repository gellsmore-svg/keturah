"""Keturah — the family's interface-manifest capability.

A single, uniform way for any product (library or service) to declare the
interfaces an LLM can consume, with descriptions and JSON-Schema, and to project
them onto Model Context Protocol (``Manifest.to_mcp()``). Built from the seam
contracts a product already enforces, so the manifest never drifts from reality.
"""

from keturah.manifest import (
    BUDGET_CLASSES,
    CANONICAL_MANIFEST,
    CAPABILITY_KINDS,
    CONFIDENCE_MODES,
    MANIFEST_SCHEMA_VERSION,
    Capability,
    Manifest,
    capability,
    manifest,
    validate_capability,
    validate_manifest,
)
from keturah.envelope import (
    CONFIDENCE_BANDS,
    CONFIDENCE_DIMENSIONS,
    ENVELOPE_VERSION,
    EVIDENCE_KINDS,
    REQUEST_FIELDS,
    RESULT_FIELDS,
    SPECIALIST_MODES,
    TERMINAL_REASONS,
    Confidence,
    Evidence,
    SpecialistRequest,
    SpecialistResult,
    band_for,
    normalise_confidence,
    normalise_evidence,
    validate_request,
    validate_result,
)
from keturah.registry import Registry
from keturah.mcp import run_stdio_server

__all__ = [
    "normalise_confidence",
    "band_for",
    "Confidence",
    "CONFIDENCE_DIMENSIONS",
    "CONFIDENCE_BANDS",
    "validate_result",
    "validate_request",
    "normalise_evidence",
    "SpecialistResult",
    "SpecialistRequest",
    "Evidence",
    "TERMINAL_REASONS",
    "SPECIALIST_MODES",
    "RESULT_FIELDS",
    "REQUEST_FIELDS",
    "EVIDENCE_KINDS",
    "ENVELOPE_VERSION",
    "Capability",
    "Manifest",
    "Registry",
    "BUDGET_CLASSES",
    "CAPABILITY_KINDS",
    "CONFIDENCE_MODES",
    "MANIFEST_SCHEMA_VERSION",
    "CANONICAL_MANIFEST",
    "capability",
    "manifest",
    "validate_capability",
    "validate_manifest",
    "run_stdio_server",
]
