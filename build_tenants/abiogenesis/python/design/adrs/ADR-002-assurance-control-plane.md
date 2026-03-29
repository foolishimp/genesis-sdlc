# ADR-002 — Assurance Control Plane

**Status**: Approved
**Date**: 2026-03-28
**Implements**: `REQ-F-CMD-*`, `REQ-F-CTRL-*`, `REQ-F-TEST-*`, `REQ-F-MVP-*`, `REQ-F-ASSURE-*`, `REQ-F-WORKER-*`
**Derives from**: `INT-008`, `INT-009`; [20260328T162800_PROPOSAL_assurance-control-plane-0_9_9.md](/Users/jim/src/apps/genesis_sdlc/.ai-workspace/comments/codex/20260328T162800_PROPOSAL_assurance-control-plane-0_9_9.md)
**Supersedes**: prior scattered operative runtime ownership across prompt-render and live-transport seams
**Degenerate case**: while the wave is in flight, `src/genesis_sdlc/release/fp_prompt.py` and `tests/e2e/live_transport.py` may remain as read-model or qualification shims, but not as operative authorities

---

## Context

`abiogenesis/python` proved the base workflow and bundled assurance lanes before it had one explicit
runtime/control model. Runtime defaults, project-local F_P tuning, live transport selection, doctor-like
checks, and prompt rendering existed as scattered surfaces.

That produced three design risks:

- the runtime model was harder to explain than the lifecycle model
- legacy prompt or transport branches could survive as co-equal operative paths during refactor
- worker identity, backend identity, and engine identity could collapse into one ambiguous runtime story

The new `0.9.9` requirements make the intended boundary explicit:

- `.gsdlc/release/active-workflow.json` is install-managed release declaration
- `build_tenants/<techlabel>/design/fp/` remains the tenant-local edge-tuning seam
- `.ai-workspace/runtime/` owns mutable runtime state
- the control-plane path is the only lawful operative runtime path

## Decision

`abiogenesis/python` introduces an explicit `assurance_control_plane` module between release bootstrap
and assurance/evidence surfaces.

This module owns:

- resolved runtime compilation
- worker-registry loading and role-to-worker assignment resolution
- backend schema and adapter boundaries
- the adapter contract shipped in the install-managed runtime carrier under `.gsdlc/release/runtime/`
- public worker/role dispatch for bounded `F_P` turns
- backend probing and selection
- backend invocation as an internal adapter helper beneath resolved worker assignment
- doctor/readiness reporting
- command/runtime read models derived from the resolved runtime

`release_bootstrap` publishes the `.gsdlc/release/runtime/` carrier because it is an install-managed
release surface. `assurance_control_plane` owns the contract content placed there and the live runtime
consumers that resolve and invoke against it.

In this model:

- `workflow_core` declares generic workflow roles and role-bearing jobs as constitutional execution law
- `release_bootstrap` ships the worker registry and default role-assignment defaults under `.gsdlc/release/runtime/`
- `assurance_control_plane` resolves `role -> worker -> backend` from that shipped runtime carrier plus runtime overrides
- backend identity is downstream of the winning worker assignment, not a co-equal selector

It does not own:

- graph law
- evaluator semantics
- gate semantics
- acceptance criteria
- solution procedure for `F_P` edges

Those remain governed by the constitutional specification and the workflow declaration.

## Transitional Live-File Classification

This refactor wave already has live files that carry parts of the prior runtime path. They are classified
explicitly so the wave does not leave ambiguous operative ownership behind.

The `classification` field below uses the canonical method vocabulary from `SPEC_METHOD.md`.
Any extra note about wave behavior is supplemental, not a second classification system.

- `src/genesis_sdlc/release/fp_prompt.py`
  - classification: `Superseded`
  - wave state: retained only as a read-model shim
  - landing: `src/genesis_sdlc/runtime/prompt_view.py`
- `tests/e2e/live_transport.py`
  - classification: `Superseded`
  - wave state: retained only as a qualification shim
  - landing: shared worker/role dispatch seam in the assurance control plane
