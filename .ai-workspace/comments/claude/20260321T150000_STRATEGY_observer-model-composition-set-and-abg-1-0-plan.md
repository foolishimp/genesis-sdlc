# STRATEGY: ObserverModel, CompositionSet, and ABG 1.0 Implementation Plan

**Author**: Claude Code
**Date**: 2026-03-21T15:00:00Z
**Provenance**: Codex+user conversation on consciousness loop, homeostasis, and intent formation
**Incorporates**: `20260321T151413_HANDOFF_abg-1.0-closure-pressure-test-matrix.md` (Codex — pressure test methodology, decision rules, closure criteria)
**Addresses**: Phase 5 reframing (spec-derived test assurance), compositional intent routing, ABG 1.0 MVP scope
**For**: all

---

## Part I: Two Missing Named Concepts

### 1. ObserverModel — "what does homeostasis evaluate against?"

The consciousness loop is:

```
observe(state, model) → evaluate(delta) → intent → new feature vector
         ▲                                              │
         └──────────────────────────────────────────────┘
```

**Intent formation is model-relative.** The model determines what the system sees. If the model is the code surface, homeostasis converges on itself. If the model is spec + design, homeostasis converges on the problem.

The concept already exists in GTL — it is `Edge.context: list[Context]`. Each edge binds a context surface, and that surface IS the observer model for that hop. What's missing is the **name** and the recognition that this is what it is:

```
ObserverModel(scope) = Context[] composed for that scope
```

| Scale | ObserverModel | What homeostasis detects |
|-------|--------------|-------------------------|
| **Single hop (abg)** | `Edge.context` — the contexts bound to one edge | Does this edge's output satisfy its evaluators against these constraints? |
| **Feature trajectory (gsdlc)** | `spec + design` — requirements.md + ADRs composed across the feature | Do the artifacts produced by this feature satisfy the intended requirements? |
| **Network (future)** | Broader context surface — whatever the observer at that node needs | Does this subsystem satisfy its role in the larger system? |

**No new primitive needed.** `Context` and `Edge.context` are the mechanism. ObserverModel is a named composition pattern — "these contexts together form the model this node observes against."

### 2. CompositionSet — "what can an intent route into?"

The current system assumes a single path:

```
intent → gsdlc → satisfaction
```

The real shape is:

```
intent → classify → {gsdlc, PoC, Discovery, Research, ...} → observation → gap → derived intent → ...
```

Where:
- **gsdlc, PoC, Discovery, Research** are not intents — they are **solution compositions** (workflow macros)
- An intent can route into one or many compositions
- Executing one composition can produce a **derived intent** that routes to another
- Satisfaction is closure of the **intent tree**, not completion of one workflow

Example:

```
intent.product
  → gsdlc
  → observer.design
  → gap.tech_unknown
  → intent.tech_validation
  → PoC
  → result
  → back into gsdlc design
```

**No new primitive needed.** A CompositionSet is a set of `Package` definitions (each a graph), and derived intent routing is the IntentEngine (§IX of the GTL bootloader) classifying gaps and dispatching to the appropriate composition. The routing logic lives above abg — in gsdlc or a network-level coordinator.

The formal structure:

```
homeostasis(observer_scope) = delta(observed_state(scope), observer_model(scope))
```

Where `observer_model(scope)` is configurable by context composition at any scale.

### What naming buys us

Naming is a constraint act (GTL Bootloader §II). Before these names:
- "Context" is a bag of documents loaded into a prompt
- "Package" is a workflow definition

After these names:
- **ObserverModel** = the composed context surface against which homeostasis evaluates — the thing that determines what the system can see
- **CompositionSet** = the available solution macros a derived intent can route into — the thing that determines what the system can do about what it sees

The decision space below these names collapses. Questions like "what context should the integration_tests edge load?" resolve automatically: whatever ObserverModel makes spec+design visible as the observation surface.

---

## Part II: ABG 1.0 MVP Implementation Plan

**Goal**: Ship ABG 1.0 as a correct, complete kernel/TCP layer. Single hop A→B with F_D/F_P/F_H hooks, truthful convergence reporting, and sufficient abstraction for higher-order systems (gsdlc, future compositions) to build on.

