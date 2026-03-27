# Spec Guide

**Governance**: Maintained by the methodology author. Read-only for agents unless explicitly asked to revise it.

**Scope**: Applies when writing or revising intent, requirements, design documents, and ADRs.

---

## Position

`SPEC_METHOD.md` is the constitutional process document.

`SPEC_GUIDE.md` is the practical writing guide for producing specification artifacts that conform to that method.

The relationship is:

- `SPEC_METHOD.md` defines authority, chain, and sufficiency
- `SPEC_GUIDE.md` explains how to write artifacts within that structure

This guide does not replace the method. It operationalizes it.

---

## What This Guide Covers

This guide covers:

- how to write clear intent
- how to write requirement families
- how to keep design downstream of requirements
- how to keep specification present-tense and current-surface
- how to avoid implementation bleed into constitutional documents

---

## Writing By Layer

### Intent

Intent states:

- why the system exists
- what directional change is being sought
- what is in scope or out of scope

Intent should not hardcode realization detail unless the detail is itself constitutional.

### Requirements

Requirements state what must be true.

They should:

- define stable obligations
- use explicit acceptance criteria
- avoid naming one implementation path unless that path is constitutional
- remain sufficient for downstream design derivation

### Design

Design states how requirement truth is realized.

Design may choose:

- interfaces
- structure
- packaging
- carrier surfaces
- tenant boundaries

If a statement is optional across lawful realizations, it probably belongs in design, not in requirements.

### ADRs

ADRs record ratified design decisions.

They should capture:

- context
- decision
- consequences

They are durable design memory, not a second requirement surface.

---

## Sufficiency Test

Before keeping a spec artifact, ask:

1. Can the next downstream layer derive from this?
2. Does this artifact state truth, or does it merely describe work in progress?
3. Does any sentence belong in a lower layer instead?

If the answer to any of these is wrong, rewrite or delete.

---

## Present-Tense Rule

Active specification should describe the current constitutional surface in present tense.

Do not preserve legacy wording inside live spec artifacts just for historical memory.

If something is no longer live:

- delete it
- supersede it
- or move it to commentary

Do not leave dead law in the active surface.

---

## Deletion Rule

When a fundamental migration is in progress, deletion is preferable to stale carry-forward.

Restore only what is intentionally re-adopted into the new model.

That keeps specification authoritative instead of archival.
