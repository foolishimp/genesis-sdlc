# STRATEGY: Manual-First Automation Discipline

**Author**: Codex
**Date**: 2026-03-21
**Status**: Proposed

## Principle

If a process cannot be executed clearly by hand, it is not ready to be
automated.

Automation is not allowed to invent semantics. It is only allowed to compress,
stabilize, and accelerate a manual process that is already intelligible.

## Why This Matters

Genesis exists to reduce cognitive load without hiding truth.

That means:

- complexity may be internalized
- it may be abstracted and encapsulated
- but it must still correspond to a process that can be explained and replayed
  manually

If humans cannot walk the chain by hand, the engine should not pretend it can
deliver it automatically.

## Rule

Every intended automation must have a valid manual walkthrough.

That walkthrough must identify:

1. inputs
2. context/model used for judgment
3. state transitions
4. outputs
5. failure modes
6. escalation points
7. where F_D, F_P, and F_H each actually apply

If any of those are unclear in the manual path, the automation target is still
ill-posed.

## What Automation Is

Automation is a semantic compression of a manual method.

It should:

- preserve the meaning of the manual path
- reduce operator and agent cognitive load
- make the process more deterministic, observable, and replayable

It should not:

- replace unclear judgment with hidden machinery
- obscure custody boundaries
- hide missing inputs or model assumptions
- collapse ambiguous human decisions into fake deterministic steps

## ABG / GSDLC Split

This discipline clarifies the boundary between the two layers.

`abg`:

- owns the hop-local kernel mechanics
- should be manually walkable as a bounded single-hop process

`gsdlc`:

- owns reliable multi-hop delivery and custody
- should automate traceability, routing, and end-to-end observability

When `gsdlc` is broken, manual walkthroughs become the temporary replacement for
the missing network layer. That is not wasted work. It is the oracle that later
automation must satisfy.

## Design Consequence

Nearly all automations should be playable through as manual walkthroughs first.

If they cannot be played through manually, then one of two things is true:

- the process is not yet understood well enough
- the proposed automation is hiding a real design gap

Both cases mean: do not automate yet.

## Practical Use

For every future Genesis automation:

1. write the manual walkthrough first
2. validate that it can be executed end-to-end without hand-waving
3. identify which parts are F_D, F_P, and F_H
4. automate only the parts whose semantics are already clear
5. use the manual walkthrough as the test oracle for the automation

## Bottom Line

Manual first, automation second.

Automation must preserve the semantics of the manual path. If it cannot, it is
not reliable automation. It is theater.
