# AI SDLC Method Concept Index

## Purpose

Read-only archaeology pass over `/Users/jim/src/apps/ai_sdlc_method`.

Goal:
- recover the key concepts that existed in the monolithic precursor
- index where each concept lives
- preserve concise descriptions so later ABG/GSDLC comparison does not require re-reading the whole retired repo

## Scope

This index is built from:
- root `README.md`
- root `CLAUDE.md`
- `specification/`
- `specification/adrs/`
- `specification/core/`
- `specification/features/`
- `specification/requirements/`
- `specification/verification/`
- `.ai-workspace/comments/` where later strategy posts carry concepts not fully crystallized in canonical ADRs

This is not an exhaustive bibliography. It is a concept-preservation index.

## Reading Guide

- `Primary reference` = best canonical source to recover the concept.
- `Supporting references` = other places the same idea is developed or reframed.
- `Forward cue` = where the concept appears to have gone in the ABG / GSDLC split, or whether it looks at risk.

## Aggregate Concept Index

### 1. Foundations and Ontology

| Concept | Description | Primary reference | Supporting references | Forward cue |
|---|---|---|---|---|
| Asset Graph Model | Formal system for AI-augmented development built from a graph of asset types and admissible transitions; SDLC graph is one instantiation, not the universal model itself. | `specification/core/AI_SDLC_ASSET_GRAPH_MODEL.md` | `README.md`; `specification/INTENT.md`; ADR-S-021 | Split across ABG kernel + GSDLC domain. |
| Four Primitives | The system reduces to `Graph`, `Iterate`, `Evaluators`, and `Spec + Context`. These are the irreducible basis, with everything else encoded above them. | `specification/core/GENESIS_BOOTLOADER.md` | `README.md`; `specification/core/AI_SDLC_ASSET_GRAPH_MODEL.md` | Strongly retained in ABG. |
| One Operation: `iterate(...)` | Universal transition function that takes current asset state, context, evaluators, and produces the next candidate state plus convergence behavior. | `specification/core/AI_SDLC_ASSET_GRAPH_MODEL.md` §3 | ADR-S-016; `README.md` | Retained in ABG as the engine center. |
| SDLC Graph as Projection | The SDLC workflow is explicitly only one projection of the universal formal system, not the formal system itself. | `README.md` ("The SDLC Graph (one projection)") | `specification/core/PROJECTIONS_AND_INVARIANTS.md`; comment `20260305T220000_STRATEGY_Graph-as-Projection-Universal-Process-Model.md` | Important to preserve; easily lost when a single workflow becomes concrete. |
| Asset as Markov Object | A converged asset is treated as a Markov object: usable from its current state without replaying the full construction history. | `specification/core/AI_SDLC_ASSET_GRAPH_MODEL.md` §2.3 | `specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md` (`REQ-GRAPH-003`); `specification/verification/UAT_TEST_CASES.md` (`UC-01-07/08/09`) | Conceptually present in ABG, often not named. |
| Markov Blankets / Active Inference Grounding | Formal boundary of a living system; gives theoretical grounding for assets, boundaries, sensory inputs, and convergence. | ADR-S-019 | `specification/core/AI_SDLC_ASSET_GRAPH_MODEL.md` §2.10, §3.3 | Mostly lost as explicit language; worth preserving. |
| Spec / Design Boundary | Separation between normative specification truth and design/implementation choice; methodology insists on boundary clarity. | `README.md` ("Spec / Design Separation") | `specification/core/AI_SDLC_ASSET_GRAPH_MODEL.md` §2.6 | Split into GSDLC project surfaces and release/spec logic. |
| Instantiation Layers | Separation between engine, graph package, and project binding; methodology definition is distinct from project instantiation. | `specification/core/AI_SDLC_ASSET_GRAPH_MODEL.md` §2.8 | ADR-S-033; GTL comments | Echoed later in ABG kernel vs GSDLC domain. |
| Invariants | Stable truths that must hold across all valid projections and zoom levels; methodology defines allowable state, not just procedure. | `specification/core/PROJECTIONS_AND_INVARIANTS.md` | ADR-S-036; ADR-S-037 | Central, but later sometimes compressed into evaluator rules. |
| Projections | Different valid views over the same underlying formal system or event substrate; not mere visualization, but lawful derived representations. | `specification/core/PROJECTIONS_AND_INVARIANTS.md` §3 | comment `20260305T220000_STRATEGY_Graph-as-Projection-Universal-Process-Model.md` | Important for later split and package/runtime distinctions. |
| Zoom Morphism | Variable grain / zoom is a structure-preserving transformation; same formal primitives apply at every scale. | ADR-S-017 | `specification/core/AI_SDLC_ASSET_GRAPH_MODEL.md` §2.5; comment `20260305T230000_STRATEGY_Zoom-Graph-Morphism-Spawn-Foldback.md` | Strong precursor to later GTL/subgraph ideas. |
| Intermediate Nodes for Computational Complexity Management | Nodes such as feature decomposition and module decomposition exist partly to manage ambiguity and bounded computation, not just to create artifacts. | `specification/core/PROJECTIONS_AND_INVARIANTS.md` §2.5 | ADR-S-006; ADR-S-007 | Retained in GSDLC asset chain. |
| Feature Vectors | Formal decomposition of capability requirements into traceable REQ-keyed vectors; not just backlog items, but typed vectors in the graph. | `specification/features/FEATURE_VECTORS.md` | ADR-S-009; ADR-S-013 | Forward descendant in requirements/features/model decomposition. |
| Multiple Vector Types | Beyond feature vectors, the model explicitly names discovery vectors, spike vectors, etc., allowing different lineage and convergence behavior. | `specification/core/PROJECTIONS_AND_INVARIANTS.md` §4 | ADR-S-009; ADR-S-030 | At risk of being collapsed into one generic artifact type. |

