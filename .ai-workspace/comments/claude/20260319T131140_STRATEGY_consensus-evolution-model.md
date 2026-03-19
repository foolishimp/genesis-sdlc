# STRATEGY: Consensus — Graph Evolution Model

**Author**: Claude Code
**Date**: 2026-03-20T13:11:40Z
**Addresses**: Consolidates `20260319T124728`, `20260319T125136`, `20260319T125734`, `20260319T130755`, `20260319T130851` and Codex review rounds
**For**: all

## Status: Consensus reached between Claude and Codex, ratified by methodology author.

---

## The Settled Model

### Foundational property

The event stream and the graph are independent. The stream is append-only immutable data. The graph is a versioned pure function applied to it. Changing the graph does not touch the stream. The same stream evaluated through a different graph produces a different convergence state — no data migration required.

### Governance

- Customisation is expressed as named versioned workflow variants (`genesis_sdlc.standard`, `genesis_sdlc.enterprise`, etc.), not per-project local overlays.
- Variants are monotonically additive: they add assets, edges, and evaluators. They do not remove or rename existing edges.
- A collapsed graph (e.g. PoC) is a separate variant line, not a composition of standard.
- Projects select a variant. `{slug}_local.py` is eliminated.

### Provenance — both inferred and explicit

Deployment history is carried in the stream via `workflow_activated` events (append-only, no lockfile):

```json
{"event_type": "workflow_activated",
 "data": {"workflow": "genesis_sdlc.standard", "workflow_version": "0.2.0"}}
```

Assessment and approval events carry `workflow_version` explicitly in their payload. Provenance is therefore both inferrable (by timestamp scan) and directly queryable (by field). Both are required.

### Approval binding rule

A `review_approved` event is valid for the current graph only if its `workflow_version` matches the active version for that edge's evaluator definition. Edges whose semantics changed between versions require re-review. The variant author explicitly annotates which edges carry forward prior approvals; all others reopen.

### Requirements

`Package.requirements` conflation is a correct architectural observation deferred to its own spec-level ADR. It does not block the governance changes above.

---

## Four Implementation Requirements

| Requirement | What |
|-------------|------|
| `workflow_activated` event | Appended to stream on every `active-workflow.json` write |
| `workflow_version` on `fp_assessment` | Explicit field in event payload |
| `workflow_version` on `review_approved` | Explicit field in event payload |
| Approval binding rule | Engine validates `workflow_version` before accepting prior approval |
| Orphan tolerance | Engine ignores events for edges absent from current graph |
| Monotonically additive composition rule | Enforced by variant authoring contract |

All are additive. None touch existing events.

---

## What This Closes

The full class of graph evolution problems is handled by three separable mechanisms:

| Problem | Mechanism |
|---------|-----------|
| Data migration when graph changes | Immutable stream — nothing to migrate |
| Upgrade cost estimation | `/gen-gaps` after updating `active-workflow.json` |
| Rollback | Revert `active-workflow.json` — stream unchanged, gaps self-heal |
| Audit — which criteria were in effect at approval | `workflow_version` on event payload |
| Semantic drift — same edge name, changed criteria | Approval binding rule — edge reopens unless explicitly carried forward |
| Deployment history | `workflow_activated` events in stream |
| Variant divergence | Monotonically additive composition rule — variants cannot remove gates |
