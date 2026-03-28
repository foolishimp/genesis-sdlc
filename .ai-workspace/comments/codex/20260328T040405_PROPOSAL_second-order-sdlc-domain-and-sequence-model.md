# PROPOSAL: Second-Order SDLC Domain And Sequence Model

**Author**: codex
**Date**: 2026-03-28T04:04:05+1100
**Addresses**: extending the SDLC with a second-order domain model, sequence model, and memory system over convergence gap analysis
**Status**: Draft

## Summary

This proposal extends the SDLC with a second-order domain that operates over the original SDLC.

The first-order SDLC continues to converge product artifacts and evidence.

The second-order SDLC converges how the first-order graph is interpreted and executed:

- how gaps are disambiguated
- how much context is needed
- how much resource pressure a gap should generate
- which prior resolutions should tighten future edge execution

The product claim is straightforward:

the system should not only close gaps
it should learn how to close recurring classes of gaps more cheaply and more precisely

That learning is not model training. It is process-level convergence driven by retained disambiguation memories, affect grading, and consolidation across iterations.

The preferred path is to do this without changing GTL at first. GTL already has enough structure to host a second-order graph using nodes, vectors, events, projection, and refinement boundaries. If the model proves valuable but awkward, then minimal GTL extensions can follow.

## Product Thesis

The original SDLC is a first-order convergence graph.

This proposal adds a second-order convergence graph whose artifacts are not product code or tests, but process artifacts:

- disambiguation memories
- edge profiles
- affect grades
- search traces
- promotion candidates
- consolidated domain memories

That second-order graph acts as a domain and sequence model for future work.

It supplies two things missing from the current method:

1. a domain model of what the system has learned about recurring gap classes
2. a sequence model of how convergence unfolds over time, including escalation, consolidation, and reuse

## Why This Matters

The current method already defines:

- events
- projection
- delta
- gap analysis
- repricing

