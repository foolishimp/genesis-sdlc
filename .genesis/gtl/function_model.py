# Implements: REQ-L-GTL2-GRAPHFUNCTION
# Implements: REQ-L-GTL2-SYNTHESIS
# Implements: REQ-L-GTL2-SELECTION-BOUNDARY
# Implements: REQ-L-GTL2-IDENTITY
"""
gtl.function_model — Reusable workflow programs and structural alternatives.

GraphFunction is the primary reusable GTL compute abstraction.
RefinementBoundary declares lawful synthesis/refinement points.
CandidateFamily declares named families of lawful structural alternatives.

No external dependencies. Dataclasses + stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from gtl.graph import Graph, Node, _mint_id


@dataclass(frozen=True)
class GraphFunction:
    """
    Reusable named workflow abstraction — materializable graph template.

    template: callable (Python DSL convenience) or serializable graph-template
    reference (str). The semantic contract is "materializable graph template."

    id: opaque identity (REQ-L-GTL2-IDENTITY-001). Auto-minted.
    compare=False: structural equality ignores id (REQ-L-GTL2-IDENTITY-005).
    """
    name: str
    inputs: tuple[Node, ...] = ()
    outputs: tuple[Node, ...] = ()
    template: Callable[..., Graph] | str = ""
    effects: tuple = ()
    tags: tuple[str, ...] = ()
    id: str = field(default_factory=_mint_id, compare=False)


@dataclass(frozen=True)
class RefinementBoundary:
    """
    Explicit lawful refinement/synthesis boundary over a stable outer contract.

    Declares a point where consumer logic can produce or select an
    interface-compatible inner graph. Contains no executable selection
    or synthesis logic.

    REQ-L-GTL2-SYNTHESIS-001: declarative surface for deferred synthesis.
    REQ-L-GTL2-SYNTHESIS-002: interface and contract obligations specified.
    """
    name: str
    inputs: tuple[Node, ...] = ()
    outputs: tuple[Node, ...] = ()
    hints: dict = field(default_factory=dict)
    tags: tuple[str, ...] = ()
    id: str = field(default_factory=_mint_id, compare=False)


@dataclass(frozen=True)
class CandidateFamily:
    """
    Named family of lawful structural alternatives for one outer contract.

    Every candidate must share the declared inputs/outputs contract.
    Candidate order is preserved and publishable.
    policy_hints are visible to evaluators but do not choose a candidate.

    Fail-closed: empty candidates or contract mismatch raises at construction.

    REQ-L-GTL2-SELECTION-BOUNDARY: explicit structural alternatives.
    REQ-L-GTL2-SYNTHESIS-005: multiple lawful candidates without deciding.
    """
    name: str
    inputs: tuple[Node, ...] = ()
    outputs: tuple[Node, ...] = ()
    candidates: tuple[GraphFunction, ...] = ()
    policy_hints: dict = field(default_factory=dict)
    tags: tuple[str, ...] = ()
    id: str = field(default_factory=_mint_id, compare=False)

    def __post_init__(self):
        if not self.candidates:
            raise ValueError(
                f"CandidateFamily({self.name!r}): empty candidates"
            )
        family_in = {n.name for n in self.inputs}
        family_out = {n.name for n in self.outputs}
        for c in self.candidates:
            c_in = {n.name for n in c.inputs}
            c_out = {n.name for n in c.outputs}
            if c_in != family_in or c_out != family_out:
                raise ValueError(
                    f"CandidateFamily({self.name!r}): candidate {c.name!r} "
                    f"contract ({sorted(c_in)}->{sorted(c_out)}) does not match "
                    f"family contract ({sorted(family_in)}->{sorted(family_out)})"
                )
