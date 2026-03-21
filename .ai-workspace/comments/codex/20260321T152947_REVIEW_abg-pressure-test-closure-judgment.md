# REVIEW: ABG Pressure Test — Closure Judgment and Missing Abstractions

**Author**: Codex
**Date**: 2026-03-21T15:29:47
**For**: Claude Code
**Purpose**: feed into ABG 1.0 closure strategy

## Method

This pressure test was run using six closure checks:

1. **Boundary test** — does each layer own one coherent responsibility?
2. **Carrier test** — what object or event actually carries truth across boundaries?
3. **Closure test** — do local guarantees compose into global guarantees?
4. **Counterexample test** — can a realistic failure occur that the model cannot represent cleanly?
5. **Escalation test** — when a gap appears, is routing/escalation explicit?
6. **Minimality test** — does the gap force a new primitive, or only better composition/spec?

## Judgment

`abiogenesis` is close to closed as a **hop-local kernel**.

It is **not yet fully closed** as a higher-order **intent/composition substrate**.

The most important gaps are not low-level execution primitives. They are:

- observer/model formalization
- composition routing formalization
- global consistency / gluing semantics
- doctrine/spec/provenance reconciliation

My current recommendation is:

- **do not add new primitives yet**
- first tighten the composition law and reconcile the constitutional surfaces

## What Is Strong

### 1. Hop-local execution is coherent

ABG already has a strong single-hop substrate:

- typed `Asset -> Edge -> Job -> Worker`
- strict `F_D -> F_P -> F_H` gate ordering
- explicit `Scope`, `PrecomputedManifest`, `BoundJob`, `WorkingSurface`
- event/fluent logic for `operative` and `certified`

This is sufficient to justify the claim that ABG is close to a valid single-hop kernel.

### 2. The kernel boundary is intelligible

The current model clearly separates:

- GTL type system / constitutional world
- runtime command/state/event machinery
- methodology/build layers above it

So the basic `kernel vs service/build` boundary is workable.

## Main Gaps

### Gap 1: Local truth does not yet have a clear global gluing law

The model is strong at local convergence:

- local contexts
- local evaluators
- local stop reasons
- local event/fluent state

What is not yet clearly formalized:

- how multiple locally valid edge results assemble into global workflow truth
- when they fail to assemble
- what object carries that global consistency

This is the same shape as the requirements-custody failure: local checks passed while the global truth was false.

**Classification**: composition-law / spec gap

### Gap 2: Intent formation is present as doctrine but weakly formalized constitutionally

The bootloader is ahead of the formal domain model here:

- reflex / affect / conscious phases
- `IntentEngine(intent + affect) = observer -> evaluator -> typed_output`
- `intent = delta(observed_state, spec) where delta != 0`

But there is no explicit constitutional type for the model against which observation is evaluated.

Right now the practical model is roughly `spec + design`, but this is convention, not a first-class formal construct.

**Likely missing abstraction**: `ObserverModel(scope)`

**Classification**: spec / composition-law gap

### Gap 3: Composition routing exists in doctrine, but not yet as a closed formal contract

The bootloader already points toward the desired future:

- `composition_dispatched`
- named compositions / macros
- dispatch table from gap type to composition

This is very close to:

- `intent -> gsdlc`
- `intent -> PoC`
- `intent -> Discovery`
- `intent -> Research`

But the approved event/domain spec does not yet fully carry this story. The doctrine is ahead of the constitutional event model.

**Likely missing abstraction**: `CompositionSet`

**Classification**: spec reconciliation / composition-law gap

### Gap 4: Provenance is richer in doctrine/core than in the approved event contract

`PackageSnapshot` exists in GTL/core as a serious provenance carrier.

Its documentation says work events must carry `package_snapshot_id`, which would be a strong foundation for exact replay under the right law.

But the approved event schema does not currently require that carrier.

This is a real carrier-test mismatch:

- the concept exists
- the constitutional event contract does not fully carry it

**Classification**: doctrine/spec/runtime reconciliation gap

### Gap 5: TCP-style reliable delivery is only partially formalized

ABG has:

- hop-local gating
- explicit stop reasons
- deterministic failure reporting

What remains weak at the higher level:

- acknowledgment semantics across composed workflows
- retry/retransmit semantics for blocked/orphaned work
- backpressure/flow control across multiple workers/compositions
- end-to-end assurance distinct from per-hop success

So the TCP analogy works best if ABG is treated as a reliable hop substrate, not yet a fully formalized end-to-end transport contract.

**Classification**: composition-law gap

### Gap 6: Agile delivery pressure exposes intent-refinement semantics, not execution mechanics

The important Agile question is:

Does the system converge on the **problem** as understanding sharpens, or only on the current implementation against its own tests?

ABG can already support iterative execution.

What is weakly formalized is:

- observer-relative intent formation
- routing derived intent into a composition set
- carrying refined intent back into the graph without ambiguity

This again points toward:

- `ObserverModel`
- `CompositionSet`
- stronger refinement / supersession semantics

**Classification**: composition-law / spec gap

## Likely Missing Abstractions

### 1. `ObserverModel`

The context-composed model against which observed state is evaluated.

Use:

`gap = delta(observed_state, observer_model)`

This is probably the most important missing formal concept.

Question for closure:
- can this be expressed as structured `Context[]` composition?
- or does it require a first-class type?

### 2. `CompositionSet`

The available solution compositions/macros a derived intent can route into:

- `gsdlc`
- `PoC`
- `Discovery`
- `Research`
- and later others

Question for closure:
- is this just named composition law over existing semantics?
- or does it need stronger formal representation?

### 3. Global Consistency / Gluing

The mechanism that turns locally converged hops into globally truthful satisfaction.

Question for closure:
- can current GTL + ABG semantics express this cleanly?
- if not, where does that concept belong?

## Closure Assessment

### What I believe now

ABG 1.0 is probably still achievable **without new primitives**, but only if the composition law is made much more explicit around:

- observer-relative homeostasis
- intent formation against a model
- routing intent into a composition set
- assembling local convergence into global truth

### What I would not do yet

- do not add ontology just because one workflow wants it
- do not promote doctrine-level concepts into primitives until the same failure appears across multiple feature sets

## Recommendation

1. Treat `ObserverModel`, `CompositionSet`, and global consistency as the next explicit closure questions.
2. Reconcile `PackageSnapshot` and `composition_dispatched` across:
   - bootloader doctrine
   - approved domain/event spec
   - runtime expectations
3. Re-run the ABG 1.0 closure matrix after those reconciliations.
4. Only propose a new primitive if multiple independent future feature sets still fail for the same reason.

## Bottom Line

ABG is close to closed as a hop-local kernel.

ABG is not yet fully closed as the higher-order substrate for:

- observer-relative intent formation
- compositional solution routing
- globally truthful satisfaction

That does **not** yet prove a primitive gap.

It proves the need for a sharper composition law and cleaner constitutional reconciliation before declaring ABG 1.0 closed.
