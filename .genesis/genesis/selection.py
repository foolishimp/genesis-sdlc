# Implements: REQ-R-ABG2-SELECTION-APPLICATION
"""
genesis.selection — Candidate enumeration and validation.

Pure kernel module — returns SelectionDecision values.
Event emission delegated to interpret.apply_selection()
(per GTL_2_MODULE_DESIGN §4.4).

No side effects, no events, no I/O. Pure functions over V2 types.
"""
from __future__ import annotations

from dataclasses import dataclass

from gtl.graph import GraphVector
from gtl.function_model import GraphFunction, RefinementBoundary, CandidateFamily
from gtl.module_model import Module


@dataclass(frozen=True)
class SelectionDecision:
    """Replayable record of a workflow selection."""
    contract_id: str
    work_key: str
    graph_function: str
    selected_by: str
    selection_mode: str
    rationale: str = ""


def _vector_source_names(vector: GraphVector) -> set[str]:
    """Extract source node names from a vector (handles tuple sources)."""
    if isinstance(vector.source, tuple):
        return {n.name for n in vector.source}
    elif vector.source is not None:
        return {vector.source.name}
    return set()


def _vector_contract(vector: GraphVector) -> tuple[tuple[str, ...], tuple[str, ...]]:
    source = vector.source if isinstance(vector.source, tuple) else (vector.source,)
    return tuple(n.name for n in source), (vector.target.name,) if vector.target else ()


def _graph_function_contract(function: GraphFunction) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return (
        tuple(node.name for node in function.inputs),
        tuple(node.name for node in function.outputs),
    )


def validate_module_selection_surface(module: Module) -> None:
    """Fail closed when a module hides structural alternatives outside CandidateFamily.

    If a GraphFunction matches the outer contract of a live GraphVector, that
    alternative must be published through Module.candidate_families. The engine
    must not infer selection topology from raw graph_functions.
    """
    family_contracts = {
        (
            tuple(node.name for node in family.inputs),
            tuple(node.name for node in family.outputs),
        )
        for family in module.candidate_families
    }

    vector_contracts = {
        _vector_contract(vector)
        for graph in module.graphs
        for vector in graph.vectors
    }

    hidden_contracts = {
        _graph_function_contract(function)
        for function in module.graph_functions
        if _graph_function_contract(function) in vector_contracts
        and _graph_function_contract(function) not in family_contracts
    }
    if hidden_contracts:
        rendered = ", ".join(
            f"{list(inputs)}->{list(outputs)}"
            for inputs, outputs in sorted(hidden_contracts)
        )
        raise ValueError(
            "validate_module_selection_surface(): graph_functions matching live "
            f"vector contracts must be published via Module.candidate_families; "
            f"hidden contracts: {rendered}"
        )


def resolve_refinement_boundary(
    module: Module,
    vector_id: str,
) -> RefinementBoundary | None:
    """Resolve the published refinement boundary for a live vector."""
    target_vec = None
    for graph in module.graphs:
        for vec in graph.vectors:
            if vec.id == vector_id:
                target_vec = vec
                break
        if target_vec is not None:
            break

    if target_vec is None:
        return None

    vec_inputs, vec_outputs = _vector_contract(target_vec)
    declared = tuple(
        boundary
        for boundary in module.refinement_boundaries
        if boundary.name == target_vec.name
        and tuple(n.name for n in boundary.inputs) == vec_inputs
        and tuple(n.name for n in boundary.outputs) == vec_outputs
    )
    if len(declared) > 1:
        raise ValueError(
            f"resolve_refinement_boundary(): ambiguous published refinement boundaries "
            f"for vector {vector_id!r}"
        )
    return declared[0] if declared else None


