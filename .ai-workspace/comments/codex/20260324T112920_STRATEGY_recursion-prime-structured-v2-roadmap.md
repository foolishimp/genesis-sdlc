# STRATEGY V2: Prime-Structured Work and Compositional Graphs — Roadmap for ABG / GSDLC

**Author**: codex  
**Date**: 2026-03-24T11:29:20+11:00  
**For**: all

## Summary

V1 established the right direction:

- work identity exists
- attempt identity exists
- work-scoped convergence exists
- fragments, zoom, spawn, and fold-back now exist in some form

But V1 is still transitional.

The repo no longer forgets the design, but the main traversal law still has not fully shifted to it.

The V2 goal is to complete that shift.

V2 should make ABG into a stronger kernel for the model we actually want:

- recursive work at variable grain
- immutable routed work identity
- compositional graphs with interfaces
- lawful local refinement
- stronger run governance

This is not a call to make ABG smarter at planning.

It is a call to make the kernel more reliable, more lawful, and more structurally complete, so a future intent engine can do richer work on top of it.

## What V2 Is Trying to Achieve

The target model is:

- the iterator remains small
- topology remains lawful and compositional
- work has immutable identity
- attempts have explicit identity
- recursion is normal
- refinement is lawful
- child lineage is event-sourced
- parent collapse is projection over descendants

The core metaphor still holds:

- **topology** is the track network
- **iterate()** is the transport primitive
- **work identity** is the addressed packet
- **recursion** is narrower lawful routing over the same substrate

So V2 is not “add more feature routing”.

V2 is:

- make the transport better
- make the work identity first-class
- make composition operational
- make refinement and attempts reliable

## What We Have Learned Since V1

### 1. The original diagnosis was right

The problem was not primarily “per-feature scheduling”.

The problem was that the split simplified the original structure too far:

- `Job = edge`
- scheduler walks edges
- work identity existed mostly as annotation

That produced imperative patches where the original design wanted prime-structured functional composition.

### 2. Work identity is real and useful

The introduction of:

- `work_key`
- `run_id`

was not accidental complexity.

It completed the event-sourcing model by making the unit of work explicit.

The right reading remains:

- `work_key` = immutable identity of the piece of work
- `run_id` = one attempt / transaction on that work

### 3. OpenClaw validates the lower layer, not the whole model

OpenClaw taught three useful lessons:

- hierarchical routed keys are practical
- run lifecycle governance matters
- bounded structured leaf tasks are useful

But OpenClaw is still:

- a routed agent gateway
- a session/run system

not:

- a convergence engine
- a recursive graph runtime
- an event-sourced work system

So the correct synthesis is:

- import its routing/run-governance strengths
- do not collapse ABG into a session router

### 4. The kernel still lags the design

The main remaining gap is not in theory.

It is in integration.

We now have many of the right pieces, but they are not yet fully the normal traversal law.

That is the V2 problem to solve.

## V2 Design Thesis

V2 should be organized around three irreducible commitments:

1. **Work is first-class**
2. **Graphs are compositional**
3. **Runs are governed explicitly**

Everything else follows from those.

## Anti-Drift Axioms

These are the core V2 discipline rules.

They matter because the target system is not just a stronger local engine.
It is a foundation for distributed, event-sourced recursive work that can later
scale toward saga-style coordination without losing lawful replay.

### 1. If something must be remembered by the caller, it is too imperative

Core runtime behavior should not depend on external procedural memory.

That includes:

- remembering to emit refinement provenance
- remembering to thread special state around a kernel seam
- remembering hidden scheduler exceptions

If a behavior matters constitutionally, it must be carried by the kernel law
and recorded through the normal event path.

### 2. If state is reconstructed outside projection, it is too imperative

The event log is the authority.

Projection should be the ordinary way current truth is derived.

If the runtime must reconstruct effective state by ad hoc command-layer logic
instead of lawful projection over events, the design has drifted.

### 3. If recursion exists only as helper functions, it is too imperative

Recursive work cannot remain a utility seam off to the side.