### 2. Traceability, State, Lineage, and Workspace

| Concept | Description | Primary reference | Supporting references | Forward cue |
|---|---|---|---|---|
| Event Stream as Formal Substrate | Canonical claim that the event stream is the foundational medium of the model; state is projection, not the authority. | ADR-S-012 | `specification/core/GENESIS_BOOTLOADER.md` §V; ADR-S-010 | Strongly inherited by ABG event model. |
| Event-Sourced Spec Evolution | Specification itself evolves by event sourcing; law/spec change is part of the same formal discipline. | ADR-S-010 | ADR-S-027; constitutional OS comments | Important precursor to package snapshots. |
| REQ Key Format and Threading | Stable requirement key identity format and threading rules for traceability through downstream assets. | ADR-S-003 | `specification/features/FEATURE_VECTORS.md`; `specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md` | Survives as trace IDs / coverage expectations. |
| Derivation Constraint | Downstream artifacts must be derivable from upstream authority surfaces; prevents invented structure detached from source requirements. | ADR-S-004 | ADR-S-037 | Still relevant in GSDLC traceability and review. |
| Spec Versioning Contract | Formal versioning obligations for spec evolution and compatibility. | ADR-S-005 | ADR-S-027 | Descends into release/version governance. |
| Completeness Visibility | System should surface feature coverage and convergence signals explicitly rather than hiding “what is still missing.” | ADR-S-013 | `specification/core/GENESIS_BOOTLOADER.md` §XII | Still a live gap/risk area in ABG/GSDLC. |
| OpenLineage Metadata Standard | Common metadata contract for events / work units, binding operational activity to typed lineage records. | ADR-S-011 | comment `20260305T210000_STRATEGY_Unit-of-Work-Event-Sourcing-Artifact-Versioning.md` | Precursor to lineage/provenance event schemas. |
| Project Instance Graph | Distinguishes schema/topology from project instance state; graph definition is not the same thing as traversal state. | ADR-S-021 | `specification/core/AI_SDLC_ASSET_GRAPH_MODEL.md`; ADR-S-029 | Key precursor to package/runtime split. |
| Project Lineage and Context Inheritance | Child or derived work inherits lawful context from parent lineage without collapsing identity. | ADR-S-022 | ADR-S-030 | Still matters for spawned or gap-driven work. |
| Workspace State Partitioning | Explicit partition of workspace into different authority/state zones instead of one undifferentiated filesystem. | ADR-S-023 | later comments on chart/values/release split | Strong ancestor of `.genesis` / `.gsdlc` / `.ai-workspace` territories. |
| Immutable Lineage Rule | Once a vector converges, later gap work should create child lineage rather than reopening the same converged identity. | ADR-S-030 | comment `20260309T120000_PROPOSAL_consensus-observer-and-event-driven-engine.md` | Very important concept; partially regained in later gap modeling. |
| Gap-Driven Vector Typing | Gap observations are not generic edits; they are typed lineage-producing events that route into specific vector behavior. | ADR-S-030 | ADR-S-039 | At risk of being simplified away. |
| Authority Boundaries | Specification and package authorities are consolidated deliberately; not every note or doc can become law. | ADR-S-027 | `specification/README.md`; constitutional OS comments | Still essential in multi-doc repos. |
| Projection Authority and Convergence Evidence | Only specific projections are authoritative for promotion; convergence claims require evidence validated against authority surfaces. | ADR-S-037 | comment `20260312T204334_REVIEW_Claude-convergence-evidence-projection-authority.md` | Strong descendant in ABG evidence/promotion model. |

### 3. Evaluation, Dispatch, and Execution

