# SCHEMA: Abiogenesis Engine — UML Domain Model, State, and Sequence Diagrams

**Author**: Claude Code
**Date**: 2026-03-21T09:00:00Z
**Revised**: 2026-03-21T11:30:00Z (r4: iterator INSPECT corrected to "first unconverged job in topological order" per convergence_model.md and commands.py:234; r3: fail-closed context handling corrected — bind_fd records missing_contexts, bind_fp raises before dispatch, iterator state machine now shows BIND_FP as separate state with error branch, sequence diagram adds ALT path; r2: Overlay + PackageSnapshot added, EventStream abstracted, F_P sequence build-neutral; r1: seven completeness criteria, GTL as SDK+IR, four-layer stack, three state machines)
**Addresses**: Logical completeness verification of abg (kernel/TCP layer); GTL as SDK+IR
**For**: all

## Purpose

Abiogenesis is the kernel — it guarantees A->B traversal with hooks for F_D, F_P, F_H. GTL is the SDK and IR (intermediate representation) — the portable type system that defines what A, B, edges, evaluators, and contexts are. Any runtime that interprets GTL is a valid engine. This post captures the complete domain model, state machines, and sequence diagrams so that all possible paths can be formally reasoned about.

## Logical Stack

```
Spec layer       Domain model and behavioral invariants (natural language, formal logic)
                      │
GTL layer        Typed SDK/IR encoding invariants as executable graph structure (gtl/core.py)
                      │
abg layer        Reference runtime interpreting GTL workflows (genesis/)
                      │
Build layer      Concrete realizations — Claude, Codex, AWS-native, distributed (builds/)
```

GTL is not the runtime. It is the semantic construction kit. Abiogenesis executes GTL definitions. Builds realize them for specific tenants. gsdlc is a Build-layer artifact providing SDLC-specific graph instantiation.

## Seven Completeness Criteria (per Codex)

| # | Criterion | SCHEMA section |
|---|-----------|----------------|
| 1 | Every first-class runtime concept is represented in the domain model | I |
| 2 | Every legal state transition is explicit | II, IIa, IIb, III |
| 3 | Every illegal transition is forbidden by model or guard | IIa (guards), IX |
| 4 | Every terminal outcome is distinguishable | VII |
| 5 | Every decision point has an evidence surface | IV, V, VI |
| 6 | Every emitted event corresponds to a modeled state change | II, III |
| 7 | Every workflow path can be traced from authored constraint to observed runtime outcome | VIII, X |

---

## I. Domain Model (Class Diagram)

GTL types are the SDK. Abiogenesis runtime types are the kernel.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         GTL SDK (gtl/core.py)                          │
│                                                                        │
│  ┌──────────────┐         ┌──────────────┐        ┌──────────────┐    │
│  │   Package     │────────>│    Asset      │        │   Operator    │    │
│  │──────────────│  *      │──────────────│        │──────────────│    │
│  │ name         │         │ name         │        │ name         │    │
│  │ requirements │         │ id_format    │        │ category: F_ │    │
│  │──────────────│         │ markov[]     │        │ uri          │    │
│  │ _validate()  │         │ operative?   │        └──────────────┘    │
│  │ to_mermaid() │         │ lineage[]*───┤                            │
│  └──────┬───────┘         └──────────────┘                            │
│         │                                                              │
│         │  *        ┌──────────────┐         ┌──────────────┐         │
│         ├──────────>│    Edge       │────────>│    Context    │         │
│         │           │──────────────│  *      │──────────────│         │
│         │           │ name         │         │ name         │         │
│         │           │ source: A|[A]│         │ locator      │         │
│         │           │ target: A    │         │ digest       │         │
│         │           │ co_evolve    │         └──────────────┘         │
│         │           │ using[]*─────┤──> Operator                      │
│         │           │ rule?────────┤──> Rule                          │
│         │           └──────────────┘                                   │
│         │                                                              │
│         │  *        ┌──────────────┐         ┌──────────────┐         │
│         ├──────────>│    Rule       │         │  Consensus    │         │
│         │           │──────────────│────────>│──────────────│         │
│         │           │ name         │         │ n (required)  │         │
│         │           │ dissent      │         │ m (total)     │         │
│         │           │ provisional  │         └──────────────┘         │
│         │           └──────────────┘                                   │
│         │                                                              │
│         │           ┌──────────────┐                                   │
│         └──────────>│  Evaluator   │                                   │
│            *        │──────────────│                                   │
│                     │ name         │                                   │
│                     │ category: F_ │                                   │
│                     │ description  │                                   │
│                     │ command      │  (F_D only)                       │
│                     └──────────────┘                                   │
│                                                                        │
│  ┌──────────────┐         ┌──────────────┐                            │
│  │    Job        │────────>│    Edge       │                            │
│  │──────────────│         └──────────────┘                            │
│  │ evaluators[] │────────> Evaluator                                   │
│  │──────────────│                                                      │
│  │ source_type  │  (derived from edge)                                │
│  │ target_type  │  (derived from edge)                                │
│  └──────────────┘                                                      │
│                                                                        │
│  ┌──────────────┐                                                      │
│  │   Worker      │                                                      │
│  │──────────────│                                                      │
│  │ id           │                                                      │
│  │ can_execute[]│────────> Job                                         │
│  │──────────────│                                                      │
│  │ writable_types│ (derived)                                           │
│  │ readable_types│ (derived)                                           │
│  │ conflicts_with()│                                                   │
│  └──────────────┘                                                      │
│                                                                        │
│  ┌──────────────┐         ┌──────────────────┐                        │
│  │   Overlay     │         │ PackageSnapshot   │                        │
│  │──────────────│         │──────────────────│                        │
│  │ name         │         │ snapshot_id       │                        │
│  │ on: Package  │         │ package_name      │                        │
│  │ restrict_to? │         │ version           │                        │
│  │ add_assets[] │         │ activated_at      │                        │
│  │ add_edges[]  │         │ activated_by      │                        │
│  │ add_operators│         │──────────────────│                        │
│  │ add_rules[]  │         │ to_dict()         │                        │
│  │ add_contexts │         │ work_binding()    │                        │
│  │ max_iter?    │         └──────────────────┘                        │
│  │ approve?     │                                                      │
│  └──────────────┘  Overlay extends/restricts a Package (profiles)     │
│                    PackageSnapshot is a runtime projection (governance)│
│                                                                        │
│  Functor Categories:  F_D (deterministic)                              │
│                       F_P (probabilistic/agent)                        │
│                       F_H (human)                                      │
│                                                                        │
│  Governance:  OPERATIVE_ON_APPROVED                                    │
│               OPERATIVE_ON_APPROVED_NOT_SUPERSEDED                     │
│                                                                        │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                   Abiogenesis Kernel (genesis/)                         │
│                                                                        │
│  ┌──────────────────┐    ┌──────────────────┐                         │
│  │   EventStream     │    │ ContextResolver   │                         │
│  │  (logical abs.)   │    │──────────────────│                         │
│  │──────────────────│    │ workspace_root    │                         │
│  │ workflow_version  │    │──────────────────│                         │
│  │──────────────────│    │ load(ctx) -> str  │                         │
│  │ append(type, data)│    │ _verify_digest()  │                         │
│  │  -> record        │    └──────────────────┘                         │
│  │ all_events()      │                                                  │
│  │  -> list[record]  │    Any ordered, append-only, replayable store   │
│  │ replay()          │    satisfies the EventStream contract:          │
│  │  -> dict          │    file, Kafka, database WAL, event store.      │
│  └──────────────────┘    Backend is a design choice per build.         │
│                                                                        │
│  ┌──────────────────┐    ┌──────────────────┐                         │
│  │PrecomputedManifest│    │    BoundJob       │                         │
│  │──────────────────│    │──────────────────│                         │
│  │ job: Job          │    │ job: Job          │                         │
│  │ current_asset     │    │ precomputed       │                         │
│  │ failing_evaluators│    │ prompt: str       │                         │
│  │ passing_evaluators│    │ result_path       │                         │
│  │ fd_results        │    └──────────────────┘                         │
│  │ relevant_contexts │                                                  │
│  │ delta_summary     │    ┌──────────────────┐                         │
│  │──────────────────│    │  WorkingSurface   │                         │
│  │ has_gap -> bool   │    │──────────────────│                         │
│  │ delta -> float    │    │ events[]          │                         │
│  └──────────────────┘    │ artifacts[]       │                         │
│                           │ context_consumed[]│                         │
│  ┌──────────────────┐    └──────────────────┘                         │
│  │     Scope         │                                                  │
│  │──────────────────│                                                  │
│  │ package: Package  │                                                  │
│  │ workspace_root    │                                                  │
│  │ feature?          │                                                  │
│  │ edge?             │                                                  │
│  │ worker?           │                                                  │
│  │ workflow_version  │ (derived from active-workflow.json)              │
│  └──────────────────┘                                                  │
│                                                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

