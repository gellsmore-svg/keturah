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


# --- layered confidence: adopted from deborah.contracts ---------------------


def test_confidence_decomposes_by_dimension():
    """One number cannot say *what* you are confident in. A result can be
    well-evidenced and badly reasoned, or vice versa."""
    from keturah import Confidence, CONFIDENCE_DIMENSIONS

    c = Confidence(evidence="high", inference="low")
    assert c.evidence == "high" and c.inference == "low"
    assert c.execution == "unassessed"  # not knowing is its own state
    assert set(c.to_dict()) == set(CONFIDENCE_DIMENSIONS)


def test_legacy_float_derives_a_usable_decomposition():
    """Producers that only set the scalar still get bands — a bare float
    genuinely carries no per-dimension information, so it maps to all three."""
    assert SpecialistResult(confidence=0.85).confidence_layered().evidence == "high"
    assert SpecialistResult(confidence=0.5).confidence_layered().inference == "medium"
    assert SpecialistResult(confidence=0.1).confidence_layered().execution == "low"
    assert SpecialistResult(confidence=0.0).confidence_layered().evidence == "unassessed"


def test_explicit_bands_win_over_the_scalar():
    res = SpecialistResult(confidence=0.9, confidence_bands={"evidence": "low"})
    layered = res.confidence_layered()
    assert layered.evidence == "low"          # the decomposition is authoritative
    assert res.confidence == 0.9              # scalar preserved for old callers


def test_scalar_is_never_inferred_back_from_bands():
    """Deriving a number from ordinals would manufacture the precision this
    model exists to avoid."""
    res = SpecialistResult(confidence_bands={"evidence": "high", "inference": "high"})
    assert res.confidence == 0.0              # untouched, not back-computed


def test_unknown_band_degrades_rather_than_raising():
    from keturah import normalise_confidence

    assert normalise_confidence({"evidence": "vibes"}).evidence == "unassessed"


def test_band_thresholds_match_the_rest_of_the_estate():
    """milcah.deborah.confidence_band must agree — two mappings would make the
    same result read differently depending on which product converted it."""
    from keturah import band_for

    assert band_for(0.7) == "high" and band_for(0.699) == "medium"
    assert band_for(0.4) == "medium" and band_for(0.399) == "low"
    assert band_for(0.0) == "unassessed" and band_for(None) == "unassessed"
    # Review L1: non-finite must not map to high
    assert band_for(float("inf")) == "unassessed"
    assert band_for(float("-inf")) == "unassessed"
    assert band_for(float("nan")) == "unassessed"


def test_validator_rejects_a_bad_band_and_unknown_dimension():
    bad_band = SpecialistResult(confidence_bands={"inference": "nonsense"})
    assert any("confidence_bands.inference" in e for e in validate_result(bad_band))
    bad_dim = SpecialistResult(confidence_bands={"vibes": "high"})
    assert any("unknown confidence dimension" in e for e in validate_result(bad_dim))


def test_is_assessed_distinguishes_unset_from_low():
    from keturah import Confidence

    assert Confidence().is_assessed is False
    assert Confidence(evidence="low").is_assessed is True
