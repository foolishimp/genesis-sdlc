# HANDOFF: ABG Theory Pressure Test — Category, Sheaf, Temporal, TCP, Event Calculus, Agile

**Author**: Codex
**Date**: 2026-03-21T15:18:42
**For**: Claude Code
**Purpose**: incorporate into ABG 1.0 closure work as a formal gap-finding method

## Position

If the goal is to close `abiogenesis` at 1.0 with confidence, one useful method is to pressure-test the current model through several strong theoretical lenses and ask the same question each time:

`What is already represented, what is missing, and does the gap force a new primitive?`

This should not become a literature exercise. It should become a disciplined model audit.

The central question across all lenses is:

`What formal mechanism turns locally converged hops into a globally truthful solution to the intended problem?`

## Proposed Use

For each lens below, Claude should capture:

1. what the current ABG/GTL model already expresses
2. what the lens reveals as missing or weakly formalized
3. whether that gap is:
   - primitive gap
   - composition-law gap
   - spec clarification gap
   - build/runtime realization gap

That output should feed directly into the ABG 1.0 closure matrix.

---

## 1. Category Theory

### What the current model already has

- `Asset` as object-like structure
- `Edge` / `Job` as morphism-like structure
- `Worker` as capability over morphisms
- typed traversal from source to target

### Pressure points

- Is edge composition explicit, or only implicit in the declared job order?
- Is there a formal composition law for whole workflows, or only for single hops?
- Can `intent -> composition set -> routed workflow` be expressed as composition without new ontology?
- Is observer/model formation functorial, or currently just "some bound contexts"?

### Likely missing concept

- a higher-order composition law over workflows and observers

### Likely classification

- probably **composition-law gap**, not new primitive

---

## 2. Sheaf Theory

### Why this lens matters

This is likely the highest-yield lens for the failures already observed.

### What the current model already has

- local context surfaces on each edge via `Context[]`
- local evaluators
- local convergence judgments

### Pressure points

- What is the gluing law from local truth to global workflow truth?
- What are the consistency conditions between overlapping context surfaces?
- When do multiple locally valid edge results fail to assemble into a globally valid section?

### Why this matters concretely

The requirements custody failure is sheaf-shaped:
- local checks passed
- the global truth was false
- there was no valid global section binding authored requirements into runtime custody

### Likely missing concept

- explicit global consistency / gluing semantics

### Likely classification

- likely **spec clarification + composition-law gap**
- only becomes a primitive gap if the existing model truly cannot represent global consistency

---

## 3. Temporal Theory

### What the current model already has

- explicit iteration
- blocked / converged / failing stop reasons
- revocation and reassessment
- workflow version lineage

### Pressure points

- how are intent refinement and supersession represented over time?
- what is the lifecycle of a derived intent?
- what temporal states exist for orphaned, stale, superseded, or partially observed work?
- how do higher-order observers evolve their model across iterations?

### Likely missing concept

- temporal semantics for intent refinement / supersession at network scale

### Likely classification

- likely **spec clarification gap**, possibly **composition-law gap**

---

## 4. Event Calculus

### What the current model already has

- strong local fluent model for `operative` and `certified`
- revocation
- event-scoped convergence logic

### Pressure points

- are there enough fluents for workflow-scale truth, not just edge-scale truth?
- is intent formation only "happensAt" today, or does it need stronger lifecycle semantics?
- how are observer-model updates represented?
- what formal relation exists between local fluents and global satisfaction?

### Likely missing concept

- workflow/global fluents or derived states beyond current edge-local focus

### Likely classification

- likely **spec clarification gap**

---

## 5. TCP / Network Theory

### Why this lens matters

This is the most operationally intuitive lens.

### What the current model already has

- hop-local traversal
- gating/order
- deterministic failure reporting
- bounded dispatch model

### Pressure points

- what counts as reliable delivery for a hop?
- what are acknowledgment semantics across composed workflows?
- what are retry / retransmit semantics for blocked or orphaned work?
- what is the backpressure/flow-control story across multiple workers or compositions?
- how is end-to-end correctness distinguished from per-hop success?

### Important distinction

- `abg` can plausibly be the hop/transport substrate
- but global delivery and routing truth are not yet formalized strongly enough

### Likely missing concept

- end-to-end assurance semantics distinct from local hop success

### Likely classification

- likely **composition-law gap**

---

## 6. Agile Delivery

### Why this belongs here

Agile is not just process rhetoric here. It pressure-tests whether the model can refine the problem, not merely execute a fixed graph.

### What the current model already has

- iterative graph traversal
- intent and requirements as mutable upstream artifacts
- backlog / `intent_raised` / promotion surfaces

### Pressure points

- can the system formally represent progressive refinement of "what done means"?
- can new intent emerge from observation against a model, not only from a human typing a new feature?
- can the system route a derived intent into the right composition (`gsdlc`, `PoC`, `Discovery`, `Research`)?
- can tests and acceptance surfaces evolve with the narrowed problem definition?

### The key agile question

Is the system converging on the **problem** as understanding sharpens, or only on the current implementation against its own tests?

### Likely missing concepts

- explicit `ObserverModel`
- explicit `CompositionSet`
- stronger intent-refinement / routing semantics

### Likely classification

- mostly **composition-law gap**
- possibly **spec clarification gap**

---

## Cross-Lens Synthesis

These lenses point toward the same likely missing abstractions.

### Candidate missing abstraction 1: `ObserverModel`

Current practical reading:
- today the model is roughly `spec + design`
- more formally: the context-composed model against which observed state is evaluated

Use:
- `gap = delta(observed_state, observer_model)`
- intent forms relative to an observer scope and its model

Question for Claude:
- can this be modeled as structured `Context[]` composition?
- or does it need a first-class type?

### Candidate missing abstraction 2: `CompositionSet`

Current need:
- `intent` does not route only to `gsdlc`
- it may route to `gsdlc`, `PoC`, `Discovery`, `Research`, or combinations

Question for Claude:
- is this just a named composition/macro library over existing GTL/ABG semantics?
- or is there a real missing primitive here?

### Candidate missing abstraction 3: Global Truth / Gluing

Current need:
- local convergence must assemble into global satisfaction

Question for Claude:
- can the current model express when local truths fail to compose into a valid global section?
- if not, where does that belong?

## Suggested Output Format for Claude

Claude should incorporate a matrix like:

| Lens | Current ABG/GTL Strength | Revealed Gap | Classification | Forces New Primitive? | 1.0 Impact |
|------|---------------------------|--------------|----------------|-----------------------|------------|
| Category | typed hop structure | workflow composition law | composition | likely no | medium |
| Sheaf | local contexts/evaluators | global gluing/consistency | spec + composition | maybe not | high |
| Temporal | iteration/revocation | intent supersession semantics | spec | likely no | medium |
| Event Calculus | local fluents | workflow/global fluents | spec | maybe not | medium |
| TCP | hop reliability | end-to-end assurance | composition | likely no | high |
| Agile | iterative refinement | observer-relative intent routing | composition + spec | maybe not | high |

## Decision Rule

The burden of proof should be:

- if a gap can be handled by better composition law, do not add a primitive
- if a gap can be handled by clearer spec semantics, do not add a primitive
- only propose a new primitive if multiple lenses fail for the same reason and the existing ontology cannot express the needed structure

## Likely Outcome

My current expectation is that ABG 1.0 can probably be closed **without** new primitives, but only if the composition law is made much more explicit around:

- observer-relative homeostasis
- intent formation against a model
- routing intent into a composition set
- assembling local convergence into global truth

That is exactly the area Claude should now pressure-test.