### Relationship Summary

```
Package  1──* Asset       (nodes in the graph)
Package  1──* Edge        (admissible transitions)
Package  1──* Operator    (execution capabilities)
Package  1──* Rule        (consensus policies)
Package  1──* Context     (constraint documents)
Package  1──* Overlay     (extension/restriction profiles)
Package  1──* Evaluator   (convergence tests, via edges)
Edge     *──1 Asset       (source)
Edge     *──1 Asset       (target)
Edge     *──* Operator    (using)
Edge     *──* Context     (constraint surface for this transition)
Edge     *──0..1 Rule     (approval policy)
Asset    *──* Asset       (lineage — DAG, not tree)
Overlay  *──1 Package     (extends/restricts this package)
Job      1──1 Edge        (the transition being iterated)
Job      1──* Evaluator   (convergence tests for this edge)
Worker   1──* Job         (execution capability)

PackageSnapshot  ──  runtime projection of Package at activation time
                     (not a composition relationship — a governance artifact)
```

---

## II. State Diagram — Edge Iteration Lifecycle

An edge transitions through states as the kernel iterates toward convergence.

```
                        ┌─────────────┐
                        │  NOT_STARTED │
                        └──────┬──────┘
                               │
                         gen_iterate() called
                         emit: edge_started
                               │
                        ┌──────▼──────┐
                   ┌───>│  EVALUATING  │<──────────────────────────┐
                   │    └──────┬──────┘                            │
                   │           │                                    │
                   │     bind_fd() runs all evaluators              │
                   │           │                                    │
                   │    ┌──────▼──────┐                            │
                   │    │ delta > 0?  │──── No ────────────┐       │
                   │    └──────┬──────┘                    │       │
                   │           │ Yes                        │       │
                   │           │                            │       │
                   │    ┌──────▼──────┐              ┌─────▼─────┐ │
                   │    │CLASSIFY FAIL│              │ CONVERGED  │ │
                   │    └──────┬──────┘              │           │ │
                   │           │                      │emit:      │ │
                   │    ┌──────┴──────┬───────┐      │edge_      │ │
                   │    │             │       │      │converged  │ │
                   │    ▼             ▼       ▼      └───────────┘ │
                   │ ┌────────┐ ┌────────┐ ┌────────┐             │
                   │ │ FD_GAP │ │FP_NEED │ │FH_GATE │             │
                   │ │        │ │        │ │        │             │
                   │ │emit:   │ │emit:   │ │emit:   │             │
                   │ │found   │ │fp_     │ │fh_gate_│             │
                   │ │        │ │dispatch│ │pending │             │
                   │ │exit: 4 │ │ed      │ │        │             │
                   │ └────────┘ │exit: 2 │ │exit: 3 │             │
                   │            └───┬────┘ └───┬────┘             │
                   │                │          │                   │
                   │         ┌──────▼──────┐   │                   │
                   │         │  F_P ACTOR   │   │                   │
                   │         │  (external)  │   │                   │
                   │         │             │   │                   │
                   │         │writes JSON  │   │                   │
                   │         │assessment   │   │                   │
                   │         └──────┬──────┘   │                   │
                   │                │          │                   │
                   │         skill reads       │                   │
                   │         result, calls     │                   │
                   │         emit-event        │                   │
                   │         assessed{fp,pass} │                   │
                   │                │          │                   │
                   │                │    ┌─────▼──────┐            │
                   │                │    │HUMAN REVIEW│            │
                   │                │    │            │            │
                   │                │    │  approve   │            │
                   │                │    │  or reject │            │
                   │                │    └─────┬──────┘            │
                   │                │          │                   │
                   │                │   emit-event                 │
                   │                │   approved{fh_review}        │
                   │                │          │                   │
                   └────────────────┴──────────┘                   │
                         re-enter gen_iterate()                    │
                         (or auto-loop continues)                  │
                                                                   │
                   ┌───────────────────────────────────────────────┘
                   │
            REVOCATION (at any time after convergence):
                   │
            ┌──────▼──────────┐
            │ revoked{kind}   │
            │                 │
            │ fh_approval  ───┤──> operative(edge) terminated
            │ fp_assessment───┤──> certified(edge,ev) terminated
            └──────┬──────────┘
                   │
                   │ delta recomputed > 0
                   │
                   └──> Edge re-enters EVALUATING
```

