"""Registry — aggregate many product manifests into one queryable surface.

A federated view over the family: collect each product's :class:`Manifest` and ask
cross-product questions — every tool, find a capability by name, everything with a
tag — and project the union onto MCP (tool names namespaced ``product.tool`` so they
stay unique across products). Pure-stdlib; the caller decides which manifests to add
(direct import, HTTP ``/api/capabilities``, or a cached index).
"""

from __future__ import annotations

from typing import Any, Iterable

from keturah.manifest import Capability, Manifest


class Registry:
    def __init__(self, manifests: Iterable[Manifest] = ()) -> None:
        self._manifests: list[Manifest] = []
        for man in manifests:
            self.add(man)

    def add(self, manifest: Manifest) -> "Registry":
        self._manifests.append(manifest)
        return self

    @property
    def manifests(self) -> list[Manifest]:
        return list(self._manifests)

    def products(self) -> list[str]:
        return [m.product for m in self._manifests]

    def capabilities(self) -> list[tuple[str, Capability]]:
        """(product, capability) for every capability across all manifests."""
        return [(m.product, cap) for m in self._manifests for cap in m.capabilities]

    def tools(self) -> list[tuple[str, Capability]]:
        return [(p, c) for p, c in self.capabilities() if c.kind == "tool"]

    def with_tag(self, tag: str) -> list[tuple[str, Capability]]:
        return [(p, c) for p, c in self.capabilities() if tag in c.tags]

    def find(self, name: str, *, product: str | None = None) -> tuple[str, Capability] | None:
        """First (product, capability) matching ``name`` (optionally within a product)."""
        for prod, cap in self.capabilities():
            if cap.name == name and (product is None or prod == product):
                return (prod, cap)
        return None

    def to_dict(self) -> dict[str, Any]:
        return {"products": self.products(), "manifests": [m.to_dict() for m in self._manifests]}

    def to_mcp(self, *, namespaced: bool = True) -> dict[str, Any]:
        """The union of all products' tools as an MCP ``tools/list``.

        With ``namespaced`` (default), tool names become ``product.tool`` so two
        products exposing the same tool name don't collide.
        """
        tools = []
        for product, cap in self.tools():
            tool = cap.to_mcp_tool()
            if namespaced:
                tool = {**tool, "name": f"{product}.{cap.name}"}
            tools.append(tool)
        return {"tools": tools}