If spawn, fold-back, descendant discovery, and routed work identity are real,
they must affect normal traversal law, not just helper APIs and tests.

### 4. If topology refinement is not replayable from events, it is too imperative

Zoom, spawn, child lineage, and refinement provenance must be reconstructable
from the log.

If replay cannot tell what structure existed, when it was refined, and how
descendant work emerged, then refinement is still procedural rather than
constitutional.

### 5. If identity collapses into session or transport identity, it is too imperative

Routing/session identity can help transport.
It cannot replace work identity.

`work_key` identifies the piece of work.
`run_id` identifies one attempt on that work.

Transport/session identifiers are subordinate and disposable.

### 6. If the kernel solves planning by exceptions, it is too imperative

ABG should not become a planner disguised as a scheduler.

The kernel should provide:

- identity
- ordering
- convergence law
- refinement provenance
- attempt governance

The planner above the kernel may decide where to refine.
The kernel should not absorb domain-specific graph tricks to compensate for a
weak planner.

### 7. If distributed coordination cannot be replayed, it is not ready for saga-scale work

The long-term ambition is distributed recursive coordination.

That means the system must be able to replay:

- what work existed
- what attempts ran
- what refinements occurred
- what child work was spawned
- what gates held or failed
- what final fold-back truth was reached

If those things are not replayable from events, the system is not yet strong
enough to scale cleanly into saga-style orchestration.

## V2 Architecture

## 1. Kernel

The kernel remains small and domain-blind.

Its concerns are:

- work identity
- attempt identity
- convergence calculation
- lawful dispatch
- event emission
- replay / projection
- refinement provenance

Its concerns are not:

- domain planning
- intent interpretation
- graph authoring policy
- feature-specific exceptions

## 2. Stable Topology

The stable topology layer is:

- `Asset`
- `Edge`
- `Job`
- `Fragment`
- `Package`

This layer defines the lawful space.

It should remain declarative and compositional.

## 3. Routed Work

The routed work layer is:

- `work_key`
- `run_id`
- `WorkInstance`

This is the level at which actual traversal happens.

The key change in V2 is that `WorkInstance` must stop being a supporting type and become the real operational unit.

## 4. Recursive Refinement

Refinement happens through:

- `zoom`
- `spawn`
- `fold-back`
- descendant discovery

This must become normal engine behavior, not just library utilities and unit-tested helpers.

## 5. Planner Above the Kernel

The intent/planning layer remains above ABG.

For now, the system can still start from a static authored graph.

Later, a stronger intent engine can:

- decide when to refine
- decide where to zoom
- choose better next-step topology

The kernel must support that future without requiring redesign.

## The V2 Contract

The V2 contract should be:

```python
iterate(work_instance, ...)
```

where:

```python
work_instance = {
  job,
  work_key,
  run_id,
}
```

This is the most important normalization step.

Not because the data is complicated.

Because it makes the unit of traversal explicit.

The old signature is not wrong as an internal primitive, but it is no longer the right constitutional surface for the runtime.

## What Must Change in ABG

## A. Make WorkInstance real end-to-end

Today, the engine still often behaves like:

- enumerate jobs
- enumerate work keys
- call bind repeatedly
- pick the first gap

V2 should instead:

- create explicit `WorkInstance`s
- schedule `WorkInstance`s
- dispatch `WorkInstance`s
- emit events against `WorkInstance`s

This gives:

- cleaner traversal law
- clearer observability
- cleaner attempt governance
- less imperative reconstruction at every command boundary

## B. Route all convergence through one lawful path

Recursive fold-back and descendant-aware convergence must not live in a side function while the main command path uses different logic.

V2 rule:

- state derivation
- gap reporting
- next-work selection
- parent/child convergence

must all flow through the same convergence law.

There should not be one convergence model in `delta()` and another in the selection path.

## C. Make refinement provenance automatic

If refinement matters constitutionally, the kernel must record it constitutionally.

That means:

- `zoomed` events should be emitted through the normal event path
- `work_spawned` should be a normal engine event, not just something tests can append manually
- descendant lineage should be reconstructable entirely from the log

