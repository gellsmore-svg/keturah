"""Keturah — the family's interface-manifest capability.

A single, uniform way for any product (library or service) to declare the
interfaces an LLM can consume, with descriptions and JSON-Schema, and to project
them onto Model Context Protocol (``Manifest.to_mcp()``). Built from the seam
contracts a product already enforces, so the manifest never drifts from reality.
"""

from keturah.manifest import (
    CANONICAL_MANIFEST,
    CAPABILITY_KINDS,
    MANIFEST_SCHEMA_VERSION,
    Capability,
    Manifest,
    capability,
    manifest,
    validate_capability,
    validate_manifest,
)

__all__ = [
    "Capability",
    "Manifest",
    "CAPABILITY_KINDS",
    "MANIFEST_SCHEMA_VERSION",
    "CANONICAL_MANIFEST",
    "capability",
    "manifest",
    "validate_capability",
    "validate_manifest",
]
