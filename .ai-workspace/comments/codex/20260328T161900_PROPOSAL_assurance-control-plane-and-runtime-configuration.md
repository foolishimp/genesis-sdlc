# PROPOSAL: Assurance Control Plane And Runtime Configuration

**Author**: codex
**Date**: 2026-03-28T16:19:00+1100
**Addresses**: turning the current `0.9` `genesis_sdlc` milestone into a shippable configurable assurance product
**Status**: Superseded by split proposals

## Disposition

This combined proposal was useful to expose the missing layer, but it mixes two separate product features:

1. assurance control plane and runtime configuration
2. second-order SDLC memory

The active follow-up notes are:

- `20260328T162800_PROPOSAL_assurance-control-plane-0_9_9.md`
- `20260328T162800_PROPOSAL_second-order-memory-sdlc-1_0.md`

Read those instead of using this file as the forward plan.

## Summary

`genesis_sdlc` is now past the proof-of-concept line.

It has:

- a real lifecycle graph
- working fake and live qualification lanes
- product-vs-source install separation
- immutable installed release surfaces
- a first project-local F_P customization surface

That is enough to call the current state `0.9`.

It is not yet enough to call the product fully shippable.

The remaining gap is no longer graph law or basic runtime viability.
The remaining gap is configuration architecture.

The system has the parts:

- active workflow declaration
- install/audit
- commands
- F_P manifests
- project-local F_P overrides
- transport selection
- run archives
- memory proposals

But it does not yet have one explicit framework that explains how those parts fit together as a coherent assurance control plane.

This proposal defines that next layer.

The governing idea is:

`genesis_sdlc` remains a lifecycle assurance product.

It gains a runtime control plane that makes it easier to configure, dispatch, inspect, diagnose, and improve convergence without weakening lifecycle law.

## Why Now

The current branch has exposed the product boundary clearly.

The install shape is now separated:

- source product remains in repo authoring territory
- installed release lives under `.gsdlc/release/`
- editable project truth lives under `specification/`

The latest improvement also exposed the next real missing surface:

- users need to tune F_P behavior for their project
- that tuning must survive reinstall
- that tuning must not require editing managed release code
- that tuning must map from project intent and requirements into bounded runtime behavior

The first local answer exists:

- `specification/design/fp/INTENT.md`
- `specification/design/fp/edge-overrides/`

But that is still only one solved slice of a bigger problem.

The bigger problem is:

how does a project configure the runtime behavior of the assurance system as a whole?

That is where the `openclaw` lesson becomes useful.

`openclaw` is not the lifecycle truth.

It is evidence that a hard system benefits from:

- explicit control-plane concepts
- backend registries
- runtime profiles
- operator diagnosis
- memory as a replaceable runtime surface

`genesis_sdlc` should import those runtime patterns while keeping lifecycle law constitutional and separate.

## Product Thesis

The next-level product shape should be:

- constitutional lifecycle law in `specification/`
- installed immutable methodology in `.gsdlc/release/`
- project-local customization in `specification/design/runtime/`
- explicit assurance control-plane state in `.ai-workspace/`

So the product is not just:

- graph + commands + bootloader

It is:

- graph law
- release package
- assurance control plane
- project-local runtime configuration
- operator-facing diagnosis and backend selection

That is the missing layer between a successful demo and a reusable product.

## Core Proposal

### 1. Name The Missing Layer Explicitly

Introduce an explicit product concept:

`assurance control plane`

This is not the lifecycle graph itself.
It is the runtime and operator layer through which the graph is executed and observed.

Its first-class surfaces are:

- active workflow declaration
- backend registry
- edge runtime profiles
- project-local runtime customization
- F_P manifest store
- F_P result store
- event log
- run archives
- doctor / health / audit
- memory surfaces
- session / compaction surfaces

This concept should be named in tenant design first, then promoted into requirements if it proves stable.

### 2. Introduce A Real Runtime Configuration Hierarchy

Right now configuration is present but scattered.

The system should instead declare an ordered configuration stack:

1. constitutional law
2. installed release defaults
3. project-local runtime customization
4. runtime/session override

That resolves to:

#### Layer 1: Constitutional Law

Lives in:

- `specification/INTENT.md`
- `specification/requirements/`

This layer answers:

- what lifecycle must exist
- what commands must exist
- what custody must hold
- what assurance must prove

This layer does not choose provider backends or prompt flavor.

#### Layer 2: Installed Release Defaults

Lives in:

- `.gsdlc/release/`

This layer answers:

- default edge transform contracts
- installed operating standards
- default backend availability expectations
- immutable templates
- release-owned helper surfaces

This is system-owned and replaced on reinstall.

#### Layer 3: Project-Local Runtime Customization

Lives in:

- `specification/design/runtime/`

This layer answers:

- what this project wants to optimize
- which F_P edges need tuning
- which backends are preferred or forbidden
- what memory scope is wanted
- what doctor/health expectations are project-specific

This is the real user customization surface.

#### Layer 4: Runtime / Session Override

Lives in:

- `.gsdlc/release/active-workflow.json`
- possibly later `.ai-workspace/session/`

This layer answers:

- active backend selection for this run
- temporary debug or qualification settings
- session-local overrides that do not rewrite project truth

This layer is runtime-oriented, not constitutional.

### 3. Generalize The Current F_P Override Surface Into A Runtime Design Surface

The current `specification/design/fp/` solution is directionally correct but too narrow.

