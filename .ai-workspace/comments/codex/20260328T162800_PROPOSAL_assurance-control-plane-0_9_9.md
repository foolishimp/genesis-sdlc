# PROPOSAL: Assurance Control Plane For 0.9.9

**Author**: codex
**Date**: 2026-03-28T16:28:00+1100
**Addresses**: the missing control-plane and runtime configuration layer needed to move `genesis_sdlc` from `0.9` to a shippable `0.9.9`
**Status**: Draft

## Summary

`genesis_sdlc` is now strong enough to be called `0.9`.

It has:

- a real lifecycle graph
- real install and release surfaces
- real fake and live qualification lanes
- product-vs-source separation
- a first project-local F_P customization seam

What it still lacks is not lifecycle law.

What it lacks is the complete runtime framework around that law:

- one named control-plane concept
- one configuration hierarchy
- one backend registry
- one edge runtime profile model
- one operator diagnosis surface

That is the `0.9 -> 0.9.9` problem.

This proposal says:

`0.9.9` should be the release where `genesis_sdlc` becomes operationally configurable and accessibly shippable, without yet adding the full second-order memory system.

## Versioning Assumption

This proposal takes an explicit position on the current mismatch between runtime labeling and product maturity:

- the current `1.0.0rc1` label is treated here as premature
- the branch is better understood as a late `0.9.x` line
- `0.9.9` is the milestone where the assurance control plane becomes complete enough for a shippable pre-1.0 product

If that repricing is rejected, the technical content of this proposal still stands, but the numbering should be shifted forward into the post-RC line.

## Product Boundary

This proposal is explicitly **not** the memory proposal.

It only covers the first-order runtime and operator layer that makes the existing lifecycle system usable as a product.

So the split is:

- `0.9.9` = assurance control plane complete
- `1.0` = second-order memory system built on top of that plane

## Problem Statement

The repo now has many pieces that behave like a control plane:

- `.gsdlc/release/active-workflow.json`
- install and audit
- command carriers
- backend transport selection
- F_P manifests and results
- run archives
- project-local F_P overrides
- release helpers

But these are still too scattered to feel like one product surface.

The result is:

- users can do meaningful work
- but they cannot yet understand the runtime holistically
- and the system cannot yet explain its own control model clearly enough to be broadly reusable

One important clarification:

- the F_P override resolution code already exists
- the installed project scaffold now includes `specification/design/fp/`
- but the `genesis_sdlc` source repo does not have a repo-root `specification/design/fp/` authoring surface

So the current seam is real as an installed project surface and runtime code path, not yet as a source-tree constitutional surface inside `genesis_sdlc` itself.

## Core Definition

Define a first-class product concept:

`assurance control plane`

This is the runtime/operator layer through which the lifecycle graph is executed, configured, dispatched, inspected, and diagnosed.

It is not the constitutional graph itself.

## Scope Of The Assurance Control Plane

The control plane should own:

- active workflow declaration
- backend registry
- edge runtime profiles
- project-local runtime customization
- F_P manifest and result stores
- command-carrier behavior
- install and audit
- doctor and health reporting
- session state
- run archive policy

It should not yet own:

- second-order memory learning logic
- promotion logic into design or specification
- affect/resource grading as a full product subsystem

Those belong to the later memory feature.

## Proposed Configuration Hierarchy

The control plane should make configuration explicit and layered.

### Layer 1: Constitutional Law

Lives in:

- `specification/INTENT.md`
- `specification/requirements/`

This layer answers what must be true.

### Layer 2: Installed Release Defaults

Lives in:

- `.gsdlc/release/`

This layer answers the shipped defaults:

- operating standards
- release helpers
- default edge runtime profiles
- default backend registry
- immutable templates
- install-managed workflow declaration in `active-workflow.json`

### Layer 3: Project-Local Runtime Customization

Lives in:

- `specification/design/fp/`

For `0.9.9`, this layer remains the current project-truth edge-tuning seam rather than a broader runtime folder.

It answers how this project wants specific constructive edges to behave where that tuning is derived from project intent, requirements, and design.

This needs one explicit territory clarification:

- in the source product repo, `specification/standards/` is the method authority surface
- in the installed target project, `specification/` is the project-owned intent/requirements/design surface
- the installed method standards remain under `.gsdlc/release/operating-standards/`

There is still an important split inside runtime configuration itself:

- project-truth tuning that is derived from project intent, requirements, and design belongs under `specification/`
- operator/environment/session policy does not

So the refined boundary should be:

- `specification/design/fp/`
  - project-local edge shaping tied to project truth
- `.ai-workspace/runtime/`
  - backend selections
  - doctor snapshots
  - resolved runtime state
  - environment and session overrides

This preserves the narrow-customization principle while keeping mutable operational policy out of constitutional or near-constitutional project surfaces.

## Deterministic Merge Model

The four-layer hierarchy is only useful if it resolves deterministically.

`0.9.9` should define one compile step:

`runtime layers -> resolved runtime artifact`

That compile step should produce:

```text
.ai-workspace/runtime/resolved-runtime.json
```

This becomes the single machine-readable answer consumed by:

- `doctor`
- command carriers
- `genesis gaps`
- `genesis iterate`
- future operator surfaces

The merge rules should be explicit:

1. installed release defaults provide the base runtime model
2. project-local edge tuning may override only approved edge-shaping fields
3. operator/environment config may override backend and execution-policy fields
4. session overrides may narrow runtime behavior further, but never widen forbidden fields

Every resolved field should carry provenance:

- winning value
- source layer
- source path
- overridden candidates if present

That is what allows the control plane to explain why a backend/profile/setting won.

### Layer 4: Runtime / Session Override

Lives in:

- `.ai-workspace/runtime/`

This layer answers environment-local, operator-local, and session-local runtime selection for the current run.

It does not mutate `.gsdlc/release/active-workflow.json`.
That file remains an install-managed release declaration, not a per-run override surface.

## Replace Transform Contracts With Edge Runtime Profiles

The current `EdgeTransformContract` is the right starting point but too narrow.

`0.9.9` should introduce a richer `EdgeRuntimeProfile` as the compiled runtime form.

For `0.9.9`, the active schema should stay constrained to fields that have real consumers:

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

This allows the system to talk about runtime behavior instead of only prompt text.

Fields such as:

- `resume_policy`
- `doctor_checks`
- `memory_scope`
- `compaction_policy`

should be treated as reserved extensions for the later memory/session line unless they gain a concrete `0.9.9` consumer.

This also resolves the migration question:

- `EdgeTransformContract` remains the shipped default declarative surface
- project-local edge overrides remain the current project-facing tuning surface
- `EdgeRuntimeProfile` is the compiled result after defaults, project tuning, and runtime policy are merged

So `0.9.9` does not need a hard replacement on day one.
It needs a compile path.

## Backend Registry

`0.9.9` should introduce one explicit backend model.

The release should ship backend schema and adapter surfaces, not project-endorsed concrete backend selections.

So the shape should be closer to:

```text
.gsdlc/release/runtime/
  backend-schema.json
  adapters/
```

Concrete project choices live under:

```text
.ai-workspace/runtime/
```

Initial supported ids:

- `codex`
- `claude_code`
- `pi`

The graph still owns F_P as a regime.
The control plane owns how an allowed backend executes a given F_P turn.

This avoids implying that the methodology itself endorses one concrete environment configuration simply because it ships an adapter for it.

## Backend Adapter Contract

The backend model must be grounded in one adapter contract, not just backend ids.

Each backend adapter should define at least:

- `probe()`
  - determine whether the backend is currently usable
  - return availability plus reason if unavailable
- `invoke()`
  - execute one bounded F_P turn with prompt, workspace, timeout, and runtime constraints
- `normalize()`
  - normalize backend output into the result artifact contract expected by the product runtime
- `failure_model`
  - classify timeout, config error, backend unavailable, malformed output, and retryable transport failure
- `capabilities`
  - whether the backend supports resume, sandboxing, bounded write roots, or session continuity

Qualification then proves adapter compliance by exercising the product adapter layer itself, not a parallel hardcoded transport branch.

## Doctor

`audit` should remain the release-integrity check.

`doctor` should become the runtime-readiness check.

Doctor should prove:

- installed release integrity
- command carrier integrity
- runtime contract resolution
- backend availability
- project-local runtime configuration validity
- manifest/result store health
- archive surface readiness

This is the most direct `openclaw` import and one of the clearest product wins.

## Test Harness Relationship

The current live harness is still test infrastructure.

The intended end state for `0.9.9` is:

- product runtime owns the backend model and prompt/profile resolution
- the qualification harness consumes that same product runtime surface
- test-only transport glue becomes a thin wrapper over the product adapter layer, not a divergent execution path

So the backend model is not meant to stay test-only. The harness should collapse toward the product runtime, not the other way around.

## Phased Migration

The migration should be explicit rather than assumed.

### Phase A

Name and ratify the assurance control plane in tenant design.

### Phase B

Keep the current `specification/design/fp/` seam as the active seed.

Do not break it.
Instead:

- continue scaffolding it in installed projects
- make its override fields explicit
- treat it as the current project-truth edge-tuning surface

### Phase C

Introduce `.ai-workspace/runtime/` and the resolved runtime compiler.

First outputs:

- `resolved-runtime.json`
- backend availability snapshot
- doctor findings snapshot

### Phase D

Introduce the backend adapter contract and product adapter layer.

At this point, the qualification harness should begin consuming product adapters rather than custom test transport logic.

### Phase E

Introduce `EdgeRuntimeProfile` as the compiled runtime form.

This can initially coexist with `EdgeTransformContract` plus overrides, then become the dominant runtime object once the compile path is stable.

### Phase F

Promote the current `specification/design/fp/` seed into the broader long-term project shape if still warranted.

That promotion may land as:

- `specification/design/runtime/edge_profiles/`

but should happen only after the compile path and territory rules are proven.

## 0.9.9 Deliverables

A `0.9.9` milestone should include:

1. explicit tenant design note for the assurance control plane
2. preserved and formalized `specification/design/fp/` seam as the active project-truth edge-tuning surface
3. `EdgeRuntimeProfile` model
4. backend registry with at least `codex`, `claude_code`, `pi`
5. `doctor` surface
6. command-carrier flow that uses the resolved runtime profile rather than ad hoc prompt assembly

Memory remains explicitly deferred to `1.0`, with the planned landing zone under `.ai-workspace/memory/` as described in the separate second-order proposal.

## What 0.9.9 Does Not Need

`0.9.9` does not need:

- second-order gap episodes
- disambiguation memory promotion
- affect-graded resource allocation
- cross-episode learning logic

Those are valuable, but they are `1.0` territory.

## Recommendation

Freeze the current line as `0.9`.

Then make the next milestone:

`0.9.9 = assurance control plane complete`

That gives the product a shippable runtime framework while leaving the more ambitious learning layer for `1.0`.