| Concept | Description | Primary reference | Supporting references | Forward cue |
|---|---|---|---|---|
| Three Evaluator Types | The model distinguishes deterministic, probabilistic, and human evaluators rather than one undifferentiated “review” layer. | `specification/core/GENESIS_BOOTLOADER.md` §VII | `specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md` (`REQ-EVAL-001`) | Direct ancestor of `F_D`, `F_P`, `F_H`. |
| Processing Phases: Reflex / Affect / Conscious | Three processing phases frame how the system reacts to inputs and selects escalation/interpretation depth. | `specification/core/GENESIS_BOOTLOADER.md` §VII | ADR-S-008 | Largely implicit now; concept worth preserving. |
| Sensory-Triage-Intent Pipeline | Consciousness loop: sensory intake, triage, and intent formation are part of the formal model, not mere UX description. | ADR-S-008 | `specification/features/FEATURE_VECTORS.md` (`REQ-F-SENSE-001`) | Precursor to intent discovery and dispatch loops. |
| IntentEngine Composition Law | Intent is computed compositionally from state/sensory inputs; output categories are constrained. | `specification/core/GENESIS_BOOTLOADER.md` §IX | `specification/core/PROJECTIONS_AND_INVARIANTS.md` §2.4 | Still present conceptually but less explicitly named. |
| Unit of Work as Transaction | Edge traversal is the atomic unit of work; commit semantics require both artifact effect and event record. | ADR-S-015 | comment `20260305T210000_STRATEGY_Unit-of-Work-Event-Sourcing-Artifact-Versioning.md` | Still a powerful design lens for ABG iterations. |
| Invocation Contract | Formal contract for invoking a transition / functor, separating transport/execution details from the lawful transition interface. | ADR-S-016 | comment `20260305T200000_STRATEGY_Edge-Traversal-as-Markov-Functor.md` | Ancestor to ABG dispatch API and transport debates. |
| Natural Language Intent Dispatch | Natural-language intent can route into lawful graph behavior rather than bypassing the model. | ADR-S-038 | `specification/core/GENESIS_BOOTLOADER.md`; GTL comments | Echoes later in slash-command / bootloader flows. |
| `graph_fragment` Compiled Dispatch Intermediate | Intermediate compiled representation between high-level methodology and executable dispatch. | ADR-S-029 | later GTL comments; dispatch contract discussions | Strong precursor to subgraph/fragment thinking. |
| IntentObserver + EDGE_RUNNER | Explicit autonomous dispatch contract separating observation of intent/gap from actual edge execution. | ADR-S-032 | comment `20260311T010000_STRATEGY_intentobserver-edgerunner-consensus-as-edge-type.md` | Direct ancestor of autonomous dispatch loops. |
| Supervisor Pattern / Choreographed Saga | Event-sourced supervisory coordination instead of hidden imperative orchestration. | ADR-S-031 | comment `20260314T134609_STRATEGY_Agentic-Saga-Pattern-draft-ADR-proposal.md` | Important precursor to later saga/governance ideas. |
| Bug Triage and Post-Mortem Escalation | Operational failure handling is part of the formal method; bug triage and post-mortem are modeled as lawful escalation surfaces. | ADR-S-039 | `specification/templates/POSTMORTEM_TEMPLATE.md` | Often at risk of being treated as outside the system. |

### 4. Workflow Structure, Planning, and Governance

| Concept | Description | Primary reference | Supporting references | Forward cue |
|---|---|---|---|---|
| Feature Decomposition as Explicit Graph Node | Feature decomposition is not just prose planning; it is a formal node with lineage and convergence meaning. | ADR-S-006 | `specification/features/REQ-F-PROXY-001-feature-decomposition.md` | Directly retained in GSDLC. |
| Module Decomposition and Basis Projections | Module boundaries and basis projections are graph nodes, not informal design notes. | ADR-S-007 | `specification/core/AI_SDLC_ASSET_GRAPH_MODEL.md` | Directly retained in GSDLC decomposition chain. |
| Design Signal Gate / Marketplace Checkpoint | There is an explicit marketplace / external-design-style evaluation gate before certain promotions. | ADR-S-024 | Gemini comment cluster on design marketplace | Partly retained as design approval/gates. |
| CONSENSUS Functor | Multi-stakeholder evaluator composition as a named lawful construct rather than ad hoc voting. | ADR-S-025 | `specification/core/HIGHER_ORDER_FUNCTORS.md` | Later echoed in consensus observer proposals. |
| Named Compositions and Intent Vector Envelope | Intent expressions can name higher-order compositions rather than only edges; intent vectors carry richer composition metadata. | ADR-S-026 | `specification/core/HIGHER_ORDER_FUNCTORS.md` | Strong precursor to later profile/composition language. |
| Higher-Order Functor Library | Library of named compositions above the primitives: `BROADCAST`, `FOLD`, `BUILD`, `CONSENSUS`, `REVIEW`, `DISCOVERY`, `RATIFY`, `EVOLVE`. | `specification/core/HIGHER_ORDER_FUNCTORS.md` | comments on PLAN and higher-order patterns | Important idea partially dispersed across later repos. |
| PLAN Functor | Repeating intermediary between assets: decompose, evaluate, order, rank, yielding a work order before build. | comment `20260308T100000_STRATEGY_PLAN-Functor-Universal-Intermediary.md` | `specification/core/HIGHER_ORDER_FUNCTORS.md` (`PLAN` named composition) | Very important planning concept; easy to lose if graph is flattened. |
| Discovery as Structured Convergence | DISCOVERY is not generic brainstorming; it is a convergent question-answer / uncertainty-reduction pattern. | `specification/core/HIGHER_ORDER_FUNCTORS.md` (`DISCOVERY`) | comments on discovery process theory | At risk if “discovery” becomes informal prompting. |
| Review / Ratify / Evolve | Promotion, approval, and versioned re-entry are explicit functorial patterns, not special cases outside the graph. | `specification/core/HIGHER_ORDER_FUNCTORS.md` | ADR-S-010; ADR-S-025; ADR-S-026 | Descends into release and governance flows. |
| Invariants as Termination Conditions, Not Procedures | The system should define what must be true for completion rather than prescribing one fixed sequence of steps. | ADR-S-036 | `specification/core/PROJECTIONS_AND_INVARIANTS.md` | Important for keeping methodology generative. |
| Multi-Tenancy Model | Genesis is designed to host multiple tenants/projects/domains lawfully rather than as one single workspace. | ADR-S-002 | ADR-S-023; ADR-S-034 | Important ancestor of ecosystem/package-general direction. |

