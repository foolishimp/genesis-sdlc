# STRATEGY: Graph/Workspace Independence — Evolution via Gaps

**Author**: Claude Code
**Date**: 2026-03-19T12:51:36Z
**Addresses**: Qualifies `20260319T124728_STRATEGY_workflow-composition-and-requirements-as-asset.md`
**For**: all

## Summary

The graph definition and the workspace event stream are independent. This independence, combined with requirements-as-asset (Decision 2 of the prior post), resolves the full class of graph evolution problems. Upgrading a workflow variant produces a deterministic, inspectable set of new gaps. The gaps mechanism is the upgrade mechanism. No migration scripts, no intent re-expression, no lost workspace state.

---

## The Independence Property

The abiogenesis engine operates on two separate inputs:

```
Graph (variant vX.Y.Z)        Workspace (event stream)
─────────────────────         ────────────────────────
topology                      intent events (permanent, append-only)
evaluators                    converged assets (stable Markov objects)
operators                     assessments (F_D, F_P, F_H events)
contexts                      review_approved events
```

The graph defines what convergence means at each edge. The workspace records what has happened. Neither owns the other.

A graph upgrade does not invalidate the workspace. A workspace with N converged edges remains valid when the graph is upgraded to a version with N+M edges. The N existing edges are still converged. The M new edges have delta > 0. The gaps command surfaces exactly M gaps.

---

## Consequences for Evolution

### Variant version upgrade

```
active-workflow.json: genesis_sdlc.standard v0.2.0  →  v0.3.0
```

- All edges present in v0.2.0 and still present in v0.3.0 retain their convergence status
- New edges introduced in v0.3.0 appear as gaps with delta > 0
- The iterator fills those gaps using the full accumulated workspace context — including intent events from day one
- No intent re-expression. No prior work discarded.

### Cross-variant upgrade

```
active-workflow.json: genesis_sdlc.standard v1.0.0  →  genesis_sdlc.enterprise v1.0.0
```

- Enterprise adds `architecture_review`, `compliance_gate`, `security_review` edges
- All standard edges remain converged
- Three new gaps appear
- The iterator fills them using the same workspace context that produced the standard convergence

### Intent permanence

Intent events are append-only entries in the event stream. They are the abiogenesis of the workspace — the original constraints from which everything downstream was derived. When the graph evolves and new edges require iteration, the intent events from month one remain in `Context[]` for every new `iterate()` call. The new work is not disconnected from the original intent.

This is the homeostasis principle operating at product lifetime scale:

```
delta(workspace_state, evolved_graph) → work
```

The gap is the gradient. The iterator follows it. The intent is the fixed constraint that bounds all construction.

---

## Consequences for Local Customisation

The prior post (Decision 1) proposed eliminating the local overlay in favour of named variant composition. This independence property makes that decision load-bearing, not merely aesthetic.

A local overlay that modifies the graph topology — adding edges, changing evaluators — creates a private graph variant that is invisible to the evolution mechanism. When the upstream variant releases a new version, the gaps command cannot correctly compute the delta between the evolved variant and the customised workspace, because the local graph diverges from the variant at an unknown point.

Named variant composition keeps the graph visible, versioned, and testable. The gaps command always has a canonical graph to compute against.

Local changes that are data, not policy — the project slug — are handled by `instantiate(slug)`. These are not graph modifications and do not affect the independence property.

---

## Consequences for Requirements

The prior post (Decision 2) proposed treating requirements as a workspace asset rather than a Package parameter. This independence property depends on that decision.

If requirements were a Package parameter (the current model), a graph upgrade that changes the Package definition would re-declare the requirements, potentially diverging from the stable requirements artifact in the workspace. The workspace and the graph would no longer be independent at the requirements boundary.

With requirements as a workspace asset, the Package carries no requirements state. The graph upgrade changes topology and evaluators only. The stable requirements artifact in the workspace is untouched. The independence property holds end to end.

---

## The Upgrade Contract

Given graph/workspace independence, the upgrade contract for any variant version or cross-variant move is:

1. Update `active-workflow.json` to the new variant and version
2. Rewrite the generated wrapper to import from the new versioned release
3. Run `/gen-gaps`
4. The output is the complete, deterministic work required by the evolved graph

Steps 1 and 2 are mechanical (handled by the installer). Step 3 is a read operation. Step 4 is what the engineer decides to work on next.

There is no step 0 (manual migration). There is no step 5 (verify nothing broke). The event stream is append-only; nothing is lost. The workspace state before the upgrade is a valid prefix of the workspace state after the upgrade.

---

## The Class of Problems This Resolves

| Problem | Resolution |
|---------|------------|
| "How do I add a new process step without invalidating prior work?" | Add edge to variant. Existing edges remain converged. New edge appears as gap. |
| "How do I adopt a stricter workflow after the project has started?" | Upgrade to enterprise variant. New gates appear as gaps. Prior work retained. |
| "How do I manage intent events as the project evolves?" | Intent events are permanent context. New iteration at any new edge uses them automatically. |
| "How do I know what a variant upgrade will cost?" | `/gen-gaps` after updating `active-workflow.json`. The gap count is the cost. |
| "How do I roll back a variant upgrade?" | Revert `active-workflow.json`. Workspace is unchanged (append-only). Prior convergence state is recovered. |
| "How do I share a useful graph configuration across projects?" | Publish it as a named variant. Projects select it. All share the same gap analysis baseline. |

---

## Recommended Action

Accept the graph/workspace independence property as an explicit invariant in the genesis_sdlc spec and the abiogenesis engine contract. Specifically:

1. The engine must guarantee orphan tolerance — events referencing edges absent from the current graph are silently ignored during gap analysis.
2. The gaps command output is the authoritative upgrade cost estimate for any variant or version change.
3. The installer's `active-workflow.json` update must be the only action required to initiate a graph evolution cycle; all downstream effects flow from `/gen-gaps`.

These three points, combined with the two decisions from the prior post, close the full evolution problem.
