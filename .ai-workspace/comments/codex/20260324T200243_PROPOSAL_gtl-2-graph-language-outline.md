# GTL 2.x Design Outline: Graph-First Language and Domain Model

**Status**: Working proposal
**Date**: 2026-03-24
**Purpose**: Propose a cohesive standalone GTL language design and domain model centered on graphs, operators, composition, recursion, and higher-order graph functions, with ABG framed as the interpreter/runtime rather than the language itself.

---

## 1. Position

GTL should now be treated as a standalone language design.

Not:

- old GTL plus patches
- ABG-specific topology notation
- a narrow workflow schema with ad hoc composition

But:

- a graph-first language
- for expressing deterministic, probabilistic, and judgment-bearing programs
- with first-class composition, substitution, recursion, and higher-order graph operators

ABG then becomes:

- the interpreter
- the convergence runtime
- the event-sourced truth engine

for GTL programs.

This is an evolution of the current system, but the design should now be written as a clean language proposal rather than as a stack of backward-looking amendments.

---

## 2. Core Thesis

The irreducible structural unit of GTL is `Graph`.

Everything else is either:

- a constituent of graph
- a function over graphs
- a rule over graph contracts
- or interpreter/runtime machinery over graph execution and replay

This leads to a small, coherent language core:

- `Graph`
- `Operator`
- `GraphFunction`
- `Rule`
- `Module`

with core operations:

- composition
- substitution
- recursion
- fan-out
- fan-in
- gating
- promotion

---

## 3. Design Goals

1. Make `Graph` the one first-class structural type.
2. Make `Operator` the first-class effectful action surface.
3. Make reusable named workflows first-class through `GraphFunction`.
4. Make composition a normal language operation rather than a special feature.
5. Make recursion and refinement native to the model.
6. Support higher-order graph programming: branch, join, gate, promote.
7. Keep strategic selection outside the language core and outside the interpreter core.
8. Let ABG interpret GTL through event sourcing, projection, and convergence.
9. Minimize legacy vocabulary in the language definition.
10. Produce a clean foundation for fresh requirements, ADRs, tests, and implementations.

---

## 4. Language vs Runtime Boundary

This separation should be explicit from the start.

### GTL language owns

- structural graph values
- operator declarations
- graph contracts
- graph functions
- composition laws
- substitution laws
- recursive and higher-order graph operations
- module/package/library structure

### ABG runtime owns

- event emission
- projection
- delta/convergence
- work lineage
- run attempts
- retries
- resets/correction boundaries
- provenance binding
- replay
- evaluator execution

This prevents interpreter mechanics from polluting the language core.

---

## 5. GTL 2.x Domain Model

### 5.1 Graph

`Graph` is the primary value.

A graph is a typed workflow/program with:

- a declared interface
- internal structure
- operator-bearing transitions
- optional contexts and rules

Minimal conceptual shape:

```python
@dataclass(frozen=True)
class Graph:
    name: str
    inputs: tuple[Port, ...]
    outputs: tuple[Port, ...]
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]
    contexts: tuple[Context, ...] = ()
    rules: tuple[Rule, ...] = ()
    tags: tuple[str, ...] = ()
```

The exact field names can change.

What should not change is:

- graph is the one structural type
- interface is part of graph
- embeddability is a property of graph, not a separate type

### 5.2 Port / Interface

GTL needs a clear interface concept.

The graph boundary should be described through ports or equivalent interface declarations.

This is how the language decides:

- substitutability
- composition legality
- candidate compatibility
- graph reuse

### 5.3 Node

A node is a state surface or semantic locus within a graph.

Whether GTL continues to call these `Asset`s or moves to a more language-shaped term is a naming choice.

The important point is:

- nodes belong to graph
- they are not the top-level semantic center

### 5.4 Edge

An edge is a directed contract step within a graph.

Edges relate node/interface state and carry one or more operators.

### 5.5 Operator

`Operator` is the typed effectful action surface.

This is one of the important stabilizations for GTL 2.x.

Operators should carry:

- name
- effect regime
- execution binding
- optional policy or safety metadata

Conceptually:

```python
@dataclass(frozen=True)
class Operator:
    name: str
    regime: Regime
    binding: str
    tags: tuple[str, ...] = ()
```