### 5. Genesis Package / Ecosystem / Language Direction

| Concept | Description | Primary reference | Supporting references | Forward cue |
|---|---|---|---|---|
| Genesis-Enabled Systems | Build-time/runtime separation and homeostatic bridge between the formal method and concrete systems using it. | ADR-S-033 | `specification/core/GENESIS_BOOTLOADER.md` | Strong precursor to ABG kernel + domain layering. |
| Genesis Ecosystem | Multiple cooperative services/packages/domains co-evolving in a broader ecology rather than one isolated application. | ADR-S-034 | comments on enterprise architecture / package generalization | Important strategic ancestor of ABG + GSDLC split. |
| GTL: Genesis Topology Language | Python / language surface for defining topology/package law instead of static bundles. | ADR-S-035 | comment `20260311T105052_STRATEGY_genesis-dsl-topology-language.md` | Major precursor to later GTL work. |
| GTL as Package Language, Not Config | Later strategy reframes GTL as the language of lawful packages, with assets, edges, operators, compositions, governance, and bindings. | comment `20260313T201342_STRATEGY_dynamic_interpretive_GTL_standalone_proposal.md` | comment `20260313T201904_STRATEGY_genesis-as-constitutional-os.md` | Forward-looking concept; not fully carried into later repos yet. |
| Dynamic / Interpretive GTL | Package loaded and interpreted at runtime, with governed activation and replayable package snapshots. | comment `20260313T201342_STRATEGY_dynamic_interpretive_GTL_standalone_proposal.md` | GTL review thread on 2026-03-13/14 | Very likely only partially retained. |
| Constitutional OS | Genesis framed as constitutional operating system: lawful space of mutation, replayable legal history, package law, immune response. | comment `20260313T201904_STRATEGY_genesis-as-constitutional-os.md` | comment `20260313T223000_REVIEW_constitutional-OS-resolves-open-questions.md` | Powerful synthesis; largely absent as explicit language later. |
| Constitutional vs Operational Streams | Separate constitutional record (law/package evolution) from operational work record, linked by active package snapshot. | comment `20260313T223000_REVIEW_constitutional-OS-resolves-open-questions.md` | ADR-S-010; ADR-S-027 | Strongly relevant to package/runtime history design. |
| Lawful Package Evolution | Package changes are not edits-in-place but governed, replayable, historically bound changes. | comment `20260313T201342_STRATEGY_dynamic_interpretive_GTL_standalone_proposal.md` | constitutional OS thread | At risk in simpler file-copy installs. |
| Mermaid as View, Not Canonical GTL | Diagrams are projections, not the canonical language surface for topology. | comment `20260314T000000_DECISION_mermaid-as-view-not-canonical-GTL.md` | GTL draft v0.1/v0.2 comments | Important if visualizations start masquerading as truth. |

### 6. Comment-Born Concepts Worth Preserving Even If Not Fully Ratified

