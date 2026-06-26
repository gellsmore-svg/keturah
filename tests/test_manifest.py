from keturah import (
    CANONICAL_MANIFEST,
    Capability,
    Manifest,
    capability,
    manifest,
    validate_manifest,
)


def test_canonical_manifest_conforms():
    assert validate_manifest(CANONICAL_MANIFEST) == []


def test_build_and_serialize():
    m = manifest(
        "tirzah",
        version="1.3.0",
        capabilities=[
            capability(
                "ask",
                "Answer a question over memory.",
                input_schema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
            ),
            capability("docs", "Read the API docs.", kind="resource"),
        ],
    )
    assert validate_manifest(m) == []
    assert m.names() == ["ask", "docs"]


def test_to_mcp_only_includes_tools():
    m = manifest(
        "p",
        capabilities=[
            capability("t", "a tool", kind="tool", input_schema={"type": "object"}),
            capability("r", "a resource", kind="resource"),
        ],
    )
    mcp = m.to_mcp()
    assert [t["name"] for t in mcp["tools"]] == ["t"]  # resources are not MCP tools
    assert mcp["tools"][0]["inputSchema"] == {"type": "object"}
    # a tool with no schema still gets a valid object schema
    bare = manifest("p", capabilities=[capability("t2", "d")])
    assert bare.to_mcp()["tools"][0]["inputSchema"] == {"type": "object"}


def test_validation_catches_problems():
    errors = validate_manifest(
        Manifest(
            product="",
            capabilities=[
                Capability(name="", description="", kind="wat"),
                Capability(name="dup", description="d"),
                Capability(name="dup", description="d2"),
            ],
        )
    )
    assert any("missing product" in e for e in errors)
    assert any("missing name" in e for e in errors)
    assert any("invalid kind" in e for e in errors)
    assert any("duplicate capability name: dup" in e for e in errors)
