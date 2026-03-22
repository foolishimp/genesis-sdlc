# GTL Bootloader: Universal Constraint Context

**Version**: 1.0.1
**Domain-agnostic.** Domain packages (SDLC, data pipeline, etc.) extend this — they do not replace it.

---

## Primitives

| Primitive | What it is |
|-----------|-----------|
| **Graph** | Topology of typed assets with admissible transitions |
| **Iterate** | `iterate(job, evaluator_fn, asset) → (Asset, WorkingSurface)` — the only operation |
| **Evaluators** | Convergence tests: F_D (deterministic), F_P (agent), F_H (human) |
| **Spec + Context** | Constraint surface — what bounds construction |

GTL types: Package, Asset, Edge, Job, Worker, Evaluator, Operator, Rule, Context. Everything else is parameterisation.

## Evaluators and Escalation

| Evaluator | Regime | What it does |
|-----------|--------|-------------|
| **F_D** | Zero ambiguity | Pass/fail — tests, schema checks, tag verification |
| **F_P** | Bounded ambiguity | Agent disambiguates — gap analysis, code generation |
| **F_H** | Persistent ambiguity | Human judgment — approval, rejection |

Escalation: F_D → F_P (deterministic blocked). F_P → F_H (agent stuck). F_H → F_D (approved → deploy).

## Event Stream

- Assets are projections: `Asset<Tn> := project(EventStream[0..n], asset_type, instance_id)`
- **Determinism**: `project(S, T, I) = project(S, T, I)` always.
- **emit() is the only write path.** event_time is system-assigned at append.
- **F_P does NOT call the event logger.** F_P produces artifacts; F_D reads them and emits events.
- Recovery is replay. No state lost beyond current iterate() call.

## Gradient

`delta(state, constraints) → work`. When delta = 0, system is at rest. Same computation at every scale — single iteration, edge convergence, feature traversal, production.

## Territories

| Territory | What | Rule |
|-----------|------|------|
| `.genesis/` | ABG engine (installed) | **Never edit directly.** Updated only by ABG installer. |
| `.gsdlc/release/` | Domain package (installed) | **Never edit directly.** Updated only by domain installer. |
| `specification/` | Authored spec | Editable — intent, requirements, standards. |
| `builds/` | Authored source | Editable — implementation, tests, design. |
| `.ai-workspace/` | Runtime state | Events, features, comments — territory-partitioned by agent. |

## Cascade Chain

Source → installer → installed territory. Order: **ABG → GSDLC → dependents** (never ABG direct to dependents).

## F_P Dispatch Contract

The manifest JSON at `fp_manifest_path` is the authoritative dispatch contract. It carries structured fields (source/target assets, markov conditions, evaluators, contexts, delta). The prompt field is a human-readable render. CLAUDE.md is transport convenience — the manifest must be sufficient alone.

## Invariants

| Invariant | What breaks if absent |
|-----------|----------------------|
| Graph with typed transitions | No structure — ad hoc work |
| Iterate loop producing events | No quality signal — one-shot |
| At least one evaluator per edge | No stopping condition |
| Spec + Context bounds construction | Degeneracy, hallucination |
| Event stream — append-only, no timestamp override | No replay, no recovery |
| Completeness visibility before downstream | Silent convergence — untrusted |
