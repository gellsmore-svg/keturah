from keturah import Registry, capability, manifest


def _milcah():
    return manifest("milcah", capabilities=[
        capability("coherence_check", "pressure-test coherence", tags=["specialist", "planner"]),
    ])


def _tirzah():
    return manifest("tirzah", capabilities=[
        capability("ask", "answer a question", input_schema={"type": "object"}),
        capability("coherence_check", "broker to milcah", tags=["planner"]),  # same name, different product
        capability("docs", "read docs", kind="resource"),
    ])


def test_registry_aggregates_and_queries():
    reg = Registry([_tirzah(), _milcah()])
    assert reg.products() == ["tirzah", "milcah"]
    # tools across products (resources excluded)
    assert sorted(name for _, name in ((p, c.name) for p, c in reg.tools())) == [
        "ask", "coherence_check", "coherence_check"
    ]
    # tag query spans products
    planners = [(p, c.name) for p, c in reg.with_tag("planner")]
    assert ("tirzah", "coherence_check") in planners and ("milcah", "coherence_check") in planners
    # find, optionally scoped to a product
    assert reg.find("ask")[0] == "tirzah"
    assert reg.find("coherence_check", product="milcah")[0] == "milcah"
    assert reg.find("nope") is None


def test_registry_federates_resources_and_prompts():
    """Registry mirrors Manifest.resources()/prompts() across products (#13)."""
    reg = Registry([
        _tirzah(),
        manifest("deborah", capabilities=[
            capability("spec", "the process spec", kind="resource"),
            capability("review", "review prompt", kind="prompt"),
        ]),
    ])
    assert [(p, c.name) for p, c in reg.resources()] == [("tirzah", "docs"), ("deborah", "spec")]
    assert [(p, c.name) for p, c in reg.prompts()] == [("deborah", "review")]
    # resources/prompts stay out of the MCP tools projection
    assert "spec" not in [t["name"] for t in reg.to_mcp(namespaced=False)["tools"]]


def test_registry_mcp_namespaces_tool_names():
    reg = Registry([_tirzah(), _milcah()])
    names = [t["name"] for t in reg.to_mcp()["tools"]]
    # same tool name in two products stays unique once namespaced
    assert "tirzah.coherence_check" in names and "milcah.coherence_check" in names
    assert "tirzah.ask" in names
    # un-namespaced view keeps raw names
    raw = [t["name"] for t in reg.to_mcp(namespaced=False)["tools"]]
    assert raw.count("coherence_check") == 2


def test_empty_registry():
    reg = Registry()
    assert reg.products() == [] and reg.to_mcp()["tools"] == []
    reg.add(_milcah())
    assert reg.products() == ["milcah"]


def test_find_accepts_namespaced_names_and_find_all():
    reg = Registry([
        manifest("tirzah", capabilities=[capability("coherence_check", "d")]),
        manifest("milcah", capabilities=[capability("coherence_check", "d")]),
    ])
    prod, _ = reg.find("milcah.coherence_check")
    assert prod == "milcah"
    assert [p for p, _ in reg.find_all("coherence_check")] == ["tirzah", "milcah"]


def test_find_all_accepts_namespaced_names():
    """find_all must parse product.tool the same way find does (#10)."""
    reg = Registry([
        manifest("tirzah", capabilities=[capability("coherence_check", "d")]),
        manifest("milcah", capabilities=[capability("coherence_check", "d")]),
    ])
    assert [p for p, _ in reg.find_all("milcah.coherence_check")] == ["milcah"]
    assert [p for p, _ in reg.find_all("coherence_check", product="tirzah")] == ["tirzah"]
    # unknown product prefix matches nothing rather than falling back to all
    assert reg.find_all("nope.coherence_check") == []


def test_namespace_parsing_does_not_break_dotted_capability_names():
    """A capability whose own name contains a dot still resolves by that name."""
    reg = Registry([manifest("tirzah", capabilities=[capability("memory.ask", "d")])])
    assert reg.find("memory.ask")[0] == "tirzah"  # 'memory' is not a product
    assert [p for p, _ in reg.find_all("memory.ask")] == ["tirzah"]
    # and the fully-qualified form still works
    assert [p for p, _ in reg.find_all("tirzah.memory.ask")] == ["tirzah"]
