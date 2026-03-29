# Implements: REQ-L-GTL2-COMPOSE
# Implements: REQ-L-GTL2-SUBSTITUTE
# Implements: REQ-L-GTL2-RECURSE
# Implements: REQ-L-GTL2-HOF
# Implements: REQ-L-GTL2-SYNTHESIS
# Implements: REQ-L-GTL2-SELECTION-BOUNDARY
# Implements: REQ-L-GTL2-IDENTITY
"""
gtl.algebra — Graph algebra: composition, substitution, identity,
              higher-order operators, and DSL sugar.

Pure functions over GTL graph types. No engine/runtime dependency.
"""
from __future__ import annotations

from gtl.graph import Graph, Node, GraphVector
from gtl.function_model import GraphFunction, RefinementBoundary, CandidateFamily
from gtl.operator_model import Evaluator, Rule


def same_object(a, b) -> bool:
    """Identity equality — same .id (REQ-L-GTL2-IDENTITY-005)."""
    return a.id == b.id


def _stable_union(*tuples: tuple) -> tuple:
    """Stable left-to-right union preserving first occurrence order."""
    seen = []
    for values in tuples:
        for value in values:
            if value not in seen:
                seen.append(value)
    return tuple(seen)


def _is_vector_boundary(node: Node) -> bool:
    """True when a node explicitly declares a Vector[...] representation."""
    schema = node.schema
    return isinstance(schema, str) and schema.strip().startswith("Vector[") and schema.strip().endswith("]")


def edge(source: Node, target: Node, *, operators=(), evaluators=(), **kw) -> Graph:
    """Construct a minimal one-vector graph (DSL sugar)."""
    vector = GraphVector(
        name=f"{source.name}→{target.name}",
        source=source,
        target=target,
        operators=operators,
        evaluators=evaluators,
        **kw,
    )
    return Graph(
        name=f"{source.name}→{target.name}",
        inputs=(source,),
        outputs=(target,),
        nodes=(source, target),
        vectors=(vector,),
    )


def _materialize(gf: GraphFunction) -> Graph:
    """Materialize a GraphFunction's template into a Graph."""
    if callable(gf.template):
        return gf.template()
    raise ValueError(f"Cannot materialize non-callable template: {gf.template!r}")


# ── Composition ──────────────────────────────────────────────────────────────


def _compose_pair(f: GraphFunction, g: GraphFunction) -> GraphFunction:
    """Binary composition: f;g where f.outputs satisfy g.inputs."""
    f_output_names = {n.name for n in f.outputs}
    g_input_names = {n.name for n in g.inputs}

    missing = g_input_names - f_output_names
    if missing:
        raise ValueError(
            f"compose({f.name}, {g.name}): g.inputs not satisfied by f.outputs — "
            f"missing: {sorted(missing)}"
        )

    g_output_names = {n.name for n in g.outputs}
    pass_throughs = g_input_names & g_output_names
    duplicates = (f_output_names & g_output_names) - pass_throughs
    if duplicates:
        raise ValueError(
            f"compose({f.name}, {g.name}): duplicate output names: {sorted(duplicates)}"
        )

    if callable(f.template) and callable(g.template):
        _f, _g = f, g

        def _composed_template() -> Graph:
            fg = _materialize(_f)
            gg = _materialize(_g)
            node_map = {n.name: n for n in fg.nodes}
            for n in gg.nodes:
                if n.name not in node_map:
                    node_map[n.name] = n
            all_vectors = fg.vectors + gg.vectors
            ctx_map = {c.name: c for c in fg.contexts}
            for c in gg.contexts:
                if c.name not in ctx_map:
                    ctx_map[c.name] = c
            return Graph(
                name=f"{_f.name};{_g.name}",
                inputs=fg.inputs,
                outputs=gg.outputs,
                nodes=tuple(node_map.values()),
                vectors=tuple(all_vectors),
                contexts=tuple(ctx_map.values()),
            )

        template = _composed_template
    else:
        template = f"{f.name};{g.name}"

    return GraphFunction(
        name=f"{f.name};{g.name}",
        inputs=f.inputs,
        outputs=g.outputs,
        template=template,
        effects=_stable_union(f.effects, g.effects),
        tags=_stable_union(f.tags, g.tags),
    )


