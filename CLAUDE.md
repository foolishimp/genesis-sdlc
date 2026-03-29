<!-- GTL_BOOTLOADER_START -->
# GTL Bootloader: Axiomatic Constraint Surface

**Version**: 2.2.0
**Status**: Present-tense constitutional read model
**Role**: Constraint manifold for LLM-guided construction over the GTL 2.x / ABG 2.x surface

This document is not a tutorial.
It is a compact statement of the live structural truths that bound lawful work.

If code, prompts, comments, or stale compatibility surfaces disagree with this document, the live constitutional source wins:
- intent
- requirements
- design
- then code

No earlier vocabulary is normative here unless explicitly retained by the live surface.

---

## 1. Core Position

GTL is the language surface.
ABG is the canonical interpreter/runtime surface for GTL.

GTL is:
- graph-first
- composition-first
- recursion-capable
- higher-order
- engine-agnostic

ABG is:
- the canonical target engine contract for GTL programs
- event-sourced
- replay-based
- provenance-carrying

This build is one realization of that contract.

---

## 2. Structural Axioms

1. `Graph` is the one first-class structural type.
2. `Node` is the typed local locus of graph meaning.
3. `GraphVector` is the admissible transition structure between nodes. It is not a rival ontology to graph; it is the internal graph-vector form.
4. `Context` is an externally located, snapshot-bound constraint dimension.
5. `Operator` is the effectful action surface.
6. `Evaluator` is the convergence and attestation surface.
7. `GraphFunction` is the reusable workflow program abstraction.
8. `RefinementBoundary` is the explicit lawful refinement/synthesis boundary.
9. `CandidateFamily` is the explicit lawful structural-alternative family.
10. `Module` is the publication boundary.
11. `Job` is the durable semantic work contract.
12. `Role` is the semantic capability class.
13. `Traversal`, `ConvergenceResult`, `Worker`, `ExecutableJob`, `WorkSurface`, `RunState`, and `LeafTask` are ABG runtime types, not GTL language types.

Nothing else should be treated as primary structural law unless explicitly promoted by requirements and design.

---

## 3. GTL Type Surface

| Type | Module | Meaning |
|------|--------|---------|
| `Graph` | `gtl.graph` | Named topology of nodes and graph vectors |
| `Node` | `gtl.graph` | Typed locus with declared markov conditions |
| `GraphVector` | `gtl.graph` | Admissible transition contract between nodes |
| `Context` | `gtl.graph` | Snapshot-bound external constraint |
| `Operator` | `gtl.operator_model` | Named capability with regime and binding |
| `Evaluator` | `gtl.operator_model` | Convergence/attestation declaration |
| `Rule` | `gtl.operator_model` | Declarative constraint with kind and config |
| `GraphFunction` | `gtl.function_model` | Reusable workflow template/program |
| `RefinementBoundary` | `gtl.function_model` | Published lawful refinement/synthesis boundary |
| `CandidateFamily` | `gtl.function_model` | Published lawful alternatives over one outer contract |
| `ContractRef` | `gtl.work_model` | Reference from a semantic job to a GTL contract |
| `Role` | `gtl.work_model` | Semantic capability class |
| `Job` | `gtl.work_model` | Durable semantic work contract |
| `Module` | `gtl.module_model` | Publication boundary for graphs, functions, boundaries, families, jobs, roles, and metadata |

Public GTL algebra (`gtl.algebra`):
- `edge` — construct a minimal one-vector graph
- `compose` — lawful sequential composition of graph functions
- `substitute` — replace a graph vector with an inner graph
- `recurse` — bounded repeated realization under an explicit termination evaluator
- `fan_out` — explicit vector-boundary expansion
- `fan_in` — explicit vector-boundary reduction
- `gate` — declarative evaluation boundary over a function, boundary, or family
- `promote` — explicit representation lift / join
- `identity` — neutral element for composition
- `deferred_refinement` — declare a `RefinementBoundary`
- `candidate_family` — declare a `CandidateFamily`
- `same_object` — identity equality by `.id`