### Evaluator Category Precedence (within CLASSIFY FAIL)

```
Priority:  F_D > F_P > F_H

If ANY F_D failing:
  → FD_GAP (exit 4) — deterministic block, cannot proceed

Else if ANY F_P failing:
  → FP_NEED (exit 2) — dispatch to agent

Else if ANY F_H failing:
  → FH_GATE (exit 3) — wait for human
```

This ordering is the kernel's core guarantee: **F_D gates F_P gates F_H.** No probabilistic evaluation until deterministic checks pass. No human gate until agent construction passes.

---

## III. State Diagram — Event Calculus Fluents

Two fluents govern edge convergence state:

### Fluent: operative(edge, workflow_version)

```
                    ┌──────────────┐
                    │  NOT HOLDING  │
                    └───────┬──────┘
                            │
                     approved{kind: fh_review}
                     approved{kind: fh_intent}
                            │
                    ┌───────▼──────┐
                    │   HOLDING     │  holdsAt(operative(edge, wv), now)
                    └───────┬──────┘
                            │
                     revoked{kind: fh_approval}
                     (matching edge, workflow_version)
                            │
                    ┌───────▼──────┐
                    │  TERMINATED   │
                    └───────┬──────┘
                            │
                     approved{kind: fh_review}  (re-approval)
                            │
                    ┌───────▼──────┐
                    │   HOLDING     │  (restored)
                    └──────────────┘
```

### Fluent: certified(edge, evaluator, spec_hash, workflow_version)

```
                    ┌──────────────┐
                    │  NOT HOLDING  │
                    └───────┬──────┘
                            │
                     assessed{kind: fp, result: pass, spec_hash: H}
                            │
                    ┌───────▼──────┐
                    │   HOLDING     │  holdsAt(certified(edge, ev, H, wv), now)
                    └───────┬──────┘
                            │
                    ┌───────┴───────────────────┐
                    │                           │
             revoked{kind:              spec_hash changed
             fp_assessment}             (identity invalidation)
             (event calculus            H_new != H_old
              termination)                      │
                    │                           │
                    ▼                           ▼
            ┌──────────────┐           ┌──────────────┐
            │  TERMINATED   │           │  INVALIDATED  │
            │  (explicit)   │           │  (identity)   │
            └──────────────┘           └──────────────┘

Both paths → delta > 0 → re-evaluation required
```

### Fluent Independence Invariant

```
operative(edge, wv) ⊥ certified(edge, ev, H, wv)

revoked{kind: fh_approval}  affects ONLY operative
revoked{kind: fp_assessment} affects ONLY certified

They are independent state machines on the same edge.
An edge converges when ALL of:
  - All F_D evaluators pass (recomputed each iteration)
  - All F_P evaluators: certified holds
  - All F_H evaluators: operative holds
```

---

## IIIa. State Diagram — Iterator (Formal State Machine)

The iterator is the kernel's core control loop. Each state has explicit guards and exactly one successor.

```
                    ┌──────────┐
                    │   IDLE    │
                    └─────┬────┘
                          │
                    gen_iterate() called
                    guard: scope has jobs
                          │
                    ┌─────▼────┐
                    │ INSPECT   │  select first unconverged job in topological order
                    └─────┬────┘
                          │
                    guard: job selected (delta > 0)
                    [else: → IDLE (nothing_to_do)]
                          │
                    ┌─────▼────┐
                    │ BIND_FD   │  run all F_D evaluators
                    │           │  check F_H operative
                    │           │  check F_P certified
                    │           │  resolve contexts (records missing)
                    └─────┬────┘
                          │
                    guard: PrecomputedManifest assembled
                    (always succeeds — missing contexts recorded,
                     not raised here)
                          │
                    ┌─────▼────┐
                    │  DECIDE   │  classify failing evaluators
                    └─────┬────┘
                          │
              ┌───────────┼───────────┬───────────┐
              │           │           │           │
        guard: F_D   guard: F_P  guard: F_H  guard: none
        failing      failing     failing     failing
              │           │           │           │
        ┌─────▼────┐┌────▼─────┐┌────▼─────┐┌────▼──────┐
        │ FD_GAP   ││ BIND_FP  ││ FH_GATE  ││ CONVERGE  │
        │          ││          ││          ││           │
        │emit:     ││guard:    ││emit:     ││emit:      │
        │found     ││missing_  ││fh_gate_  ││edge_      │
        │          ││contexts  ││pending   ││converged  │
        │exit: 4   ││empty?    ││exit: 3   ││exit: 0    │
        └──────────┘└─────┬────┘└──────────┘└───────────┘
              │           │           │           │
              │     ┌─────┴─────┐     │           │
              │     │           │     │           │
              │   yes          no     │           │
              │     │           │     │           │
              │ ┌───▼──────┐ ┌─▼────────┐        │
              │ │ DISPATCH │ │  ERROR    │        │
              │ │ _FP      │ │          │        │
              │ │          │ │bind_fp() │        │
              │ │emit:     │ │raises    │        │
              │ │edge_     │ │FileNot   │        │
              │ │started   │ │Found     │        │
              │ │then      │ │          │        │
              │ │fp_       │ │exit: 1   │        │
              │ │dispatched│ │no edge_  │        │
              │ │exit: 2   │ │started   │        │
              │ └──────────┘ └──────────┘        │
              │       │           │               │
              ▼       ▼           ▼               ▼
           TERMINAL BLOCKED    TERMINAL        TERMINAL
           (fix)   (await F_P) (fix context)   (done)

ILLEGAL TRANSITIONS (enforced by guards):
  - IDLE → DECIDE          (cannot skip INSPECT and BIND_FD)
  - BIND_FD → DISPATCH_FP  (cannot skip DECIDE and BIND_FP)
  - FD_GAP → BIND_FP       (F_D must pass before F_P dispatch)
  - BIND_FP → FH_GATE      (F_P must pass before F_H gate)
  - BIND_FP → DISPATCH_FP  (only if missing_contexts is empty)
  - Any state → CONVERGE   (only from DECIDE when all pass)
  - CONVERGE → any state   (terminal — re-entry requires new gen_iterate)
  - ERROR → DISPATCH_FP    (missing context blocks dispatch permanently)
```