No caller-side “remember to emit provenance” should remain around core refinement operations.

## D. Strengthen run governance

This is the largest lesson to borrow from OpenClaw.

ABG should develop a much stronger run lifecycle around `(work_key, run_id)`.

At minimum:

- queued
- started
- dispatched
- pending
- assessed
- converged
- failed
- timed_out
- superseded

This should include:

- waiter dedupe
- cached terminal snapshots
- retry grace for transient failures
- clearer timeout semantics
- better distinction between:
  - transport failure
  - no output
  - bad output
  - failed certification

This is a kernel responsibility, not a domain-package responsibility.

## E. Normalize bounded leaf tasks

OpenClaw’s `llm-task` is a good pattern for leaf work:

- bounded
- schema-driven
- JSON-only
- toolless by default
- explicitly timed out

V2 should adopt an equivalent idea inside ABG as a subordinate primitive:

- not as the whole engine
- not as a substitute for graph traversal
- but as a disciplined leaf-task surface

That would help with:

- narrow transforms
- structured agent sub-work
- well-bounded helper tasks

## F. Keep the degenerate case

V2 must preserve:

- V1 global traversal when no `work_key` exists
- static authored graph when no refinement is applied
- no-fragment packages

The richer system must continue to degrade to the simpler one lawfully.

That matters because the design is a generalization, not a break.

## What Must Change in GTL

## A. Iterate protocol must acknowledge routed work

The GTL iterate contract should stop pretending the primary runtime unit is only:

- `job`
- candidate asset
- evaluator function

That was appropriate for a simpler fixed-point description.

It is no longer enough for the runtime we are actually building.

V2 should make routed work visible in the constitutional runtime surface.

## B. Fragment must become ordinary, not exotic

`Fragment` now exists.

V2 should treat it as a normal reusable structural unit:

- smaller than package
- interface-bearing
- reusable
- lawful

This is what lets graph functions become real.

## C. Graph functions and interfaces

V2 should explicitly embrace graph-valued functions.

Examples:

- `requirements_to_design()`
- `design_to_module_decomp()`
- `module_decomp_to_code()`
- `code_to_test_evidence()`

These functions are valuable because they give:

- reusable topology
- explicit interfaces
- late binding
- local refinement without monolithic graph rewrite

This is central to the original design and should be treated as such.

## What Must Change in GSDLC

GSDLC should stop trying to compensate for missing kernel structure with graph-local hacks.

Its job is:

- author package law
- define useful fragments
- define useful refinement points
- define work-scoped evaluator surfaces

Its job is not:

- invent scheduler exceptions
- encode kernel deficits into graph tricks

So for GSDLC, V2 means:

- keep improving topology
- identify lawful zoom points
- express reusable patterns as fragments
- rely on ABG for traversal, work identity, and run governance

## Roadmap

## Phase 1 — Finish the kernel identity shift

Goal:

- `WorkInstance` becomes the real unit of traversal

Work:

- normalize dispatch, pending, and selection around `WorkInstance`
- generate and propagate `run_id` as standard attempt identity
- make command outputs consistently work-instance-oriented

Exit condition:

- runtime no longer reconstructs work ad hoc from `jobs × work_keys`

## Phase 2 — Unify convergence law

Goal:

- one convergence model for gaps, state, iteration, and fold-back

Work:

- route selection through recursive `delta`
- ensure child work affects live traversal, not only utility functions
- remove divergence between `bind_fd()` path and recursive convergence path

Exit condition:

- parent/child convergence is materially live, not just defined

## Phase 3 — Make refinement constitutional

Goal:

- zoom/spawn/fold-back become ordinary event-sourced runtime operations

Work:

- automatic `zoomed` provenance
- automatic `work_spawned` provenance
- descendant discovery as normal scheduler input
- lawful replay of topology refinement

Exit condition:

- refinement is reconstructable entirely from the event log

## Phase 4 — Strengthen run governance

Goal:

- more reliable transport substrate for higher-level work

Work:

- explicit run lifecycle model
- retry/dedupe/grace handling
- better failure classification
- clearer pending and supersession semantics

