# GTL 2.x Domain Model

**Status**: Draft
**Date**: 2026-03-24
**Purpose**: Define the core domain model of GTL 2.x as a graph-first Python DSL/SDK.

---

## 1. Core Principle

The core structural type is `Graph`.

Everything else is:

- a constituent of graph
- a declared action surface over graph
- a reusable function that builds or transforms graph
- or a module-level organization surface

There is no need for a second structural type for bounded or embeddable graph structure.

Current GTL should be understood as a partial projection of this fuller model.

It already contains:

- typed topology
- operator regimes
- rule surfaces
- recursive and compositional hints

But it still centers `Asset`, `Edge`, `Job`, `Worker`, `Package`, and runtime-oriented constructs more than the fuller GTL 2.x algebra does.

---

## 2. Core Types

### 2.1 Graph

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
    tags: tuple[str, ...] = ()
```

Responsibilities:

- declare boundary/interface
- contain internal structure
- carry local constraints
- serve as the unit of substitution and composition

### 2.2 Node[T]

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

- a node has local graph identity
- a node carries a declared semantic/schema type
- multiple nodes may share the same schema while remaining distinct nodes

This is the cleaner reading of what the current system partially models through `Asset`.

### 2.3 Interface

Interface is expressed through designated graph boundary nodes.

Inputs and outputs are not a rival type system.

They are graph roles over nodes.

Interfaces are how GTL expresses:

- required inputs
- promised outputs
- compatibility between graphs
- compatibility between graph functions

The exact representation can be lightweight, but GTL 2.x should treat interface as explicit rather than inferred from ad hoc structural coincidence.

### 2.4 Edge / Vector

`Edge` is a directed graph vector between typed nodes.

Edges carry:

- source
- target
- operators
- optional local tags or constraints

Edges are graph-local program steps.

They are not a rival structural ontology.

An edge is a minimal graph shape.

### 2.5 Asset as Schema Payload

The current `Asset` concept fits best as:

- a node payload/schema declaration
- or a domain-specific schema class used by `Node[T]`

That means GTL 2.x should avoid making `Asset` the structural center.

`Asset` is better understood as the semantic type carried by nodes.

### 2.6 Operator

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

Possible regimes:

- deterministic
- probabilistic
- human

This keeps the current evaluator triad while giving it a cleaner language-level shape.

### 2.7 Rule

`Rule` is a declarative constraint or gate.

Examples:

- consensus threshold
- type consistency
- coverage minimum
- policy gate

Rules belong to the language surface.

Their execution belongs to the interpreter.

### 2.8 GraphFunction

`GraphFunction` is a reusable named workflow abstraction.

Conceptually:

```python
@dataclass(frozen=True)
class GraphFunction:
    name: str
    inputs: tuple[Node[Any], ...]
    outputs: tuple[Node[Any], ...]
    build: Callable[..., Graph]
    tags: tuple[str, ...] = ()
```

Responsibilities:

- capture reusable workflow patterns
- produce named graph programs
- support libraries and importable workflow modules
- support composition and higher-order graph behavior

### 2.9 Module

`Module` is the top-level organizational unit.

A module owns:

- base graphs
- graph functions
- operator declarations
- rules
- imports
- metadata visible to policy/evaluator layers

---

## 3. Derived Concepts

These are not new structural kinds.

They are views or properties over graphs.

### 3.1 Interface-bearing graph

A graph with explicit boundary nodes suitable for substitution or composition.

### 3.2 Recursive graph

A graph whose application may induce child graph applications.

### 3.3 Higher-order graph program

A graph or graph function participating in fan-out, fan-in, gating, or promotion.

### 3.4 Imported graph function

A graph function supplied by another module/library.

### 3.5 Primitive edge graph

A graph whose internal structure is just one directed vector between typed nodes.

This is the cleaner GTL 2.x interpretation of a primitive edge declaration.

---

## 4. Relationships

The domain model can be summarized as:

- modules contain graphs, graph functions, operators, and rules
- graphs contain typed nodes, edges/vectors, contexts, and rules
- edges carry operators
- graph functions build graphs
- rules constrain graph contracts

This is enough to define the core language surface.

---

## 5. Out of Scope for the Language Model

These are important, but they are not GTL core domain concepts:

- event stream
- work lineage
- run attempts
- retries
- resets
- provenance binding
- convergence calculation

Those belong to ABG as interpreter/runtime.

---

## 6. Summary

The GTL 2.x domain model is intentionally small:

- `Graph`
- `Node[T]`
- `Edge`
- `Operator`
- `Rule`
- `GraphFunction`
- `Module`

That is enough for a graph-first Python DSL/SDK without carrying forward unnecessary structural duplication.