| Concept | Description | Primary reference | Supporting references | Why it matters |
|---|---|---|---|---|
| E2E Runner as Canonical Invocation Model | The proven end-to-end runner is treated as the real executable form of `iterate(...)`, with scaffolding, validation, and archival all included. | comment `20260305T190000_STRATEGY_E2E-Runner-as-Canonical-Invocation-Model.md` | ADR-S-016; ADR-S-023 | Strong precursor to “tests as executable methodology.” |
| Edge Traversal as Autonomous Markov Functor | Each edge traversal is a Markov step; transport is incidental, state/current context is what matters. | comment `20260305T200000_STRATEGY_Edge-Traversal-as-Markov-Functor.md` | ADR-S-016; ADR-S-019 | Helps separate engine law from transport details. |
| Unit of Work + Artifact Versioning + Side-Effect Discipline | A traversal is not complete unless artifact state and event record cohere; side effects must be versioned and bounded. | comment `20260305T210000_STRATEGY_Unit-of-Work-Event-Sourcing-Artifact-Versioning.md` | ADR-S-011; ADR-S-015 | Important operational rigor concept. |
| Graph as Universal Process Model | The same formal model can describe SDLC, approval, CI/CD, data pipelines, etc.; differences are boundary/grain choices. | comment `20260305T220000_STRATEGY_Graph-as-Projection-Universal-Process-Model.md` | `specification/core/PROJECTIONS_AND_INVARIANTS.md` | Prevents overfitting the method to one workflow. |
| Spawn / Fold-Back as Zoom In / Out | Sub-work and child vectors are not ad hoc recursion; they are zoom transformations on the graph. | comment `20260305T230000_STRATEGY_Zoom-Graph-Morphism-Spawn-Foldback.md` | ADR-S-017 | Very strong precursor to fragment/subgraph composition. |
| High-Order Concepts as Constraint Surfaces | Higher-order constructs are not merely macros; they act as constraint surfaces over lawful execution. | comment `20260307T225000_STRATEGY_High-Order-Concepts-as-Constraint-Surfaces.md` | `specification/core/HIGHER_ORDER_FUNCTORS.md` | Good synthesis lens for later GTL work. |
| Public Review Node Between Intent and Requirements | Suggests explicit public/external review checkpoint before requirements harden. | comment `20260308T050000_STRATEGY_Public-Review-Node-Between-Intent-and-Requirements.md` | ADR-S-024 | May explain later design-review gating instincts. |
| Consensus Observer / Event-Driven Engine | Observer-style capability that reacts to consensus-relevant events instead of central imperative loops. | comment `20260309T120000_PROPOSAL_consensus-observer-and-event-driven-engine.md` | ADR-S-025; ADR-S-032 | Important bridge from theory to runtime orchestration. |
| Human-Proxy Mode | Explicit concept that a human can stand in for autonomous agentic steps without violating the formal model. | comment `20260313T031500_STRATEGY_human-proxy-mode-for-autonomous-runs.md` | human-proxy gap comments | Useful for partial autonomy and real enterprise rollout. |
| Discovery Not a Primitive | Strong warning from later comments that “discovery” should remain a named pattern above the primitives, not become a new primitive. | comment `20260313T210000_FOLLOWUP_discovery-not-a-primitive.md` | `specification/core/HIGHER_ORDER_FUNCTORS.md` | Preserves minimal kernel discipline. |
| GTL Minimal Algebraic Core | Drive to reduce GTL to a minimal lawful algebra rather than an accreting bag of syntax. | comments `20260314T003000_STRATEGY_GTL-minimal-algebraic-core.md`, `20260314T020000_SPEC_GTL-language-draft-v0.1.md`, `20260314T030000_SPEC_GTL-language-draft-v0.2.md` | GTL review thread | Key if GTL is resumed. |
| Agentic Saga Pattern | Separates immutable operational truth from lagging paperwork/trace completeness; forbids falsification, not delayed packaging. | comment `20260314T134609_STRATEGY_Agentic-Saga-Pattern-draft-ADR-proposal.md` | ADR-S-012; ADR-S-037 | Important operational governance idea that may otherwise disappear. |

## High-Risk Concepts That Look Easy to Lose in the ABG / GSDLC Split

These are the ideas I would explicitly check for when comparing the retired monolith to the newer split repos:

1. `SDLC graph is only one projection of a universal formal system`
2. `state is projection; event stream is authority`
3. `feature/module decomposition are computational boundary-management nodes, not just artifacts`
4. `multiple vector types beyond a generic feature backlog`
5. `immutable lineage after convergence`
6. `projection authority and convergence evidence`
7. `PLAN as the universal intermediary between major asset transitions`
8. `higher-order functors as lawful named patterns above the primitives`
9. `constitutional/package law distinct from operational work state`
10. `dynamic / interpretive GTL as package language rather than static config`
11. `human-proxy and mixed-autonomy operation as first-class`
12. `agentic saga distinction between truthful event history and delayed trace packaging`

## Practical Use

This post can now be used as:
- a concept dictionary while reading `abiogenesis` and `genesis_sdlc`
- a migration checklist for “what did we accidentally drop?”
- a reference index for recovering the older rationale before re-inventing it in the split repos

## Explicit Backlog Inventory

This is the explicit backlog I could recover from the retired repo without treating every speculative comment as a backlog item.

### A. Root Active-Task Backlog

Source: `/Users/jim/src/apps/ai_sdlc_method/.ai-workspace/tasks/active/ACTIVE_TASKS.md`