These are graph semantics, not business-priority logic.

---

## 4. GTL / ABG Boundary

The language/runtime split is strict:

- GTL declares structure, semantics, and lawful contracts.
- ABG realizes traversal, replay, binding, execution, correction, transport, provenance, and self-hosting.

GTL must not import ABG runtime modules.
ABG may import GTL declarations.

GTL owns:
- graph structure
- composition/substitution semantics
- higher-order graph algebra
- refinement boundaries
- structural alternative families
- semantic jobs
- semantic roles
- module packaging
- selection boundary
- engine independence

ABG owns:
- append-only events
- projection
- convergence
- traversal
- lineage
- worker identity
- role binding
- run state
- lawful selection application
- transport
- correction
- provenance
- self-hosting/drift governance

---

## 5. Evaluator Regimes

Three evaluator regimes exist:

| Regime | Meaning | Role |
|--------|---------|------|
| `F_D` | Deterministic | Objective checks, schema checks, tests, hash/trace/provenance checks |
| `F_P` | Probabilistic | Agent disambiguation and bounded construction |
| `F_H` | Human | Human judgment, approval, escalation, or rejection |

Rules:

1. Deterministic proof precedes probabilistic judgment wherever applicable.
2. Agent output is not constitutional truth by itself.
3. Human approval is not a replacement for deterministic failure.
4. Evaluators decide whether graph contracts are satisfied. Operators perform work.

A higher regime is invoked when the current regime cannot close the relevant part of the contract, or when the contract explicitly requires higher-regime attestation. Lower regimes discharge all objective truth before higher-regime judgment is used.

F_D → F_P (deterministic slice satisfied, residual ambiguity remains). F_P → F_H (agent stuck or governance requires human attestation). F_H → F_D (approved → deploy).

---

## 6. Job, Role, Worker, Run

Do not collapse these concepts:

- `Job` is the GTL semantic work contract.
- `Role` is the GTL semantic capability class.
- `Traversal` is the ABG first-class runtime contract over a target boundary plus explicit evaluator/rule input.
- `ConvergenceResult` is the ABG aggregate convergence truth for one evaluator or evaluator vector.
- `Worker` is the ABG concrete actor identity.
- `Run` is the ABG execution attempt/lifecycle realization.

Binding is engine-owned:
- `Worker -> Role`
- `Run -> Job`

`ExecutableJob` is a runtime-resolved form of a semantic job against a concrete graph-vector contract.
`SelectionDecision` is an explicit ABG decision contract. It is required for `CandidateFamily` traversal and must remain provenance-carrying.

---

## 7. Event, Replay, Projection, Delta

ABG is event-sourced.

Rules:

1. The event stream is append-only.
2. `emit()` is the only lawful write path into runtime truth.
3. Projection is pure replay over the event stream: `project(S, T, I) = project(S, T, I)` always.
4. Delta is derived truth, not stored authority.
5. F_P does NOT call the event logger. F_P produces artifacts; F_D reads them and emits events.
6. Correction shadows prior certification/history; it does not erase history.
7. Provenance must accompany executable realization so stale assessments cannot be reused silently.
8. Convergence may be over one evaluator or an explicit evaluator-result vector.
9. Selection may validate and apply only lawful declared alternatives; it must not invent strategy.

The system is replayable or it is not lawful.

## Gradient

`delta(state, constraints) → work`. When delta = 0, system is at rest. Same computation at every scale — single iteration, vector convergence, feature traversal, production.

---

## 8. Selection Boundary

GTL may expose:
- lawful candidates
- interface families
- named `CandidateFamily` declarations
- named `RefinementBoundary` declarations
- tags
- hints
- graph-function catalogs

GTL may not hide strategic business choice inside the language or interpreter.

