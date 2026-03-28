# REVIEW: Agent Compaction Vs Second-Order SDLC Memory

**Author**: codex
**Date**: 2026-03-28T04:10:20+1100
**Addresses**: relationship between existing coder-agent compaction behavior and the proposed second-order SDLC memory layer
**Status**: Draft

## Summary

The proposed second-order SDLC memory layer is in the same family as existing coder-agent compaction, but it is not the same thing.

Coder-agent compaction is a primitive instance of the general mechanism:

- compress prior work
- retain enough context to continue
- reduce rediscovery cost

That is real value. But it remains mostly implicit, session-shaped, and agent-local.

The proposed second-order SDLC memory layer turns that implicit convenience into an explicit graph-level product surface.

## What Existing Agent Compaction Already Does

Current compaction behavior already resembles a minimal memory system.

Functionally, it provides:

- short-horizon retention of what matters from the prior turn
- compression of long episodes into smaller reusable summaries
- carry-forward of some disambiguations
- lower repeated search cost inside the same task thread

That looks roughly like:

- `working_memory`: current active context
- `episodic_memory`: compacted session summary
- weak `semantic_memory`: any persisted preferences or durable workspace memories

So the proposal is not inventing the need for memory from nothing. It is recognizing and formalizing a mechanism that already appears useful in practice.

## What Agent Compaction Does Not Yet Do

Agent compaction is still too narrow for the proposed product surface.

It is generally:

- session-local
- opaque
- not typed as domain artifacts
- not attached to explicit edge classes
- not derived from formal gap episodes
- not graded by affect or resource pressure
- not consolidated through an offline process
- not systematically promoted into design or specification

That is the main difference.

Compaction helps an agent keep going.

The proposed memory layer helps the graph get better at converging recurring classes of work.

## The Product Difference

Second-order SDLC memory would add what compaction lacks:

- first-class memory artifacts
- explicit memory scopes
- gap-derived provenance
- edge profiles and disambiguation memories
- affect-informed resource grading
- consolidation across episodes
- promotion pathways into design or specification

So the product surface is not:

"make compaction better"

It is:

"make remembered disambiguation and convergence learning part of the SDLC itself"

## Practical Interpretation

The right reading is:

- coder-agent compaction proves that memory compression and carry-forward are useful
- the second-order SDLC proposal generalizes that pattern from agent survival to graph optimization

In other words:

compaction is a local survival mechanism
second-order SDLC memory is a domain-level convergence mechanism

## Working Thesis

Existing coder-agent compaction is a primitive example of the same family of behavior the second-order SDLC proposal wants to formalize. It already shows that compressed carry-forward context reduces repeated disambiguation cost. The proposal extends that idea from opaque agent-local summaries into explicit graph-level memory artifacts with scope, provenance, consolidation, affect grading, and promotion rules. Compaction helps one agent continue. Second-order SDLC memory helps the system learn how to converge recurring edge classes.