| Item | Status | Priority/Severity | Description |
|---|---|---|---|
| `REQ-F-INTENT-001` | Pending | high | Intent composition layer: implement REQ-INTENT-002/003/004 so the system can autonomously compose, deduplicate, and prioritize intents. |
| `REQ-F-TOOL-015` | Pending | medium | One-line traceability fix: add `Validates: REQ-TOOL-015` to installer e2e test. |
| `REQ-F-EVOL-NFR-002` | Pending | low | Resolve orphan `REQ-EVOL-NFR-002` tag in code: either define it in spec or retag to an existing requirement. |
| Installer telemetry gap under `REQ-F-TELEM-001` | Deferred | Phase 2 / non-blocking | `gen-setup.py` lacks `req=` telemetry tags for the `code→cicd` edge; explicitly deferred until homeostasis/runtime monitoring exists. |

### B. Cross-Tenant Backlog

Source: `/Users/jim/src/apps/ai_sdlc_method/.ai-workspace/tasks/active/ACTIVE_TASKS.md` (`## Backlog (cross-tenant)`)

| Item | Description |
|---|---|
| Marketplace Observer | Feature vector for per-tenant implementation of ADR-S-024 consensus decision gate: session-start scan, task-boundary gate, ambiguity routing. |
| ADR-S-014 OTLP/Phoenix | Ratified design ADR and cross-tenant implementation alignment for OTLP/Phoenix observability; Gemini had implementation, Claude did not. |
| INTRO-005 Build Health monitor | Build health monitor needing CI/CD integration. |
| ADR cleanup | Remove historical rationale sections from ADRs that no longer constrain construction, to reduce spec drift. |
| `INT-TRACE-001` | Code annotation pass: 52/83 REQ keys lacked `Implements:` tags. |
| `INT-TRACE-002` | Test annotation pass: 1078 tests lacked `Validates: REQ-*` links. |
| `INT-TRACE-003` | Orphan fixture key cleanup in command markdown files. |

### C. Pending Proposal Queue

Source: `/Users/jim/src/apps/ai_sdlc_method/.ai-workspace/reviews/pending/`

| Proposal | Status | Severity | Description |
|---|---|---|---|
| `PROP-019` | draft | high | GTL Phase 1 object model as pure Python dataclasses: Package, Asset, Edge, Operator, Rule, Context, Overlay, PackageSnapshot, functor categories, `consensus(n,m)`, topology rendering, and example packages. |
| `PROP-020` | draft | medium | Traceability tag sweep for 15 untagged spec keys that already have implementation/test coverage but are missing `Implements:` annotations. |
| `PROP-021` | draft | medium | Telemetry instrumentation: add `req=` tags to engine execution paths; advisory until the `code→cicd` edge is formally active. |
| `PROP-022` | approved | high | Strategic pivot to new project `abiogenesis`: clean GTL-first Genesis v1.0 implementation; effectively marks `ai_sdlc_method` as frozen bootstrap/prior art. |

### D. UX Scenario Backlog

Source: `/Users/jim/src/apps/ai_sdlc_method/specification/ux/UX.md` (`## 6. Scenario Backlog`)

| Scenario | Title | Focus |
|---|---|---|
| `SC-008` | Enterprise Compliance — Audit Trail Generation | Regulatory traceability, lifecycle assurance |
| `SC-009` | Library Release — Full Profile with Versioning | Semver, changelog, release process |
| `SC-010` | Cross-Platform — Same Spec, Claude + Gemini Implementations | Multi-tenancy, spec/design separation |
| `SC-011` | Methodology Self-Application — Genesis Builds Genesis | Recursive compliance, dogfooding |
| `SC-012` | Time-Boxed Exploration — PoC with Expiry | Time-box mechanics, fold-back-or-discard |
| `SC-013` | Context Window Pressure — Large Project Scaling | Context selection and scaling behavior |
| `SC-014` | Ecosystem Shock — Major Dependency Breaks | Exteroceptive response and ecosystem sensing |
| `SC-015` | CI/CD Pipeline — Build from Spec on Commit | Pipeline integration and exit-code semantics |

### E. Structural Backlog Surfaces

These are not itemized backlog entries by themselves, but they show how backlog/state was expected to exist in the methodology:

| Surface | Meaning | Reference |
|---|---|---|
| Cross-tenant backlog as first-class runtime state | Backlog belongs at the shared `.ai-workspace/` root, not to any one tenant. | `specification/adrs/ADR-S-023-workspace-state-partitioning.md` |
| Feature queue | Shared feature vectors under `.ai-workspace/features/` act as formal work inventory. | `.ai-workspace/features/` |
| Proposal/review queue | Proposed work and governance decisions live under `.ai-workspace/reviews/pending/`. | `.ai-workspace/reviews/pending/` |
| Cross-tenant active tasks | Shared goal and backlog coordination live in root `.ai-workspace/tasks/active/ACTIVE_TASKS.md`. | `.ai-workspace/tasks/active/ACTIVE_TASKS.md` |

### F. Historical / Stale Backlog Signals

One historical tenant task file still carries an older pending subtask:

- `/Users/jim/src/apps/ai_sdlc_method/.ai-workspace/claude/tasks/active/ACTIVE_TASKS.md`
  - `T-COMPLY-008` notes engine-side complete but “LLM-layer side pending”.

