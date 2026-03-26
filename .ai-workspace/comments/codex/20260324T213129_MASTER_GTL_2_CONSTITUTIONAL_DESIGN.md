# GTL 2.x Constitutional Design

**Status**: Consolidated draft
**Date**: 2026-03-24
**Purpose**: Bring the GTL 2.x intent, domain model, language semantics, interpreter boundary, engine-mapping stance, and fresh requirement structure into one canonical review document.

---

## 1. Position

GTL 2.x is a language redesign, not a parser redesign.

It remains:

- an embedded Python DSL
- an SDK
- a programmatic language surface

What changes is the semantic center and the rigor of the model.

GTL 2.x is:

- graph-first
- composition-first
- recursion-capable
- higher-order
- engine-agnostic

ABG is then positioned as:

- the canonical target engine surface for GTL

but not the only possible engine mapping.

---

## 2. Core Thesis

The irreducible structural type of GTL 2.x is `Graph`.

Everything structural is graph:

- a primitive edge is graph
- a multi-step workflow is graph
- a subgraph is graph
- a reusable workflow is graph
- a refined workflow is graph
- a recursively applied workflow is graph

There is no need for a second structural ontology.

This yields the core simplification:

- `Graph` is the one structural type
- `Node[T]` is the typed local locus of graph meaning
- `Operator` is the effectful action surface
- `Evaluator` is the convergence/attestation surface
- `GraphFunction` is the reusable workflow/program abstraction
- composition, substitution, recursion, and higher-order operators are graph semantics

Historically, older terms like `Fragment` were useful bootstrap scaffolding during major refactors.

They helped land local refinement before the full graph algebra was explicit.

But they are not the end-state ontology.

---

## 2A. Layered Graph Model

The phrase "everything structural is graph" does not mean there is only one graph.

It means the same algebra appears at multiple layers.

### Topology graph

The admissible structure of work:

- what nodes exist
- what graph vectors are lawful
- what composition and substitution are admissible

This is GTL-owned.

### Materialized graph

A concrete graph instance produced from graph templates/functions and parameters.

This sits at the GTL/engine boundary.

### Execution graph

A concrete traversal of the topology/materialized graph under actual operator and evaluator activity.

This is engine-owned.

### Lineage graph

Multiple related graph executions across work lineage.

This is engine-owned.

### Composition graph

Graphs built from graphs/functions by composition, substitution, and higher-order combinators.

This is GTL-owned.

This layered view is the right answer to branching and collection-like behavior:

- fan-out is graph materialization into branching execution structure
- fan-in is graph reduction across branch executions
- promotion is graph reshaping between compatible interface forms

---

## 3. Constitutional Intent

### INT-GTL2-001: Graph Primacy and Typed Nodes

GTL 2.x shall treat `Graph` as the one first-class structural type.

Graphs shall be composed from typed nodes.

An edge is not a rival type.

It is a minimal graph vector between typed nodes.

### INT-GTL2-002: Embedded Python Form

GTL 2.x shall remain an embedded Python DSL/SDK.

It shall not depend on a new standalone parser or syntax.

### INT-GTL2-003: Operators as First-Class Regimes

GTL 2.x shall model effectful action through first-class `Operator` declarations.

The language must support at least:

- deterministic
- probabilistic
- human/judgment

### INT-GTL2-003A: Evaluators as First-Class Convergence Surfaces

GTL 2.x shall model convergence, checking, and attestation through first-class `Evaluator` declarations.

Operators do work.

Evaluators determine whether graph contracts have been satisfied.

### INT-GTL2-004: Graph Functions as Reusable Workflow Programs

GTL 2.x shall support reusable named workflow programs through `GraphFunction`.

### INT-GTL2-005: Composition and Substitution

GTL 2.x shall make lawful composition and lawful substitution native operations.

### INT-GTL2-006: Recursion and Higher-Order Graph Programming

GTL 2.x shall support:

- recursive graph application
- fan-out
- fan-in
- gating
- promotion

### INT-GTL2-007: Structural Selection Boundary

GTL 2.x may expose lawful candidates, interface families, tags, and hints.

GTL 2.x shall not embed hidden strategic choice.

### INT-GTL2-008: ABG as Canonical Interpreter

ABG shall be treated as the canonical target engine surface for GTL programs, not part of GTL’s structural ontology.

