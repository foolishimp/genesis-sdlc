# PROPOSAL: Second-Order Memory SDLC For 1.0

**Author**: codex
**Date**: 2026-03-28T16:28:00+1100
**Addresses**: the second-order memory system that sits above the assurance control plane and completes the `1.0` product
**Status**: Draft

## Versioning Assumption

This proposal assumes the same release framing as the control-plane note:

- current branch maturity is best read as late `0.9.x`
- `0.9.9` completes the assurance control plane
- `1.0` is the milestone where second-order memory completes the product thesis

If the current `1.0.0rc1` line is not repriced, this proposal should be re-labeled to the appropriate post-RC release while keeping the same sequencing.

## Summary

The second-order memory system should be treated as a separate feature from the assurance control plane.

It is not the runtime shell.
It is not the operator access layer.
It is not install/audit/backend selection.

It is a second SDLC running over the first.

Its job is to observe recurring convergence work, retain useful disambiguation, and improve future execution without changing the constitutional lifecycle law.

That is why it is a strong candidate for:

- `0.9.9` first for the control plane
- `1.0` second for the memory system

## Product Thesis

The first-order SDLC converges product artifacts:

- requirements
- design
- code
- tests
- release evidence

The second-order SDLC converges process artifacts:

- gap episodes
- search traces
- disambiguation memories
- edge profiles
- promotion candidates
- resource/affect grades

So the `1.0` claim becomes:

the system not only closes gaps
it improves how future gaps are closed

## Dependency On The Control Plane

The memory system depends on the control plane.

It needs stable first-order surfaces for:

- events
- manifests
- results
- run archives
- backend selections
- edge profiles
- session state
- doctor/health signals

Without those, memory would be opaque and ad hoc.

With them, memory becomes explicit and typed.

So the dependency order is:

1. assurance control plane
2. second-order memory system

The planned persistence landing zone remains:

```text
.ai-workspace/memory/
```

with project-local policy and configuration expected to sit under the runtime customization surface introduced by the control-plane milestone.

More concretely, the memory system should consume the same compiled runtime answer the control plane exposes, rather than bypassing it.

So the dependency is not only on manifests and archives, but also on:

- the backend adapter layer
- the resolved runtime artifact
- stable edge runtime profiles

## What The Memory System Is

It is best understood as:

`observer + tuner over first-order SDLC execution`

This is the role that emerged during live qualification:

- observe where disambiguation cost accumulates
- observe which contexts matter
- observe which repairs recur
- tune the runtime profile for future edges

That observer/tuner behavior should become a product feature rather than remain an implicit agent habit.

## Domain Objects

The core second-order domain remains:

- `gap_episode`
- `search_trace`
- `disambiguation_memory`
- `edge_profile`
- `promotion_candidate`
- `affect_state`

These are not first-order project artifacts.
They are process artifacts over first-order convergence.

## Why This Is Separate From The Control Plane

The control plane gives the system:

- rails
- config
- backend routing
- diagnosis
- persistent state surfaces

The memory system does something different:

- consolidates observed episodes
- extracts reusable disambiguations
- grades recurrence and pressure
- recommends or writes better runtime profiles
- promotes stable lessons upward when warranted

So the split is clean:

- control plane = machinery
- memory = adaptive intelligence over the machinery

## Working Model

The second-order memory system should be modeled as a second graph over the first.

Its rough lifecycle is:

1. observe first-order edge execution
2. record episode and search trace
3. classify ambiguity and resolution
4. retain disambiguation memory
5. update edge profile candidate
6. promote stable patterns into runtime profiles or design law

That is why it deserves to be called a second SDLC.

## Relationship To Agent Compaction

Agent compaction is evidence that compressed carry-forward context is useful.

It is not yet the full product.

Compaction is:

- local
- session-shaped
- mostly opaque
- agent survival oriented

Second-order memory should be:

- typed
- provenance-carrying
- episode-derived
- edge-oriented
- consolidation-capable
- promotable

So `1.0` should not mean “better compaction”.

It should mean:

`memory becomes a first-class SDLC feature`

## Proposed 1.0 Surfaces

The memory system should sit under the control plane, likely in:

```text
.ai-workspace/
  memory/
    episodes/
    traces/
    disambiguation/
    edge_profiles/
    promotion/
```

And it should be configurable from project-local runtime design, for example:

```text
specification/design/runtime/memory/
```

That keeps memory explicit and replaceable.

## What 1.0 Should Deliver

A `1.0` memory release should include:

1. typed memory artifacts for episodes, traces, and disambiguation
2. edge-profile updates derived from recurring episodes
3. explicit promotion candidates
4. a policy surface for retention, promotion, and compaction
5. observable improvement of recurring F_P edge execution over time

That is enough to justify calling the product feature-complete for its first stable line.

## Why This Fits Your Release Strategy

Your proposed line makes sense:

- `0.9` = real system proven
- `0.9.9` = runtime/control-plane completeness
- `1.0` = second-order memory completes the product thesis

That gives you:

- one final feature-completeness push before `1.0`
- then a likely long period of `1.0.x` patch releases
- while attention moves to the broader ecosystem

That is structurally cleaner than forcing the memory system into `0.9.9`.

## Recommendation

Treat the memory system as:

- a separate product feature
- a second-order SDLC over the first
- the main candidate for `1.0`

And treat the assurance control plane as the prerequisite `0.9.9` milestone that makes the memory system possible without architectural confusion.