The next-level shape should be:

```text
specification/
  design/
    runtime/
      INTENT.md
      README.md
      backends/
        README.md
        codex.json
        claude_code.json
      edge_profiles/
        README.md
        requirements__to__feature_decomp.json
        feature_decomp__to__design.json
      memory/
        README.md
      doctor/
        README.md
```

This does two things:

- preserves the insight that customization starts from intent
- lifts the surface from “prompt patching” to “runtime configuration”

`fp/` can be treated as the seed that gets absorbed into this broader shape.

### 4. Replace EdgeTransformContract With EdgeRuntimeProfile

The current `EdgeTransformContract` is the right seed, but it is too prompt-centric.

The next object should be something like:

`EdgeRuntimeProfile`

Minimum fields:

- `edge`
- `target_asset`
- `artifact_kind`
- `authority_contexts`
- `suggested_output`
- `required_sections`
- `guidance`
- `preferred_backend`
- `allowed_backends`
- `sandbox_mode`
- `allowed_write_roots`
- `result_schema`
- `memory_scope`
- `compaction_policy`
- `resume_policy`
- `doctor_checks`

This keeps the good parts of the current transform contract, while making room for:

- backend choice
- operator guardrails
- repeatability
- diagnosis
- memory

That is much closer to the `openclaw` skill/runtime profile idea, but scoped to assurance.

### 5. Add A Tenant-Local F_P Backend Registry

The current state has:

- one active transport agent field
- live test transport bridge
- hardcoded backend logic in qualification code

That is enough for proof.
It is not enough for a product.

The product needs one runtime registry:

```text
.gsdlc/release/runtime/
  backends/
    codex.json
    claude_code.json
    pi.json
```

And one project-local override surface:

```text
specification/design/runtime/backends/
  codex.json
  claude_code.json
```

Registry responsibilities:

- backend id
- execution adapter
- availability probes
- required environment
- timeout defaults
- session/resume legality
- output expectations

Project-local overrides can then say:

- prefer `codex` for code-heavy edges
- prefer `claude_code` for design-heavy edges
- forbid some backends for release-critical edges

This turns worker selection into runtime configuration rather than scattered test logic.

### 6. Introduce Doctor As A First-Class Product Surface

The current audit is useful but too thin.

The next product needs:

- install integrity checks
- backend availability checks
- command carrier checks
- runtime contract resolution checks
- customization-surface validity checks
- event/memory/archive health checks

This should likely become:

- `install --audit` for release drift
- `doctor` for runtime readiness

The distinction matters:

- `audit` proves the installed product matches its declared release
- `doctor` proves the environment is ready to operate

That is an `openclaw` import worth taking.

### 7. Treat Memory As A Runtime Surface, Not A Mystery

The second-order memory proposal is still the stronger long-term direction.

This proposal does not replace it.
It gives it a product home.

Memory should sit under the assurance control plane as an explicit replaceable surface:

```text
.ai-workspace/
  memory/
    episodes/
    disambiguation/
    edge_profiles/
    promotion/
```

Project-local runtime design can then choose:

- memory retention policy
- promotion thresholds
- compaction policy
- whether memory is local-only or shared

That preserves the current deeper research direction without forcing it prematurely into constitutional law.

## Proposed Project-Local Flow

A future user story should look like this:

1. install `genesis_sdlc` into a new project
2. fill in `specification/INTENT.md`
3. write project requirement families in `specification/requirements/`
4. define runtime intent in `specification/design/runtime/INTENT.md`
5. tune edge profiles in `specification/design/runtime/edge_profiles/`
6. configure preferred backends in `specification/design/runtime/backends/`
7. run `doctor`
8. run `gen-gaps`, `gen-iterate`, `gen-review`
9. inspect archives and memory surfaces
10. tighten or relax runtime profiles as the project learns

That is the product loop we are currently missing.

## Immediate Migration Path

This should not be introduced as a big-bang rewrite.

### Phase A

Ratify the concept of `assurance control plane` in tenant design.

Outcome:

- explicit runtime layer name
- explicit boundary from lifecycle graph

### Phase B

Promote `specification/design/fp/` into `specification/design/runtime/`.

Outcome:

- preserve existing work
- widen it into a proper configuration framework

### Phase C

Replace `EdgeTransformContract` with `EdgeRuntimeProfile`.

Outcome:

- prompt tuning becomes one slice of a larger runtime profile

### Phase D

Implement backend registry and execution adapter.

Outcome:

- test/live transport becomes product runtime, not harness glue

### Phase E

Add `doctor` and richer runtime diagnosis.

Outcome:

- operator can answer “is the system ready?” before trying to iterate

### Phase F

Attach memory and compaction policy surfaces.

Outcome:

- disambiguation learning moves into an explicit product subsystem

## What This Proposal Rejects

This proposal is intentionally narrow.

It does not propose:

- making `genesis_sdlc` a general assistant shell
- loosening lifecycle law for convenience
- embedding provider-specific logic into requirements
- turning the runtime control plane into constitutional ontology
- replacing assurance with agent preference

The graph remains the workflow truth.

The control plane exists to make the truth usable, inspectable, and improvable.

## Recommendation

Call the current pushed branch `0.9`.

Then take one step back and make the next milestone:

`runtime configuration and assurance control plane`

That should be the framing for the next design cycle.

The current product now has enough working pieces that this step can be architectural instead of speculative.
