# Core Proposal: Graph-First GTL and ABG Interpreter

**Status**: Core proposal
**Date**: 2026-03-24
**Purpose**: Recast GTL and ABG around the principle that everything is graph, make composition first-class, keep selection outside the kernel, and restate existing functionality through that lens.

---

## Core Thesis

The correct semantic center of the system is `Graph`.

Everything else is a role, operation, or evented interpretation over graphs:

- subgraph = graph
- interface graph = graph
- bounded graph = graph
- reusable workflow graph = graph
- composed graph = graph
- zoomed graph = graph
- branch graph = graph

This immediately simplifies the design:

- composition stops being a special feature
- refinement becomes graph substitution
- fan-out and fan-in become graph combinators
- package reuse becomes graph-library reuse
- ABG becomes an event-sourced interpreter for a functional graph language

The right kernel posture is therefore:

- **graph-first**
- **composition-aware**
- **selection-blind**
- **event-sourced**

---

## Why This Revision Exists

The earlier composition proposal was directionally right, but still carried too much legacy subgraph framing.

That left the design looking more complex than it really is:

- named workflows looked like convenience wrappers around embedded graph structure
- composition looked like an add-on rather than the normal operation
- higher-order cases looked like future special features
- selection policy risked collapsing into engine behavior

The graph-first view resolves that.

The system is best understood as:

- a functional, interpreted graph language for deterministic, probabilistic, and judgment-bearing programs

ABG is the interpreter and convergence engine for that language.

---

## Ontology

### 1. Graph is the one first-class structural type

There should be one primary structural value:

- `Graph`

Everything else is derivative:

- `Asset` and `Edge` are graph constituents
- `Package` is a module/library of graphs and graph functions
- `GraphFunction` is a reusable function that produces or transforms graphs
- `zoom`, `compose`, `fan_out`, `fan_in`, `gate`, and `promote` are graph operations

### 2. Graph roles are not rival types

Embeddable graphs, interface-declared graphs, bounded graphs, and locally substituted graphs are all still just graphs.

Those are useful roles or predicates.

They are not different kinds of thing.

### 3. Graphs are workflow programs

In GTL, a graph is not just a picture of topology.

It is a typed workflow/program value that can:

- encode deterministic checks
- encode probabilistic construction surfaces
- encode human or stakeholder gates
- be refined, composed, branched, reduced, and replayed

---

## Language Direction

GTL should be understood as a **functional, interpreted language for composing deterministic, probabilistic, and judgment-bearing programs under an event-sourced convergence model**.

In that framing:

- `Graph` is the program value
- `GraphFunction` is the reusable named program
- ABG is the interpreter
- evaluators are effectful execution surfaces over graph contracts
- the event stream is the truth substrate for replay and convergence

This yields the right split:

- **functional core**:
  - graph values
  - graph functions
  - graph composition laws
  - higher-order graph combinators
  - pure projection over event history
- **effectful shell**:
  - F_D execution
  - F_P execution
  - F_H approvals
  - runtime orchestration
  - event emission

---

## First-Class Types

### Graph

```python
@dataclass(frozen=True)
class Graph:
    name: str
    inputs: tuple[Asset, ...]
    outputs: tuple[Asset, ...]
    assets: tuple[Asset, ...]
    edges: tuple[Edge, ...]
    contexts: tuple[Context, ...] = ()
    effects: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
```

Meaning:

- `inputs` and `outputs` declare the graph contract
- `assets` and `edges` hold the internal structure
- `contexts` carry structural dependencies
- `effects` declare which execution regimes the graph composes across
- `tags` support discovery, classification, and policy hints

The important point is not the exact field list.

It is that the primary reusable structural value is `Graph`.

### GraphFunction

```python
@dataclass(frozen=True)
class GraphFunction:
    name: str
    inputs: tuple[Asset, ...]
    outputs: tuple[Asset, ...]
    build: Callable[..., Graph]
    effects: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
```

Meaning:

- a graph function is a reusable named workflow/program
- it has an explicit interface
- it materializes a graph
- it may cross deterministic, probabilistic, and human/judgment surfaces

This is what makes named workflows first-class rather than ad hoc Python helpers.

### Package

`Package` becomes the module surface for graph truth:

- base graph
- graph functions
- graph libraries
- candidate metadata
- interface families
- policy hints consumed by evaluators

The package is where structural possibility lives.

The event stream is where chosen reality lives.

---

## Graph Operations

### Sequential composition

```python
compose(gf_left, gf_right) -> GraphFunction
```

Meaning:

- compose two graph functions when the outputs of the left satisfy the inputs of the right
- the result is a new graph function with:
  - `inputs = left.inputs`
  - `outputs = right.outputs`

This is the first-class answer to workflow composition.

### Zoom as graph substitution

```python
zoom(outer_graph, edge, inner_graph) -> Graph
```

Meaning:

- replace a coarse edge contract with an interface-compatible graph
- preserve the outer contract
- expose the refined internal structure

Zoom is not a special-case refinement trick.

It is graph substitution.

### Spawn and fold-back

