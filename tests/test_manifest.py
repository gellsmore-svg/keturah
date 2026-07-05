from keturah import (
    validate_capability,
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


def test_output_schema_projects_to_mcp():
    cap = capability("t", "d", output_schema={"type": "object", "properties": {"ok": {"type": "boolean"}}})
    tool = cap.to_mcp_tool()
    assert tool["outputSchema"]["properties"]["ok"]["type"] == "boolean"
    assert "outputSchema" not in capability("t2", "d").to_mcp_tool()


def test_schema_version_is_validated():
    man = manifest("p", capabilities=[capability("t", "d")]).to_dict()
    assert validate_manifest(man) == []
    man["schema_version"] = "9.9"
    assert any("schema_version" in e for e in validate_manifest(man))
    del man["schema_version"]
    assert any("missing schema_version" in e for e in validate_manifest(man))


def test_capability_validation_strictness():
    bad_name = capability("has spaces!", "d").to_dict()
    assert any("MCP-safe" in e for e in validate_capability(bad_name))
    bad_tags = capability("t", "d", tags=["ok"]).to_dict()
    bad_tags["tags"] = ["ok", 3]
    assert any("tags" in e for e in validate_capability(bad_tags))
    junk_schema = capability("t", "d", input_schema={"whatever": 1}).to_dict()
    assert any("JSON Schema" in e for e in validate_capability(junk_schema))


def test_prompt_and_resource_accessors():
    man = manifest("p", capabilities=[
        capability("t", "d"),
        capability("r", "d", kind="resource"),
        capability("pr", "d", kind="prompt"),
    ])
    assert [c.name for c in man.resources()] == ["r"]
    assert [c.name for c in man.prompts()] == ["pr"]
    assert [t["name"] for t in man.to_mcp()["tools"]] == ["t"]
