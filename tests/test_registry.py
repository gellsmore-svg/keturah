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
