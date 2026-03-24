# NOTE: Intent-to-Design Methodology — Resolve Requirement Conflicts Early

**Author**: codex  
**Date**: 2026-03-24T12:30:47+11:00  
**For**: all

One of the clearest lessons from the ABG / GSDLC transition is this:

conflicting ideas must be called out and resolved early, or execution turns
them into expensive incoherence.

## Core Rule

Maintain harmony across the chain:

- **Intent → Requirements**
- **Requirements → Design**
- **Design → Code**
- **Code → Tests**

Most execution problems are downstream effects of unresolved conflict higher in
that chain.

## Methodological Principle

Resolve requirement conflicts early.

Do not allow two incompatible constitutional ideas to remain live in the repo
at the same time without explicitly naming the conflict and choosing which one
governs.

If conflict is left unresolved, it becomes:

- contradictory requirements
- ADR drift
- partial implementations of incompatible models
- tests locking in the wrong semantics
- release decisions made on false coherence

## Practical Rule

When introducing a new requirement, ADR, or design direction:

1. identify which older requirements, ADRs, or docs it conflicts with
2. decide which idea is constitutional
3. explicitly supersede, narrow, or demote the conflicting idea
4. reprice requirements, design, code, and tests together

## Why This Matters

The cost of unresolved conceptual conflict rises sharply during execution.

At intent/design level, the cost is clarification.
At requirements level, the cost is repricing.
At code/test level, the cost becomes migration and rework.

So the right discipline is:

- preserve design vision
- detect conceptual conflict early
- resolve it at the highest level possible
- let lower layers flow from that decision

## Closing Rule

Harmony should be preserved first at:

- intent to requirements
- requirements to design

If those layers are coherent, most lower-layer work can flow cleanly from them.
If they are not coherent, the lower layers will amplify the conflict.