- `tests/e2e/sandbox_runtime.py`
  - classification: `Active`
  - owning module: `evidence_acceptance`
  - role: real sandbox install/execution harness for qualification
- `src/genesis_sdlc/workflow/transforms.py`
  - classification: `Active`
  - wave state: transitional declarative transform-contract seed
  - owning module: `workflow_core`
  - role: current declarative transform-contract seed
  - landing: runtime prompt-view and runtime-resolution concerns move into the assurance control plane while declarative defaults remain with workflow declaration

This keeps the live wave state honest: transitional files may exist while the wave is in flight, but they
must be named, classified, and given a replacement path.

## Runtime Boundary

The variant uses four runtime layers:

1. constitutional law in `specification/INTENT.md` and `specification/requirements/`
2. install-managed release defaults in `.gsdlc/release/`
3. tenant-local edge tuning in `build_tenants/<techlabel>/design/fp/`
4. mutable runtime/session state in `.ai-workspace/runtime/`

These compile into one resolved runtime artifact consumed by product commands and qualification.

## Worker Assignment Boundary

The runtime worker model stays subordinate to constitutional graph law.

- the graph declares generic roles such as constructive `F_P` execution
- shipped runtime defaults declare which workers can satisfy which roles
- mutable runtime state may override worker assignment within that declared coverage
- the resolved runtime records the winning `role -> worker -> backend` mapping together with provenance for the layer that supplied it

This keeps vendor choice in runtime configuration while preserving role identity as workflow law.

## Backend Adapter Contract

Each backend adapter is designed as one explicit control-plane contract, not as backend-specific ad hoc
branching.

For `0.9.9`, the contract has five required facets:

- `probe`
- `invoke`
- `normalize`
- `failure_model`
- `capabilities`

The shipped release carrier under `.gsdlc/release/runtime/` publishes the schema and defaults for these
adapter surfaces. The assurance control plane loads that carrier, compiles it with runtime state, and
uses the resulting adapter contract as the only lawful backend-execution path.

The same runtime carrier also publishes the worker registry and default role assignments that bind those
backend adapters to declared workers. The assurance control plane resolves worker choice first and then
derives backend choice from that winning assignment.

For `0.9.9`, worker/backend declarations assume the selected vendor CLI is already installed and authenticated.
The control plane owns invocation, normalization, readiness reporting, and provenance over that declared tool.
It does not own vendor install or login bootstrap.

The public operative seam is therefore worker- and role-based, not backend-named. Backend invocation remains
an internal adapter concern once the control plane has resolved the winning worker assignment.

## Exclusivity Rule

Any rendered prompt helper is a read model derived from the resolved runtime.

It is not a separate operative authority.

Legacy prompt-assembly or transport-branch runtime paths do not remain as co-equal design options in
the steady-state product. Transitional mixed state may exist while a refactor wave is in flight, but
the landed design carries one operative runtime path only.

## Landing Criteria

The control-plane wave lands when all of the following are true:

- the assurance control plane can compile one resolved runtime artifact from release defaults, project-local tuning, and runtime state
- the assurance control plane can probe at least one backend through the shared adapter contract
- product commands and live qualification both invoke bounded `F_P` work through the shared worker/role dispatch seam, with backend invocation hidden beneath it
- rendered prompt output is derived from the resolved runtime as a read model rather than used as a separate operative runtime path

At that point:

- `src/genesis_sdlc/release/fp_prompt.py` ceases to be part of the operative path
- `tests/e2e/live_transport.py` ceases to be part of the operative path
- any direct operative dependency on `workflow/transforms.py` for prompt execution is removed from the landed runtime path

## Consequences

- the runtime model becomes an explicit design surface rather than an emergent side effect
- multi-worker routing becomes explicit runtime policy rather than a hidden singleton
- product commands and qualification collapse toward the same runtime path
- backend choice becomes runtime policy rather than project truth
- backend provisioning and authentication remain external prerequisites for this release line
- engine build identity, worker identity, and backend identity remain separable provenance surfaces
- prompt rendering remains available as an operator/readability surface without becoming a second runtime
- the control plane can evolve independently of the later second-order memory system