```python
spawn(parent_work, graph) -> child_work_lineage
fold_back(parent_work, child_lineage) -> parent_delta
```

Meaning:

- when a graph introduces child work, the engine materializes child lineage
- convergence on the parent becomes a function of child lineage truth

Spawn/fold-back are recursive graph application mechanics.

### Higher-order combinators

```python
compose(f, g)     # sequential composition
fan_out(f)        # apply a graph function across a collection/vector
fan_in(r)         # reduce branch outputs into a synthesized result
gate(g)           # require a gate before continuation or promotion
promote(p)        # lift one representation into another
```

These are graph combinators, not planners.

They are how the language expresses:

- branching
- joining
- voting
- consensus
- promotion from scalar to vector
- synthesis from many branch results back to one contract

---

## Existing Functionality, Reframed Through Graph

### Assets and edges

Assets and edges stay.

But they are no longer the highest-level semantic story.

They are the internal structural constituents of graphs.

### Evaluator triad

`F_D`, `F_P`, and `F_H` remain fundamental.

But they are better understood as effectful surfaces over graph contracts:

- `F_D`: deterministic validation or transformation over graph boundaries
- `F_P`: probabilistic construction or contextual selection over graph boundaries
- `F_H`: human or stakeholder gate over graph boundaries

They do not compete with graph.

They act over graph truth.

### Work identity

`work_key` is the lineage identity of graph application.

It scopes:

- convergence
- replay
- spawn/fold-back
- selection
- correction

The core unit is not “job in the abstract.”

It is “this graph application for this work lineage.”

### Run identity

`run_id` is an execution attempt over a graph application.

That makes run governance conceptually clean:

- runs are attempts
- work lineage is identity
- graph is structure

### Delta and convergence

`delta()` is graph-scoped truth over event history.

It tells you whether the graph contract for a given lineage has converged.

This makes convergence one law:

- not per helper
- not per command
- not per special structural subtype

It is graph truth under replay.

### Correction and reset

Correction becomes graph-certificate correction.

Reset does not damage structure.

It shadows certifications for a graph application within a lineage boundary.

The mental model becomes:

- graph remains
- history remains
- truth after a boundary is re-evaluated

### Leaf tasks

Leaf tasks are bounded graph-local subwork.

They are not a rival orchestration model.

They are small governed internal computations or dispatches that do not deserve a full top-level graph application of their own.

### Bootloader

The bootloader is a derived graph asset.

Its value is not “special bootstrap magic.”

Its value is that it is governed by the same graph truth:

- source-of-truth graph/materials exist
- deterministic consistency can be checked
- eventual synthesis can be governed
- drift can be detected and repaired

### Terminology translation

The graph-first reading of the current system is:

| Earlier term | Graph-first reading |
| --- | --- |
| `Asset` | Graph constituent and contract surface |
| `Edge` | Directed graph contract step |
| `zoom()` | Graph substitution |
| `spawn()` | Child graph-application lineage creation |
| `fold_back()` | Reduction of child lineage truth into parent graph truth |
| `work_key` | Lineage identity of graph application |
| `run_id` | Execution attempt over a graph application |
| `delta()` | Replayed truth function over graph application history |
| `reset` | Certification-shadowing boundary over graph truth |
| `LeafTask` | Bounded graph-local subwork |
| `Package` | Module/library of graphs and graph functions |
| `bootloader_doc` | Derived graph asset governed by the same convergence laws |

---

## Selection Boundary

The engine must not choose workflows strategically.

Selection is real, but it belongs above the kernel.

### Kernel responsibility

The kernel may:

- enumerate compatible graph functions for an edge or contract
- validate interface compatibility
- validate composition
- apply the selected graph
- record the choice and resulting topology

### Evaluator or business responsibility

Selection may be performed by:

- `F_D` when a deterministic rule is sufficient
- `F_P` when contextual analysis is needed
- `F_H` when stakeholder choice is required
- higher business/intent logic when selection is a product decision

### Declarative selection surface

The package may carry:

- candidate families
- interface-equivalent graph functions
- tags
- pattern hints
- optional priority hints

These are lawful inputs for selection.

They are not hidden engine heuristics.

---

## Event-Sourced Interpreter Model

ABG should be described as an interpreter over:

- graph truth from the package/module layer
- event truth from the event stream

The interpreter flow is:

1. identify unconverged graph application for a work lineage
2. enumerate compatible graph-function candidates if refinement/composition is needed
3. obtain selection from evaluator or intent/business layer
4. record the selection
5. materialize the selected graph
6. apply zoom/substitution if needed
7. spawn child lineage if needed
8. execute deterministic, probabilistic, or human gates
9. replay events and recompute graph truth via projection/delta

This is the right picture:

- package truth defines lawful possible structure
- event truth defines chosen and executed reality
- projection/delta defines current truth

### Selection provenance

Add an explicit control event such as:

```python
workflow_selected{
  edge,
  work_key,
  graph_function,
  selected_by,
  selection_mode,
  rationale?
}
```