### Auto-loop state machine (gen_start --auto)

```
                    ┌──────────┐
                    │  LOOPING  │  iteration_count = 0
                    └─────┬────┘
                          │
                    ┌─────▼────────┐
                    │ gen_iterate() │
                    └─────┬────────┘
                          │
              ┌───────────┼──────────┬──────────┬──────────┐
              │           │          │          │          │
         converged   fp_dispatched  fd_gap  fh_gate    iterated
         nothing_to_do              │      pending      │
              │           │          │          │          │
              ▼           ▼          ▼          │          ▼
           EXIT 0      EXIT 2     EXIT 4       │     iteration++
                                               │     guard: < 50
                                               │     [else: EXIT 5]
                                         ┌─────┴─────┐    │
                                         │--human-    │    │
                                         │proxy?      │    │
                                         └─────┬──────┘    │
                                          yes  │  no       │
                                          │    │           │
                                          │  EXIT 3       │
                                          │               │
                                          ▼               │
                                    proxy-evaluate        │
                                    emit approved         │
                                          │               │
                                          └───────┬───────┘
                                                  │
                                            ┌─────▼────────┐
                                            │ gen_iterate() │ (re-enter)
                                            └──────────────┘
```

---

## IIIb. State Diagram — Manifest/Assessment Provenance Lifecycle

A manifest is the F_P dispatch unit. Its lifecycle tracks whether construction work was requested, performed, and accepted.

```
                    ┌──────────────┐
                    │  NOT_EXISTS   │  no F_P gap detected
                    └───────┬──────┘
                            │
                      bind_fp() assembles prompt
                      writes manifest JSON to fp_manifests/
                            │
                    ┌───────▼──────┐
                    │   DRAFTED     │  PrecomputedManifest + prompt assembled
                    │               │  emit: fp_dispatched
                    └───────┬──────┘
                            │
                      F_P actor invoked (MCP / skill)
                      actor reads manifest
                            │
                    ┌───────▼──────┐
                    │  DISPATCHED   │  actor is working
                    └───────┬──────┘
                            │
                 ┌──────────┼──────────┐
                 │                     │
           actor writes           actor fails / times out
           result JSON            no result written
                 │                     │
          ┌──────▼──────┐       ┌──────▼──────┐
          │  COMPLETED   │       │   ORPHANED   │
          │              │       │              │
          │result_path   │       │no result at  │
          │has JSON      │       │result_path   │
          └──────┬──────┘       └──────────────┘
                 │
           skill reads result
           for each passing evaluator:
             emit assessed{kind: fp, result: pass, spec_hash: H}
                 │
          ┌──────▼──────┐
          │  ASSESSED    │  certified fluent initiated
          └──────┬──────┘
                 │
          ┌──────┴──────────────────┐
          │                         │
    spec_hash changes         revoked{kind:
    (identity invalidation)   fp_assessment}
          │                         │
   ┌──────▼──────┐           ┌──────▼──────┐
   │ INVALIDATED  │           │   REVOKED    │
   │              │           │              │
   │ new manifest │           │ new manifest │
   │ required     │           │ required     │
   └──────────────┘           └──────────────┘

ILLEGAL TRANSITIONS:
  - DRAFTED → ASSESSED       (cannot skip DISPATCHED — actor must do work)
  - ORPHANED → ASSESSED      (no result to assess)
  - REVOKED → ASSESSED       (must go through new DRAFTED → DISPATCHED cycle)
  - ASSESSED → DRAFTED       (cannot re-draft; new manifest is a new instance)

DETECTION:
  - ORPHANED: result_path does not exist after dispatch timeout
  - INVALIDATED: spec_hash in assessed event ≠ current job_evaluator_hash()
  - REVOKED: revoked{kind: fp_assessment} event with later event_time
```

---

## IIIc. State Diagram — Workflow Execution Lifecycle

The workflow is the aggregate state across all edges for a feature traversal. This is the level at which gsdlc operates — routing requirements through the full graph.

