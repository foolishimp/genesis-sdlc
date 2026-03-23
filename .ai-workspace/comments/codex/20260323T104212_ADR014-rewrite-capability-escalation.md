# REVIEW: ADR-014 Rewrite — Capability Escalation, Not Deterministic Blockage

**Author**: Codex
**Date**: 2026-03-23T10:42:12+11:00
**For**: Jim / Claude
**Targets**: `abiogenesis` ADR-014, engine escalation semantics

## Summary

ADR-014 should be rewritten. Its core message is backwards for the intended ABG enterprise model.

The current ADR message is:

- `F_D` failure means do not escalate to `F_P`
- `F_D` and `F_P` must both be green before `F_H`

That is a conservative gate model, but it is not the intended capability model.

The intended message is:

- `F_D` runs first because deterministic machinery is cheapest and least ambiguous
- when deterministic machinery is insufficient to close the delta, the work escalates to `F_P`
- `F_P` is an agentic builder/reviewer, not a formatter over already-valid state
- `F_H` is reserved for irreducible judgment, policy, and acceptance

## What broke

This doctrinal turn was introduced on 2026-03-16:

- `40d1209` changed `schedule.iterate()` so same-edge `F_D` failure blocks `F_P` dispatch
- `3ee4e7e` then made `gen_iterate()` consistent with that rule by returning `fd_gap` without producing a manifest
- ADR-014 was added to justify that rule

Before `40d1209`, the engine still dispatched `F_P` when `F_P` evaluators were failing, even if `F_D` was also red.

## Why ADR-014 is wrong

The phrase “broken deterministic state” is the problem.

In construction work, a broken deterministic state is often the normal reason to escalate:

- missing files
- missing sections
- missing structure
- failing structural checks
- incomplete artifacts

Those are not necessarily reasons to stop escalation. They are often the reason to invoke the builder.

This matters especially because ABG uses agentic codebuilders. Their value is not just formatting valid state. Their value is discovery, repair, synthesis, and navigation of ambiguity. If `F_D` blocks escalation on ordinary construction deficits, the system collapses `F_P` into a shallow post-processing role.

## Replacement doctrine

ADR-014 should be replaced with:

1. `F_D` is first-pass capability.
   It resolves what deterministic machinery can resolve cheaply and safely.

2. `F_D` failure is usually an escalation trigger, not a stop condition.
   Deterministic findings describe the problem surface to `F_P`.

3. `F_P` is the constructive layer.
   It may build, repair, synthesize, and review where deterministic capability is insufficient.

4. `F_H` is the judgment layer.
   It handles policy, tradeoffs, acceptance, and ambiguity that remains after `F_P`.

5. Only fatal engine/runtime failures should stop escalation outright.
   Ordinary artifact incompleteness is not a fatal condition.

## The needed semantic distinction

The engine currently treats all same-edge `F_D` failures as blockers.

It needs at least this distinction:

- `F_D_blocking`
  - fatal preconditions
  - impossible environment
  - missing required upstream source that makes construction meaningless or unsafe

- `F_D_certifying`
  - structural findings
  - shallow correctness checks
  - post-build validations
  - conditions that may still require `F_P` to create or repair the artifact

Without this distinction, domain graphs get distorted to fit the wrong engine law.

## Practical implications

1. Pause GSDLC topology decisions that are being forced by ADR-014 semantics.

2. Return to ABG engine semantics first.

3. Rewrite ADR-014 so it describes capability escalation, not deterministic blockage.

4. Revisit `schedule.iterate()` and `gen_iterate()`:
   - same-edge `F_D` findings should not automatically suppress `F_P`
   - manifests should describe deterministic findings when escalation is appropriate

5. Re-run the GSDLC topology work only after the engine law is corrected.

## Proposed replacement one-liner

Use this message instead of the current ADR-014 message:

`F_D runs first; unresolved deterministic deficits escalate to F_P; unresolved judgment escalates to F_H.`

That is the ABG ladder the current March 16 gate rule replaced, and it should be restored.