The engine may enumerate lawful options.
The decision surface must remain explicit and provenance-carrying.
If a `CandidateFamily` is traversed, the choice must arrive as an explicit `SelectionDecision`.

---

## 9. Transport and Dispatch

Transport is an ABG runtime concern.

The authoritative dispatch contract is the manifest/work surface, not an informal prompt.

Rules:

1. The manifest carries structured execution truth.
2. Prompt text is transport convenience, not sole authority.
3. Transport failures are classified and surfaced as runtime truth.
4. Agent transport is replaceable behind the ABG transport boundary.

No agent-specific shell surface is constitutional law.

---

## 10. Self-Hosting and Derived Artifacts

Bootloaders, manifests, and related derived artifacts are not outside the system.

They are governed artifacts and must remain under:
- convergence
- provenance
- replay suitability
- drift detection

If a derived artifact drifts from the live structural surface, that drift must be visible.

Derived artifacts are read models, not constitutional source.
They must be synthesized from the live surface, not treated as independent law.

---

## 11. Territory Rules

| Territory | Meaning | Rule |
|-----------|---------|------|
| `specification/` | Constitutional source | Authoritative intent, requirements, and design inputs |
| `builds/*/design/` | Shipping design surfaces | Structural bridge between requirements and code |
| `builds/*/code/` | Mutable implementation surfaces | Realization of the current build |
| `builds/*/test_env/` | Execution harness | Verification bed owned by that build |
| `.genesis/` in a target project | Installed runtime | Never treated as authored source |
| `.ai-workspace/` | Runtime evidence and agent territory | Events, comments, reviews, archives |

Do not treat the source repo root as the installed runtime.
Do not treat a test harness as constitutional source.

## Cascade Chain

Source → installer → installed territory. Order: **ABG → domain package → dependents** (never ABG direct to dependents).

---

## 12. Hard Prohibitions

Do not infer or invent:

- a second rival structural ontology to graph
- hidden business-priority logic inside GTL
- code authority without requirement/design trace
- compatibility shims as primary truth
- silent mutation of live domain history
- derived-artifact authority over constitutional source

If a surface cannot be traced back to live constitutional authority, it is accidental law.

---

## 13. Construction Heuristic for LLMs

When acting under this bootloader:

1. Start from live requirements and design, not stale code precedent.
2. Preserve the GTL / ABG boundary.
3. Use the smallest lawful concept that satisfies the requirement.
4. Prefer present-tense current-surface assertions over migration narration.
5. Treat missing traceability as a defect, not as permission to improvise.
6. If a live requirement is not yet realized, represent it as explicit deferment rather than silent omission.
7. If a live domain artifact is wrong, supersede or withdraw it; do not silently rewrite history.

The purpose of this document is to prevent unconstrained synthesis.

<!-- GTL_BOOTLOADER_END -->

<!-- SDLC_BOOTLOADER_START -->
The installed genesis_sdlc release is active.
Read workspace://.gsdlc/release/SDLC_BOOTLOADER.md first, then follow its referenced docs.

Installed axioms:
- Specification defines project truth; design surfaces define realization.
- `workspace://build_tenants/TENANT_REGISTRY.md` is the canonical registry of tenant families, variants, and activity state.
- The only lawful operative path is the resolved runtime at workspace://.ai-workspace/runtime/resolved-runtime.json.
- One edge traversal binds one role and one worker assignment.
- Backend identity is derived from worker assignment, not selected independently.
- Managed methodology surfaces live under workspace://.gsdlc/release/; project-owned surfaces live under workspace://specification/, workspace://build_tenants/, and workspace://docs/.
- Runtime/session state lives under workspace://.ai-workspace/runtime/; when it differs from release defaults, the resolved runtime wins.

Default role assignments for this install:
- `constructor` -> `claude_code`
- `implementer` -> `claude_code`
<!-- SDLC_BOOTLOADER_END -->