```
                    ┌──────────────┐
                    │ NOT_STARTED   │  no events for this feature
                    └───────┬──────┘
                            │
                      gen_start() called
                      first edge_started event
                            │
                    ┌───────▼──────┐
                    │    ACTIVE     │  at least one edge iterating
                    │               │  total_delta > 0
                    └───────┬──────┘
                            │
              ┌─────────────┼─────────────┬──────────────┐
              │             │             │              │
        all edges      F_D blocks    F_P/F_H blocks   version
        delta = 0      (exit 4)      (exit 2, 3)      changes
              │             │             │              │
       ┌──────▼──────┐ ┌───▼────────┐ ┌──▼─────────┐ ┌─▼───────────┐
       │  CONVERGED   │ │  FAILED     │ │  BLOCKED    │ │ SUPERSEDED   │
       │              │ │             │ │             │ │              │
       │all evaluators│ │F_D cannot   │ │waiting for  │ │new workflow  │
       │pass across   │ │pass — code/ │ │external     │ │version       │
       │all edges     │ │test/coverage│ │actor or     │ │invalidates   │
       │              │ │issue        │ │human        │ │assessments   │
       │feature moves │ │             │ │             │ │              │
       │to completed/ │ │operator     │ │resume when  │ │re-evaluate   │
       └──────────────┘ │must fix     │ │event arrives│ │with new hash │
                        └─────────────┘ └─────┬───────┘ └──────┬───────┘
                                              │                │
                                        event arrives    carry-forward
                                        (assessed or     resolves or
                                         approved)       full re-eval
                                              │                │
                                              └────────┬───────┘
                                                       │
                                                 ┌─────▼──────┐
                                                 │   ACTIVE    │ (re-enters)
                                                 └─────────────┘

REVOCATION (at any point after CONVERGED):
       ┌──────────────┐
       │  CONVERGED    │
       └───────┬──────┘
               │
         revoked{kind: fh_approval | fp_assessment}
         delta recomputed > 0
               │
       ┌───────▼──────┐
       │    ACTIVE     │  (re-enters iteration)
       └──────────────┘

TERMINAL STATES:
  - CONVERGED (stable — all evaluators pass, feature complete)
  - FAILED (terminal until operator intervenes — F_D block)

NON-TERMINAL BLOCKED STATES:
  - BLOCKED (waiting for external event — F_P actor or F_H human)
  - SUPERSEDED (version change — may auto-resolve via carry-forward)

ILLEGAL TRANSITIONS:
  - NOT_STARTED → CONVERGED    (cannot converge without iterating)
  - FAILED → CONVERGED         (cannot converge without fixing F_D)
  - BLOCKED → CONVERGED        (cannot converge without external event)
  - CONVERGED → FAILED         (revocation returns to ACTIVE, not FAILED)
```

### Workflow State Derivation

Workflow state is NOT stored — it is projected from the event stream:

```
project(stream, feature) → {
  status:
    NOT_STARTED   if no edge_started events for this feature
    CONVERGED     if all edges have edge_converged and no later revocation
    FAILED        if last gen_iterate returned fd_gap
    BLOCKED       if last gen_iterate returned fp_dispatched or fh_gate_pending
    ACTIVE        otherwise (edges iterating, delta > 0)
}
```

---

## IV. Sequence Diagram — gen_start --auto (Happy Path)

```
User          __main__      commands       bind           schedule       EventStream    F_P Actor
 │               │             │             │               │              │              │
 │  gen start    │             │             │               │              │              │
 │──────────────>│             │             │               │              │              │
 │               │ gen_start() │             │               │              │              │
 │               │────────────>│             │               │              │              │
 │               │             │             │               │              │              │
 │               │             │ ┌─LOOP (auto, max 50)──────────────────────────────────┐ │
 │               │             │ │           │               │              │              │
 │               │             │ │gen_iterate│               │              │              │
 │               │             │ │           │               │              │              │
 │               │             │ │bind_fd()  │               │              │              │
 │               │             │ │──────────>│               │              │              │
 │               │             │ │           │ project()     │              │              │
 │               │             │ │           │──────────────────────────────>│              │
 │               │             │ │           │ <─── asset ───────────────── │              │
 │               │             │ │           │               │              │              │
 │               │             │ │           │ run_fd_eval() │              │              │
 │               │             │ │           │ (subprocess)  │              │              │
 │               │             │ │           │               │              │              │
 │               │             │ │           │ bind_fh()     │              │              │
 │               │             │ │           │ (scan events) │              │              │
 │               │             │ │           │──────────────────────────────>│              │
 │               │             │ │           │ <─── events ─────────────────│              │
 │               │             │ │           │               │              │              │
 │               │             │ │           │bind_fp_cert() │              │              │
 │               │             │ │           │ (scan events) │              │              │
 │               │             │ │           │               │              │              │
 │               │             │ │           │ resolve ctx   │              │              │
 │               │             │ │           │ (load files)  │              │              │
 │               │             │ │           │               │              │              │
 │               │             │ │<──────────│               │              │              │
 │               │             │ │ PrecomputedManifest       │              │              │
 │               │             │ │ (missing_contexts may be  │              │              │
 │               │             │ │  non-empty — recorded,    │              │              │
 │               │             │ │  not raised here)         │              │              │
 │               │             │ │           │               │              │              │
 │               │             │ │ [if delta > 0]            │              │              │
 │               │             │ │           │               │              │              │
 │               │             │ │bind_fp()  │               │              │              │
 │               │             │ │──────────>│               │              │              │
 │               │             │ │           │               │              │              │
 │               │             │ │  ┌─ALT: missing_contexts non-empty──┐   │              │
 │               │             │ │  │ bind_fp() raises FileNotFoundError│   │              │
 │               │             │ │  │ NO edge_started emitted          │   │              │
 │               │             │ │  │ NO fp_dispatched emitted         │   │              │
 │               │             │ │  │ command returns exit 1 (error)   │   │              │
 │               │             │ │  └──────────────────────────────────┘   │              │
 │               │             │ │           │               │              │              │
 │               │             │ │<──────────│               │              │              │
 │               │             │ │ BoundJob (happy path only)│              │              │
 │               │             │ │           │               │              │              │
 │               │             │ │ append(edge_started)      │              │              │
 │               │             │ │─────────────────────────────────────────>│              │
 │               │             │ │           │               │              │              │
 │               │             │ │iterate()  │               │              │              │
 │               │             │ │──────────────────────────>│              │              │
 │               │             │ │           │               │              │              │
 │               │             │ │<──────────────────────────│              │              │
 │               │             │ │ WorkingSurface{fp_dispatched}            │              │
 │               │             │ │           │               │              │              │
 │               │             │ │ append(fp_dispatched)     │              │              │
 │               │             │ │─────────────────────────────────────────>│              │
 │               │             │ │           │               │              │              │
 │               │ <───────────│ │           │               │              │              │
 │ exit(2)       │             │ │           │               │              │              │
 │<──────────────│             │ └───────────────────────────────────────────────────────┘ │
 │               │             │             │               │              │              │
 │  (build-specific dispatch: F_P actor invoked via transport binding)     │              │
 │─────────────────────────────────────────────────────────────────────────────────────────>│
 │               │             │             │               │              │              │
 │               │             │             │               │              │  actor       │
 │               │             │             │               │              │  constructs  │
 │               │             │             │               │              │  artifacts + │
 │               │             │             │               │              │  assessment  │
 │               │             │             │               │              │<─────────────│
 │               │             │             │               │              │              │
 │  (F_D-controlled write path: orchestrator reads result, emits assessed) │              │
 │  emit-event --type assessed               │               │              │              │
 │──────────────>│             │             │               │              │              │
 │               │ validate governance       │               │              │              │
 │               │ append to stream          │               │              │              │
 │               │─────────────────────────────────────────────────────────>│              │
 │               │             │             │               │              │              │
 │  gen start (re-enter)       │             │               │              │              │
 │──────────────>│             │             │               │              │              │
 │               │ ... (loop continues until converged)      │              │              │
```

