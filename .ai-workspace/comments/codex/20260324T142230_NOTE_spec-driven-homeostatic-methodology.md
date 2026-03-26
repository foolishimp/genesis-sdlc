# Spec-Driven Homeostatic Methodology

## Core Thesis

The system is governed by a constitutional chain:

```text
Intent -> Requirements -> ADRs -> Code -> Events -> Projection -> Delta -> Repricing
```

This is not just documentation traceability. It is the homeostatic loop of the system.

- **Intent** defines purpose and direction.
- **Requirements** define invariant truths the system must satisfy.
- **ADRs** define the structural decisions that make those truths achievable.
- **Code** realizes those decisions.
- **Events** record what actually happened.
- **Projection** reconstructs current truth from the event stream.
- **Delta** reveals drift between intended truth and realized state.
- **Repricing** updates requirements, ADRs, or code when the system no longer harmonizes.

## Constitutional Rule

Every live requirement family must have ADR ownership.

Every ADR must ground itself in requirements.

Unowned requirements and ungrounded ADRs create design drift. When that happens, code becomes accidental law.

## Method

When a feature is introduced or changed:

1. Update **Intent** if the purpose or scope has changed.
2. Update **Requirements** so the invariant truths are explicit.
3. Update or write **ADRs** so the governing design choice is explicit.
4. Only then implement **Code**.
5. Use **Events, Projection, and Delta** to verify whether reality still satisfies the requirements.

## Anti-Drift Rules

- If a requirement is active law, it must map to one or more owning ADRs.
- If an ADR has no requirement grounding, it is design without constitutional authority.
- If code behavior has no ADR owner, the design has already drifted.
- If tests validate implementation habit rather than requirement truth, they lock in drift.
- If events and projection reveal persistent delta, either code is wrong or the requirement/ADR stack is stale.

## Classification Rule

Every inherited or legacy requirement must be classified as one of:

- **Replaced by V2**: ownership moves to an existing V2 ADR.
- **Still needed**: it remains live and must have an owning ADR.
- **Orphaned**: it is no longer part of the intended system and should be removed or explicitly superseded.

Nothing live should remain unclassified.

## Stone Version

Intent defines purpose. Requirements define invariant truths. ADRs define the structural decisions that make those truths achievable. Code realizes those decisions. Events, projection, and delta reveal drift. Every live requirement family must have ADR ownership; every ADR must ground itself in requirements.

## Promotion Target

This note should eventually be promoted into the constitutional layer of the repo, either:

- `specification/INTENT.md` as a methodology section, or
- `specification/SPEC_METHODOLOGY.md` as a dedicated constitutional note.
