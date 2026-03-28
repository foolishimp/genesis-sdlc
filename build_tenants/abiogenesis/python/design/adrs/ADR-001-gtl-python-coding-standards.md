# ADR-001 — GTL And Python Coding Standards

**Status**: Approved
**Date**: 2026-03-28
**Implements**: `REQ-F-GRAPH-*`, `REQ-F-CMD-*`, `REQ-F-CUSTODY-*`, `REQ-F-TEST-*`

---

## Context

The GTL library is intentionally permissive. It provides the semantic primitives for graph, work,
operator, evaluator, and module declaration, but it does not impose one composition style.

That freedom is necessary. Over-constraining GTL at the engine layer would collapse design range and
turn local discipline into framework dogma.

At the same time, the `abiogenesis/python` realization has now learned a set of coding patterns that
make this domain materially easier to reason about, qualify, and evolve:

- narrow authority context beats ambient context
- explicit transform contracts beat vague constructive prompts
- deterministic judges should certify artifacts separately from the agent that constructs them
- package boundaries should stay cheap to import and explicit about side effects
- Python composition should remain modular, typed, and readable rather than ceremonial

This ADR records those lessons as variant-local design standards.

---

## Decision

`abiogenesis/python` adopts the following coding standards.

### 1. GTL stays permissive

These standards apply to this realization. They are not promoted as engine law for GTL itself.

GTL remains a library of primitives, not a mandatory architectural style.

### 2. Composition is explicit

Use GTL primitives directly, but compose them in small, named surfaces:

- asset declarations in one place
- graph and evaluator declarations in one place
- requirement loading and publication boundaries in one place
- transform contracts in one place

Do not bury realization law inside ad hoc strings or hidden side effects.

### 3. Edge transforms are first-class design surfaces

For constructive `F_P` edges, declare the transform contract explicitly:

- authority contexts
- target artifact kind
- suggested output location
- bounded guidance
- deterministic certification boundary

Common edge patterns should be factored into named Python constants, dataclasses, or helper
functions rather than repeated inline across tests or runtime code.

### 4. Deterministic and probabilistic work stay separated

Use the agent for bounded construction or bounded judgment.

Use deterministic checks for:

- file existence
- structural sections
- traceability markers
- version/spec-hash currency
- reference validity

Do not ask the agent to certify what Python can check directly.

### 5. Context is intentionally narrow

Edge context should be the minimum lawful authority surface for that edge.

Prefer edge-local context families over one large shared context bundle. Add breadth only when the
edge genuinely needs it.

### 6. Python should be best-of-breed, not ceremonial

Within this realization:

- prefer small pure helpers over sprawling control flow
- use named constants for repeated textual contracts
- use dataclasses where they make contracts clearer
- keep import-time side effects minimal
- keep filesystem discovery explicit and deterministic
- prefer clear composition over magic or implicit global state

This is meant to produce good Python, not pseudo-framework COBOL.

### 7. Lazy boundaries are allowed when dependency weight matters

If importing a surface would eagerly pull in the full runtime stack, use a lazy export boundary so
lightweight consumers can access design-level helpers without paying for engine initialization.

### 8. Qualification patterns may become defaults

When a live-qualification or steel-thread pattern proves broadly reusable, it may be promoted into
the realization as a default helper or contract registry.

Promotion should capture the pattern, not the scenario-specific artifact names or one-off project
content.

---

## Consequences

- the realization keeps GTL flexible while still benefiting from disciplined composition
- common constructive-edge patterns can be reused without copy-paste drift
- edge qualification becomes easier to automate because the transform contract is explicit
- Python stays modular and readable instead of collapsing into one giant orchestration file
- future realizations may borrow these standards, but they are not forced to inherit them as engine law
