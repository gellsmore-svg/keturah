"""The shared capability-call envelope.

Extracted from two hand-maintained copies (tirzah.coherence, milcah.contract)
that had already drifted — the consumer carried error/error_type, the provider
did not.
"""

from keturah import (
    SPECIALIST_MODES,
    TERMINAL_REASONS,
    Evidence,
    SpecialistRequest,
    SpecialistResult,
    normalise_evidence,
    validate_request,
    validate_result,
)


def test_request_round_trips():
    req = SpecialistRequest(query="is this coherent?", context="ctx", max_iterations=2)
    assert validate_request(req) == []
    assert req.to_dict()["max_iterations"] == 2


def test_request_rejects_empty_query_and_unknown_mode():
    assert "query must be non-empty" in validate_request(SpecialistRequest(query=""))
    errors = validate_request(SpecialistRequest(query="q", mode="vibes"))
    assert any("invalid mode" in e for e in errors)


def test_result_carries_error_fields_both_sides_now_share():
    """The drift this extraction resolves: only the consumer had these."""
    res = SpecialistResult(error="adapter timeout", error_type="TimeoutError")
    assert validate_result(res) == []
    assert res.to_dict()["error_type"] == "TimeoutError"


def test_result_rejects_out_of_range_confidence_and_unknown_terminal_reason():
    assert any("confidence" in e for e in validate_result(SpecialistResult(confidence=1.4)))
    assert any(
        "terminal_reason" in e
        for e in validate_result(SpecialistResult(terminal_reason="gave_up"))
    )


# --- evidence: the part that makes "evidence-backed" checkable --------------


def test_bare_strings_are_accepted_and_upgraded():
    """No producer has to change first — the pre-existing shape still works."""
    items = normalise_evidence(["the argument assumes X", "see the third para"])
    assert [i.kind for i in items] == ["note", "note"]
    assert items[0].note == "the argument assumes X"


def test_anchored_evidence_is_distinguishable_from_prose():
    """A result can carry reasoning about its conclusion and still not be
    anchored to anything. That distinction is the whole point."""
    prose = SpecialistResult(evidence=["it seems internally consistent"])
    anchored = SpecialistResult(
        evidence=[{"kind": "cited_span", "ref": "manuscript#p12", "note": "defines the term"}]
    )
    assert prose.is_anchored is False
    assert anchored.is_anchored is True


def test_mixed_shapes_normalise_together():
    res = SpecialistResult(
        evidence=[
            "loose note",
            {"kind": "source_ref", "ref": "doc-7"},
            Evidence(kind="counterexample", ref="case-3", note="fails when empty"),
        ]
    )
    items = res.evidence_items()
    assert [i.kind for i in items] == ["note", "source_ref", "counterexample"]
    assert res.is_anchored is True


def test_unknown_evidence_kind_degrades_rather_than_raising():
    """A producer using a vocabulary we don't know yet should degrade."""
    items = normalise_evidence([{"kind": "telepathy", "ref": "r1"}])
    assert items[0].kind == "note"
    assert items[0].ref == "r1"


def test_empty_and_none_evidence_are_safe():
    assert normalise_evidence(None) == []
    assert normalise_evidence([]) == []
    assert SpecialistResult().is_anchored is False


def test_vocabularies_are_shared_not_redefined():
    """Both sides must agree on these; that is why they live here."""
    assert "coherence" in SPECIALIST_MODES and "research" in SPECIALIST_MODES
    assert "max_iterations" in TERMINAL_REASONS  # bounded loops are first-class