This keeps selection replayable without moving strategy into the engine.

### Graph application provenance

Existing and future topology events should be read in graph terms:

- `zoomed`: graph substitution occurred
- `work_spawned`: graph application created child lineage
- `reset`: certifications for graph truth are shadowed after a boundary
- future branch/join events may capture fan-out/fan-in/gate/promote structure explicitly

---

## Composition Laws

The design should state the laws clearly.

### 1. Graph primacy

All workflow structure is graph.

No separate structural kind is needed for subgraph, bounded graph, or interface graph.

### 2. Interface law

A graph may substitute for a contract only when its declared inputs and outputs satisfy the outer contract.

### 3. Composition law

Graph functions compose only when interfaces align lawfully.

### 4. Associativity

Lawful composition groups without changing the outer contract.

### 5. Identity

An identity graph function preserves the interface.

### 6. Substitutability

Interface-equivalent graph functions are interchangeable at the contract boundary.

### 7. Contract preservation

Refinement may change internals but must preserve the outer contract.

### 8. Replayability

Chosen topology and resulting truth must be reconstructable from package truth plus event history.

### 9. Selection externality

Candidate enumeration is kernel behavior.

Choice is external behavior.

### 10. Lineage preservation

Composition, zoom, fan-out, fan-in, and fold-back must preserve explainable work lineage.

---

## Higher-Order Functional Direction

If GTL is graph-first, higher-order structure falls out naturally.

The next layer is not a different language.

It is the natural extension of graph combinators.

### Consensus as gate/reducer

Consensus should not remain only edge metadata.

It should also be available as a graph-level gate or reducer over branch outputs.

Example:

- `intent_event -> gate(consensus(2, 3)) -> intent_vector`

### Promotion and vectorization

The language should support promotion between representations:

- event to vector
- vector to branch set
- branch set to synthesized result
- synthesized result to new context

### Fan-out and fan-in

The language should express:

- branch creation
- branch execution
- branch reduction
- gated continuation

as first-class graph operations rather than runtime accidents.

This is the path toward:

- multi-discovery workflows
- consensus-gated promotion
- higher-order exploration programs
- imported graph-function libraries
- distributed saga coordination

---

## What This Solves

### Scenarios 11 and 12

They become properly first-class because:

- named workflows are graph functions
- reusable application is lawful graph reuse
- repeated application is distinct in lineage and provenance

### Scenario 13

It becomes real because composition is a first-class graph-function operation rather than manual assembly.

### Scenario 14

It becomes real because:

- the engine enumerates candidates
- selection is explicit
- the choice is replayable

### Scenarios 15 to 18

They become the natural higher-order layer:

- gate
- promote
- fan_out
- fan_in

### Scenarios 19 to 23

They become easier to place:

- leaf tasks are bounded graph-local subwork
- bootloader is graph-derived self-description
- cross-package propagation is graph/module propagation
- imported libraries are graph-function libraries
- saga coordination is distributed lineage over graph applications

---

## Minimal Kernel Changes

1. Make `Graph` the first-class GTL structural type.
2. Remove separate subgraph ontology; keep one structural type: `Graph`.
3. Add `GraphFunction`.
4. Add `Package.graph_functions` and related library/catalog surfaces.
5. Replace first-match embedded-graph lookup with candidate enumeration over graph functions.
6. Add lawful graph-function composition.
7. Make zoom operate as graph substitution.
8. Add or formalize higher-order graph combinators: `fan_out`, `fan_in`, `gate`, `promote`.
9. Add replayable selection provenance such as `workflow_selected`.
10. Rephrase runtime/event doctrine in terms of graph application, lineage, and replay.

---

## Recommended Phasing

### Phase 1: Graph-first reframe

- make `Graph` explicit
- remove legacy subgraph terminology from the design surface
- update docs and doctrine to use graph-first language

### Phase 2: First-class graph functions

- add `GraphFunction`
- add package catalog/library surface
- add candidate enumeration

### Phase 3: Composition and substitution

- add lawful composition
- add interface validation
- formalize zoom as graph substitution

### Phase 4: Higher-order combinators

- add `fan_out`
- add `fan_in`
- add `gate`
- add `promote`
- lift consensus into reusable gate/reducer semantics

### Phase 5: Selection provenance and interpreter wiring

- add explicit workflow-selection events
- wire evaluator-driven choice into graph application
- keep strategy outside the kernel

### Phase 6: Scenario and test migration

- restate scenario set in graph-first terms
- derive tests from graph laws and product scenarios
- retire implementation-mirror language and tests

---

## Bottom Line

The correct end-state is:

- a graph-first functional language
- interpreted by ABG
- event-sourced for replay and convergence
- composition-aware
- selection-blind
- capable of sequential, recursive, and higher-order graph composition

The main simplification is this:

**everything is graph.**

Once that is accepted:

- composition becomes normal
- refinement becomes substitution
- fan-out/fan-in/gate/promote become ordinary graph combinators
- old special cases collapse into clearer roles
- the existing functionality becomes easier to explain, test, and extend

That is the coherent proposal.
