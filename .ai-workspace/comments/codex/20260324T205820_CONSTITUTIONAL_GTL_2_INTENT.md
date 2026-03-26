# Constitutional Intent: GTL 2.x

**Status**: Draft
**Date**: 2026-03-24
**Purpose**: State the constitutional intent for GTL 2.x as a graph-first embedded Python DSL/SDK, with ABG positioned as interpreter/runtime rather than part of the language ontology.

---

## Position

GTL 2.x is a language redesign, not a parser redesign.

It remains:

- an embedded Python DSL
- an SDK
- a programmatic language surface

Its semantic center is clarified and tightened:

- graph is the one first-class structural type
- typed nodes are the local loci of graph meaning
- operators are the effectful action surface
- graph functions are the reusable workflow abstraction
- composition, substitution, recursion, and higher-order graph operations are first-class language semantics

ABG remains separate:

- ABG is the canonical event-sourced interpreter/runtime for GTL programs
- GTL itself is not bound to a single engine implementation

---

## Intent Statements

### INT-GTL2-001: Graph Primacy and Typed Nodes

GTL 2.x shall treat `Graph` as the one first-class structural type.

Graphs shall be composed from typed nodes.

All structural workflow forms are graphs, including:

- reusable workflows
- subgraphs
- interface-bearing graphs
- refined graphs
- composed graphs
- recursively applied graphs

No second structural ontology is required.

An edge is not a rival structural type.

It is a minimal graph vector between typed nodes.

### INT-GTL2-002: Embedded Python Form

GTL 2.x shall remain an embedded Python DSL/SDK.

The next increment shall not depend on a new standalone parser or syntax.

Language evolution shall occur through:

- Python types
- constructors
- helpers
- semantic laws

### INT-GTL2-003: Operators as First-Class Regimes

GTL 2.x shall model effectful action through first-class `Operator` declarations.

The language must support at least three regimes:

- deterministic
- probabilistic
- human/judgment

These are language-level operator classes, not merely runtime implementation categories.

### INT-GTL2-004: Graph Functions as Reusable Workflow Programs

GTL 2.x shall support reusable named workflow programs through `GraphFunction`.

A graph function must:

- declare an interface
- produce or transform a graph
- be reusable across sites
- participate in composition

### INT-GTL2-005: Composition and Substitution

GTL 2.x shall make lawful composition and lawful substitution native operations.

Composition shall chain graph functions across interface-compatible contracts.

Substitution shall refine a coarse contract step with a finer graph while preserving the outer contract.

### INT-GTL2-006: Recursion and Higher-Order Graph Programming

GTL 2.x shall support recursion and higher-order graph programming.

The language trajectory must include:

- recursive graph application
- fan-out
- fan-in
- gating
- promotion

These are part of the language model, not special-case runtime behavior.

### INT-GTL2-007: Structural Selection Boundary

GTL 2.x may expose lawful candidates, tags, interface families, and policy hints.

GTL 2.x shall not embed hidden strategic choice.

Selection of one lawful workflow over another belongs to:

- deterministic rule execution
- probabilistic contextual analysis
- human judgment
- or business/intent logic above the interpreter

### INT-GTL2-008: ABG as Canonical Interpreter

ABG shall be treated as the canonical interpreter/runtime for GTL programs rather than as part of GTL's structural ontology.

ABG is responsible for:

- event emission
- replay
- convergence
- work lineage
- run attempts
- retries
- correction/reset
- provenance

GTL is responsible for structural law.

### INT-GTL2-009: Engine Independence

GTL 2.x shall be defined independently of any single engine implementation.

It must be possible in principle to map GTL programs onto multiple runtimes, including but not limited to:

- ABG
- Temporal
- Prefect
- Step Functions

with varying fidelity.

ABG is the canonical interpreter, not the exclusive possible runtime.

### INT-GTL2-010: Replay Suitability

GTL 2.x constructs shall be defined so they can be lawfully interpreted by an event-sourced runtime.

The language must therefore preserve:

- stable structural meaning
- explicit interfaces
- explicit composition/substitution semantics

### INT-GTL2-011: Clean Re-foundation

GTL 2.x shall be specified as a clean language design rather than as a stack of amendments to older wording.

Migration from earlier terminology may be documented, but the new constitutional text should read as a standalone language.

---

## Non-Goals

GTL 2.x is not intended to be:

- a planner
- a business-priority engine
- a hidden workflow selector
- a place where runtime lineage mechanics become language primitives
- a language whose semantics collapse into one host engine

Those concerns belong either above GTL or in ABG.

---

## Guiding Statement

GTL 2.x is a graph-first Python DSL/SDK for expressing deterministic, probabilistic, and judgment-bearing workflow programs through graphs, typed nodes, operators, graph functions, and higher-order graph composition, with ABG serving as the canonical event-sourced interpreter/runtime.
