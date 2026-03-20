# STRATEGY: Prime Operator Refactor Plan

**Author**: Claude Code
**Date**: 2026-03-20T02:04:32Z (updated 2026-03-20)
**Addresses**: Prime operator consensus, Codex reviews on ontology/scope/EC consistency/referent contract/rejection/dependent scope, clean-start assumption
**For**: all

## Summary

Refactor the abiogenesis engine and genesis_sdlc to use the five prime consciousness-loop operators with Event Calculus projection semantics. Clean start — no backward compatibility, no migration of historical logs. Add `revoked` with exact referent scoping.

**Clean-start assumption**: All dependent workspaces get fresh event logs. Old `events.jsonl` files are archived (read-only, not rewritten). No backward-compat branches in code. No migration script.

---

## Formal Foundation: Event Calculus

The projection layer implements Event Calculus over `events.jsonl`:

| EC Primitive | Meaning | Implementation |
|---|---|---|
| `happensAt(E, T)` | Event E occurred at time T | Line in `events.jsonl` with `event_type` and `event_time` |
| `initiates(E, F, T)` | Event E starts fluent F at time T | e.g. `approved` initiates `operative(edge, wv)` |
| `terminates(E, F, T)` | Event E ends fluent F at time T | e.g. `revoked` terminates `operative(edge, wv)` |
| `holdsAt(F, T)` | Fluent F is true at time T | Projection query: was F initiated and not subsequently terminated? |

### Fluents (time-varying properties projected from the log)

| Fluent | Initiated by | Terminated by |
|--------|-------------|---------------|
| `operative(edge, wv)` | `approved{kind: fh_review}`, `approved{kind: fh_intent}` | `revoked{kind: fh_approval}` |
| `certified(edge, evaluator, spec_hash, wv)` | `assessed{kind: fp, result: pass}` | spec_hash change, workflow_version change |

Two fluents. No others. Every convergence-gating query is either a `holdsAt` on one of these, or a live F_D execution.

### F_D: Stateless — No Fluent

F_D evaluators re-run their command on every iteration. Their results are not projected state — they are live computation. `found{kind: fd_gap}` is a `happensAt`-only event: it records the observation for audit but does not initiate or terminate any fluent and does not gate anything.

### Two Convergence Models, One System

| Evaluator type | Convergence model | Query |
|---|---|---|
| F_D | Live execution | `run_fd_evaluator(ev) -> passes` |
| F_H | Fluent projection | `holdsAt(operative(edge, wv), now)` |
| F_P | Fluent projection | `holdsAt(certified(edge, ev, spec_hash, wv), now)` |

The `_passes()` function in `bind_fd` dispatches by evaluator category. F_H and F_P use `holdsAt` queries against the log. F_D runs its command. These are the only three paths.

### Three-Layer Architecture

```
Layer 1: Event Calculus    — fluent truth over time (holdsAt, initiates, terminates)
         + F_D live eval   — stateless re-computation (no fluent)
Layer 2: Scheduler rules   — which work to dispatch given current convergence state
Layer 3: Orchestrator      — resource allocation, parallelism, retry policy
```

Only Layer 1 changes in this refactor.

---

## Governance Decision: Prime Rename

Event Calculus lives in the projection rules (`initiates`, `terminates`, `holdsAt`), not in the short English names of persisted events. Adding `revoked` and formal projection logic gives the EC foundation without forcing a rename from `review_approved`/`fp_assessment`/`fd_gap_found` to `approved`/`assessed`/`found`.

**The rename is a governance choice for conceptual cleanliness, not a formal EC requirement.**

Rationale for proceeding with the rename:

1. Five primes with `kind` discriminator is a smaller, more composable vocabulary
2. Clean start eliminates the rollout cost that would otherwise make this questionable
3. The `kind` field makes the event schema extensible without adding new `event_type` values
4. Alignment between the formal model (five operators) and the persisted schema (five event types) reduces cognitive load

If the rename cost is judged too high even under clean start, the alternative is: keep existing names, add `revoked` as the only new event type, and implement EC projection rules using the current names. The formal benefits are identical.

---

## Three-Tier Event Taxonomy

