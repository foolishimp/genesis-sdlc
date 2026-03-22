# WORKORDER: MVP Blocker — Restore WorkingSurface as the Authoritative Iteration Evidence Surface

**Date**: 2026-03-22T08:23:07Z  
**Priority**: Blocker  
**Status**: Open  
**Applies to**: `abiogenesis` / `abg 1.0`

## Decision

This is an MVP blocker. Do not ship `abg 1.0` with the current split between the GTL `WorkingSurface` contract and the app's real iteration evidence.

## Problem

The constitutional GTL model says:

`iterate(job, evaluator_fn, asset) -> (Asset, WorkingSurface)`

and `WorkingSurface` is defined as the structured side-effect product of a job execution:

- `events`
- `artifacts`
- `context_consumed`

In current `abiogenesis`, that contract has drifted:

- `schedule.iterate()` still returns a `WorkingSurface`
- but the engine only uses `surface.events`
- `surface.artifacts` is not populated
- `surface.context_consumed` is not preserved by the command result
- the real audit artifacts now live outside the surface:
  - `.ai-workspace/fp_manifests/...`
  - `.ai-workspace/fp_results/...`

This creates constitutional drift:

- GTL says the iteration evidence surface is `WorkingSurface`
- shipped behavior says the real evidence surface is split across side channels

That is technical debt and should not ship as `1.0`.

## Why This Blocks MVP

1. The SDK type contract and app behavior no longer agree.
2. The iterator's audit surface has been hollowed out into mostly an event envelope.
3. Real F_P evidence exists, but it is no longer carried by the iteration surface itself.
4. This will make future refactors harder because transport-specific artifacts are escaping the typed contract instead of being represented inside it.

## Current State

Observed shape:

- `WorkingSurface` still exists and still declares `events`, `artifacts`, `context_consumed`
- `schedule.iterate()` populates:
  - `events`
  - `context_consumed`
- it does not populate:
  - `artifacts`
- `gen_iterate()` emits `surface.events`
- `gen_iterate()` writes manifests separately
- `assess-result` consumes result files separately

Net:

- typed iterator surface = partial
- real iteration evidence = externalized

## Required Fix

Restore `WorkingSurface` as the authoritative iteration evidence surface.

Minimum acceptable shape before release:

1. `WorkingSurface.artifacts` must carry iteration evidence paths.
   At minimum:
   - F_P manifest path when dispatched
   - F_P result path when allocated
   - any other audit artifact path created by the iteration

2. `WorkingSurface.context_consumed` must remain meaningful and be preserved by the caller.

3. `gen_iterate()` must not drop the surface contract.
   It must either:
   - return the relevant surface fields explicitly, or
   - persist them in a clearly typed way derived from the surface

4. The app's real iteration evidence must be representable through the same typed surface that GTL declares.

## Non-Solution

Do not "solve" this by rewriting the GTL docs to match the current drift.

If the system creates or depends on:

- manifest files
- result files
- consumed contexts
- audit references

then those belong in the iteration evidence model, not only in ad hoc app-side file handling.

## Acceptance Criteria

This blocker is resolved only when all of the following are true:

1. A single iteration that dispatches F_P produces a `WorkingSurface` that is audit-meaningful.
2. The manifest path is represented in the surface.
3. The result path is represented in the surface.
4. `context_consumed` is not dropped by the command layer.
5. Tests assert more than `isinstance(surface, WorkingSurface)`.
   They must assert that the expected evidence is actually present.
6. The docs/spec describe the same architecture the code implements.

## Review Position

This is not polish.

This is structural integrity work between:

- GTL constitutional types
- ABG app behavior
- auditability of real F_P iterations

Treat it as the next workorder and an explicit MVP blocker for `abg 1.0`.
