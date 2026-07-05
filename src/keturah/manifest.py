"""Keturah — a uniform manifest of a product's LLM-consumable interfaces.

One small, dependency-free shape so any family product (library or service) can
answer a single question: *what can an LLM call here, and how?* Each interface is a
:class:`Capability` (name, description, JSON-Schema input/output); a
:class:`Manifest` bundles them with the product + version. ``to_mcp()`` projects the
manifest onto Model Context Protocol's ``tools/list`` shape, so a real MCP server is
a thin adapter rather than a parallel definition.

The intent is that products build their manifest *from the seam contracts they
already have* (e.g. Cairn's plan schema, Milcah's specialist request/result), so the
manifest and the enforced contract never drift.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

MANIFEST_SCHEMA_VERSION = "1.0"
# An interface is callable (tool), readable (resource), or a prompt template (prompt).
CAPABILITY_KINDS = frozenset({"tool", "resource", "prompt"})

_EMPTY_OBJECT_SCHEMA: dict[str, Any] = {"type": "object"}

import re as _re

_MCP_NAME = _re.compile(r"^[A-Za-z0-9_.-]{1,128}$")


@dataclass
class Capability:
    """One LLM-consumable interface."""

    name: str
    description: str
    kind: str = "tool"
    input_schema: dict[str, Any] = field(default_factory=dict)  # JSON Schema
    output_schema: dict[str, Any] = field(default_factory=dict)  # JSON Schema
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_mcp_tool(self) -> dict[str, Any]:
        """This capability as an MCP ``tools/list`` entry (outputSchema included
        when declared — family products define rich result shapes)."""
        tool = {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema or _EMPTY_OBJECT_SCHEMA,
        }
        if self.output_schema:
            tool["outputSchema"] = self.output_schema
        return tool


@dataclass
class Manifest:
    """A product's full set of LLM-consumable interfaces."""

    product: str
    version: str = "0.0.0"
    description: str = ""
    capabilities: list[Capability] = field(default_factory=list)
    schema_version: str = MANIFEST_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["capabilities"] = [c.to_dict() for c in self.capabilities]
        return data

    def to_mcp(self) -> dict[str, Any]:
        """The MCP view: tools/list (only ``tool`` capabilities are callable tools)."""
        return {"tools": [c.to_mcp_tool() for c in self.capabilities if c.kind == "tool"]}

    def names(self) -> list[str]:
        return [c.name for c in self.capabilities]

    def resources(self) -> list[Capability]:
        """Readable interfaces (kind="resource") — not projected by to_mcp()."""
        return [c for c in self.capabilities if c.kind == "resource"]

    def prompts(self) -> list[Capability]:
        """Prompt templates (kind="prompt") — not projected by to_mcp(); a real
        MCP server would surface these via prompts/list, which is out of scope
        for this thin manifest (documented, not silently dropped)."""
        return [c for c in self.capabilities if c.kind == "prompt"]


def capability(
    name: str,
    description: str,
    *,
    kind: str = "tool",
    input_schema: dict[str, Any] | None = None,
    output_schema: dict[str, Any] | None = None,
    tags: list[str] | None = None,
) -> Capability:
    """Convenience builder."""
    return Capability(
        name=name,
        description=description,
        kind=kind,
        input_schema=input_schema or {},
        output_schema=output_schema or {},
        tags=tags or [],
    )


def manifest(product: str, *, version: str = "0.0.0", description: str = "", capabilities: list[Capability] | None = None) -> Manifest:
    return Manifest(product=product, version=version, description=description, capabilities=capabilities or [])


def validate_capability(cap: Any, *, index: int = 0) -> list[str]:
    data = cap.to_dict() if isinstance(cap, Capability) else cap
    if not isinstance(data, dict):
        return [f"capability[{index}] must be an object"]
    errors = []
    if not data.get("name"):
        errors.append(f"capability[{index}] missing name")
    if not data.get("description"):
        errors.append(f"capability[{index}] ({data.get('name', '?')}) missing description")
    if data.get("kind") not in CAPABILITY_KINDS:
        errors.append(f"capability[{index}] invalid kind: {data.get('kind')!r} (allowed: {sorted(CAPABILITY_KINDS)})")
    name = data.get("name")
    if name and data.get("kind", "tool") == "tool" and not _MCP_NAME.match(str(name)):
        errors.append(
            f"capability[{index}] tool name {name!r} is not MCP-safe "
            "(letters, digits, _ - . only; max 128 chars)"
        )
    tags = data.get("tags")
    if tags is not None and (
        not isinstance(tags, list) or any(not isinstance(t, str) for t in tags)
    ):
        errors.append(f"capability[{index}] tags must be a list of strings")
    for schema_field in ("input_schema", "output_schema"):
        if schema_field in data and not isinstance(data[schema_field], dict):
            errors.append(f"capability[{index}] {schema_field} must be a JSON-Schema object")
        elif isinstance(data.get(schema_field), dict) and data[schema_field]:
            schema = data[schema_field]
            if not any(key in schema for key in ("type", "$ref", "properties", "oneOf", "anyOf", "allOf", "enum")):
                errors.append(
                    f"capability[{index}] {schema_field} does not look like JSON Schema "
                    "(expected one of: type/$ref/properties/oneOf/anyOf/allOf/enum)"
                )
    return errors


def validate_manifest(man: Any) -> list[str]:
    """Conformance errors for a manifest (empty list = conformant)."""
    data = man.to_dict() if isinstance(man, Manifest) else man
    if not isinstance(data, dict):
        return ["manifest must be an object"]
    errors = []
    if not data.get("product"):
        errors.append("manifest missing product")
    schema_version = data.get("schema_version")
    if not schema_version:
        errors.append("manifest missing schema_version")
    elif str(schema_version) != MANIFEST_SCHEMA_VERSION:
        errors.append(
            f"unknown manifest schema_version: {schema_version!r} "
            f"(this keturah speaks {MANIFEST_SCHEMA_VERSION})"
        )
    caps = data.get("capabilities")
    if not isinstance(caps, list):
        errors.append("manifest capabilities must be a list")
    else:
        seen: set[str] = set()
        for index, cap in enumerate(caps):
            errors.extend(validate_capability(cap, index=index))
            name = (cap.to_dict() if isinstance(cap, Capability) else cap).get("name")
            if name and name in seen:
                errors.append(f"duplicate capability name: {name}")
            if name:
                seen.add(name)
    return errors


# Executable fixture — a known-conformant manifest.
CANONICAL_MANIFEST: dict[str, Any] = {
    "product": "example",
    "version": "1.0.0",
    "description": "An example product.",
    "schema_version": MANIFEST_SCHEMA_VERSION,
    "capabilities": [
        {
            "name": "ask",
            "description": "Answer a question over the product's memory.",
            "kind": "tool",
            "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
            "output_schema": {"type": "object", "properties": {"answer": {"type": "string"}}},
            "tags": ["qa"],
        }
    ],
}