### Tier 1 — Consciousness-loop primes (participate in EC fluent projection or audit)

| Prime | Concrete rename | Payload `kind` | EC role |
|-------|----------------|----------------|---------|
| `found` | `fd_gap_found` becomes `found` | `kind: fd_gap` | `happensAt` only (audit) |
| `approved` | `review_approved` becomes `approved` | `kind: fh_review` | `initiates operative(edge, wv)` |
| `approved` | `intent_approved` becomes `approved` | `kind: fh_intent` | `initiates operative(edge, wv)` |
| `assessed` | `fp_assessment` becomes `assessed` | `kind: fp` | `initiates certified` when `result: pass` |
| `assessed` | `review_rejected` becomes `assessed` | `kind: fh_review, result: reject` | `happensAt` only (see below) |
| `revoked` | *(new)* | `kind: fh_approval` | `terminates operative(edge, wv)` |
| `intent_raised` | unchanged | unchanged | `happensAt` only |

### Placement of `review_rejected`

`review_rejected` is an F_H evaluation outcome — the reviewer evaluated the candidate and said no. In the prime model it maps to `assessed{kind: fh_review, result: reject}`:

- Does **not** initiate any fluent (rejection doesn't grant authority)
- Does **not** terminate any fluent (rejection is not revocation — nothing was approved to withdraw)
- Records the evaluation outcome and reason for the audit trail
- The gate was already not passing (no `approved` for this edge); rejection records *why*

**Distinction from `revoked`**: Rejection says "this candidate doesn't pass." Revocation says "a prior approval is no longer valid." Rejection is a judgment on the current work. Revocation is a withdrawal of previously granted authority. They are different speech acts with different EC consequences.

**Distinction from `approved`**: `approved` initiates the `operative` fluent (authority grant). `assessed{kind: fh_review, result: reject}` is `happensAt`-only (no fluent change). The asymmetry is correct — approval changes state, rejection confirms the existing state (gate not passing).

### Tier 2 — Control/audit (scheduler bookkeeping, not fluent operators)

These stay as-is. Emitted by the scheduler and command layer (Layer 2), not the consciousness loop.

| Event | Emitter | Purpose |
|-------|---------|---------|
| `edge_started` | commands.py | Traversal start marker |
| `fp_dispatched` | schedule.py | Scheduler requests F_P work |
| `fh_gate_pending` | schedule.py | Scheduler announces gate wait |
| `edge_converged` | commands.py | Convergence certificate |

### Tier 3 — Lifecycle (infrastructure, unchanged)

| Event | Purpose |
|-------|---------|
| `genesis_installed` | Engine install |
| `genesis_sdlc_installed` | Workflow install |
| `genesis_sdlc_released` | Release record |
| `workflow_activated` | Lens/provenance change |
| `bug_fixed` | Reflex-level fix record |

---

## Revocation Referent Contract (EC: terminates)

### What `revoked` terminates

`revoked` terminates a **fluent**, not a specific event. The referent is `operative(edge, wv)` — a time-varying property that is either true or false at any given moment.

```
terminates(revoked{kind: fh_approval, edge: E, wv: W}, operative(E, W), T)
```

This means:
- `revoked` does not "point at" or "undo" a particular `approved` event
- It sets `holdsAt(operative(E, W), now)` to false from time T onward
- The number of prior `approved` events is irrelevant — the fluent is binary
- A subsequent `approved` can re-initiate the fluent (re-approval after revocation is valid)

### Scope fields and matching rules

| Field | Required | Matching rule |
|-------|----------|--------------|
| `kind` | yes | Must be `fh_approval` (only F_H revocation defined in V1) |
| `edge` | yes | Exact match against fluent's edge, OR `"*"` for all edges |
| `workflow_version` | yes | Exact match against fluent's wv |
| `feature` | no | Informational — narrows audit scope but does not affect fluent matching |
| `actor` | yes | `"human"` or `"human-proxy"` — authority source for audit |
| `reason` | yes | Free text — why the authority is being withdrawn |

### Projection algorithm

```
holdsAt(operative(E, W), now):
  1. Scan all events chronologically
  2. Find the latest approved{kind: fh_*, edge: E, wv: W} at time T_a
  3. If none found: return false
  4. Find any revoked{kind: fh_approval, edge: E or *, wv: W} at time T_r where T_r > T_a
  5. If found: return false
  6. Return true
```

### What `revoked` is NOT

- Not a rejection (that's `assessed{result: reject}` — judgment on current work)
- Not an observation (that's `found` — something detected)
- Not a new evaluation (that's `assessed` — bounded judgment with result)
- It is exclusively: withdrawal of previously granted authority

### Revocation lifecycle

```
T0: approved{kind: fh_review, edge: E}     -> holdsAt(operative(E, W)) = true
T1: revoked{kind: fh_approval, edge: E}    -> holdsAt(operative(E, W)) = false
T2: [iterate, fix the issue]
T3: approved{kind: fh_review, edge: E}     -> holdsAt(operative(E, W)) = true (re-approval)
```

### Wildcard semantics

`edge: "*"` is syntactic sugar. The projection expands it:

```
revoked{kind: fh_approval, edge: "*", wv: W}
  ≡ for all E where holdsAt(operative(E, W)): terminates(operative(E, W))
```

This enables full-graph reset without emitting one event per edge.

### Example payloads

**Single edge revocation:**
```json
{
  "event_type": "revoked",
  "data": {
    "kind": "fh_approval",
    "edge": "feature_decomp->design",
    "workflow_version": "genesis_sdlc.standard@0.3.0",
    "actor": "human",
    "reason": "design assumptions invalidated by new constraint"
  }
}
```

**Full graph reset:**
```json
{
  "event_type": "revoked",
  "data": {
    "kind": "fh_approval",
    "edge": "*",
    "workflow_version": "genesis_sdlc.standard@0.3.0",
    "actor": "human",
    "reason": "spec change requires full re-evaluation"
  }
}
```

---

## Rename Mapping (event_type field)

| Before | After | Payload changes | EC semantics |
|--------|-------|----------------|--------------|
| `fd_gap_found` | `found` | add `kind: fd_gap` | `happensAt` only |
| `review_approved` | `approved` | add `kind: fh_review` | `initiates operative` |
| `intent_approved` | `approved` | add `kind: fh_intent` | `initiates operative` |
| `fp_assessment` | `assessed` | add `kind: fp` | `initiates certified` (when pass) |
| `review_rejected` | `assessed` | add `kind: fh_review, result: reject` | `happensAt` only |
| *(new)* | `revoked` | `kind: fh_approval` + scope fields | `terminates operative` |
| `intent_raised` | `intent_raised` | unchanged | `happensAt` only |
| `edge_started` | `edge_started` | unchanged | Tier 2 — not EC |
| `fp_dispatched` | `fp_dispatched` | unchanged | Tier 2 — not EC |
| `fh_gate_pending` | `fh_gate_pending` | unchanged | Tier 2 — not EC |
| `edge_converged` | `edge_converged` | unchanged | Tier 2 — not EC |

---

## File Change Inventory

### Phase 1 — Abiogenesis engine (EC projection + prime rename)

**Source (5 files):**

| File | Change | EC concept |
|------|--------|-----------|
| `code/genesis/bind.py` | Rename queries; `revoked` terminates check in `bind_fh`; rename F_P assessment queries; handle `assessed{kind: fh_review, result: reject}` | `holdsAt(operative)`, `holdsAt(certified)` |
| `code/genesis/schedule.py` | Rename emitted primes (`fd_gap_found` to `found`, etc); keep Tier 2 names | `happensAt` emission |
| `code/genesis/commands.py` | Rename `fd_gap_found` emission to `found`; keep Tier 2 names | `happensAt` emission |
| `code/genesis/core.py` | Rename `fp_assessment` validation to `assessed`; add `revoked` to valid event types; keep Tier 2 | Schema validation |
| `code/genesis/__main__.py` | Rename governance validation for primes (`review_approved` to `approved`, `fp_assessment` to `assessed`, `review_rejected` to `assessed`); add `revoked` emit-event support; keep Tier 2 | CLI emit-event |

**Note**: `bind.py` already has `bind_fh` changes applied (premature edit from prior session). Verify consistency with remaining files during Phase 1. Remove any backward-compat branches — clean start means no dual acceptance.

**Tests (9 files):**

| File | Scope |
|------|-------|
| `tests/test_bind.py` | Rename all event type strings; add `revoked` terminates tests; add `assessed{result: reject}` tests |
| `tests/test_core.py` | Rename `fp_assessment` to `assessed`; add `revoked` schema tests |
| `tests/test_schedule.py` | Rename prime event assertions |
| `tests/test_commands.py` | Rename prime assertions; keep Tier 2 |
| `tests/test_integration_workflows.py` | Rename all prime assertions |
| `tests/test_property_invariants.py` | Rename `fp_assessment` refs |
| `tests/test_e2e_sandbox.py` | Rename prime assertions |
| `tests/test_e2e_domain_blind.py` | Rename prime assertions |
| `tests/test_provenance_integration.py` | Rename `fp_assessment` and `review_approved` |

**ADRs (5 files):**

| File | Change |
|------|--------|
| `design/adrs/ADR-002-bind-fd-fp-split.md` | Update `review_approved` ref |
| `design/adrs/ADR-005-event-stream.md` | Update prime event refs |
| `design/adrs/ADR-008-fh-gate-routing.md` | Update `review_approved`, `fh_gate_pending` refs |
| `design/adrs/ADR-011-spec-snapshot-binding.md` | Update `fp_assessment` ref |
| `design/adrs/ADR-015-integration-primary-test-architecture.md` | Update `fp_assessment` refs |

**Commands (1 file):**

| File | Change |
|------|--------|
| `commands/gen-start.md` | Rename prime event names |

### Phase 2 — Genesis SDLC (spec + installer + commands)

**Source (2 files):**

| File | Change |
|------|--------|
| `src/genesis_sdlc/sdlc_graph.py` | Rename evaluator names if they match event types |
| `src/genesis_sdlc/install.py` | Rename `fp_assessment`, `review_approved`, `review_rejected` refs |

**Spec (3 files):**

| File | Change |
|------|--------|
| `gtl_spec/packages/genesis_core.py` | Rename `intent_approved` evaluator |
| `gtl_spec/packages/genesis_sdlc.py` | Rename `intent_approved` evaluator; update event schema documentation |
| `gtl_spec/GENESIS_BOOTLOADER.md` | Update event type refs to prime names; document EC formal foundation; add `revoked` and `assessed{reject}` |

**Commands (3 files):**

| File | Change |
|------|--------|
| `.claude/commands/gen-start.md` | Rename prime event names |
| `.claude/commands/gen-iterate.md` | Rename prime event names |
| `.claude/commands/gen-review.md` | Rename `review_approved` to `approved`; rename `review_rejected` to `assessed{kind: fh_review, result: reject}` |

**Tests (1 file):**

| File | Change |
|------|--------|
| `tests/test_e2e_sandbox.py` | Rename `review_approved` assertions |

**Docs (2 files):**

| File | Change |
|------|--------|
| `CHANGELOG.md` | Historical refs — leave as-is |
| `design/adrs/ADR-005-three-layer-install-architecture.md` | Update `fp_assessment` ref |

### Phase 3 — Dependent Projects

**Constraint surface (specs + intents) — manual update required:**

#### genesis-manager

| File | Change |
|------|--------|
| `gtl_spec/packages/genesis_manager.py` | Rename prime event refs in evaluator definitions, REQ criteria, requirement descriptions; add `revoked` to control API valid types; rename `review_rejected` to `assessed{kind: fh_review, result: reject}` |
| `INTENT.md` | Update event type documentation to prime names |

#### gen_enterprise_arch

| File | Change |
|------|--------|
| `gtl_spec/packages/gen_enterprise_arch.py` | Rename prime event refs in evaluator descriptions |

#### genesis_chat

| File | Change |
|------|--------|
| `gtl_spec/packages/genesis_chat.py` | Rename prime event refs |

**Runtime code — explicit migration surface:**

Downstream code is rebuilt from updated specs, but this is not free. Each dependent with runtime code requires a rebuild cycle:

| Dependent | Runtime artifacts | Rebuild method |
|-----------|------------------|---------------|
| genesis-manager | `ProjectDashboard.tsx`, `control.ts`, `WorkspaceReader.ts`, `EventStream.test.tsx`, ADRs, feature YAMLs | Full rebuild from updated spec via `/gen-start --auto` after cascade install. Touches ~100 event type references across ~15 files. |
| genesis_chat | `test_workflow.py` | Rebuild from spec. Fewer references (~10). |
| gen_enterprise_arch | Spec-only project, no runtime code beyond what engine provides | Cascade install only. |
| abiogenesis | `CLAUDE.md`, `README.md`, `gtl_spec/packages/abiogenesis.py` | Manual update during Phase 1 (it's the engine itself). |

**Rebuild is not instant.** genesis-manager has substantial runtime code with ~100 hardcoded event type references. The rebuild from spec will traverse multiple edges and iterate until the code converges on the new event names. Budget for this as real work, not a side effect of install.

### Phase 4 — Clean Epoch Cutover + Release

For each workspace:

1. `mv .ai-workspace/events/events.jsonl .ai-workspace/events/events.pre-v0.4.0.jsonl.archive`
2. Cascade install new abiogenesis engine + genesis_sdlc
3. Fresh `events.jsonl` starts with `genesis_installed` + `genesis_sdlc_installed` + `workflow_activated`
4. Rebuild dependent from updated spec

Release sequence:

1. Release abiogenesis with engine changes
2. Bump genesis_sdlc to v0.4.0 (breaking event schema change)
3. Update dependent specs (genesis_manager.py, gen_enterprise_arch.py, genesis_chat.py)
4. Cascade install to all dependents (archive old logs, fresh epoch)
5. Rebuild dependents from spec — genesis-manager is the largest, budget accordingly

---

## Execution Order

```
1. abiogenesis engine source (bind.py, schedule.py, commands.py, core.py, __main__.py)
   - bind.py: verify premature edit, remove backward-compat branches
   - __main__.py: add revoked to emit-event, rename review_rejected
2. abiogenesis engine tests (all 9 files) — run tests, confirm green
3. abiogenesis non-engine files (CLAUDE.md, README.md, gtl_spec, ADRs, commands)
4. genesis_sdlc source (sdlc_graph.py, install.py)
5. genesis_sdlc spec (genesis_core.py, genesis_sdlc.py, GENESIS_BOOTLOADER.md)
6. genesis_sdlc commands (gen-start.md, gen-iterate.md, gen-review.md)
7. genesis_sdlc tests — run tests, confirm green
8. Release abiogenesis, release genesis_sdlc v0.4.0
9. Update dependent specs (prime event refs in requirements/evaluators)
10. Cascade install + archive old logs
11. Rebuild genesis-manager from spec (largest dependent, ~100 refs)
12. Rebuild genesis_chat from spec
```

---

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Missed reference in engine | Grep sweep for all old event names before test run |
| Dependent spec has stale event refs | Grep sweep of all `gtl_spec/` dirs before cascade |
| genesis-manager rebuild doesn't converge | Verify spec is complete w.r.t. new event names before starting rebuild |
| review_rejected semantics confused with revoked | Documented distinction: rejection = judgment on current work, revocation = withdrawal of prior authority |
| revoked scope fields under-specified | Full referent contract with matching rules, algorithm, examples, and lifecycle |
| Archive logs needed for audit | Archive files preserved at known path, never deleted |
| Control/audit events accidentally renamed | Clear tier boundary — only Tier 1 primes participate in EC fluents |

---

## Decision Gate

Clean-start refactor. The constraint surface changes are:

- **Engine** (abiogenesis): ~20 source + test files — EC projection rules, prime rename, `revoked` operator, `assessed{reject}` placement
- **Methodology** (genesis_sdlc): ~10 source + spec + command files
- **Dependent specs**: ~4 GTL spec files + intent docs — event type refs in requirements
- **Dependent rebuilds**: genesis-manager (~100 refs, full rebuild from spec), genesis_chat (~10 refs)

Confirm before executing.