I do **not** treat that as authoritative current backlog because the later root active-task file records `v3.0.0` and `v3.0.1` as shipped and supersedes the older tenant sprint state.

## Deduped Migration Table — Retired Backlog vs ABG / GSDLC

This table dedupes overlapping backlog items and classifies where they went after the split.

Allowed status values:
- `carried into abiogenesis`
- `carried into genesis_sdlc`
- `lost`
- `superseded`

| Retired backlog theme | Status | Where it went | Evidence / rationale |
|---|---|---|---|
| Intent composition layer (`REQ-F-INTENT-001`) | `lost` | Fragments only | The explicit layer for composing, deduplicating, and prioritising intents did not survive as a named subsystem. Fragments survive as backlog promotion in GSDLC and `(edge, feature)` dedup in ABG, but not the full composition layer. |
| Backlog as pre-intent holding area | `carried into genesis_sdlc` | Formal backlog sidecar | Survives strongly in `genesis_sdlc` as `specification/standards/BACKLOG.md`, `REQ-F-BACKLOG-001..004`, and `builds/python/src/genesis_sdlc/backlog.py`. ABG references backlog keys in its packaged requirements, but GSDLC is where it is explicitly operationalised. |
| Marketplace Observer / ADR-S-024 consensus gate observer | `superseded` | Repriced into simpler marketplace conventions | The rich observer/gate idea did not survive intact. What remains is the `Multivector Design Marketplace` and post conventions in `genesis_sdlc/specification/standards/CONVENTIONS.md`, but not a dedicated observer subsystem with session-start/task-boundary gating. |
| OTLP / Phoenix observability (`ADR-S-014`) | `lost` | No clear descendant | I found no live OTLP/Phoenix observability stack in the split repos. Observability narrowed to event/provenance/audit mechanics rather than the old OTLP/Phoenix direction. |
| Build Health monitor (`INTRO-005`) | `lost` | No clear descendant | No current ABG/GSDLC surface looks like a direct successor to a dedicated build-health monitor. Health is now inferred from tests, convergence status, and audits rather than a named monitor feature. |
| ADR cleanup / historical-rationale cleanup | `superseded` | Replaced by fresh repo-specific ADR sets | The cleanup goal effectively dissolved into the repo split. Both ABG and GSDLC now have their own newer ADR stacks rather than carrying forward the old cleanup task as a distinct item. |
| Traceability tag sweeps (`REQ-F-TOOL-015`, `PROP-020`, `INT-TRACE-001/002/003`) | `superseded` | Became first-class product requirements | In the split repos this stopped being backlog maintenance and became built-in discipline: ABG has traceability commands/REQs in `specification/requirements.md` and `builds/claude_code/design/adrs/ADR-009-traceability-commands.md`; GSDLC has `REQ-F-TAG-*`, `REQ-F-COV-001`, `check-tags`, and backlog/tests enforcing them. |
| Orphan legacy key cleanup (`REQ-F-EVOL-NFR-002`) | `superseded` | Repo-local cleanup vanished with the new key systems | This was a stale-tag cleanup item in the retired monolith. It does not appear as a meaningful descendant in the split repos and is best treated as obsolete cleanup superseded by new requirement registries. |
| Telemetry instrumentation (`REQ-F-TELEM-001` installer gap + `PROP-021`) | `lost` | Not carried as a live roadmap item | The explicit `req=` telemetry instrumentation backlog did not survive cleanly. Current repos retain provenance/audit/event mechanics, but I did not find an active `REQ-F-TELEM-*` style roadmap in ABG/GSDLC. |
| GTL Phase 1 object model (`PROP-019`) | `carried into abiogenesis` | Implemented as GTL Python model | This migrated directly into ABG: `docs/GTL_Technical_Guide.md`, `builds/claude_code/code/gtl/core.py`, `Overlay`, `PackageSnapshot`, and GTL requirements all show the Phase 1 object-model direction landed there. |
| New project `abiogenesis` (`PROP-022`) | `carried into abiogenesis` | Direct descendant | This proposal is the pivot itself. ABG is the approved clean successor. |
| Enterprise compliance / audit-trail generation (`SC-008`) | `superseded` | Reframed as provenance + audit surfaces | The exact scenario name did not survive, but its substance moved into ABG workflow provenance (`REQ-F-PROV-*`, auditable domain model) and GSDLC install/deep-audit surfaces (`install --audit`, release audits, traceability). |
| Library release / versioning scenario (`SC-009`) | `carried into genesis_sdlc` | Strong release-process descendant | GSDLC carries this strongly via versioned `.gsdlc/release/` installs, `specification/standards/RELEASE.md`, and `builds/python/CHANGELOG.md`. |
| Cross-platform same-spec / multi-implementation scenario (`SC-010`) | `lost` | Multi-tenant comparative execution abandoned | The split repos are not pursuing the old Claude+Gemini same-spec multi-implementation journey. That idea largely disappeared when the monolith froze and ABG/GSDLC became focused repos. |
| Methodology self-application (`SC-011`) | `carried into abiogenesis` | Strong self-hosting descendant | Self-hosting is explicit in `abiogenesis/README.md`, `abiogenesis/specification/INTENT.md`, and self-hosting E2E tests. GSDLC is also self-hosting, but ABG is the clearer direct descendant of the “Genesis builds Genesis” scenario. |
| Time-boxed exploration / PoC with expiry (`SC-012`) | `lost` | No direct descendant found | I did not find a live split-repo equivalent for time-boxed PoC-with-expiry mechanics. |
| Context-window pressure / large-project scaling (`SC-013`) | `lost` | No direct descendant found | Context management exists, but the explicit large-project scaling scenario backlog did not survive as an active split-repo program. |
| Ecosystem shock / major dependency breaks (`SC-014`) | `lost` | No direct descendant found | I did not find a direct successor scenario for exteroceptive ecosystem-shock handling in the current repos. |
| CI/CD pipeline from spec on commit (`SC-015`) | `superseded` | Repriced into installer/release discipline | The exact scenario did not survive, but its intent moved into installer-as-deployment and release-process discipline, especially in GSDLC. It is not present as an explicit pipeline scenario. |

