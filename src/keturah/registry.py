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

    def resources(self) -> list[tuple[str, Capability]]:
        """Federated :meth:`Manifest.resources` — readable interfaces, all products."""
        return [(p, c) for p, c in self.capabilities() if c.kind == "resource"]

    def prompts(self) -> list[tuple[str, Capability]]:
        """Federated :meth:`Manifest.prompts` — prompt templates, all products."""
        return [(p, c) for p, c in self.capabilities() if c.kind == "prompt"]

    def with_tag(self, tag: str) -> list[tuple[str, Capability]]:
        return [(p, c) for p, c in self.capabilities() if tag in c.tags]

    def _resolve(self, name: str, product: str | None) -> tuple[str, str | None]:
        """Split a namespaced ``product.tool`` into its parts.

        Only splits when the prefix is a registered product, so a capability
        whose own name contains a dot still resolves. An explicit ``product``
        argument always wins.
        """
        if product is None and "." in name:
            candidate_product, _, candidate_name = name.partition(".")
            if candidate_product in self.products():
                return candidate_name, candidate_product
        return name, product

    def find(self, name: str, *, product: str | None = None) -> tuple[str, Capability] | None:
        """(product, capability) for ``name``.

        Accepts the namespaced form ``product.tool`` (the same names to_mcp()
        emits), which disambiguates when several products expose the same tool
        name. An unqualified name returns the first match in registration
        order — use ``find_all`` when you need every match.
        """
        name, product = self._resolve(name, product)
        for prod, cap in self.capabilities():
            if cap.name == name and (product is None or prod == product):
                return (prod, cap)
        return None

    def find_all(self, name: str, *, product: str | None = None) -> list[tuple[str, Capability]]:
        """Every (product, capability) whose name matches — the disambiguation
        surface for names shared across products.

        Accepts the same namespaced ``product.tool`` form as :meth:`find`, in
        which case at most one match can come back.
        """
        name, product = self._resolve(name, product)
        return [
            (p, c)
            for p, c in self.capabilities()
            if c.name == name and (product is None or p == product)
        ]

    def to_dict(self) -> dict[str, Any]:
        return {"products": self.products(), "manifests": [m.to_dict() for m in self._manifests]}

    def to_mcp(self, *, namespaced: bool = True) -> dict[str, Any]:
        """The union of all products' tools as an MCP ``tools/list``.

        With ``namespaced`` (default), tool names become ``product.tool`` so two
        products exposing the same tool name don't collide.

        ``namespaced=False`` raises :class:`ValueError` when the emission would
        contain duplicate tool names — MCP requires unique names in
        ``tools/list`` (review M1).
        """
        tools = []
        for product, cap in self.tools():
            tool = cap.to_mcp_tool()
            if namespaced:
                tool = {**tool, "name": f"{product}.{cap.name}"}
            tools.append(tool)
        if not namespaced:
            names = [t.get("name") for t in tools]
            dupes = sorted({n for n in names if n and names.count(n) > 1})
            if dupes:
                raise ValueError(
                    "to_mcp(namespaced=False) would emit duplicate MCP tool "
                    f"names {dupes}; use namespaced=True (default) or resolve "
                    "the collision before projecting"
                )
        return {"tools": tools}