---

## V. Sequence Diagram — F_H Gate (with human-proxy)

```
User/Proxy    __main__      commands       bind           EventStream
 │               │             │             │               │
 │               │             │ gen_iterate  │               │
 │               │             │             │               │
 │               │             │ bind_fd()   │               │
 │               │             │────────────>│               │
 │               │             │<────────────│               │
 │               │             │ PrecomputedManifest         │
 │               │             │ (F_H failing)               │
 │               │             │             │               │
 │               │             │ iterate()   │               │
 │               │             │ → fh_gate_pending           │
 │               │             │             │               │
 │               │ <───────────│             │               │
 │ exit(3)       │             │             │               │
 │<──────────────│             │             │               │
 │               │             │             │               │
 │ [--human-proxy mode]        │             │               │
 │               │             │             │               │
 │ Evaluate criteria           │             │               │
 │ Write proxy-log             │             │               │
 │               │             │             │               │
 │ emit-event approved         │             │               │
 │──────────────>│             │             │               │
 │               │ validate    │             │               │
 │               │ (kind, edge, actor=human-proxy, proxy_log)│
 │               │─────────────────────────────────────────>│
 │               │             │             │               │
 │ gen start (re-enter)        │             │               │
 │──────────────>│             │             │               │
```

---

## VI. Sequence Diagram — Revocation (F_P and F_H)

```
Operator      __main__      EventStream       bind (next gen_gaps)
 │               │              │                    │
 │ emit-event    │              │                    │
 │ --type revoked│              │                    │
 │ kind=fp_assessment           │                    │
 │ edge=X        │              │                    │
 │──────────────>│              │                    │
 │               │ validate     │                    │
 │               │ append       │                    │
 │               │─────────────>│                    │
 │               │              │                    │
 │ gen gaps      │              │                    │
 │──────────────>│              │                    │
 │               │ gen_gaps()   │                    │
 │               │──────────────────────────────────>│
 │               │              │                    │
 │               │              │  bind_fp_certified()
 │               │              │  scans events:     │
 │               │              │  assessed{pass} at T1
 │               │              │  revoked{fp} at T2 │
 │               │              │  T2 > T1 →         │
 │               │              │  certified = FALSE  │
 │               │              │                    │
 │               │              │  → F_P evaluator   │
 │               │              │    now FAILING      │
 │               │              │  → delta > 0       │
 │               │<─────────────────────────────────│
 │ {delta: N}    │              │                    │
 │<──────────────│              │                    │
```

---

## VII. Complete Path Enumeration — All Exit States

The kernel has exactly **6 terminal states** for any invocation:

```
┌─────────────────────────────────────────────────────────┐
│                    gen_start()                            │
│                                                          │
│  Exit 0: CONVERGED                                       │
│    All evaluators pass. delta = 0.                       │
│    emit: edge_converged                                  │
│    Terminal: work complete.                               │
│                                                          │
│  Exit 0: NOTHING_TO_DO                                   │
│    No jobs in scope, or already converged.               │
│    Terminal: no work needed.                              │
│                                                          │
│  Exit 1: ERROR                                           │
│    Package/Worker resolution failed.                     │
│    Context resolution failed (FileNotFoundError).        │
│    Event stream corrupted.                               │
│    Invalid arguments.                                    │
│    Terminal: operator must fix.                           │
│                                                          │
│  Exit 2: FP_DISPATCHED                                   │
│    F_D passed. F_P failing.                              │
│    emit: fp_dispatched                                   │
│    Blocked: waiting for external F_P actor.              │
│    Resume: assessed{fp, pass} → re-enter gen_start.     │
│                                                          │
│  Exit 3: FH_GATE_PENDING                                 │
│    F_D passed. F_P passed. F_H failing.                  │
│    emit: fh_gate_pending                                 │
│    Blocked: waiting for human approval.                  │
│    Resume: approved{fh_review} → re-enter gen_start.    │
│                                                          │
│  Exit 4: FD_GAP                                          │
│    F_D failing after F_P resolved.                       │
│    emit: found{fd_gap}                                   │
│    Terminal: deterministic block. Operator must fix      │
│    underlying code/test/coverage issue.                  │
│                                                          │
│  Exit 5: MAX_ITERATIONS                                  │
│    Auto-loop hit 50 iterations without converging.       │
│    Terminal: operator must inspect.                       │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Path Matrix — What Can Follow What

```
         ┌──> Exit 0 (converged)        ── DONE
         │
         ├──> Exit 0 (nothing_to_do)    ── DONE
         │
