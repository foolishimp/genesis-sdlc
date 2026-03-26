# GTL 2.x / ABG Interpreter Boundary

**Status**: Draft
**Date**: 2026-03-24
**Purpose**: Define the clean boundary between GTL 2.x as a graph-first Python DSL/SDK and ABG as the canonical event-sourced interpreter/runtime.

---

## 1. Boundary Principle

GTL defines lawful structure.

ABG interprets lawful structure through evented execution and replay.

This boundary should stay explicit.

If it blurs:

- the language gets polluted by runtime mechanics
- the runtime quietly becomes the true language
- requirements and tests drift toward implementation habit

ABG is the canonical interpreter.

It is not the only possible engine mapping for GTL.

---

## 2. GTL Owns

GTL owns:

- graph structure
- graph interfaces
- operators and regimes
- rules
- graph functions
- composition
- substitution
- recursion as a language capability
- higher-order graph operations
- module/library structure

GTL answers:

- what can be declared
- what is structurally lawful
- what can compose
- what can substitute

---

## 3. ABG Owns

ABG owns:

- event emission
- operator execution
- projection
- convergence/delta
- work lineage
- run attempts
- retries
- resets/correction
- provenance
- replay
- next-action determination

ABG answers:

- what happened
- what is true now
- what remains unconverged
- what attempt is live
- what certifications are shadowed

---

## 4. How the Layers Meet

ABG consumes:

- graphs
- graph functions
- operators
- rules
- module declarations

ABG then:

1. materializes graph functions when needed
2. enumerates lawful candidate graphs if refinement/composition is needed
3. receives selection from deterministic, probabilistic, human, or business logic
4. applies substitution/composition
5. executes operator surfaces
6. emits events
7. replays truth
8. computes convergence

This keeps GTL declarative and ABG operational.

---

## 5. Canonical Interpreter vs Alternate Mappings

ABG is the canonical interpreter because it is explicitly designed around:

- event emission
- replay
- convergence
- lineage
- correction
- provenance

Other runtimes may still host GTL programs or partial GTL mappings.

Examples include:

- Temporal
- Prefect
- Step Functions

Those should be treated as mappings or adapters, not as the definition of GTL itself.

---

## 6. Selection Boundary

ABG may enumerate lawful candidates.

ABG should not silently decide which candidate is "best."

Choice belongs to:

- deterministic rule execution
- probabilistic contextual selection
- human judgment
- or business/intent logic above the engine

ABG's job is:

- enumerate
- validate
- apply
- record

not:

- strategize
- prioritize business outcomes
- hide choice logic in engine internals

---

## 7. Replay Boundary

GTL must be replay-suitable.

ABG must implement replay.

That means:

- GTL constructs should have stable structural meaning
- ABG should emit enough event truth to reconstruct chosen topology and resulting convergence

This is where runtime concepts properly live:

- `work_key`
- `run_id`
- `workflow_version`
- `reset`
- `approved`
- `assessed`
- `zoomed`
- `work_spawned`

These are interpreter/runtime concepts over GTL programs, not language primitives.

---

## 8. Product Scenario Implication

Product scenarios should now be read through this split:

- GTL says whether a use case is structurally expressible
- ABG says whether the expressed graph program can be executed, replayed, and converged lawfully

This helps identify the real source of a gap:

- language gap
- interpreter gap
- policy/selection gap
- or scenario gap

---

## 9. Summary

The clean model is:

- GTL = graph-first Python DSL/SDK
- ABG = canonical event-sourced interpreter/runtime for GTL

GTL should stay structural.

ABG should stay operational.

That separation is one of the main things GTL 2.x needs to make explicit.
