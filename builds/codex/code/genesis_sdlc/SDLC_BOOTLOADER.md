# SDLC Bootloader: AI SDLC Instantiation of the GTL Formal System

**Version**: 1.2.0
**Purpose**: Domain-specific instantiation of the GTL formal system for software development lifecycle projects. This bootloader extends the universal GTL bootloader with SDLC-specific graph topology, feature vectors, workspace territory, and bug triage.

**Requires**: GTL Bootloader (universal axioms — four primitives, event stream, gradient, evaluators)

---

## XII. Completeness Visibility

Two questions must be answerable at any time: **"Did I get all the features?"** and **"Is it done?"**

### Feature Decomposition Convergence

The `requirements → feature_decomposition` edge converges when both hold:

- **F_D (coverage)**: Every `REQ-*` key in requirements appears in the `satisfies:` field of at least one feature vector.
- **F_H (approval)**: A human has explicitly approved the decomposition, dependency ordering, and MVP boundary.

F_D gates F_H. No human review is requested until coverage delta reaches zero.

### Coverage Projection

At any point after feature decomposition is initiated, the system must be able to compute:

```text
FEATURE COVERAGE
  Requirements: N REQs defined
  Covered:      n/N
  Gaps:         [list of uncovered REQ-* keys]
  Features:     M vectors  ✓ converged / ⟳ in-progress / ○ not started
```

### Convergence Visibility

Every edge transition must make convergence visible before downstream work proceeds:

- iteration summary after every `iterate()` call
- edge convergence summary when an edge reaches zero delta
- feature completion summary when all edges in a feature converge

Silent convergence is a methodology violation.

---

## XIII. Feature Vectors

A feature is a trajectory through the graph:

```text
Feature F = |req⟩ + |feature_decomp⟩ + |design⟩ + |module_decomp⟩ + |code⟩ + |unit_tests⟩ + |integration_tests⟩ + |user_guide⟩ + |uat_tests⟩
```

Feature vectors carry a required `satisfies:` field listing the covered `REQ-*` keys. The REQ key is the traceability thread from spec to runtime.

---

## XIV. The SDLC Graph

```text
intent → requirements → feature_decomp → design → module_decomp → code ↔ unit_tests
                                                                          │
                                                                          ↓
                                                   uat_tests ← user_guide ← integration_tests
```

Feature decomposition is a first-class node with its own evaluators and convergence criteria.

Standard profile edge chain:

`intent → requirements → feature_decomp → design → module_decomp → code ↔ unit_tests → integration_tests → user_guide → uat_tests`

---

## XV. Projections

Named profiles preserve the same invariants while varying the graph encoding:

| Profile | When |
|---------|------|
| `full` | regulated, high-stakes |
| `standard` | normal feature work |
| `poc` | proof-of-concept |
| `spike` | research / experiment |
| `hotfix` | emergency fix |
| `minimal` | trivial change |

---

## XVI. Spec / Design Separation

- **Spec** = WHAT, tech-agnostic, up to and including feature decomposition.
- **Design** = HOW architecturally, from design onwards.

Code disambiguation feeds back to either spec or design. Never conflate them.

---

## XVII. Invariants

| Invariant | Meaning |
|-----------|---------|
| Graph | typed assets with admissible transitions |
| Iterate | convergence loop producing events and assets |
| Evaluators | at least one evaluator per active edge |
| Spec + Context | bounded construction surface |
| Event stream | state derives from append-only events |
| Completeness visibility | convergence transitions are surfaced before downstream work |

Observability is constitutive, not optional.

---

## XVIII. Workspace Territory

Two runtime territories exist and they serve different purposes:

| Territory | Purpose | Ownership |
|-----------|---------|-----------|
| `.ai-workspace/` | shared, auditable metabolic state | cross-agent / shared |
| `builds/<tenant>/.workspace/` | tenant-local manifests, iterations, working surfaces, scratch traces | single tenant only |

### Shared `.ai-workspace/`

- `events/events.jsonl`: append-only event log, written only through the event logger
- `features/active/` and `features/completed/`: shared feature state
- `reviews/`: human and proxy review state
- `comments/<tenant>/`: tenant-owned posts
- `backlog/`: pre-intent holding area

### Private `builds/<tenant>/.workspace/`

Each tenant owns a private build-local workspace. For Codex this is `builds/codex/.workspace/`.

- `manifests/`: work manifests generated for local execution
- `iterations/`: private iteration traces
- `working_surfaces/`: local scratch construction surfaces

Shared metabolic state and private execution traces must not be collapsed into one territory.

---

## XIX. Human Proxy Mode

`--human-proxy` allows the LLM to act as an authorised F_H substitute during unattended `--auto` runs.

- activation requires `--auto`
- each decision writes a proxy log before any approval event
- proxy approvals use `actor: "human-proxy"`
- proxy rejections halt the edge immediately

Humans remain the authority. Proxy decisions are provisional.

---

## XX. Bug Triage

Bugs during active development do not require a feature vector. The minimum viable artifact is a log entry. Post-mortem determines whether a formal feature or backlog item is warranted.