def compose(*functions: GraphFunction) -> GraphFunction:
    """Variadic left-folded composition. Requires at least two functions.

    compose(f, g, h) == compose(compose(f, g), h)
    """
    if len(functions) < 2:
        raise ValueError(
            f"compose() requires at least 2 functions, got {len(functions)}"
        )
    result = functions[0]
    for fn in functions[1:]:
        result = _compose_pair(result, fn)
    return result


# ── Substitution ─────────────────────────────────────────────────────────────


def substitute(outer: Graph, contract_vector: str, inner: Graph) -> Graph:
    """Replace a coarse contract vector with an interface-compatible inner graph.

    contract_vector: the .id of the target vector (REQ-L-GTL2-IDENTITY-006).
    Id-only — no name fallback.
    """
    target_vec = None
    for v in outer.vectors:
        if v.id == contract_vector:
            target_vec = v
            break
    if target_vec is None:
        raise ValueError(
            f"substitute(): vector {contract_vector!r} not found in graph {outer.name!r}"
        )

    if isinstance(target_vec.source, tuple):
        vec_source_names = {n.name for n in target_vec.source}
    elif target_vec.source is not None:
        vec_source_names = {target_vec.source.name}
    else:
        vec_source_names = set()

    inner_input_names = {n.name for n in inner.inputs}
    if not inner_input_names <= vec_source_names:
        raise ValueError(
            f"substitute(): inner.inputs {sorted(inner_input_names)} not subset of "
            f"vector source {sorted(vec_source_names)}"
        )

    inner_output_names = {n.name for n in inner.outputs}
    vec_target_name = target_vec.target.name if target_vec.target else ""
    if vec_target_name and vec_target_name not in inner_output_names:
        raise ValueError(
            f"substitute(): vector target {vec_target_name!r} not in "
            f"inner.outputs {sorted(inner_output_names)}"
        )

    merged_vectors_list = []
    for vector in outer.vectors:
        if vector.id == target_vec.id:
            merged_vectors_list.extend(inner.vectors)
        else:
            merged_vectors_list.append(vector)
    merged_vectors = tuple(merged_vectors_list)

    outer_node_names = {n.name for n in outer.nodes}
    extra_nodes = tuple(n for n in inner.nodes if n.name not in outer_node_names)
    merged_nodes = outer.nodes + extra_nodes

    outer_ctx_names = {c.name for c in outer.contexts}
    extra_contexts = tuple(c for c in inner.contexts if c.name not in outer_ctx_names)
    merged_contexts = outer.contexts + extra_contexts

    return Graph(
        name=outer.name,
        inputs=outer.inputs,
        outputs=outer.outputs,
        nodes=merged_nodes,
        vectors=merged_vectors,
        contexts=merged_contexts,
        rules=outer.rules,
        effects=outer.effects,
        tags=outer.tags + (f"substituted:{target_vec.name}",),
    )


# ── Identity ─────────────────────────────────────────────────────────────────


def identity(interface: tuple[Node, ...]) -> GraphFunction:
    """Identity function — neutral element under composition."""
    return GraphFunction(
        name="id",
        inputs=interface,
        outputs=interface,
    )


# ── Recursion ────────────────────────────────────────────────────────────────


def recurse(graph_function: GraphFunction, termination: Evaluator) -> GraphFunction:
    """Express repeated graph-function application under a declared termination.

    Returns a GraphFunction with the same outer contract. Recursion is
    bounded by the termination evaluator. ABG owns the execution loop.
    """
    return GraphFunction(
        name=f"recurse({graph_function.name})",
        inputs=graph_function.inputs,
        outputs=graph_function.outputs,
        template=graph_function.template,
        effects=graph_function.effects,
        tags=_stable_union(graph_function.tags, (f"termination:{termination.name}",)),
    )


# ── Higher-Order Operators ───────────────────────────────────────────────────