## Migration Read

The retired backlog did **not** migrate evenly.

What clearly survived:
- GTL object-model work → **abiogenesis**
- self-hosting / Genesis-builds-Genesis → **abiogenesis** (and secondarily `genesis_sdlc`)
- release/versioning discipline → **genesis_sdlc**
- backlog as pre-intent holding area → **genesis_sdlc**
- traceability discipline → **both repos**, but as a **superseded** first-class system rather than a backlog sweep

What appears to have dropped:
- explicit intent composition layer
- OTLP/Phoenix observability direction
- build-health monitor
- time-boxed exploration mechanics
- large-project context-pressure scenario
- ecosystem-shock scenario
- old multi-implementation / cross-platform same-spec journey

The big pattern is:
- **ABG** inherited the formal GTL / self-hosting / package-law thread
- **GSDLC** inherited the release/install/backlog/operator-discipline thread
- several observability and ecosystem ideas from the monolith were simply not carried forward

## Source Anchors

Canonical spec anchors:
- `/Users/jim/src/apps/ai_sdlc_method/README.md`
- `/Users/jim/src/apps/ai_sdlc_method/specification/INTENT.md`
- `/Users/jim/src/apps/ai_sdlc_method/specification/core/AI_SDLC_ASSET_GRAPH_MODEL.md`
- `/Users/jim/src/apps/ai_sdlc_method/specification/core/PROJECTIONS_AND_INVARIANTS.md`
- `/Users/jim/src/apps/ai_sdlc_method/specification/core/HIGHER_ORDER_FUNCTORS.md`
- `/Users/jim/src/apps/ai_sdlc_method/specification/core/GENESIS_BOOTLOADER.md`
- `/Users/jim/src/apps/ai_sdlc_method/specification/features/FEATURE_VECTORS.md`
- `/Users/jim/src/apps/ai_sdlc_method/specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md`
- `/Users/jim/src/apps/ai_sdlc_method/specification/verification/UAT_TEST_CASES.md`
- `/Users/jim/src/apps/ai_sdlc_method/specification/adrs/`

High-signal comment anchors:
- `.ai-workspace/comments/claude/20260305T190000_STRATEGY_E2E-Runner-as-Canonical-Invocation-Model.md`
- `.ai-workspace/comments/claude/20260305T200000_STRATEGY_Edge-Traversal-as-Markov-Functor.md`
- `.ai-workspace/comments/claude/20260305T210000_STRATEGY_Unit-of-Work-Event-Sourcing-Artifact-Versioning.md`
- `.ai-workspace/comments/claude/20260305T220000_STRATEGY_Graph-as-Projection-Universal-Process-Model.md`
- `.ai-workspace/comments/claude/20260305T230000_STRATEGY_Zoom-Graph-Morphism-Spawn-Foldback.md`
- `.ai-workspace/comments/claude/20260308T100000_STRATEGY_PLAN-Functor-Universal-Intermediary.md`
- `.ai-workspace/comments/claude/20260309T120000_PROPOSAL_consensus-observer-and-event-driven-engine.md`
- `.ai-workspace/comments/claude/20260311T105052_STRATEGY_genesis-dsl-topology-language.md`
- `.ai-workspace/comments/codex/20260313T201342_STRATEGY_dynamic_interpretive_GTL_standalone_proposal.md`
- `.ai-workspace/comments/codex/20260313T201904_STRATEGY_genesis-as-constitutional-os.md`
- `.ai-workspace/comments/claude/20260313T223000_REVIEW_constitutional-OS-resolves-open-questions.md`
- `.ai-workspace/comments/codex/20260314T134609_STRATEGY_Agentic-Saga-Pattern-draft-ADR-proposal.md`
