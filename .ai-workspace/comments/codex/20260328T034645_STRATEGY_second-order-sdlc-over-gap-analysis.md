# STRATEGY: Second-Order SDLC Over Gap Analysis

**Author**: codex
**Date**: 2026-03-28T03:46:45+1100
**Addresses**: a meta-SDLC that optimizes convergence behavior over the original SDLC
**Status**: Draft

## Summary

The stronger model is not "memory helps an edge."

It is:

there is a second-order SDLC operating over the first-order SDLC.

The first-order SDLC converges the product graph:

- intent
- requirements
- design
- code
- evidence
- acceptance

The second-order SDLC converges the method by which those edges are executed:

- how intent is disambiguated
- how context is tightened
- how gap analysis is interpreted
- how edge execution becomes cheaper and more precise over repeated iterations

So every iteration is doing two things at once:

1. trying to close the immediate first-order gap
2. producing a meta-analysis of how that gap was understood and reduced

That meta-analysis can be retained as disambiguation memory. Over time, those memories reduce the operating surface of future runs. If stable enough, they can be promoted into stronger authority surfaces.

This looks like a learning-discovery vector, but the learning happens at the process layer. The system is not retraining a model. It is evolving a second-order convergence surface over repeated gap analysis.

## Analysis

### First-order and second-order loops

The first-order loop is already present in the method:

- events
- projection
- delta
- gap analysis
- repricing

That structure is explicit in [SPEC_METHOD.md](/Users/jim/src/apps/genesis_sdlc/specification/standards/SPEC_METHOD.md#L91) and [SPEC_METHOD.md](/Users/jim/src/apps/genesis_sdlc/specification/standards/SPEC_METHOD.md#L197).

But every real iteration also generates a second kind of output:

- which ambiguities mattered
- which context distinctions were decisive
- which search steps were necessary
- which interpretations were accepted or rejected
- which edge-local heuristics reduced cost

Those are not the product artifact. They are observations about the convergence process itself.

So the full system is better modeled as:

- first-order SDLC: converge the product graph
- second-order SDLC: converge the process that closes first-order gaps

### What the second-order SDLC is optimizing

The second-order loop optimizes the cost and precision of future convergence.

A useful way to frame an edge gap is:

`gap = artifact_delta + evidence_delta + disambiguation_delta`

The first-order SDLC is concerned mainly with reducing artifact and evidence delta.

The second-order SDLC is concerned with reducing disambiguation delta over time.

That means the system is not only asking:

- what artifact is missing
- what evidence is missing

It is also asking:

- what remained ambiguous on this iteration
- what was learned about resolving that ambiguity
- what can be reused next time so the same edge becomes cheaper to converge

### Disambiguation memory is the state of the second-order SDLC

Disambiguation memories are not generic history. They are retained resolutions of prior ambiguity.

They can capture:

- mappings from vague intents to concrete task shapes
- stable project-local vocabulary
- edge-local context reductions
- successful search and probe patterns
- known bad interpretations
- repeated evidence expectations that are not yet constitutional

These memories tighten context and reduce the operating surface of later runs.

That is why they look like a learning vector. The system is discovering which distinctions matter, retaining them, and using them to narrow future execution.

In effect, repeated convergence induces a category over intents and disambiguation memories:

- raw intents arrive broad and ambiguous
- execution resolves some of that ambiguity in context
- retained disambiguation memories collapse recurring ambiguity classes
- future runs operate over a narrower interpreted intent surface

So the graph is not only converging outputs. It is converging its own interpretation space.

### Why this is an SDLC and not just a cache

A cache stores prior results.

A second-order SDLC does more than that:

- it has inputs: iteration traces, edge failures, accepted resolutions, search paths
- it has analysis: meta-gap analysis over repeated convergence attempts
- it has artifacts: disambiguation memories, edge profiles, narrowed operating surfaces
- it has promotion paths: local memory, design adoption, specification adoption
- it has its own notion of drift: remembered disambiguation may become stale as the first-order graph changes

So this layer has real lifecycle behavior:

- discovery
- retention
- projection
- qualification
- promotion
- repricing

That is SDLC-like behavior operating over the convergence process itself.

### Why GTL is a plausible substrate

The existing realization is already close enough to host this layer.

The current Python variant states that lifecycle assets are GTL `Node` declarations and lifecycle edges are `GraphVector` boundaries at [design/README.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/design/README.md#L63). It also already materializes edge-level refinement boundaries using `deferred_refinement(...)` at [graph.py](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/src/genesis_sdlc/workflow/graph.py#L447).

That suggests a direct path:

- treat first-order edge executions as observable events
- project repeated executions into second-order memory assets
- define second-order vectors that assess or refine disambiguation surfaces
- use GTL boundaries to express where remembered disambiguation is allowed to narrow later edge execution

This would not replace the original SDLC graph. It would sit over it.

The first graph converges the product.
The second graph converges the convergence process.

### Authority boundary

This second-order layer must not silently create law.

Disambiguation memories should begin below constitutional authority:

- run-local
- workspace-local
- edge-local

Only repeated stable memories should be promoted upward into design or specification.

That keeps the process adaptive without letting local heuristics become accidental law. It is consistent with the promotion and repricing discipline already required by [SPEC_METHOD.md](/Users/jim/src/apps/genesis_sdlc/specification/standards/SPEC_METHOD.md#L419) and with the ownership rules at [SPEC_METHOD.md](/Users/jim/src/apps/genesis_sdlc/specification/standards/SPEC_METHOD.md#L224).

## Current Reality

Current reality:

- the first-order SDLC is explicit
- gap analysis is explicit
- edge boundaries are explicit
- GTL already models typed assets, vectors, and refinement boundaries

What is missing is an explicit second-order surface that captures and reuses disambiguation outcomes across iterations.

Right now that knowledge mostly lives as ephemeral operator intuition, agent memory, or ad hoc commentary posts.

## Target Direction

The target is a second-order convergence layer that:

- records disambiguation outcomes from first-order iterations
- projects recurring ambiguity patterns
- narrows future context lawfully
- reduces the operating surface of repeated edge execution
- identifies when remembered narrowing should be promoted into design or specification

## Recommended Action

1. Define second-order assets.
   Candidate assets:
   disambiguation_memory
   edge_profile
   search_trace
   ambiguity_budget
   promotion_candidate

2. Define second-order events and projections.
   First-order iterations should emit enough structure to reconstruct how ambiguity was resolved, not only whether the edge passed or failed.

3. Define second-order gap analysis.
   Measure not only artifact and evidence deltas, but recurring disambiguation delta.

4. Use GTL to model the layer.
   Represent second-order assets and vectors explicitly instead of leaving them as commentary or hidden agent state.

5. Keep authority separation strict.
   Disambiguation memory narrows execution first. Only repeated stable resolutions should be promoted into design or specification.

## Working Thesis

The graph should be understood as two coupled SDLCs. The first-order SDLC converges product artifacts and evidence. The second-order SDLC converges the method by which first-order gaps are interpreted and closed. Each iteration therefore performs a meta-analysis over itself. The retained output of that analysis is disambiguation memory, which tightens context, reduces the operating surface of later runs, and creates a process-level learning-discovery vector. GTL tooling appears sufficient to model this second-order layer explicitly rather than leaving it implicit in operator intuition.
