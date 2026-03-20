# ADR-012: Variant and Projection Support

**Status**: Accepted
**Date**: 2026-03-21
**Implements**: REQ-F-VAR-001

## Context

Not every project needs the full 10-asset graph. Hotfixes need `code↔tests` only. PoCs skip module decomposition. The graph must be zoomable without losing invariant guarantees.

## Decision

### Named profiles as projections

Each profile selects a subgraph of the full SDLC graph. A valid projection preserves the four invariants: graph, iterate, evaluators, context.

| Profile | Graph subset | When |
|---------|-------------|------|
| full | All 10 assets, 9 edges | Regulated, high-stakes |
| standard | Core + decomposition (default) | Normal feature work |
| poc | Core edges, decomp collapsed | Proof of concept |
| spike | Minimal edges | Research/experiment |
| hotfix | code↔unit_tests only | Emergency fix |
| minimal | Single edge | Trivial change |

### Projection validity

`valid(P) ⟺ ∃ G ⊆ G_full ∧ ∀ edge ∈ G: iterate(edge) defined ∧ evaluators(edge) ≠ ∅ ∧ convergence(edge) defined ∧ context(P) ≠ ∅`

Collapsing intermediate nodes removes them from the convergence path but preserves the endpoints. The graph is zoomable — any sub-graph that satisfies the invariant is a valid projection.

### V1 scope

V1 runs the standard profile. Profile selection is not yet configurable at runtime — the full graph is always loaded and the engine iterates all edges. Profile support is structural (the Package can be projected) but not yet operationalized (no `--profile` flag).

## Consequences

- The Package defines the superset; projections select subsets
- Future `--profile` flag would filter edges before the convergence loop
- No code change required for V1 — the concept is recorded for when projection selection is needed