That chain is explicit in [SPEC_METHOD.md](/Users/jim/src/apps/genesis_sdlc/specification/standards/SPEC_METHOD.md#L91) and [SPEC_METHOD.md](/Users/jim/src/apps/genesis_sdlc/specification/standards/SPEC_METHOD.md#L419).

But the system still loses most of the value produced by each iteration.

Today, a difficult convergence cycle may teach the operator or agent something real:

- which ambiguity actually mattered
- which context subset was decisive
- which search path worked
- which interpretation was wrong
- how serious the gap really was

That knowledge is usually left in:

- transient context
- operator intuition
- isolated commentary

So the next iteration often pays the same disambiguation cost again.

This proposal turns that waste into a product surface.

## Domain Model

The proposed second-order domain contains the following core entities.

### 1. `gap_episode`

A single first-order convergence attempt viewed as an analyzable process object.

Fields:

- edge
- iteration_id
- source state summary
- target state summary
- artifact_delta
- evidence_delta
- disambiguation_delta
- outcome
- closure path used
- elapsed cost

### 2. `search_trace`

The observed sequence of discovery and action steps used while resolving a gap.

Fields:

- files inspected
- tools invoked
- commands run
- probes attempted
- branches rejected
- stopping condition

### 3. `disambiguation_memory`

A retained resolution of prior ambiguity.

Fields:

- memory_id
- scope
- edge class
- triggering ambiguity
- accepted interpretation
- rejected interpretations
- evidence that supported the interpretation
- reuse count
- confidence
- promotion status

### 4. `edge_profile`

A durable operating profile for a recurring edge class.

Fields:

- edge class
- ambiguity budget
- discovery budget
- preferred tools
- trusted evidence shapes
- common failure modes
- expected affect range

### 5. `affect_state`

A projection of gap pressure into resource-allocation intensity.

This follows the model in [20260328T035147_SCHEMA_affect-as-resource-grade-over-gap-analysis.md](/Users/jim/src/apps/genesis_sdlc/.ai-workspace/comments/codex/20260328T035147_SCHEMA_affect-as-resource-grade-over-gap-analysis.md).

Fields:

- severity
- uncertainty
- urgency
- recurrence
- stakes
- available_control
- affect_grade
- affect_bucket

### 6. `promotion_candidate`

A memory or profile that has recurred enough to be considered for promotion.

Fields:

- source memory ids
- recurrence evidence
- proposed target layer
- design impact
- constitutional impact
- status

## Memory Categories

The memory system should be explicit and layered. Brain-inspired names are useful here because they describe functional roles, not because the system is pretending to be biological.

### `amygdala_memory`

Fast threat/salience memory.

Purpose:

- preserve which edge patterns are dangerous
- retain prior panic, stress, or escalation triggers
- bias future runs toward faster containment

Typical contents:

- high-blast-radius failure signatures
- irreversible-loss signatures
- known control-collapse patterns
- hard stop conditions

### `working_memory`

Short-horizon task memory for the current convergence episode.

Purpose:

- hold active context
- record immediate interpretations
- maintain current search state

Typical contents:

- live hypotheses
- active file set
- current probe results
- current ambiguity reductions

### `episodic_memory`

Per-iteration memory of how a specific gap episode unfolded.

Purpose:

- preserve case history
- allow later replay and comparison

Typical contents:

- ordered search trace
- resolved ambiguities
- failure and recovery steps
- final outcome

### `semantic_memory`

Long-term reusable memory about the domain and recurring edge classes.

Purpose:

- encode stable disambiguations
- encode conventions and domain vocabulary
- reduce ambiguity for future similar runs

Typical contents:

- stable mappings from vague requests to concrete task classes
- trusted evidence patterns
- durable edge profiles
- recurring interpretation rules

### `sleep_memory`

Offline consolidation state.

Purpose:

- merge episodic traces into semantic memory
- decay weak memories
- detect repeated patterns
- form promotion candidates

This is not runtime execution. It is batch consolidation over prior iterations.

### `dreaming_memory`

Offline synthetic rehearsal and counterfactual recombination.

Purpose:

- simulate near-neighbor gap classes
- test whether a memory generalizes
- detect false overfitting before ratification

This is the most speculative category and should remain optional until the rest of the model works.

## Sequence Model

The second-order sequence model should sit over every first-order iteration.

### Runtime sequence

1. First-order edge execution begins.
2. The system performs normal convergence work.
3. The runtime emits a `gap_episode` and `search_trace`.
4. The second-order layer computes `affect_state`.
5. The affect grade adjusts resource recruitment:
   context size, planning depth, search breadth, escalation, or containment.
6. Resolved ambiguities are written into `working_memory` and `episodic_memory`.
7. Reused prior memories tighten the active operating surface.
8. The first-order edge completes, blocks, or escalates.

### Offline sequence

1. Completed episodes are replayed during consolidation.
2. Repeated ambiguity patterns are clustered.
3. Durable patterns are promoted into `semantic_memory` and `edge_profile`.
4. Threat-heavy patterns are retained in `amygdala_memory`.
5. Recurrent stable patterns create `promotion_candidate` records.
6. Ratification moves selected memories upward into design or specification.

This is the point of the sequence model: the system should improve not only from live edge execution, but from offline consolidation over prior execution.

## GTL Fit

Phase 1 should avoid GTL changes if possible.

Why this is plausible:

- GTL already gives typed nodes and vectors
- the current realization already treats edges as explicit `GraphVector` boundaries
- the current realization already emits events and works through projection/delta logic
- the current graph already materializes `deferred_refinement(...)` boundaries at [graph.py](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/src/genesis_sdlc/workflow/graph.py#L447)

That means a second-order graph can likely be expressed as:

- new second-order nodes
- new second-order vectors
- event-derived projections from first-order runs
- memory artifacts stored in workspace territory

### Phase 1: no GTL changes

Represent the new layer as ordinary GTL-managed surfaces:

- memory artifacts as files plus typed nodes
- consolidation as explicit jobs
- affect grading as F_D/F_P evaluators
- promotion as F_H or F_P gated transitions

### Phase 2: optional GTL improvements

Only introduce GTL changes if Phase 1 proves structurally awkward.

Likely candidates:

- first-class memory scopes
- first-class episodic vs semantic artifact classes
- consolidation operators
- coupling primitives between first-order and second-order graphs
- native support for replay-derived profile updates

The bar for GTL change should be high. The product idea should prove itself inside the existing GTL surface first.

## Product Shape

The proposal naturally yields a product extension to SDLC:

- the original SDLC remains the work graph
- the extension adds domain memory and sequence memory over repeated convergence
- the system gains explicit affect grading and resource recruitment
- the system gains offline consolidation and promotion pathways

This turns SDLC from a graph that only closes work into a graph that also improves how it closes work.

## MVP

The smallest credible MVP is:

1. Add `gap_episode`, `search_trace`, and `disambiguation_memory` artifacts.
2. Add `affect_state` projection over gap episodes.
3. Add `semantic_memory` and `amygdala_memory` stores.
4. Add one consolidation job that promotes repeated episodic disambiguations into semantic memory.
5. Use those memories to narrow context on a single recurring edge class.

That is enough to prove whether the second-order layer lowers convergence cost in practice.

## Risks

- accidental law: local memories harden too quickly into authoritative truth
- overfitting: reused disambiguations narrow the edge before the domain is stable
- memory bloat: too much episodic material with too little consolidation
- false affect: poor affect grading over-recruits or under-recruits resources
- GTL inflation: premature type-system changes before the product shape is validated

## Recommended Action

1. Treat this as a product extension, not only a research thread.
2. Model the second-order layer in workspace territory first.
3. Keep GTL unchanged for Phase 1 unless a hard blocker appears.
4. Define the artifact schemas for:
   `gap_episode`
   `search_trace`
   `disambiguation_memory`
   `affect_state`
   `edge_profile`
5. Implement memory categories in this order:
   working
   episodic
   semantic
   amygdala
   sleep
   dreaming
6. Add a single end-to-end pilot edge and measure whether repeated runs get cheaper and more precise.

## Working Thesis

The next useful extension to SDLC is a second-order domain and sequence model that operates over the original convergence graph. The first-order graph closes product work. The second-order graph captures how gaps were interpreted, how much affective resource pressure they generated, what disambiguations were learned, and how those lessons should shape future execution. This can likely be built on top of current GTL primitives first. Memory categories inspired by the brain are useful as functional classes: fast threat memory, working memory, episodic memory, semantic memory, and offline consolidation. If this works, SDLC stops being only a graph that converges artifacts and becomes a graph that also converges its own method of convergence.