START ───┼──> Exit 1 (error)            ── FIX, re-enter
         │
         ├──> Exit 2 (fp_dispatched)    ── F_P actor writes ── assessed ── re-enter
         │
         ├──> Exit 3 (fh_gate_pending)  ── human approves ── approved ── re-enter
         │                              ── human rejects  ── DONE (or iterate spec)
         │
         ├──> Exit 4 (fd_gap)           ── operator fixes code/tests ── re-enter
         │
         └──> Exit 5 (max_iterations)   ── operator inspects ── re-enter
```

### Within Auto-Loop — State Transitions

```
gen_iterate() can produce:
  converged       → stop loop, return exit 0
  nothing_to_do   → stop loop, return exit 0
  fp_dispatched   → stop loop, return exit 2
  fh_gate_pending → if --human-proxy: continue loop
                    else: stop loop, return exit 3
  fd_gap          → stop loop, return exit 4
  iterated        → continue loop (one step done, more work)
```

---

## VIII. GTL as SDK + IR — Four-Layer Logical Stack

GTL is both **SDK** (authoring interface for defining workflows) and **IR** (portable intermediate representation interpretable by any runtime). A GTL Package definition should be interpretable by Claude, Codex, or an AWS-native engine without modification.

```
┌────────────────────────────────────────────────────────────┐
│              Spec Layer (behavioral invariants)              │
│                                                             │
│  Defines:                                                   │
│    - What the system must do (natural language, formal logic)│
│    - Domain model and constraints                           │
│    - Completeness criteria                                  │
│    - Tolerances (measurable thresholds)                     │
│                                                             │
│  Encoding-independent. Could be expressed in any formalism. │
│                                                             │
└──────────────────────┬─────────────────────────────────────┘
                       │ encoded as
                       ▼
┌────────────────────────────────────────────────────────────┐
│                  GTL Layer (SDK + IR)                        │
│                          gtl/core.py                        │
│                                                             │
│  Declares (SDK):                                            │
│    - What a graph looks like (Package, Asset, Edge)         │
│    - What evaluation means (Evaluator, F_D/F_P/F_H)        │
│    - What execution means (Job, Worker, Operator)           │
│    - What constraints are (Context, Rule, Consensus)        │
│    - What governance means (Operative, PackageSnapshot)     │
│                                                             │
│  Encodes (IR):                                              │
│    - Portable workflow definitions                          │
│    - Runtime-agnostic graph topology                        │
│    - Evaluator contracts (not implementations)              │
│    - Same Package interpretable by any conformant engine    │
│                                                             │
│  Does NOT:                                                  │
│    - Execute anything                                       │
│    - Store state                                            │
│    - Make decisions                                         │
│    - Manage events                                          │
│                                                             │
└──────────────────────┬─────────────────────────────────────┘
                       │ interpreted by
                       ▼
┌────────────────────────────────────────────────────────────┐
│              Abiogenesis Layer (reference runtime)           │
│                          genesis/                           │
│                                                             │
│  Implements:                                                │
│    - Event stream (append-only state substrate)             │
│    - Projection (derive asset state from events)            │
│    - Binding (evaluate F_D, check F_H/F_P fluents)         │
│    - Scheduling (classify gaps, route to evaluator type)    │
│    - Commands (gen_start, gen_iterate, gen_gaps)            │
│    - Context resolution (load constraint documents)         │
│    - Event governance (validate prime events)               │
│                                                             │
│  Guarantees (kernel/TCP):                                   │
│    - A→B traversal completes or reports failure             │
│    - F_D gates F_P gates F_H (precedence)                  │
│    - Event stream is append-only, event_time is F_D        │
│    - Convergence is deterministic (same stream → same state)│
│    - Revocation terminates fluents symmetrically            │
│    - Every exit state is explicit and distinguishable       │
│    - Every hop is delivered or known to have failed         │
│                                                             │
└──────────────────────┬─────────────────────────────────────┘
                       │ realized by
                       ▼
┌────────────────────────────────────────────────────────────┐
│              Build Layer (concrete realizations)             │
│                          builds/                            │
│                                                             │
│  gsdlc (SDLC instantiation — OS/IP layer):                 │
│    - SDLC graph instantiation (Package with edges)          │
│    - Workflow versioning (immutable releases)               │
│    - Installer (three-layer model)                          │
│    - Operating standards                                    │
│    - Slash commands (gen-start skill with auto-loop)        │
│    - Feature vector management                              │
│    - Human-proxy evaluation protocol                        │
│                                                             │
│  gsdlc Guarantees (OS/IP):                                  │
│    - Full route x→y→z with observability                    │
│    - Requirement dropped into x morphs to z          [BROKEN]│
│    - F_D coverage checks enforce traceability        [BROKEN]│
│    - Project requirements visible to engine          [BROKEN]│
│                                                             │
│  Tenant builds (concrete workers):                          │
│    - builds/claude_code/  (Claude Code realization)         │
│    - builds/codex/        (Codex realization)               │
│    - builds/gemini/       (Gemini realization)              │
│    - builds/aws/          (future: AWS-native realization)  │
│                                                             │
│  Each build provides:                                       │
│    - F_P actor implementation (how the agent constructs)    │
│    - F_H protocol (how human gates are surfaced)            │
│    - Transport binding (MCP, API, CLI)                      │
│    - Tenant-specific write territory                        │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

### Layer Boundaries and Questions

| Question | Layer | Answer |
|----------|-------|--------|
| Is the spec complete? | Spec | Are all behavioral invariants stated with tolerances? |
| Is GTL expressive enough? | GTL | Can every spec invariant be encoded as a Package? |
| Is abg a correct interpreter? | abg | Does every GTL construct execute faithfully? |
| Is a given build a faithful realization? | Build | Does the tenant satisfy the evaluator contracts? |
| Can a requirement flow from x to z? | Build (gsdlc) | **Currently: NO — custody handoff broken** |