Multiple ABG-compatible implementations may exist.

The current local/workspace implementation is only one realization of that surface.

### INT-GTL2-009: Engine Independence

GTL 2.x shall be defined independently of any single engine implementation.

### INT-GTL2-010: Replay Suitability

GTL 2.x constructs shall be defined so they can be lawfully interpreted by an event-sourced runtime.

### INT-GTL2-011: Clean Re-foundation

GTL 2.x shall be specified as a clean language design rather than as a stack of amendments to older wording.

---

## 4. What GTL 2.x Is and Is Not

### GTL 2.x is

- a graph-first Python DSL/SDK
- a compositional semantic library
- a language for expressing deterministic, probabilistic, and judgment-bearing workflow programs
- a structural definition that can map onto multiple runtimes
- a language whose canonical engine contract may have multiple implementations

### GTL 2.x is not

- a planner
- a business-priority engine
- a hidden workflow selector
- a runtime/event model
- a single-engine language whose semantics collapse into ABG

---

## 5. Domain Model

### 5.1 Graph

`Graph` is the primary workflow/program value.

Conceptually:

```python
@dataclass(frozen=True)
class Graph:
    name: str
    inputs: tuple[Node[Any], ...]
    outputs: tuple[Node[Any], ...]
    nodes: tuple[Node[Any], ...]
    edges: tuple[Edge, ...]
    contexts: tuple[Context, ...] = ()
    rules: tuple[Rule, ...] = ()
    effects: tuple[Regime, ...] = ()
    tags: tuple[str, ...] = ()
```

Responsibilities:

- declare boundary/interface
- contain internal structure
- carry local constraints
- declare or derive composed execution regimes
- serve as the unit of substitution and composition

### 5.2 Node[T]

`Node[T]` is the local typed locus within a graph.

Conceptually:

```python
@dataclass(frozen=True)
class Node(Generic[T]):
    name: str
    schema: type[T] | str
    tags: tuple[str, ...] = ()
```

Meaning:

- node identity is graph-local
- node type/schema defines the semantic kind that flows there
- multiple nodes may share the same schema while remaining distinct nodes

### 5.3 Interface

Interface is expressed through designated boundary nodes.

Inputs and outputs are graph roles over nodes, not a rival structural type.

### 5.4 Vector[T]

`Vector[T]` is a schema family used when a node carries a collection of `T`.

It is not a rival structural type.

The structural type is still `Graph`, and the local locus is still `Node[Vector[T]]`.

This is the semantic foundation for:

- `fan_out`
- `fan_in`
- `promote`

`Vector[T]` is therefore not a rival structural type.

It is a node schema/payload shape used when graph materialization depends on collection cardinality.

### 5.5 Edge / Vector

`Edge` is a directed graph vector between typed nodes.

It is:

- a graph-local step
- a minimal graph shape
- not a rival ontology

Publicly, `edge(a, b, operators=...) -> Graph` can remain as DSL sugar for a primitive graph.

### 5.6 Asset as Schema Payload

The current `Asset` concept is best reinterpreted as:

- a node payload/schema declaration
- or a domain-specific schema type used by `Node[T]`

`Asset` should not remain the structural center.

### 5.7 Operator

`Operator` is the typed effectful action surface.

Conceptually:

```python
@dataclass(frozen=True)
class Operator:
    name: str
    regime: Regime
    binding: str
    tags: tuple[str, ...] = ()
```

Regimes include:

- deterministic
- probabilistic
- human

Operators perform work or effectful transitions over graph contracts.

### 5.8 Evaluator

`Evaluator` is the typed convergence and attestation surface.

Conceptually:

```python
@dataclass(frozen=True)
class Evaluator:
    name: str
    regime: Regime
    binding: str
    tags: tuple[str, ...] = ()
```

Evaluators answer:

- is this graph contract satisfied?
- has this output converged?
- has this gate been passed?

Evaluators may be:

- deterministic checks
- probabilistic assessments
- human sign-offs

This preserves the distinction that exists in GTL 1.0:

- `Operator` answers "who/what does work"
- `Evaluator` answers "what checks or attests convergence"

Evaluators are first-class GTL declarations.

Their realization is plugin-dependent.

So the clean split is:

- GTL declares `Evaluator`
- engine plugins provide evaluator bindings/implementations
- ABG-compatible engines create evaluation instances, attempts, results, and provenance