where `Regime` includes:

- deterministic
- probabilistic
- human

This preserves the current evaluator triad while making it look like language-level operator classes rather than ad hoc runtime categories.

### 5.6 Rule

Rules are declarative constraints or gates over graph contracts.

Examples:

- consensus thresholds
- type-consistency requirements
- coverage requirements
- policy gates

Rules are part of the graph language surface.

Their execution and truth are interpreter concerns.

### 5.7 GraphFunction

`GraphFunction` is a reusable named workflow program that builds or transforms graphs.

Conceptually:

```python
@dataclass(frozen=True)
class GraphFunction:
    name: str
    inputs: tuple[Port, ...]
    outputs: tuple[Port, ...]
    build: Callable[..., Graph]
    tags: tuple[str, ...] = ()
```

This is the mechanism for:

- reusable workflows
- named compositions
- imported workflow libraries
- higher-order graph programming

### 5.8 Module

The module/package surface should own:

- base graphs
- graph functions
- operator declarations
- rule families
- imported libraries
- candidate metadata visible to selection logic

This is where lawful structural possibility is declared.

---

## 6. Core Semantics

### 6.1 Graph primacy

All workflow structure is graph.

There should be no rival structural ontology for:

- subgraph
- interface graph
- bounded graph
- embedded graph

These are all graphs.

### 6.2 Interface satisfaction

A graph may substitute for a contract only when its declared inputs and outputs satisfy the outer interface.

### 6.3 Composition

Graphs and graph functions compose when interfaces align lawfully.

### 6.4 Substitution

Refinement is substitution:

- a graph may replace a coarse edge contract with a finer graph that preserves the outer interface

### 6.5 Recursion

A graph may induce child graph applications.

Recursive decomposition is therefore part of the language trajectory, not a runtime hack.

### 6.6 Higher-order structure

Graphs and graph functions may be:

- composed
- mapped across collections
- reduced
- gated
- promoted between representations

---

## 7. Core Operations

### 7.1 Sequential composition

```python
compose(f, g)
```

Meaning:

- chain two graph functions lawfully
- preserve interface truth
- produce a new graph function

### 7.2 Substitution

```python
substitute(outer_graph, contract_edge, inner_graph)
```

Meaning:

- replace a coarse contract step with a finer graph

This is the graph-first name for what older language called `zoom`.

### 7.3 Recursion

```python
recurse(graph, lineage)
```

Meaning:

- graph application may produce child graph applications with preserved lineage

This is a semantic capability, not necessarily a literal surface API.

### 7.4 Fan-out

```python
fan_out(f)
```

Apply a graph function across a vector or collection.

### 7.5 Fan-in

```python
fan_in(r)
```

Reduce multiple branch outputs into a synthesized result.

### 7.6 Gate

```python
gate(g)
```

Require a gate before continuation or promotion.

Consensus should be expressible here.

### 7.7 Promote

```python
promote(p)
```

Lift one representation into another:

- event to vector
- vector to branch set
- synthesized result to new context

---

## 8. Laws

GTL 2.x should state its laws directly.

1. **Graph primacy**
   All workflow structure is graph.

2. **Interface law**
   Composition and substitution require interface satisfaction.

3. **Associativity**
   Lawful composition groups without changing the outer contract.

4. **Identity**
   Identity graph functions preserve interface.

5. **Substitutability**
   Interface-equivalent graphs or graph functions are interchangeable at the contract boundary.

6. **Contract preservation**
   Internal refinement may change internals but must preserve the declared outer contract.

7. **Recursion legality**
   Child graph application must preserve explainable lineage.

8. **Higher-order legality**
   Fan-out, fan-in, gate, and promote must preserve type/interface truth.

9. **Interpreter separation**
   Strategic choice is not a language law.

10. **Replay suitability**
    GTL constructs must be interpretable by an event-sourced runtime.

---

## 9. Selection and Policy

Selection exists, but it should not be baked into the GTL core as hidden engine intelligence.

The language should expose:

- candidate visibility
- tags
- interface families
- optional policy hints

The interpreter may enumerate lawful possibilities.

Choice should be made by:

- deterministic rule evaluation
- probabilistic contextual analysis
- human judgment
- or higher business logic

This keeps GTL structural and keeps ABG honest.

---

## 10. ABG as Interpreter

ABG should now be described in terms of graph interpretation.

### ABG input

- GTL graphs
- GTL graph functions
- GTL operators
- module declarations
- event history

### ABG responsibilities

- materialize graph functions
- enumerate compatible graph candidates
- apply substitutions
- execute operator surfaces
- emit replayable events
- project truth from events
- compute convergence
- preserve lineage
- govern attempts, retries, resets, and provenance

### ABG output

- current graph truth
- unconverged graph applications
- emitted event history
- convergence and next action surfaces

This makes ABG clearly a runtime/interpreter rather than part of the language ontology.

---

## 11. Reframing Existing Capability

The current body of work can be re-read this way:

- typed asset graph -> graph domain model
- evaluators -> operator regimes
- zoom -> graph substitution
- spawn/fold-back -> recursive graph application
- work_key -> lineage identity over graph application
- run_id -> execution attempt over graph application
- delta -> replayed truth over graph application history
- correction/reset -> graph-certificate boundary rules
- provenance -> interpreter binding of graph truth to versioned context
- bootloader -> derived graph artifact

This is why the graph-first design simplifies rather than discards existing progress.

---

## 12. Fresh GTL 2.x Document Stack

Rather than continue to patch older materials, the next clean design stack should be:

1. `GTL_2_INTENT.md`
2. `GTL_2_DOMAIN_MODEL.md`
3. `GTL_2_LANGUAGE.md`
4. `GTL_2_SEMANTICS.md`
5. `GTL_2_OPERATOR_MODEL.md`
6. `GTL_2_HIGHER_ORDER_COMPOSITION.md`
7. `GTL_2_ABG_INTERPRETER_BOUNDARY.md`
8. `GTL_2_MIGRATION.md`

Only the migration document should spend real energy on legacy terminology.

The others should read as a clean language design.

---

## 13. Requirement Mining Strategy

The current requirement set should be mined into three buckets:

### Preserve as GTL language law

Examples:

- typed interfaces
- composition and substitution
- graph reuse
- operator classes
- graph/module structure
- higher-order workflow semantics

### Preserve as ABG interpreter law

Examples:

- event calculus
- projection
- delta
- work lineage
- run attempts
- retries
- reset/correction
- provenance

### Drop as legacy phrasing

Examples:

- special structural terminology that duplicates graph
- old boundary concepts that no longer add semantic value
- command-shaped wording embedded in language law

---

## 14. Open Design Choices

These should be decided early in GTL 2.x:

1. Whether `Asset` remains the language term for node/state surfaces.
2. Whether `Port` or `Interface` is the better boundary term.
3. Whether operator regimes are named as:
   - deterministic / probabilistic / human
   or
   - F_D / F_P / F_H
4. Whether `substitute` replaces `zoom` in public language.
5. Whether modules and packages are separate concepts.
6. How imported graph-function libraries are represented.
7. How much higher-order structure is in the first public increment versus staged later.

---

## 15. Immediate Next Moves

1. Accept the graph-first premise explicitly.
2. Use this outline to draft `GTL_2_INTENT.md`.
3. Draft `GTL_2_DOMAIN_MODEL.md` without legacy terminology.
4. Draft `GTL_2_LANGUAGE.md` around graphs, operators, graph functions, and core operations.
5. Draft `GTL_2_ABG_INTERPRETER_BOUNDARY.md` so runtime concerns stay separate.
6. Only then re-mine the current requirements and ADRs into the new stack.

---

## Bottom Line

The strongest next step is not another local adjustment to ABG-era vocabulary.

It is to define GTL 2.x cleanly as:

- a graph-first language
- with operators as effectful action surfaces
- with graphs and graph functions as first-class values
- with native composition, substitution, recursion, and higher-order operations
- and with ABG positioned cleanly as the event-sourced interpreter/runtime

That is the design that gives you:

- simpler ontology
- cleaner requirements
- cleaner ADRs
- cleaner tests
- clearer product scenarios
- and a much stronger language foundation

for the next increment.
