# GTL 2.x Language

**Status**: Draft
**Date**: 2026-03-24
**Purpose**: Define GTL 2.x as an embedded Python DSL/SDK with graph-first semantics and first-class composition.

---

## 1. Language Form

GTL 2.x remains an embedded Python DSL/SDK.

That means:

- no new parser is required
- no new standalone syntax is required
- language evolution happens through Python types, constructors, helpers, and semantic laws

So this document is about:

- language semantics
- language API shape
- language laws

not about inventing a new textual grammar.

The definition is not the implementation.

GTL is the semantic language surface.

Multiple engines may interpret or map GTL programs.

---

## 2. Language Primitives

The language primitives are:

- `Graph`
- `Node[T]`
- `Operator`
- `Rule`
- `GraphFunction`
- `Module`

All other public language constructs should be derivable from these.

---

## 3. Language Operations

### 3.1 Compose

```python
compose(f, g)
```

Compose two graph functions when interfaces align.

Result:

- a new graph function
- preserving lawful outer interface

### 3.2 Primitive edge construction

```python
edge(a, b, operators=...) -> Graph
```

This is DSL sugar for constructing a minimal graph vector from typed node `a` to typed node `b`.

An edge is therefore a graph form, not a rival structural type.

### 3.3 Substitute

```python
substitute(outer_graph, contract_edge, inner_graph)
```

Replace a coarse contract step with a finer graph.

This is the graph-first public language surface for refinement.

### 3.4 Recurse

```python
recurse(graph, lineage)
```

Express the fact that graph application may induce child graph applications.

This is primarily semantic, but the language should name it clearly.

### 3.5 Fan-out

```python
fan_out(f)
```

Apply a graph function across a collection or vector.

### 3.6 Fan-in

```python
fan_in(r)
```

Reduce branch outputs into one synthesized result.

### 3.7 Gate

```python
gate(g)
```

Require a gate before continuation or promotion.

Consensus belongs naturally here.

### 3.8 Promote

```python
promote(p)
```

Lift one representation into another.

Examples:

- event to vector
- vector to branches
- branch outputs to synthesized context

---

## 4. Language Semantics

### 4.1 Graph primacy

All workflow structure is graph.

### 4.2 Typed node primacy

Local graph meaning is carried by typed nodes.

### 4.3 Interface satisfaction

Composition and substitution are only lawful when interfaces align.

### 4.4 Contract preservation

Internal refinement may change structure but must preserve declared outer contract.

### 4.5 Reuse

Named workflows are reusable through graph functions, not through copied structure.

### 4.6 Higher-order legality

Fan-out, fan-in, gate, and promote must preserve interface/type truth.

---

## 5. Language Laws

1. Graph primacy
2. Typed node law
3. Interface law
4. Composition associativity
5. Identity graph function
6. Substitutability at interface-equivalent boundaries
7. Contract preservation under substitution
8. Recursion with preserved lineage semantics
9. Higher-order legality
10. Separation from strategic choice
11. Suitability for event-sourced interpretation
12. Engine independence of language semantics

---

## 6. Selection Boundary

The language may expose:

- candidate families
- tags
- interface equivalence
- optional policy hints

But the language should not embed:

- hidden workflow choice
- business priority
- engine strategy

Selection belongs above the language and is consumed by the interpreter/runtime.

---

## 7. Engine Mappings

GTL 2.x is not defined by one engine.

It should be possible to interpret or map GTL programs onto:

- ABG
- Temporal
- Prefect
- Step Functions
- other future runtimes

ABG is the canonical interpreter because it is designed around GTL's event-sourced convergence model.

Other engines may support full or partial mappings depending on their execution model.

---

## 8. Example Shape

Conceptual Python DSL shape:

```python
review_gate = Rule("consensus", threshold=(2, 3))

intent = Node("intent", schema=Intent)
synthesized_results = Node("synthesized_results", schema=SynthesizedResults)
new_context = Node("new_context", schema=NewContext)

discovery = GraphFunction(
    name="discovery_workflow",
    inputs=(intent,),
    outputs=(synthesized_results,),
    build=build_discovery_graph,
)

contextual_discovery = compose(
    discovery,
    GraphFunction(
        name="promote_to_context",
        inputs=(synthesized_results,),
        outputs=(new_context,),
        build=build_context_graph,
    ),
)
```

This is still Python.

What changes is that the semantics are now cleanly graph-first.

Current GTL can be read as a partial projection of this fuller model:

- `Asset` approximates node schema/type
- `Edge` approximates primitive graph vector
- `Package` approximates a graph/module carrier
- runtime-heavy concepts in current GTL belong more naturally to ABG than to the language core

---

## 9. What GTL 2.x Does Not Specify

GTL 2.x does not specify:

- event schema
- replay algorithm
- delta implementation
- retry loops
- correction/reset runtime behavior
- provenance mechanics

Those belong to ABG.

---

## 10. Summary

GTL 2.x is a graph-first Python DSL/SDK.

Its public surface should make graphs, typed nodes, graph vectors, operators, graph functions, composition, substitution, recursion, and higher-order graph operations explicit without changing the hosting language or binding the language to a single engine.
