# STRATEGY: Graph Edge Disambiguation Economics

**Author**: codex
**Date**: 2026-03-28T03:43:10+1100
**Addresses**: ambiguity, gap analysis, and memory for any graph that converges edge by edge
**Status**: Draft

## Summary

This is broader than `genesis_sdlc`.

For any graph where work is organized as edge convergence and assessed by gap analysis, an edge carries two kinds of load:

1. transformation load
2. disambiguation load

Transformation load is the work required to produce or assess the target artifact. Disambiguation load is the work required to determine what the edge actually means in this context: what inputs matter, what evidence is relevant, what counts as sufficient, what tools should be used, and how broadly the runtime may search.

An edge can pay more of that cost up front through explicit configuration, or it can defer more of that cost to runtime interpretation. Up-front narrowing gives cheaper repeated execution but a smaller lawful problem envelope. Runtime ambiguity gives broader reach but makes each convergence pass more expensive.

The method should support both. Memory is what lets the graph stop paying the same disambiguation cost on every pass.

## Analysis

### Gap analysis is not only artifact comparison

In a convergence graph, a gap is usually treated as "distance between current state and target state."

That is incomplete.

A real gap on an edge often includes:

- missing target work
- missing evidence
- unresolved interpretation
- unclear boundary conditions
- unclear tool-selection strategy
- unclear success criteria at this edge

So part of what the system is measuring is not just "what is missing?" but "how much ambiguity remains before the edge can be evaluated cheaply and repeatably?"

That means ambiguity itself is part of edge cost.

### Two ways to reduce edge ambiguity

An edge can be tightened in two different places.

1. Before runtime

- clearer manifests
- stronger schemas
- narrower inputs
- more explicit evaluator criteria
- constrained search space
- pre-bound tools or protocols

2. During runtime

- discovery over the local graph context
- search over repo or workspace state
- interpretation of vague intent
- adaptive choice of probes or transformation strategy

Both are lawful. They simply place the cost in different parts of the process.

### The economic tradeoff

If ambiguity is collapsed earlier:

- each run gets cheaper
- reuse gets easier
- convergence gets more repeatable
- the edge becomes narrower

If ambiguity is carried into runtime:

- each run gets more expensive
- convergence requires more discovery and interpretation
- the edge can operate over a wider class of situations

So the question for any edge is:

"Should this edge be cheap and narrow, or expensive and broad?"

That should be a deliberate design choice, not an accident of weak specification or weak tooling.

### Memory changes the shape of the graph

Without memory, a broad edge re-pays the same ambiguity bill every time.

It must repeatedly rediscover:

- which inputs actually matter
- which evidence patterns are trusted
- which local conventions are stable
- which tool sequences work
- which interpretations were already accepted or rejected

Memory changes that.

It does not remove the need for discovery everywhere, but it lets prior disambiguation become reusable process structure.

That means memory is not just a convenience layer. It changes convergence economics.

An edge that was initially broad can become cheaper over time if remembered disambiguations are reused.

### Memory is not the same as law

Not every remembered resolution should become constitutional truth.

There are at least four levels:

- run-local memory
- workspace-local memory
- graph-local or edge-local memory
- ratified design or specification

The system should keep resolutions at the smallest lawful scope until repetition proves they are stable enough to promote.

Otherwise the graph hardens too quickly and local convenience becomes accidental law.

### F_P agents are one execution mechanism for this broader rule

A coding agent on an F_P edge is a concrete example of runtime disambiguation.

It has shell access, tools, and discovery capacity. So it can absorb ambiguity at runtime. That makes it useful for broad edges. It also makes it expensive if the same ambiguity is rediscovered over and over.

But the principle is larger than F_P.

Any edge execution regime has the same question:

- how much ambiguity is precompiled into the edge contract
- how much ambiguity is left for runtime
- how much remembered disambiguation can be reused

## Recommended Action

1. Treat disambiguation load as an explicit part of edge design.
   Edge design should say not only what the edge transforms or evaluates, but how much ambiguity the edge is allowed to carry into runtime.

2. Add an ambiguity budget to gap analysis.
   A gap should include both missing artifact/evidence and unresolved ambiguity burden where that burden materially affects convergence cost.

3. Add memory scoped to graph reality.
   Remembered disambiguations should be attachable at run, workspace, edge, or graph scope.

4. Add promotion rules.
   When the same ambiguity is resolved the same way repeatedly, the resolution should be reviewed for promotion into manifests, design, or specification.

5. Distinguish narrow edges from broad edges intentionally.
   Some edges should be cheap and rigid. Some should be exploratory and adaptive. The graph should know which is which.

## Working Thesis

In any convergence graph, an edge does not only carry transformation work. It also carries disambiguation work. Narrow edge design pays that cost earlier and buys cheaper repeated convergence. Broad edge design pays that cost later and buys wider applicability. Memory is the mechanism that prevents broad edges from paying the same disambiguation cost forever. Good gap analysis should therefore measure not only what artifact or evidence is missing, but how much unresolved ambiguity still sits on the edge.