### 5.9 Rule

`Rule` is a declarative constraint or gate.

Examples:

- consensus thresholds
- policy gates
- type-consistency rules
- coverage rules

Rules are passive declarations.

They describe what must hold.

### 5.10 GraphFunction

`GraphFunction` is a reusable named workflow abstraction.

Conceptually:

```python
@dataclass(frozen=True)
class GraphFunction:
    name: str
    inputs: tuple[Node[Any], ...]
    outputs: tuple[Node[Any], ...]
    template: Callable[..., Graph] | GraphTemplate
    effects: tuple[Regime, ...] = ()
    tags: tuple[str, ...] = ()
```

Semantically, a graph function is a parameterized graph template.

In the embedded Python DSL, that template may be authored as a callable that materializes a graph.

`GraphTemplate` here means any serializable or materializable graph-template representation.

The callable form is an authoring convenience, not the semantic requirement.

For engine independence, the semantic contract is not "arbitrary Python behavior."

It is "materializable graph template with explicit interface and declared effects."

Graph materialization may legitimately depend on parameters such as:

- input cardinality
- selected workflow family
- policy-visible structural parameters

What is engine-independent is the template contract and resulting graph semantics, not the host-language callable itself.

The `effects` surface is used for:

- static analysis
- candidate filtering
- engine capability matching
- human-vs-machine workflow visibility

### 5.11 Module

`Module` is the top-level organizational unit.

A module owns:

- graphs
- graph functions
- operators
- evaluators
- rules
- imports
- metadata visible to policy/evaluator layers

Modules may be published as reusable workflow libraries.

Imported graph functions must preserve:

- interface truth
- declared effects
- module provenance

---

## 6. Core Semantics

### 6.1 Graph primacy

All workflow structure is graph.

### 6.2 Typed node primacy

Local graph meaning is carried by typed nodes.

### 6.3 Interface satisfaction

Composition and substitution are only lawful when interfaces align.

### 6.4 Evaluator separation

Work and convergence remain distinct concerns.

Operators perform or dispatch work.

Evaluators check or attest convergence.

### 6.5 Contract preservation

Internal refinement may change structure but must preserve declared outer contract.

### 6.6 Reuse

Named workflows are reusable through graph functions, not through copied structure.

### 6.7 Higher-order legality

Fan-out, fan-in, gate, and promote must preserve interface/type truth.

### 6.8 Bounded sub-work expressibility

The language may declare that a graph vector or graph function permits bounded sub-work dispatch.

The runtime realization of that declaration is not a language primitive.

ABG may realize it through `LeafTask` or an equivalent runtime construct.

This is the clean answer to leaf-task placement:

- GTL can express bounded sub-work capability
- ABG-compatible engines choose how to realize that capability operationally

---

## 7. Core Operations

### 7.1 Compose

```python
compose(f, g)
```

Compose two graph functions when interfaces align.

### 7.2 Primitive edge construction

```python
edge(a, b, operators=...) -> Graph
```

Construct a minimal graph vector from typed node `a` to typed node `b`.

### 7.3 Substitute

```python
substitute(outer_graph, contract_edge, inner_graph)
```

Replace a coarse contract step with a finer graph.

This is the graph-first surface for what older language called `zoom`.

### 7.4 Recurse

```python
recurse(graph, lineage)
```

Express that graph application may induce child graph applications.

### 7.5 Fan-out

```python
fan_out(f)
```

Apply a graph function across a collection/vector.

### 7.6 Fan-in

```python
fan_in(r)
```

Reduce branch outputs into one synthesized result.

### 7.7 Gate

```python
gate(g)
```

Require a gate before continuation or promotion.

Consensus belongs here.

`gate(...)` is the active combinator that applies rules and/or evaluators to control flow.

So the relationship is:

- `Rule` = declarative statement of what must hold
- `Evaluator` = mechanism of checking/attesting whether it holds
- `gate(...)` = graph combinator that blocks or allows continuation based on those declarations and checks

### 7.8 Promote

```python
promote(p)
```

Lift one representation into another.

Examples:

- event to vector
- vector to branches
- branch outputs to synthesized context

---

## 8. Language Laws

