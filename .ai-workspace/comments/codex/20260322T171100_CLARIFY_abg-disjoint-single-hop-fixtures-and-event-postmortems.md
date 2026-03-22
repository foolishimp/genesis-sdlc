# Clarification: Disjoint Single-Hop Fixtures, Not One Chained Graph

## Correction

The intended ABG integration proof is **not** one synthetic end-to-end graph.

It is a **disjoint matrix of independent single-hop fixtures**.

Each fixture should prove one explicit `A -> B` transformation in isolation.

Examples:

- `intent -> requirements`
- `design -> data_schema`
- `documents -> essential_details`
- `modules + design + schema -> code`
- `requirements -> uat_testcases`
- `ux_testcases -> playwright_tests`

## Why This Matters

One chained graph hides too much:

- upstream assets can mask missing local intent
- upstream context can mask missing required context for the hop under test
- failures become ambiguous
- event review becomes polluted by earlier steps

The purpose here is not to prove a synthetic mini-SDLC.

The purpose is to prove that the ABG kernel can faithfully carry **one transformation at a time** with the correct:

- process
- intent
- context
- destination

## Required Test Shape

For each fixture:

1. fresh sandbox
2. vanilla `abg.install`
3. explicit synthetic project package for that fixture only
4. exactly one meaningful `A -> B` hop under test
5. minimal local assets and context needed for that hop
6. run `gaps`
7. run dispatch / iterate path
8. inspect asset result
9. inspect event and review trail

## Two Equal Proofs Per Fixture

Each fixture must prove **both**:

### 1. Asset truth

Did the system create the correct output artifact for the hop?

### 2. Event / postmortem truth

Can the system explain what happened and why?

This means event review is not secondary. It is part of the test contract.

## Event / Postmortem Assertions

For every fixture, the audit surface should be sufficient to reconstruct:

- which edge ran
- which package/workflow identity was active
- which evaluators failed or passed
- what context was supplied
- what result path / manifest path was used
- why dispatch happened
- why convergence happened
- why failure happened if it did not converge

Minimum evidence should include:

- event stream entries
- F_D assessment evidence
- F_P manifest
- F_P result artifact
- approval/proxy record where relevant

## What This Replaces

This replaces the idea of:

- one broad synthetic graph proving everything at once

with:

- a matrix of isolated single-hop proofs with hop-local auditability

That is a much better kernel test because it makes missing intent, missing context, and missing destination semantics visible immediately.

## Recommended Interpretation

Call this a:

**disjoint transformation matrix**

not an integration graph.

The integration is in the install/bind/dispatch/audit pipeline, not in chaining many edges together.

## Done Means

ABG is ready for `gsdlc` again when these disjoint fixtures show that the kernel can, for each hop:

- bind the correct process
- carry the required intent
- resolve the required context
- expose the correct destination
- create the expected asset
- emit an audit trail strong enough for postmortem review
