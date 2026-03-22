# ABG Integration Matrix: Process, Intent, Context, Destination

## Purpose

Before returning to `gsdlc`, `abg` should be proven in a clean sandbox as a kernel/app that can carry a range of explicit `A -> B` transformations without hidden self-hosting assumptions.

The goal is not to prove one toy edge. The goal is to prove that the kernel can faithfully transport:

- process
- intent
- context
- destination

through the full install -> bind -> evaluate -> dispatch -> converge path.

## Scope

This is a kernel validation exercise, not a `gsdlc` validation exercise.

The test fixture should use:

- fresh temp sandbox
- vanilla `abg.install`
- explicit synthetic project package written by the test
- no `.gsdlc`
- no `abiogenesis` repo-path assumptions
- no reliance on `CLAUDE.md` side effects

## Core Principle

Each integration test should model one materially different `A -> B` transformation and verify that the dispatched F_P manifest truthfully carries:

- source asset / target asset
- source markov / target markov
- evaluators / convergence criteria
- context references and resolved content
- intent surface appropriate to the hop
- destination / work surface / result path

This is the bar for deciding whether `abg` is a trustworthy kernel substrate.

## Recommended A -> B Matrix

### 1. `intent -> requirements`

Purpose:
- prove broad problem framing can become normative requirement structure

Should exercise:
- high-level intent
- policy / standards context
- structured textual output

Destination:
- requirements artifact

### 2. `design -> data_schema`

Purpose:
- prove architectural decisions can become a structured technical artifact

Should exercise:
- ADR context
- naming / integrity constraints
- target postconditions that are technical rather than narrative

Destination:
- schema artifact

### 3. `documents -> essential_details`

Purpose:
- prove extraction / condensation rather than synthesis-heavy generation

Should exercise:
- multi-document context loading
- traceable extraction
- preservation of salient facts

Destination:
- structured extracted-details artifact

### 4. `modules + design + schema -> code`

Purpose:
- prove multi-input synthesis into executable output

Should exercise:
- multiple upstream assets
- technical context resolution
- explicit write surface

Destination:
- source file output

### 5. `requirements -> uat_testcases`

Purpose:
- prove normative requirements can become acceptance artifacts

Should exercise:
- requirement lineage
- success criteria projection
- test-case structure

Destination:
- UAT testcase artifact

### 6. `ux_testcases -> playwright_tests`

Purpose:
- prove human-readable test procedures can become executable automation

Should exercise:
- stepwise interaction intent
- app-map / selector context
- code/test destination

Destination:
- executable e2e test file

## What Each Test Must Assert

For every hop:

1. Install truth
- `abg.install` creates only kernel/runtime territory
- no implicit project package is smuggled in

2. Binding truth
- the explicit synthetic package is what the runtime resolves

3. Gap truth
- `gaps` reports a believable delta
- missing required context causes truthful failure

4. Dispatch truth
- `start --auto` or equivalent produces F_P dispatch
- `fp_manifest_path` contains the structured contract, not just prompt prose

5. Intent truth
- the manifest exposes hop-appropriate intent, not just generic asset metadata

6. Context truth
- required context arrives fully enough to be authoritative
- no silent truncation of constitutionally required material

7. Destination truth
- the actor can see where the work belongs
- result path and write surface are explicit

8. Convergence truth
- after writing the expected result artifact, rerun converges

9. Reinstall safety
- reinstalling `abg` over the sandbox does not destroy domain-owned binding

## Minimum Useful Starting Set

If the matrix is introduced incrementally, start with:

1. `intent -> requirements`
2. `design -> data_schema`
3. `modules + design + schema -> code`
4. `requirements -> uat_testcases`

These four already cover:

- narrative -> normative
- design -> structured technical artifact
- multi-input synthesis
- normative -> acceptance artifacts

Then add:

5. `documents -> essential_details`
6. `ux_testcases -> playwright_tests`

## What This Replaces

This should replace the old idea that `abiogenesis` proves itself by implicit self-hosting.

The new proof should be:

- kernel installs cleanly
- explicit project package binds cleanly
- materially different `A -> B` hops converge honestly

That is a stronger and more truthful proof than repo-specific self-hosting assumptions.

## Definition of Done

`abg` is ready to hand back to `gsdlc` when:

- fresh sandbox install is minimal and honest
- explicit project package binding works
- the selected `A -> B` matrix passes end-to-end
- manifest truth is sufficient for F_P dispatch without transport side channels
- reinstall preserves domain binding and does not corrupt the sandbox

At that point, `gsdlc` can be treated as a domain consumer of a stable kernel again.