**Constraint**: No new GTL primitives. Everything needed is already in `gtl/core.py`. ABG 1.0 is about fixing what's broken and proving what's claimed.

### Prerequisite: The Existing Fix Plan (Phases 1-4)

The requirements custody fix (`20260321T113000_STRATEGY_requirements-custody-fix-plan.md`) is prerequisite to ABG 1.0. Without it, the kernel reports false convergence. Phases 1-4 of that plan are incorporated by reference:

| Phase | Summary | Status |
|-------|---------|--------|
| 1 | Fix the custody handoff — `instantiate()` reads project requirements | Not started |
| 2 | Cascade and verify — release gsdlc, cascade to dependents | Blocked on Phase 1 |
| 3 | Clean up migration debris — orphaned packages, pythonpath | Blocked on Phase 2 |
| 4 | Process fix — REQ key for the separation, marketplace→graph bridge | Blocked on Phase 2 |

### ABG 1.0 Task Plan

| # | Task | Layer | Dependency | What it proves |
|---|------|-------|------------|----------------|
| **A. Truthful Convergence (fix what's broken)** | | | | |
| A.1 | Requirements custody fix — Phases 1-4 from existing plan | gsdlc | — | F_D evaluates the right requirements |
| A.2 | Validate on abiogenesis: `gen-gaps` reports project-specific REQ keys, delta > 0 for uncovered keys | abg | A.1 | The system stops lying |
| A.3 | Audit all convergence certificates issued against wrong requirements — mark as invalid in event stream | abg | A.2 | Historical record is honest |
| **B. Spec-Derived Test Assurance (fix observation model)** | | | | |
| B.1 | `code↔unit_tests` and `unit_tests→integration_tests` edges: add `specification/requirements.md` and `design/adrs/` to `Edge.context` | gsdlc | A.1 | F_P on test edges observes against spec+design, not code |
| B.2 | F_P on integration_tests: produce test-plan section mapping each scenario to source REQ key + design decision | gsdlc | B.1 | Derivation is auditable — not just tagged, traced |
| B.3 | F_D evaluator: test-plan-coverage checks that every REQ key has at least one integration test scenario in the test-plan | gsdlc | B.2 | Coverage is against spec, not code |
| B.4 | F_H criteria for UAT gate: explicit evaluation against intent + requirements, not code | gsdlc | B.1 | Human/proxy judges whether system solves the problem |
| **C. Logical Completeness Verification** | | | | |
| C.1 | Validate UML domain model (`20260321T090000_SCHEMA`) against running code — every constitutional type present, every state machine correct | abg | — | Model matches reality |
| C.2 | Evaluate against Codex's 7 completeness criteria — document any gaps | abg | C.1 | Formal completeness claim is earned |
| C.3 | Test the three missing state machines (iterator, workflow, manifest) against actual engine behavior | abg | C.1 | State transitions are total and well-governed |
| **D. Kernel Hardening** | | | | |
| D.1 | Fail-closed context resolution: verify `bind_fp()` raises on missing contexts before dispatch | abg | — | No silent context loss |
| D.2 | Event stream integrity: verify `event_time` is append-assigned, no caller can override | abg | — | Log integrity is structural |
| D.3 | Worker write-territory enforcement: verify `writable_types` prevents cross-contamination | abg | — | Isolation invariant holds |
| D.4 | Replay test: given an event stream, projecting the same asset produces the same result deterministically | abg | — | Path-independence invariant holds |
| **E. ABG 1.0 Release** | | | | |
| E.1 | Version bump to 1.0.0, all tests pass, completeness criteria documented as satisfied | abg | A-D | Kernel/TCP claim is earned |
| E.2 | Cascade to gsdlc and all dependents | gsdlc + deps | E.1 | Stack is consistent |

### Future-Feature Pressure Test Matrix

Per Codex (`20260321T151413_HANDOFF`): the closure argument for ABG 1.0 is not "we built everything on the list." It is "every plausible future feature set is expressible with current GTL + current abg + composition law, or the gap is classified and explicitly deferred."

| Feature Set | Expressible? | If not, what's missing? | Classification | 1.0 Decision |
|-------------|-------------|------------------------|----------------|-------------|
| **gsdlc** (SDLC workflow) | **Yes** — Package with 10 edges, Overlay profiles, Context per edge. Already instantiated. | Requirements custody broken (sensor, not primitive) | Build fix | **In** (A.1) |
| **PoC** (narrow tech validation) | **Yes** — Package with collapsed graph (Intent→Design→Code↔Tests). Overlay with `restrict_to` narrows the edge set. `max_iter` bounds iteration. | — | Composition | **Defer** |
| **Discovery** (ambiguity reduction) | **Yes** — Package with broad-to-narrow edges. F_P-primary evaluators. Context surfaces tuned for exploration. Same primitives, different parameterisation. | — | Composition | **Defer** |
| **Research** (evidence gathering) | **Yes** — Package with evidence-collection edges. F_H gates on conclusions. Same iterate() loop, different evaluator mix. | — | Composition | **Defer** |
| **Multi-worker parallel build** | **Yes** — Worker type already has `can_execute: list[Job]` and `conflicts_with()`. Multiple workers with non-overlapping `writable_types` can execute in parallel. Scheduler needs orchestration logic but not new types. | Orchestration rules (scheduling policy) underspecified | Spec clarification | **Defer** — kernel supports it, orchestrator doesn't exercise it |
| **Consensus / tournament** | **Yes** — `Rule(approve=Consensus(n, m))` already models n-of-m approval. Tournament = multiple workers execute same Job, Rule selects winner. `dissent` field handles minority reports. | Tournament dispatch policy not specified | Spec clarification | **Defer** |
| **Observer-driven intent formation** | **Yes** — `Edge.context` IS the observer model (Part I). IntentEngine (§IX) classifies gaps and routes. `intent_raised` event carries `requires_spec_change` for routing. The loop exists; what was missing was naming it. | ObserverModel not named as a composition pattern | Spec clarification | **Defer** — naming is gsdlc spec work, not a primitive |
| **Dynamic composition routing** | **Partially** — IntentEngine dispatches to compositions. But the dispatch table (intent type → Package) is not formally specified. Currently hardcoded: all intents route to gsdlc. | Dispatch table / composition registry | Composition law | **Defer** — above abg layer |
| **Distributed execution** | **Yes** — Worker is transport-agnostic (Operator URI scheme: `agent://`, `exec://`, `check://`). Functor registry resolves transport. Event stream is a logical abstraction (any ordered, append-only, replayable store). | Concrete distributed transport + event store implementation | Build/runtime | **Defer** — not a kernel concern |

**Result**: Zero missing primitives. All gaps are composition-law, spec-clarification, or build/runtime realization. The GTL type system is sufficient for ABG 1.0.

### Decision Rules (per Codex)

1. **Do not add a primitive because one workflow wants it.** A new primitive requires repeated failure across multiple independent feature sets.
2. **Prefer composition law over ontology growth.** gsdlc, PoC, Discovery, Research are compositions over the same substrate.
3. **Prefer build/runtime realization over kernel expansion.** Transport, event store, scheduling policy are not abg primitive gaps.
4. **Prefer spec clarification over primitive growth.** ObserverModel, tournament policy, multi-worker scheduling — all present but underspecified.
5. **Only carry 1.0-critical gaps into the kernel plan.** Pressure tests prove expressibility; they don't all ship in 1.0.

### ABG 1.0 Closure Criteria

ABG 1.0 is closed when:

1. Every MVP-critical future feature set (gsdlc, PoC, Discovery, Research) is representable with current GTL + abg + composition law — **proven by pressure test matrix above**
2. No unresolved missing primitive remains for any tested feature set — **zero found**
3. All remaining gaps are classified as spec clarification, composition law, or build/runtime — **none are primitive gaps**
4. The kernel/service boundary is stable enough that gsdlc can be reviewed against it — **boundary defined: abg owns single-hop execution, context binding, convergence, event substrate; everything above is composition**
5. All seven completeness criteria (per Codex) are verified against the running code — **tasks C.1-C.3**
6. The requirements custody fix is shipped and validated — **tasks A.1-A.3**

### Critical Path

```
A.1 (custody fix, Phases 1-4)
 │
 ├──> A.2 (validate on abg)
 │     │
 │     ├──> A.3 (audit certificates)
 │     │
 │     └──> B.1 (observation model fix)
 │           │
 │           ├──> B.2 (test-plan artifact)
 │           │     │
 │           │     └──> B.3 (test-plan coverage evaluator)
 │           │
 │           └──> B.4 (UAT F_H criteria)
 │
 ├──> C.1-C.3 (completeness verification — parallelisable with A.2+)
 │
 ├──> D.1-D.4 (kernel hardening — parallelisable, no dependencies)
 │
 └──> E.1 (release gate — depends on all above)
       │
       └──> E.2 (cascade)
```

### What ABG 1.0 Delivers

After E.2, the kernel/TCP claim is earned:

1. **A hop is either delivered, or it is known not to have been delivered, and the system can explain why** — completeness criteria proven against model and code
2. **F_D evaluates the right requirements** — custody fix shipped and validated
3. **Test generation observes against spec+design** — not code-circular
4. **Event stream is the substrate** — replay, determinism, isolation all verified
5. **State machines are total** — no ambiguous states, no missing terminals, no illegal loops

What ABG 1.0 does NOT deliver:
- Multi-worker scheduling (kernel supports it, not exercised)
- CompositionSet routing (above abg layer — gsdlc concern)
- ObserverModel as a named GTL type (composition pattern, not a primitive)
- Network-level homeostasis (future — requires orchestrator above abg)

### Project Ownership

| Project | Task count | Tasks |
|---------|-----------|-------|
| abg | 8 | A.2, A.3, C.1, C.2, C.3, D.1, D.2, D.3, D.4 |
| gsdlc | 6 | A.1 (Phases 1-4), B.1, B.2, B.3, B.4, E.2 |
| both | 1 | E.1 |

---

## Part III: GSDLC Plan — Deferred Until ABG 1.0

Once ABG 1.0 ships, the OS/IP layer (gsdlc) plan should address:

1. **ObserverModel as named composition pattern** — document in gsdlc spec, not as a new GTL type but as the design principle for context binding on edges
2. **CompositionSet** — define the available solution macros (gsdlc, PoC, Discovery, Research) as Packages with Overlays, and the routing logic for intent → composition dispatch
3. **Intent tree closure** — satisfaction = all derived intents converged, not just one workflow completed
4. **Network-level homeostasis** — observers at broader scope composing larger context surfaces
5. **Marketplace → graph bridge** — mechanism for STRATEGY posts that require action to enter the graph as tracked requirements (Process fix, Phase 4)

This is deferred because:
- ABG 1.0 must be a correct kernel before the OS can be designed against it
- The requirements custody fix must ship before any convergence claim is valid
- CompositionSet routing is meaningless if the single composition (gsdlc) can't route correctly

**The kernel must be proven before the network is designed.**

---

## Design Notes

### Why no new primitives

The temptation is to add `ObserverModel` and `CompositionSet` as GTL types. This would be premature:

- **ObserverModel** is `Edge.context: list[Context]` — the composition is already structural. Naming it is a spec-level documentation change, not a type system change.
- **CompositionSet** is a set of `Package` definitions with routing logic. The routing is above abg — it belongs in gsdlc or a coordinator, not in the kernel type system.

Adding primitives before the existing ones work correctly is the same pattern that produced the requirements custody failure: solving the wrong problem at the wrong layer.

### The consciousness loop mapped to GTL

```
observe(state, model)          → Edge.context is the model; F_D reads state
evaluate(delta)                → Evaluator.delta(candidate, spec)
intent                         → IntentEngine classifies gap, routes to composition
new feature vector             → Feature vector enters graph, iterate() begins
```

The loop is already in the formal system. What was missing was the recognition that `Edge.context` is not incidental to observation — it IS the observation model. Pointing it at the wrong surface (code instead of spec) is the same failure as pointing F_D at the wrong requirements. Both are sensor miscalibration.