def validate_module_traversal_surface(module: Module) -> None:
    """Fail closed when a live vector has no published traversal target."""
    missing: list[str] = []
    for graph in module.graphs:
        for vector in graph.vectors:
            if (
                resolve_refinement_boundary(module, vector.id) is None
                and resolve_candidate_family(module, vector.id) is None
            ):
                missing.append(vector.name)
    if missing:
        raise ValueError(
            "validate_module_traversal_surface(): every live graph vector must publish "
            f"a RefinementBoundary or CandidateFamily; missing: {sorted(missing)}"
        )


def resolve_candidate_family(
    module: Module,
    vector_id: str,
) -> CandidateFamily | None:
    """Resolve the canonical candidate family for a vector.

    Returns one explicitly declared Module.candidate_families match, or None.
    Fails closed on ambiguous declared families.
    """
    target_vec = None
    for graph in module.graphs:
        for vec in graph.vectors:
            if vec.id == vector_id:
                target_vec = vec
                break
        if target_vec is not None:
            break

    if target_vec is None:
        return None

    vec_inputs, vec_outputs = _vector_contract(target_vec)
    declared = tuple(
        family
        for family in module.candidate_families
        if tuple(n.name for n in family.inputs) == vec_inputs
        and tuple(n.name for n in family.outputs) == vec_outputs
    )
    if len(declared) > 1:
        raise ValueError(
            f"resolve_candidate_family(): ambiguous declared candidate families "
            f"for vector {vector_id!r}"
        )
    if declared:
        return declared[0]
    return None


def validate_selection(
    decision: SelectionDecision,
    candidate: GraphFunction,
    vector: GraphVector,
) -> bool:
    """
    Validate that a SelectionDecision is interface-compatible.

    Checks:
    - decision.graph_function matches candidate.name
    - decision.contract_id matches vector.id (REQ-L-GTL2-IDENTITY-006)
    - candidate interface satisfies vector (same rules as enumerate_candidates)
    """
    if decision.graph_function != candidate.name:
        return False
    if decision.contract_id != vector.id:
        return False

    vec_source_names = _vector_source_names(vector)
    vec_target_name = vector.target.name if vector.target else ""

    gf_input_names = {n.name for n in candidate.inputs}
    gf_output_names = {n.name for n in candidate.outputs}

    return gf_input_names <= vec_source_names and vec_target_name in gf_output_names


# ── V2 CandidateFamily-based selection ───────────────────────────────────────


def enumerate_candidates(
    family: CandidateFamily,
) -> tuple[GraphFunction, ...]:
    """Enumerate lawful candidates from one explicit candidate family."""
    return family.candidates


def accept_selection(
    family: CandidateFamily,
    candidate: GraphFunction,
    *,
    contract_id: str,
    work_key: str,
    selected_by: str,
    selection_mode: str,
    rationale: str = "",
) -> SelectionDecision:
    """Validate that candidate belongs to family and satisfies the family contract.

    REQ-R-ABG2-SELECTION-APPLICATION-003: validate interface compatibility.
    REQ-R-ABG2-SELECTION-APPLICATION-004: validate family membership.
    """
    # Membership check — by identity
    if not any(c.id == candidate.id for c in family.candidates):
        raise ValueError(
            f"accept_selection(): candidate {candidate.name!r} not in family "
            f"{family.name!r}"
        )

    # Interface check — candidate must satisfy family contract
    family_in = {n.name for n in family.inputs}
    family_out = {n.name for n in family.outputs}
    cand_in = {n.name for n in candidate.inputs}
    cand_out = {n.name for n in candidate.outputs}
    if cand_in != family_in or cand_out != family_out:
        raise ValueError(
            f"accept_selection(): candidate {candidate.name!r} interface "
            f"({sorted(cand_in)}->{sorted(cand_out)}) does not match family contract "
            f"({sorted(family_in)}->{sorted(family_out)})"
        )

    return SelectionDecision(
        contract_id=contract_id,
        work_key=work_key,
        graph_function=candidate.name,
        selected_by=selected_by,
        selection_mode=selection_mode,
        rationale=rationale,
    )
