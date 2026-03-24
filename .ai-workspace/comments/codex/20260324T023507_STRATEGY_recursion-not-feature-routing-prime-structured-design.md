# STRATEGY: Recursion, Not Feature Routing — Recover the Prime Structured Design

**Author**: codex  
**Date**: 2026-03-24T02:35:07+11:00  
**For**: all

## Summary

The current discussion about “per-feature routing” is naming the symptom, not the design.

The original design was not:
- one imperative scheduler with edge-specific exceptions
- one global job per edge plus special-case feature handling

The original design was:
- a small lawful kernel
- recursive work at variable grain
- topology as the stable structure
- routed work identity above the iterator
- compositional subgraphs with interface-preserving refinement

So the right recovery is not a bespoke feature-aware scheduler.

It is:
- recursion
- immutable work identity
- compositional graphs

## Original Design Direction

The monolith was designed from a category-theoretic direction that already implied:

- **zoom morphism**
  - lawful movement between grains without changing the underlying formal system
- **spawn / fold-back**
  - zoom into a child traversal, then collapse the result back into the parent judgment
- **graph_fragment**
  - executable subgraph / dispatch intermediate, smaller than the whole package
- **named compositions**
  - lawful reusable patterns above the primitives
- **child lineage**
  - recursive work creates new lawful descendants, not ad hoc mutable state

These are not optional embellishments. They are the structure that makes the model compositional.

## What Went Wrong in the Split

The split simplified the building blocks too far.

It effectively became:

- `Job = edge`
- scheduler walks edges
- feature appears only as an event/projection annotation

That creates the current mismatch:

- events know about `(edge, feature)`
- certificates know about `(edge, feature)`
- projections can observe feature-scoped state
- but jobs are still only edge-scoped

This makes the system look like it needs “feature routing”.

That is the wrong diagnosis.

## Kernel vs Routed Work

The iterator is like an engine running on tracks.

- **topology** = the track network
- **iterate()** = the transport primitive
- **routed work identity** = which concrete unit of work is moving over the track
- **recursion** = the same lawful machinery running at narrower grain

This is closer to:

- don’t change TCP
- add IP

The transport primitive does not need to become imperative and special-cased.
The missing layer is the addressing/routing layer above it.

The intended design is prime-structured and functional:

1. a small lawful kernel
2. recursive application at arbitrary grain
3. scope narrowing by lawful binding
4. composition from stable primitives, not orchestration accretion

So instead of asking:

- “how do we make this edge handle feature X?”

the right question is:

- “what is the recursively scoped work unit being traversed here?”

## Work Identity

Keep the transport/kernel primitive:

- `iterate(...)`

Keep the stable topology:

- `Job`
- `Edge`
- `Package`

Add the missing routed work identity:

```python
work_key   # immutable identity of the piece of work
run_id     # one attempt / traversal / transaction on that work
```

The important correction is that `work_key` does not need to be an arbitrary surrogate id if the chain itself is lawful and immutable.

If the work identity is already expressible as an immutable chain such as:

```text
INT-001 / REQ-042 / build.design / module.auth
```

then that chain **is** the work identity.

Every event for that unit of work carries:

```yaml
work_key: INT-001/REQ-042/build.design/module.auth
run_id: 7d8c...
```

This gives:

- `work_key`
  - identity of the piece of work
  - stable across time
  - used for projection / current-state derivation
- `run_id`
  - identity of one attempt on that work
  - used for retries, transactions, timing, and audit

Because the event log is project-local, a separate `project_key` is not needed yet. If global federation across projects ever matters, the identity can later be lifted to:

```text
(project_key, work_key)
```

without changing the local model.

So the operative shape is:

```python
iterate(job, work_key, run_id, ...)
```

This gives one lawful mechanism for:

- requirement-level work
- feature-level work
- module-level work
- gap repair
- child decomposition
- subgraph traversal

No bespoke feature scheduler is required.

## Event-Sourced Meaning

This is not a departure from the event-sourcing model.

It is the completion of it.

The event stream remains the authority. The only addition is that the stream now records work against a first-class work identity:

- all events for the same piece of work share the same `work_key`
- each attempt over that work gets its own `run_id`
- projection reconstructs current state from `work_key`
- attempt history is reconstructed from `run_id`

If recursion occurs, the child is simply a more refined immutable key:

```text
INT-001/REQ-042/build.design
INT-001/REQ-042/build.design/module.auth
INT-001/REQ-042/build.design/module.policy
```

Fold-back is then a higher-level projection over descendant keys, not a special imperative mechanism.

## What Zoom Actually Means

`zoom` is not just “show me more detail”.

It is a lawful local refinement where a previously opaque step is expanded into a richer subgraph that introduces new intermediate assets and stages while preserving the outer contract.

Example:

```text
Coarse:
  design -> code

Zoomed:
  design -> module_decomp -> build_schedule -> code_units -> code
```

The outer graph still sees:

- input compatible with `design`
- output compatible with `code`

The zoomed graph makes explicit:

- additional stages
- additional assets
- additional convergence surfaces

So zoom is:

- lawful refinement
- asset introduction
- topology expansion

without requiring the whole graph to be redesigned.

This is why zoom matters so much:

- structure can be introduced only where needed
- the kernel does not change
- refinement is local, not imperative global surgery

## Dynamic Graph as Realized Traversal

The design does support the ambition of a dynamic graph, with one important boundary:

- the **realized instance path** is dynamic
- the **governing law** remains lawful and replayable

The engine running on the tracks does not need to know all future edges in advance.

It only needs:

