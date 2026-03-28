# ADR-002 — Assurance Control Plane

**Status**: Approved
**Date**: 2026-03-28
**Implements**: `REQ-F-CMD-*`, `REQ-F-CTRL-*`, `REQ-F-TEST-*`, `REQ-F-MVP-*`, `REQ-F-ASSURE-*`
**Derives from**: `INT-008`; [20260328T162800_PROPOSAL_assurance-control-plane-0_9_9.md](/Users/jim/src/apps/genesis_sdlc/.ai-workspace/comments/codex/20260328T162800_PROPOSAL_assurance-control-plane-0_9_9.md)
**Supersedes**: prior scattered operative runtime ownership across prompt-render and live-transport seams
**Degenerate case**: while the wave is in flight, `src/genesis_sdlc/release/fp_prompt.py` and `tests/e2e/live_transport.py` may remain as read-model or qualification shims, but not as operative authorities

---

## Context

`abiogenesis/python` proved the base workflow and bundled assurance lanes before it had one explicit
runtime/control model. Runtime defaults, project-local F_P tuning, live transport selection, doctor-like
checks, and prompt rendering existed as scattered surfaces.

That produced two design risks:

- the runtime model was harder to explain than the lifecycle model
- legacy prompt or transport branches could survive as co-equal operative paths during refactor

The new `0.9.9` requirements make the intended boundary explicit:

- `.gsdlc/release/active-workflow.json` is install-managed release declaration
- `specification/design/fp/` remains the project-truth edge-tuning seam
- `.ai-workspace/runtime/` owns mutable runtime state
- the control-plane path is the only lawful operative runtime path

## Decision

`abiogenesis/python` introduces an explicit `assurance_control_plane` module between release bootstrap
and assurance/evidence surfaces.

This module owns:

- resolved runtime compilation
- backend schema and adapter boundaries
- backend probing and selection
- shared backend invocation for bounded `F_P` turns
- doctor/readiness reporting
- command/runtime read models derived from the resolved runtime

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
  - landing: shared `invoke_backend(...)` seam in the assurance control plane
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
3. project-truth edge tuning in `specification/design/fp/`
4. mutable runtime/session state in `.ai-workspace/runtime/`

These compile into one resolved runtime artifact consumed by product commands and qualification.

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
- product commands and live qualification both invoke bounded `F_P` work through the shared `invoke_backend(...)` seam
- rendered prompt output is derived from the resolved runtime as a read model rather than used as a separate operative runtime path

At that point:

- `src/genesis_sdlc/release/fp_prompt.py` ceases to be part of the operative path
- `tests/e2e/live_transport.py` ceases to be part of the operative path
- any direct operative dependency on `workflow/transforms.py` for prompt execution is removed from the landed runtime path

## Consequences

- the runtime model becomes an explicit design surface rather than an emergent side effect
- product commands and qualification collapse toward the same runtime path
- backend choice becomes runtime policy rather than project truth
- prompt rendering remains available as an operator/readability surface without becoming a second runtime
- the control plane can evolve independently of the later second-order memory system