1. Graph primacy
2. Typed node law
3. Interface law
4. Operator/evaluator separation
5. Composition associativity
6. Identity graph function
7. Substitutability at interface-equivalent boundaries
8. Contract preservation under substitution
9. Recursion with preserved lineage semantics
10. Higher-order legality
11. Separation from strategic choice
12. Suitability for event-sourced interpretation
13. Engine independence of language semantics

---

## 9. Selection Boundary

The language may expose:

- candidate families
- interface equivalence
- tags
- optional policy hints

But the language should not embed:

- hidden workflow choice
- business priority
- engine strategy

Selection belongs to:

- deterministic rule execution
- probabilistic contextual analysis
- human judgment
- business/intent logic above the interpreter

The interpreter may enumerate lawful candidates.

It should not silently decide the “best” one.

---

## 10. Language vs Runtime Boundary

### GTL owns

- graph structure
- typed nodes
- interfaces
- operators and regimes
- evaluators and regimes
- rules
- graph functions
- composition
- substitution
- recursion as language capability
- bounded sub-work declarations
- higher-order graph operations
- module/library structure

### ABG owns

- event emission
- projection
- convergence/delta
- work lineage
- run attempts
- retries
- correction/reset
- provenance
- replay
- next-action determination
- Job binding for scheduling
- Worker identity and execution capability
- LeafTask runtime dispatch and bounded sub-work execution
- working surfaces and execution traces

This separation is constitutional, not incidental.

---

## 11. ABG as Canonical Target Engine Surface

ABG consumes:

- GTL graphs
- GTL graph functions
- GTL operators
- GTL rules
- module declarations
- event history

ABG then:

1. materializes graph functions when needed
2. enumerates lawful candidate graphs if refinement/composition is needed
3. receives selection from deterministic, probabilistic, human, or business logic
4. applies substitution/composition
5. executes operator surfaces
6. executes evaluator surfaces
7. emits events
8. replays truth
9. computes convergence

ABG is the canonical target engine surface because it is explicitly designed around:

- event emission
- replay
- convergence
- lineage
- correction
- provenance

An ABG-compatible implementation may be:

- local/workspace oriented
- distributed/cloud first
- queue driven
- service oriented

as long as it preserves the ABG surface contract expected by GTL.

---

## 12. Engine Mappings

GTL 2.x is not defined by one engine.

It should be possible to interpret or map GTL programs onto:

- ABG
- Temporal
- Prefect
- Step Functions
- other future runtimes

ABG is canonical because it is designed around GTL’s event-sourced convergence model.

Other engines may support:

- full mappings
- partial mappings
- capability-profile mappings

depending on their execution model.

The language definition must stay independent of any one backend.

The ABG surface is one mapping target family.

Other engines are alternate mapping targets, potentially with reduced fidelity.

---

## 13. Current GTL as Partial Projection

Current GTL should be understood as a partial projection of the fuller GTL 2.x algebra.

It already contains:

- typed topology
- operator regimes
- rule surfaces
- recursive and compositional hints
- the embedded Python form

But it still centers:

- `Asset`
- `Edge`
- `Job`
- `Worker`
- `Package`
- runtime-oriented constructs

more than the fuller GTL 2.x algebra does.

A useful rereading of current GTL is:

- `Asset` approximates node schema/type
- `Edge` approximates primitive graph vector
- `Package` approximates a graph/module carrier
- `Evaluator` is a real convergence concept that should survive into GTL 2.x
- `Job` and `Worker` are ABG/runtime concepts that should move out of the language core
- runtime-heavy concepts in current GTL belong more naturally to ABG than to the language core

So GTL 2.x is not a repudiation of current GTL.

It is the explicit reconstruction of the fuller model from that partial projection.

In that history, `Fragment` should be read as a successful transitional abstraction:

- useful during bootstrap and major refactor
- not wrong in context
- but no longer needed once graph primacy is made explicit

---

## 14. Requirement Structure

The next constitutional requirement set should be split into four layers.

### 14.1 GTL language requirement families

