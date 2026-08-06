"""The shared capability-call envelope: request, result, evidence.

Keturah already describes *what* a product can do (``Capability``). This
describes the shape of *one call* to such a capability, and what comes back.

It exists because the same contract had been written twice by hand — the
consumer side in ``tirzah.coherence`` and the provider side in
``milcah.contract`` — and had already drifted: the consumer carried ``error``
and ``error_type``, the provider did not. Two hand-maintained copies of one
contract is exactly the seam a shared library is for.

**Why here.** Keturah is a hard dependency of both sides already, is
dependency-free itself, and is the family's contract layer. Putting the
envelope anywhere else would add a dependency edge to carry a definition.

**The evidence type is the new part.** Both sides returned
``evidence: list[str]`` — free text, so "the result must be evidence-backed"
could be asserted but never *checked*. :class:`Evidence` gives a ``kind`` and a
``ref``, so a validator can ask whether evidence actually points at anything.
:func:`normalise_evidence` accepts the existing bare strings and upgrades them,
so no producer has to change first.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

ENVELOPE_VERSION = "1"

# A specialist call is either a coherence pressure-test or counter-framework
# research. Held here so provider and consumer cannot disagree about the set.
SPECIALIST_MODES = frozenset({"coherence", "research"})

# Why a bounded loop stopped — so the caller can reason about completeness
# rather than assuming a returned result means a finished one.
TERMINAL_REASONS = frozenset(
    {"converged", "max_iterations", "no_objections", "insufficient_evidence", "blocked"}
)

# What a piece of evidence *is*. Deliberately small: enough to check that a
# claim points at something, not an attempt to model epistemology.
EVIDENCE_KINDS = frozenset(
    {
        "cited_span",     # a span of a supplied source
        "source_ref",     # an external or stored document
        "counterexample",  # a case that contradicts a claim
        "tool_output",    # something a tool returned
        "note",           # unstructured; what a bare string upgrades to
    }
)

# Only genuinely required fields — everything else carries a default, so its
# absence from a dict is not an error. Matches the semantics the consumer side
# has always enforced; tightening it here would silently break callers.
REQUEST_FIELDS: tuple[str, ...] = ("query",)
RESULT_FIELDS: tuple[str, ...] = (
    "claims",
    "objections",
    "evidence",
    "citations",
    "confidence",
    "terminal_reason",
    "trace_metadata",
    "error",
    "error_type",
)


@dataclass
class Evidence:
    """One piece of support for a claim.

    ``kind`` and ``ref`` are the checkable part; ``note`` is free text. A bare
    string becomes ``kind="note"`` with no ref — still recorded, but a
    validator can tell the difference between evidence that points somewhere
    and evidence that merely asserts.
    """

    kind: str = "note"
    ref: str | None = None
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def is_anchored(self) -> bool:
        """True when this evidence points at something identifiable."""
        return bool(self.ref) and self.kind != "note"


def normalise_evidence(items: Any) -> list[Evidence]:
    """Coerce whatever a producer supplied into :class:`Evidence`.

    Accepts bare strings (the pre-existing shape), dicts, and Evidence
    instances, in any mixture. Unknown ``kind`` values fall back to ``note``
    rather than raising — a producer using a vocabulary we do not know yet
    should degrade, not fail.
    """
    if items is None:
        return []
    if isinstance(items, (str, bytes)) or not hasattr(items, "__iter__"):
        items = [items]
    out: list[Evidence] = []
    for item in items:
        if isinstance(item, Evidence):
            out.append(item)
        elif isinstance(item, dict):
            kind = str(item.get("kind") or "note")
            out.append(
                Evidence(
                    kind=kind if kind in EVIDENCE_KINDS else "note",
                    ref=item.get("ref"),
                    note=str(item.get("note") or ""),
                )
            )
        else:
            out.append(Evidence(kind="note", ref=None, note=str(item)))
    return out


@dataclass
class SpecialistRequest:
    """What a caller sends a specialist capability."""

    query: str
    mode: str = "coherence"
    context: str = ""
    max_iterations: int = 3
    trace_id: str | None = None
    session_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SpecialistResult:
    """What a specialist capability returns: findings plus their support.

    ``error``/``error_type`` are part of the shared shape. They were present on
    the consumer side only, which meant a provider-side result could not
    represent its own failure without the caller inventing one.
    """

    claims: list[str] = field(default_factory=list)
    objections: list[str] = field(default_factory=list)
    evidence: list[Any] = field(default_factory=list)  # str | dict | Evidence
    citations: list[str] = field(default_factory=list)
    confidence: float = 0.0
    terminal_reason: str = "converged"
    trace_metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    error_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def evidence_items(self) -> list[Evidence]:
        """The evidence as typed items, whatever shape the producer used."""
        return normalise_evidence(self.evidence)

    @property
    def is_anchored(self) -> bool:
        """True when at least one piece of evidence points at something.

        This is what makes an ``evidence-backed`` validator possible: a result
        can carry prose about its reasoning and still not be anchored.
        """
        return any(item.is_anchored for item in self.evidence_items())


def validate_request(request: Any) -> list[str]:
    """Conformance errors for a request (empty list = conformant)."""
    data = request.to_dict() if isinstance(request, SpecialistRequest) else request
    if not isinstance(data, dict):
        return ["request must be an object"]
    errors = [f"missing request field: {f}" for f in REQUEST_FIELDS if f not in data]
    if not data.get("query"):
        errors.append("query must be non-empty")
    mode = data.get("mode", "coherence")
    if mode not in SPECIALIST_MODES:
        errors.append(f"invalid mode: {mode!r} (allowed: {sorted(SPECIALIST_MODES)})")
    return errors


def validate_result(result: Any) -> list[str]:
    """Conformance errors for a result (empty list = conformant)."""
    data = result.to_dict() if isinstance(result, SpecialistResult) else result
    if not isinstance(data, dict):
        return ["result must be an object"]
    errors = [f"missing result field: {f}" for f in RESULT_FIELDS if f not in data]
    for list_field in ("claims", "objections", "evidence", "citations"):
        if list_field in data and not isinstance(data[list_field], list):
            errors.append(f"{list_field} must be a list")
    confidence = data.get("confidence")
    if confidence is not None and not (
        isinstance(confidence, (int, float)) and 0.0 <= float(confidence) <= 1.0
    ):
        errors.append("confidence must be a number in [0, 1]")
    reason = data.get("terminal_reason")
    if reason is not None and reason not in TERMINAL_REASONS:
        errors.append(
            f"invalid terminal_reason: {reason!r} (allowed: {sorted(TERMINAL_REASONS)})"
        )
    return errors