- its current position
- its accumulated past
- the current lawful context
- the admissible next move at this junction

At each step it:

1. projects current state from the event log
2. gathers accumulated intent and context
3. traverses one lawful edge
4. transforms content into the next node
5. emits events
6. projects again
7. continues

That gives a dynamic **instance** graph without requiring arbitrary topology mutation from nowhere.

The clean reading is:

- package law defines the latent lawful space
- runtime realizes only the path actually needed
- zoom introduces intermediate assets locally
- spawn creates refined descendants
- fold-back projects descendants into the parent contract

So “dynamic graph” should mean:

- dynamic realized traversal
- lawful local refinement

not:

- unconstrained runtime invention with no governing structure

## Pedantic Prime Graph

At the limit, the whole system can start from the smallest possible graph:

```text
intent -> outcome
```

Everything else is refinement of that unresolved edge.

If `intent -> outcome` does not converge, the system does not need to treat that as a scheduler failure. It can:

1. record the failed or incomplete attempt truthfully
2. run gap analysis on the unresolved traversal
3. decide that more structure is needed
4. refine the edge locally

Example:

```text
intent -> outcome
```

becomes:

```text
intent -> requirements -> outcome
```

and later:

```text
intent -> requirements -> design -> code -> tests -> outcome
```

Nothing about the kernel changes.

The event log preserves the truth that:

- `intent -> outcome` was attempted
- it was insufficient
- refinement was introduced
- child work keys carried the refined work

So the methodology can stay maximally coarse at first and only add detail when reality demands it.

## Weak Planner Now, Stronger Intent Engine Later

To reach the strongest version of this model, a strong intent engine is needed.

That future engine would:

- interpret gaps more deeply
- choose when refinement is needed
- emit better next-step topology
- realize the graph more intelligently as it runs

But that does **not** need to block the engine design now.

The engine should already support the end-state model even if the current intent engine is weak.

So the practical model today can be:

- start from a **static hand-crafted graph**
- traverse it
- if a traversal proves too coarse or wrong, refine locally
- continue on the refined structure

So:

- **future**: strong dynamic intent engine
- **now**: static authored graph
- **engine requirement**: support lawful local refinement so the weak planner does not trap the system in a static world

That keeps the architecture correct even while planning quality is still immature.

Important clarification:

- “best-guess graph” here does **not** mean the system is already evolving topology intelligently
- it means the current graph is the static hand-crafted authored graph you start from today
- without the future refinement / intent machinery, that graph does not evolve by itself

So the architectural requirement is:

- the engine must support the end-state refinement model now
- even though the current authored graph remains static until the dynamic system exists

## Graphs Must Be Compositional

The graphs themselves must be compositional.

The system must support convenient, reusable **graph functions** or **graph fragments** rather than forcing every design into one monolithic package graph.

This is already implied by the original design:

- `graph_fragment`
- named compositions
- zoom morphism
- spawn / fold-back

But it needs to be stated directly:

- a graph should be reusable as a lawful part of another graph
- a refined subgraph should be insertable at a point of need
- common patterns should be definable once and reused compositionally

Examples:

- `requirements_to_design()`
- `design_to_module_decomp()`
- `module_decomp_to_code()`
- `code_to_test_evidence()`

These are not imperative helper scripts.

They are graph-valued functions:

- they introduce assets
- they introduce edges
- they preserve interface contracts
- they can be composed into larger lawful structures

## Interfaces and Late Binding

Graph functions are also what give the system real **interfaces** and **late binding**.

A graph function can expose:

- required input assets
- produced output assets
- invariants or convergence surfaces
- required context

without forcing immediate commitment to the internal realization.

That means:

- the outer graph can bind to the interface now
- the internal subgraph can be selected, refined, or swapped later
- lawful composition remains intact as long as the interface contract is preserved

So graph functions are not just a convenience mechanism.

They are the structural basis for:

- interface boundaries
- delayed specialization
- interchangeable refinements
- lawful late binding of subgraphs into larger topologies

## The Missing Units

The missing unit is not only the routed work identity.

It is also the reusable **subgraph unit**.

The clean model becomes:

- `Package`
  - constitutional boundary / full lawful world
- `Fragment`
  - reusable compositional subgraph
- `Job`
  - static transition contract
- `work_key`
  - concrete identity of the piece of work
- `run_id`
  - one attempt on that work

Then composition happens at two levels:

1. **Topology composition**
   - combine graph fragments into larger lawful graphs
2. **Runtime recursion**
   - route concrete work through those graphs at variable grain

Without this, the system collapses back into:

- one giant graph
- duplicated local patterns
- imperative special-case refinement

With it, the system becomes what the original design wanted:

- prime-structured
- functional
- recursive
- compositional

## Recovery Path

The recovery path is now clear:

- the iterator must be recursive
- the work must have identity
- the graph must be compositional

Those three together are the actual recovery path.

This is not primarily a GSDLC graph problem.

It is the place where the current ABG + GTL split is missing the same structural layer:

- GTL has topology
- ABG has iteration
- event/projection layer already hints at finer-grain identity
- but routed recursive work and compositional fragments are not first-class

So the next design move should be framed as:

- restore routed recursive work
- restore lawful subgraph / fragment traversal
- keep the kernel minimal
- avoid imperative feature-routing patches

## Final Rule

Do not solve this by teaching the scheduler more exceptions.

Solve it by restoring the original structure:

- recursion
- zoom morphism
- spawn / fold-back
- graph fragments
- named compositions
- child lineage

That is the prime-structured solution.

The imperative reading is the regression.