- `REQ-L-GTL2-GRAPH`
- `REQ-L-GTL2-NODE`
- `REQ-L-GTL2-VECTOR`
- `REQ-L-GTL2-INTERFACE`
- `REQ-L-GTL2-OPERATOR`
- `REQ-L-GTL2-EVALUATOR`
- `REQ-L-GTL2-RULE`
- `REQ-L-GTL2-GRAPHFUNCTION`
- `REQ-L-GTL2-COMPOSE`
- `REQ-L-GTL2-SUBSTITUTE`
- `REQ-L-GTL2-RECURSE`
- `REQ-L-GTL2-SUBWORK`
- `REQ-L-GTL2-HOF`
- `REQ-L-GTL2-MODULE`
- `REQ-L-GTL2-SELECTION-BOUNDARY`
- `REQ-L-GTL2-LAWS`
- `REQ-L-GTL2-ENGINE-INDEPENDENCE`

### 14.2 ABG interpreter requirement families

- `REQ-R-ABG2-INTERPRET`
- `REQ-R-ABG2-EVENTS`
- `REQ-R-ABG2-PROJECTION`
- `REQ-R-ABG2-CONVERGENCE`
- `REQ-R-ABG2-LINEAGE`
- `REQ-R-ABG2-RUN`
- `REQ-R-ABG2-CORRECTION`
- `REQ-R-ABG2-PROVENANCE`
- `REQ-R-ABG2-SELECTION-APPLICATION`
- `REQ-R-ABG2-JOB-WORKER`
- `REQ-R-ABG2-LEAFTASK`
- `REQ-R-ABG2-SELFHOSTING`

### 14.3 Engine-mapping requirement families

- `REQ-M-GTL2-MAPPING`
- `REQ-M-GTL2-CAPABILITY`
- `REQ-M-GTL2-PROVENANCE`

### 14.4 Product/policy/scenario requirement families

- `REQ-P-POLICY`
- `REQ-P-SCENARIOS`
- `REQ-P-LIBRARIES`

---

## 15. Recommended First Wave

### GTL first wave

1. `REQ-L-GTL2-GRAPH`
2. `REQ-L-GTL2-NODE`
3. `REQ-L-GTL2-INTERFACE`
4. `REQ-L-GTL2-OPERATOR`
5. `REQ-L-GTL2-EVALUATOR`
6. `REQ-L-GTL2-GRAPHFUNCTION`
7. `REQ-L-GTL2-COMPOSE`
8. `REQ-L-GTL2-SUBSTITUTE`
9. `REQ-L-GTL2-LAWS`

### ABG first wave

1. `REQ-R-ABG2-INTERPRET`
2. `REQ-R-ABG2-EVENTS`
3. `REQ-R-ABG2-PROJECTION`
4. `REQ-R-ABG2-CONVERGENCE`
5. `REQ-R-ABG2-LINEAGE`
6. `REQ-R-ABG2-SELECTION-APPLICATION`
7. `REQ-R-ABG2-JOB-WORKER`

This is enough to establish:

- graph-first language law
- interpreter separation
- composition/substitution
- evented replay

before pushing further into recursion, higher-order behavior, self-hosting, and alternate-engine mappings.

---

## 16. Fresh Document Stack

Once this consolidated document is accepted, the clean next canonical stack is:

1. `GTL_2_INTENT.md`
2. `GTL_2_DOMAIN_MODEL.md`
3. `GTL_2_LANGUAGE.md`
4. `GTL_2_SEMANTICS.md`
5. `GTL_2_OPERATOR_MODEL.md`
6. `GTL_2_HIGHER_ORDER_COMPOSITION.md`
7. `GTL_2_ABG_INTERPRETER_BOUNDARY.md`
8. `GTL_2_REQUIREMENT_FAMILIES.md`
9. `GTL_2_MIGRATION.md`

Only the migration document should spend material effort on legacy terminology.

---

## 17. Guiding Statement

GTL 2.x is a graph-first Python DSL/SDK for expressing deterministic, probabilistic, and judgment-bearing workflow programs through graphs, typed nodes, operators, evaluators, graph functions, and higher-order graph composition, with ABG serving as the canonical target engine surface and other engines remaining possible mapping targets.

---

## 18. Bottom Line

The main simplification is this:

**everything structural is graph.**

From that:

- node meaning becomes explicit through `Node[T]`
- edge becomes a minimal graph vector
- reusable workflows become `GraphFunction`
- refinement becomes substitution
- recursion becomes graph application over lineage
- fan-out/fan-in/gate/promote become graph operators
- ABG becomes the interpreter rather than the language
- GTL becomes portable across engines rather than trapped in one runtime

This is the coherent GTL 2.x design.