---

## IX. Invariants Checklist — Kernel Completeness

| # | Invariant | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Event stream append-only | OK | EventStream.append() — no mutation API |
| 2 | event_time system-assigned | OK | append() assigns from clock, no caller override |
| 3 | F_D gates F_P gates F_H | OK | schedule.iterate() classifies by priority |
| 4 | Projection determinism | OK | project() is pure function of stream |
| 5 | Job evaluators non-empty | OK | Job.__post_init__() validates |
| 6 | Worker can_execute non-empty | OK | Worker.__post_init__() validates |
| 7 | Context digest verified | OK | ContextResolver._verify_digest() |
| 8 | Fail-closed F_P dispatch on missing context | OK | bind_fd() records missing_contexts in manifest; bind_fp() raises FileNotFoundError before dispatch |
| 9 | F_H revocation terminates operative | OK | bind_fh() scans revoked{fh_approval} |
| 10 | F_P revocation terminates certified | OK | bind_fp_certified() scans revoked{fp_assessment} |
| 11 | Spec-hash invalidates certification | OK | bind_fp_certified() compares spec_hash |
| 12 | Event governance validation | OK | _validate_prime_event() + _emit_event_cmd() |
| 13 | Workflow version scoping | OK | bind_fh/bind_fp_certified check wv |
| 14 | F_P does not call emit | OK | Architectural — skill calls emit-event |
| 15 | Convergence = all evaluators pass | OK | gen_gaps() sums delta across all jobs |

### Kernel Gaps (if any)

| # | Concern | Status | Notes |
|---|---------|--------|-------|
| 1 | project() edge_started filtering | VERIFY | Does it correctly observe in-progress edges? |
| 2 | Concurrent worker scheduling | DEFERRED | schedule() exists but multi-worker not exercised |
| 3 | Carry-forward across workflow versions | VERIFY | Implemented but edge cases unclear |
| 4 | Event stream corruption recovery | MINIMAL | ValueError on parse, but no repair mechanism |

---

## X. Criterion #7 — End-to-End Traceability Analysis

Codex criterion #7: *"Every workflow path can be traced from authored constraint to observed runtime outcome."*

### The Path (as designed)

```
Human authors REQ key          specification/requirements.md
        │
        ▼
Package.requirements           gtl_spec/packages/{slug}.py (via instantiate())
        │
        ▼
check-req-coverage (F_D)       compares Package.requirements against feature vectors
        │
        ▼
Feature vector created         .ai-workspace/features/active/{feature}.yml
        │
        ▼
Edge iteration begins          gen_iterate() selects job, bind_fd() runs
        │
        ▼
check-impl-coverage (F_D)      scans code for # Implements: REQ-F-* tags
        │
        ▼
check-validates-coverage (F_D) scans tests for # Validates: REQ-F-* tags
        │
        ▼
F_P construction               agent writes code/tests with tags
        │
        ▼
F_H approval                   human reviews
        │
        ▼
edge_converged                 all evaluators pass, delta = 0
        │
        ▼
Feature complete               all edges converged for this feature
```

### Where It Breaks (current state)

```
Human authors REQ key          specification/requirements.md         ✓ WORKS
        │
        ▼
Package.requirements           instantiate() copies workflow's       ✗ BROKEN
                               hardcoded 33 keys, ignores project    (custody handoff)
                               requirements.md entirely
        │
        ▼
check-req-coverage (F_D)       checks 33 gsdlc keys, not project    ✗ WRONG TARGET
                               keys → reports delta=0 falsely
        │
        ▼
Feature vector                 satisfies: references gsdlc keys     ✗ WRONG KEYS
                               not project keys
        │
        ▼
check-impl-coverage (F_D)      checks 33 gsdlc keys against code    ✗ WRONG TARGET
                               project-specific tags unchecked
        │
        ▼
check-validates-coverage (F_D) checks 33 gsdlc keys against tests   ✗ WRONG TARGET
                               project-specific tags unchecked
        │
        ▼
edge_converged                 emitted against wrong requirements    ✗ INVALID
                               convergence certificate is false

BREAK POINT: step 2 — instantiate() ignores specification/requirements.md
CONSEQUENCE: everything downstream evaluates the wrong requirements
DETECTION: impossible from within the system — the sensor is miscalibrated
```

### What a Fixed Path Looks Like

```
Human authors REQ key          specification/requirements.md         ✓
        │
        ▼
instantiate() reads            parses REQ-F-* keys from              ✓ FIX HERE
specification/requirements.md  specification/requirements.md
        │
        ▼
Package.requirements           populated with project-specific keys  ✓
        │
        ▼
check-req-coverage (F_D)       checks PROJECT keys against features  ✓
        │
        ... (rest of chain is sound once the input is correct)
```

The kernel (abg) is correct — it faithfully executes whatever Package it receives. The break is at the Build layer (gsdlc) — `instantiate()` doesn't read the project's requirements. Fix `instantiate()` and criterion #7 is satisfied end-to-end.

---

## Recommended Action

1. **Ratify** Codex's seven completeness criteria as the formal standard for abg kernel correctness.
2. **Fix criterion #7** — `instantiate()` must read project requirements from `specification/requirements.md`. This is the single point of failure that breaks end-to-end traceability.
3. **Codex review**: Share this revised post for independent verification against the codebase. Any type, state, or transition missing from this model is a logical gap.
4. **Path coverage in tests**: Cross-reference the 6 exit states, 3 state machines (iterator, manifest, workflow), and 2 fluent state machines against the test suite. Every path should have at least one integration test.
5. **GTL SDK boundary**: Confirm that `gtl/core.py` contains NO runtime logic — it is purely declarative types. Any runtime behavior that leaked into GTL types is a boundary violation.
6. **Render to standard UML**: These ASCII diagrams capture the semantics. If formal UML tooling (PlantUML, Mermaid) is desired for wider review, this post provides the complete input.
