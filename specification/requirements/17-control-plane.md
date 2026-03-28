# Control Plane Requirements

**Family**: REQ-F-CTRL-*
**Status**: Active
**Category**: Runtime Control

This family defines the assurance control plane that makes the installed workflow operationally configurable and inspectable without yet adding the second-order memory system.

### REQ-F-CTRL-001 — The runtime resolves through one deterministic control-plane compile

The assurance control plane must compile the active runtime from the installed release declaration, project-local edge tuning, and runtime/session policy into one inspectable artifact.

**Acceptance Criteria**:
- AC-1: The control plane produces one machine-readable resolved runtime artifact under `.ai-workspace/runtime/`
- AC-2: Runtime resolution is deterministic across the active layer set rather than ad hoc in each command or helper
- AC-3: The resolved runtime records provenance for each winning field, including source layer and source path
- AC-4: The resolved runtime is the common machine-readable answer for command carriers, doctor, and other runtime consumers

### REQ-F-CTRL-002 — Release declaration, project truth, and runtime state remain in separate territories

The control plane must preserve the narrow customization boundary by keeping install-managed release declaration, project-truth tuning, and mutable runtime state in distinct territories.

**Acceptance Criteria**:
- AC-1: `.gsdlc/release/active-workflow.json` remains an install-managed release declaration rather than a per-run override file
- AC-2: The active project-local edge-tuning seam for `0.9.9` remains `specification/design/fp/`
- AC-3: Backend selection, doctor state, resolved runtime, and session-local overrides live under `.ai-workspace/runtime/`
- AC-4: The control plane does not require a broader `specification/design/runtime/` scaffold to satisfy `0.9.9`

### REQ-F-CTRL-003 — Backend execution uses an explicit adapter contract

The graph owns that an edge requires `F_P`. The control plane owns how an allowed backend executes that `F_P` turn.

**Acceptance Criteria**:
- AC-1: The installed release ships backend schema and adapter surfaces under `.gsdlc/release/runtime/`
- AC-2: Concrete backend choice is resolved from runtime state under `.ai-workspace/runtime/` as a consequence of the winning worker assignment, not as a co-equal authority independent of worker binding or from project-truth specification surfaces
- AC-3: Each backend adapter defines `probe`, `invoke`, `normalize`, `failure_model`, and `capabilities`
- AC-4: The winning backend for a given run is visible in the resolved runtime artifact even if the installed release declaration also carries a shipped default hint
- AC-5: Qualification proves the product adapter layer itself rather than a parallel hardcoded transport branch
- AC-6: For `0.9.9`, a declared backend is assumed to be preinstalled and preauthenticated if selected for use; the control plane proves invocation, normalization, and readiness over that declared tool, but does not own backend installation or authentication bootstrap

### REQ-F-CTRL-004 — Edge runtime profiles are compiled from defaults, project tuning, and runtime policy

The control plane must move from prompt-only defaults to a compiled runtime profile for each live constructive edge.

**Acceptance Criteria**:
- AC-1: The shipped transform-contract surface may remain the declarative default for `0.9.9`
- AC-2: The control plane compiles an edge runtime profile from shipped defaults, project-local edge tuning, and runtime policy
- AC-3: The active `0.9.9` profile schema is limited to fields with real runtime consumers
- AC-4: Memory- or session-learning fields that lack a concrete `0.9.9` consumer remain deferred rather than being required in the active profile schema

### REQ-F-CTRL-005 — Doctor is the runtime-readiness counterpart to audit

Install audit and runtime doctor answer different questions and must remain separate surfaces.

**Acceptance Criteria**:
- AC-1: `audit` remains the release-integrity check over installed artifacts and declarations
- AC-2: `doctor` reports runtime readiness, including runtime resolution, backend availability, manifest/result-store health, and archive readiness
- AC-3: `doctor` returns structured findings that distinguish release drift from runtime unavailability or misconfiguration
- AC-4: `doctor` operates over the same resolved runtime and backend adapter layer used by the live command path
- AC-5: For `0.9.9`, doctor may assume backend installation and authentication are external prerequisites and report them only as readiness findings rather than trying to provision or repair them

### REQ-F-CTRL-006 — Command-carrier flow consumes the resolved runtime

The installed command carrier must stop behaving like an ad hoc wrapper set and instead act as one front door into the resolved control plane.

**Acceptance Criteria**:
- AC-1: The active command-carrier flow resolves backend and edge runtime behavior through the control-plane compile rather than bespoke prompt assembly paths
- AC-2: Runtime/session overrides can affect command execution without mutating install-managed release declarations
- AC-3: The same resolved runtime surface is consumable by both product commands and qualification harnesses

### REQ-F-CTRL-007 — The control plane constrains execution legality, not solution strategy

The assurance control plane governs which runtime may act, under what constraints, and how its output is normalized and diagnosed. It must not replace the framework's declarative gates with backend-specific solution procedure.

**Acceptance Criteria**:
- AC-1: Control-plane surfaces may constrain backend choice, sandbox mode, allowed write roots, timeout, failure handling, and result-schema expectations
- AC-2: Control-plane surfaces do not prescribe backend-specific solution tactics or implementation procedure for satisfying an `F_P` edge
- AC-3: Backend adapters choose transport mechanics and normalize results, but do not redefine graph law, evaluator semantics, gate semantics, or acceptance criteria
- AC-4: Backend preference or availability is runtime policy, not project truth
- AC-5: No runtime-control surface may override constitutional lifecycle law or evaluator outcomes declared by the active specification

### REQ-F-CTRL-008 — The control-plane path is the only lawful operative runtime path

Once the assurance control plane exists, it replaces co-equal legacy runtime branches. Transitional mixed state may exist during refactor, but it is not a lawful steady-state product model.

**Acceptance Criteria**:
- AC-1: Product commands and live qualification consume runtime behavior through the control-plane compile and backend adapter layer
- AC-2: Legacy direct prompt-assembly or transport-branch runtime paths are deleted once superseded
- AC-3: Any remaining prompt-render or inspection helper is derived from the resolved runtime as a read model, not a separate operative authority
- AC-4: Mixed old/new runtime models are permitted only as transient refactor state, not as a stable conforming release shape
- AC-5: `0.9.9` defines no legacy operative compatibility path; any future compatibility surface would require a separate explicit requirement