def fan_out(f: GraphFunction, *, over: Node) -> GraphFunction:
    """Apply f across an explicit Vector[T] boundary.

    over is mandatory — no hidden inference of cardinality.
    Returns a GraphFunction whose outer contract is vectorized relative to f.
    """
    if not _is_vector_boundary(over):
        raise ValueError(
            f"fan_out({f.name}): over must declare an explicit Vector[...] boundary, got {over.schema!r}"
        )

    return GraphFunction(
        name=f"fan_out({f.name})",
        inputs=(over,),
        outputs=(over,),
        template=f.template,
        effects=f.effects,
        tags=_stable_union(f.tags, (f"over:{over.name}",)),
    )


def fan_in(reducer: GraphFunction, *, over: Node) -> GraphFunction:
    """Reduce an explicit vector boundary into one synthesized result.

    over is mandatory — no hidden inference.
    """
    if not _is_vector_boundary(over):
        raise ValueError(
            f"fan_in({reducer.name}): over must declare an explicit Vector[...] boundary, got {over.schema!r}"
        )

    return GraphFunction(
        name=f"fan_in({reducer.name})",
        inputs=(over,),
        outputs=reducer.outputs,
        template=reducer.template,
        effects=reducer.effects,
        tags=_stable_union(reducer.tags, (f"over:{over.name}",)),
    )


def gate(
    target: GraphFunction | RefinementBoundary | CandidateFamily,
    *,
    rule: Rule,
    evaluators: tuple[Evaluator, ...],
) -> GraphFunction:
    """Block continuation behind rule + evaluators over an explicit boundary.

    target may be a GraphFunction, RefinementBoundary, or CandidateFamily.
    gate does not choose a candidate, invent a refinement, or define
    domain pass/fail semantics.
    """
    if not evaluators:
        raise ValueError("gate() requires at least one evaluator")

    target_effects = target.effects if isinstance(target, GraphFunction) else ()
    target_tags = target.tags if hasattr(target, "tags") else ()

    return GraphFunction(
        name=f"gate({target.name})",
        inputs=target.inputs,
        outputs=target.outputs,
        effects=target_effects,
        tags=_stable_union(target_tags, (f"rule:{rule.name}",)),
    )


def promote(*, source: Node, to: Node) -> GraphFunction:
    """Lift one declared representation boundary into another.

    Both source and to are mandatory. No hidden inference.
    promote does not change semantic truth — only the declared
    representation boundary available to later algebraic steps.
    """
    return GraphFunction(
        name=f"promote({source.name}->{to.name})",
        inputs=(source,),
        outputs=(to,),
        tags=(f"source:{source.name}", f"to:{to.name}"),
    )


# ── Synthesis / Selection sugar ──────────────────────────────────────────────


def deferred_refinement(
    name: str,
    *,
    inputs: tuple[Node, ...],
    outputs: tuple[Node, ...],
    hints: dict | None = None,
    tags: tuple[str, ...] = (),
) -> RefinementBoundary:
    """Declare a lawful refinement/synthesis boundary without embedding strategy."""
    return RefinementBoundary(
        name=name,
        inputs=inputs,
        outputs=outputs,
        hints=hints or {},
        tags=tags,
    )


def candidate_family(
    name: str,
    *,
    inputs: tuple[Node, ...],
    outputs: tuple[Node, ...],
    candidates: tuple[GraphFunction, ...],
    policy_hints: dict | None = None,
    tags: tuple[str, ...] = (),
) -> CandidateFamily:
    """Declare a named family of lawful alternatives over one contract boundary.

    Validates that all candidates share the declared outer contract.
    """
    if not candidates:
        raise ValueError(f"candidate_family({name!r}): empty candidates")

    for c in candidates:
        c_in = {n.name for n in c.inputs}
        c_out = {n.name for n in c.outputs}
        family_in = {n.name for n in inputs}
        family_out = {n.name for n in outputs}
        if c_in != family_in or c_out != family_out:
            raise ValueError(
                f"candidate_family({name!r}): candidate {c.name!r} contract "
                f"({sorted(c_in)}->{sorted(c_out)}) does not match family contract "
                f"({sorted(family_in)}->{sorted(family_out)})"
            )

    return CandidateFamily(
        name=name,
        inputs=inputs,
        outputs=outputs,
        candidates=candidates,
        policy_hints=policy_hints or {},
        tags=tags,
    )