Exit condition:

- F_P attempts are governed robustly enough that higher-level recursion can rely on them

## Phase 5 — Add disciplined leaf-task primitives

Goal:

- bounded structured sub-work without flattening the engine

Work:

- define JSON/schema-oriented leaf task surface
- constrain tool access by default
- integrate with run governance

Exit condition:

- ABG has a safe leaf-task mechanism for narrow agent sub-work

## Phase 6 — Strengthen the planner above the kernel

Goal:

- move from static authored graph plus manual refinement toward dynamic realized traversal

Work:

- stronger intent interpretation
- gap-driven refinement decisions
- better topology realization

Exit condition:

- the system can start from coarse structure and lawfully refine where needed

## Lessons from OpenClaw

What to import:

- hierarchical routed identity discipline
- run lifecycle governance
- waiter dedupe and transient failure grace
- bounded structured task surfaces
- operator-friendly targeting

What not to import:

- session routing as a substitute for work identity
- conversation branching as a substitute for recursive work
- one-shot tasks as a substitute for graph traversal

The right reading is:

- OpenClaw helps make our transport and run-governance layer stronger
- it does not replace our convergence and recursive work model

## Notes on Saga as the End-State Distribution Model

Saga is a good fit for the eventual distributed form of this system, but only
if it is treated as the distributed expression of the same local law.

It should not introduce a second model.

The right mapping is:

- `work_key` = the identity of the saga-level unit of work
- `run_id` = one attempt / transaction within that unit
- child `work_key`s = spawned child sagas
- fold-back = parent completion projected over descendants
- compensation = semantic corrective work, not destructive rollback

This matters because the system is already shaped correctly for saga:

- event-sourced history
- immutable work identity
- recursive decomposition
- explicit attempts
- eventual convergence rather than global atomicity

### 1. Start orchestrated, not choreographed

The first distributed form should be orchestrated:

- one coordinator per work lineage or subtree
- explicit child spawning
- explicit fold-back
- explicit gate and completion rules

Pure choreography can come later if it ever proves useful.

For this system, orchestration is the more lawful and replayable first step.

### 2. Compensation should be semantic, not rollback-shaped

Distributed failure should not be handled by pretending the past can be erased.

The lawful forms are:

- `revoked`
- `superseded`
- corrective child work
- new attempts on the same `work_key`

That keeps the event log truthful and makes distributed recovery compatible
with the existing event-sourced model.

### 3. Partition by work lineage

The natural distributed partition is work identity.

That means:

- strong ordering is needed within a `work_key` lineage
- coordination is local to the parent/child tree
- global total ordering is not required

This is what makes scale possible without abandoning replayability.

### 4. Transport identity must remain subordinate

Worker ids, queue ids, session ids, transport channels, and network addresses
are operational routing identifiers.

They are not the constitutional identity of the work.

The distributed system must preserve:

- `work_key` as work identity
- `run_id` as attempt identity

Everything else is replaceable infrastructure.

### 5. Distribution should come after local saga law is complete

ABG should first become a strong single-node saga kernel.

That means:

- first-class routed work
- replayable refinement provenance
- explicit run lifecycle
- replayable child lineage
- fold-back as normal convergence law

Only then should distribution be added.

The correct path is:

- make local law complete
- then distribute the same law
- not invent a separate distributed model later

## Non-Goals

V2 is not:

- a feature-routing patch release
- a domain-specific scheduler
- a replacement of graph law with agent improvisation
- a collapse of work identity into session identity
- a move away from event sourcing

## Final Statement

The V1 note established the design truth.

V2 must now turn that truth into a build order.

The build order is:

1. make work instances real
2. unify convergence law
3. make refinement constitutional
4. strengthen run governance
5. add disciplined leaf-task primitives
6. only then rely on a stronger intent engine

That is the clean path.

The key rule remains:

- do not teach the scheduler more exceptions
- strengthen the kernel so recursive routed work can exist lawfully on top of it

That is how we make TCP stronger so IP can do the interesting work.
