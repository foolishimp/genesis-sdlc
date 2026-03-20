# SDLC Bootloader: AI SDLC Instantiation of the GTL Formal System

**Version**: 1.0.0
**Purpose**: Domain-specific instantiation of the GTL formal system for software development lifecycle projects. This bootloader extends the universal GTL Bootloader (sections I–XI) with SDLC-specific graph topology, feature vectors, profiles, workspace territory, and bug triage. It is loaded by the genesis_sdlc installer — a non-SDLC GTL Package would use its own domain bootloader instead.

**Requires**: GTL Bootloader (universal axioms — four primitives, event stream, gradient, evaluators)

---

## XII. Completeness Visibility

Two questions must be answerable at any time: **"Did I get all the features?"** and **"Is it done?"**

### Feature Decomposition Convergence

The `requirements → feature_decomposition` edge converges when BOTH:

- **F_D (coverage)**: Every REQ-* key in requirements appears in the `satisfies:` field of at least one feature vector. Computable by grep — no LLM required.
- **F_H (approval)**: A human has explicitly approved the decomposition, dependency ordering, and MVP boundary.

F_D gates F_H — no human review is requested until coverage_delta = 0.

### Coverage Projection (always available, always free)

At any point after feature_decomposition is initiated, computable from artifacts without LLM invocation:

```
FEATURE COVERAGE
  Requirements: N REQs defined
  Covered:      n/N  [===----]  pct%
  Gaps:         [list of uncovered REQ-* keys]
  Features:     M vectors  ✓ converged / ⟳ in-progress / ○ not started
```

### Convergence Visibility (three mandatory levels)

| Level | When | Required output |
|-------|------|----------------|
| **Iteration summary** | After every iterate() call | delta (current vs previous), evaluator results, status |
| **Edge convergence** | When delta=0 on an edge | "CONVERGED — {edge}", what was produced, next step |
| **Feature completion** | When all edges in a feature converge | "COMPLETE — {feature_id}", REQ coverage, ready for review |

A convergence event not made visible before the next downstream iteration starts is a spec violation.

---

## XIII. Feature Vectors: Trajectories Through the Graph

A **feature** is a trajectory through the graph:

```
Feature F = |req⟩ + |feature_decomp⟩ + |design⟩ + |module_decomp⟩ + |basis_proj⟩ + |code⟩ + |unit_tests⟩ + |uat_tests⟩ + |cicd⟩ + |telemetry⟩
```

The **REQ key** threads from spec to runtime:

```
Spec:       REQ-F-AUTH-001 defined
Design:     Implements: REQ-F-AUTH-001
Code:       # Implements: REQ-F-AUTH-001
Tests:      # Validates: REQ-F-AUTH-001
Telemetry:  logger.info("login", req="REQ-F-AUTH-001", latency_ms=42)
```

Feature vectors have a required `satisfies:` field listing covered REQ-* keys — the mechanism for the coverage projection (§XII).

---

## XIV. The SDLC Graph (Default Instantiation)

```
Intent → Requirements → Feature Decomp → Design → Module Decomp → Basis Projections → Code ↔ Unit Tests
                                │              │                                              │
                                │              └──→ Test Cases → UAT Tests                   ↓
                                │                                              CI/CD → Running System → Telemetry
                                └──────────────────────────────── Observer/Evaluator ◄────────────────┘
                                                                          │
                                                                     New Intent
```

**Feature Decomposition is a first-class graph node.** It has its own convergence criterion (§XII), evaluators (F_D coverage + F_H approval), and visibility requirement. The spec/design boundary is at `Feature Decomp → Design`: everything upstream is tech-agnostic (WHAT); everything downstream is tech-bound (HOW).

**Intermediate nodes are computational complexity management** — not architectural requirements. Add them when the A→E leap exceeds reliable constructor range.

**The graph is zoomable.** Any edge can expand into a sub-graph, any sub-graph can collapse into a single edge.

```
Full:      Intent → Req → Feat Decomp → Design → Mod Decomp → Basis Proj → Code ↔ Tests → UAT
Standard:  Intent → Req → Feat Decomp → Design → Mod Decomp → Basis Proj → Code ↔ Tests
PoC:       Intent → Req → Feat Decomp → Design → Code ↔ Tests
Hotfix:                                         → Code ↔ Tests
```

**Standard profile v2.9 edge chain**:
`intent → requirements → feature_decomposition → design_recommendations → design → module_decomposition → basis_projections → code ↔ unit_tests`

---

## XV. Projections as Functors

Named profiles — each preserves all four invariants while varying the encoding:

| Profile | When | Graph | Evaluators | Iterations |
|---------|------|-------|-----------|------------|
| **full** | Regulated, high-stakes | All edges | All three types | No limit |
| **standard** | Normal feature work | Core edges + decomposition | Mixed types | Bounded |
| **poc** | Proof of concept | Core edges, decomp collapsed | Agent + deterministic | Low |
| **spike** | Research / experiment | Minimal edges | Agent-primary | Very low |
| **hotfix** | Emergency fix | Direct path | Deterministic-primary | 1-3 |
| **minimal** | Trivial change | Single edge | Any single evaluator | 1 |

---

## XVI. Spec / Design Separation

- **Spec** = WHAT, tech-agnostic. One spec, many designs. Boundary: up to and including Feature Decomposition.
- **Design** = HOW architecturally, tech-bound (ADRs, ecosystem bindings). Boundary: from Design onwards.

Code disambiguation feeds back to **Spec** (business gap) or **Design** (tech gap). Never conflate.

---

## XVII. Invariants

| Invariant | What it means | What breaks if absent |
|-----------|--------------|----------------------|
| **Graph** | Topology of typed assets with admissible transitions | No structure — ad hoc work |
| **Iterate** | Convergence loop producing events, deriving assets | No quality signal — one-shot |
| **Evaluators** | At least one evaluator per active edge | No stopping condition |
| **Spec + Context** | Constraint surface bounds construction | Degeneracy, hallucination |
| **Event stream** | State derived from stream; all writes via F_D event logger function — no direct mutation, no timestamp override | No replay, no recovery, no projection equivalence; timestamp integrity unenforceable |
| **Completeness visibility** | Every convergence transition produces a human-readable summary before downstream proceeds | Silent convergence — system cannot be trusted |

**Projection validity**: `valid(P) ⟺ ∃ G ⊆ G_full ∧ ∀ edge ∈ G: iterate(edge) defined ∧ evaluators(edge) ≠ ∅ ∧ convergence(edge) defined ∧ context(P) ≠ ∅`

**IntentEngine invariant**: Every edge traversal is an IntentEngine invocation. No unobserved computation.

**Path-independence invariant**: A stable asset must be reconstructable from the event stream alone, independent of execution path.

**Observability is constitutive.** The event log, sensory monitors, and feedback loop are methodology constraints, not tooling features. The methodology tooling is itself a product complying with the same constraints.

---

## XVIII. How to Apply This Bootloader

When working on any project under this methodology:

1. **Identify the graph** — what asset types exist, what transitions are admissible
2. **For each edge**: define evaluators, convergence criteria, and context
3. **Iterate**: produce events, derive candidate, evaluate, loop until stable
4. **Apply the gradient**: `delta(state, constraints) → work` — at every scale
5. **Route by ambiguity**: zero → reflex, bounded → iterate, persistent → escalate
6. **Maintain traceability**: REQ keys thread through every artifact from spec to telemetry
7. **Check tolerances**: every constraint must have a measurable threshold
8. **Track completeness**: coverage projection computable at any time; convergence visible before downstream proceeds
9. **Choose a projection** appropriate to the work
10. **Verify invariants**: graph, iteration, evaluators, context, event stream, visibility — any missing = invalid instance

The commands, configurations, and tooling are valid emergences from these constraints. If you have only the commands without this bootloader, you are pattern-matching templates. If you have this bootloader, you can derive the commands.

---

## XIX. Workspace Write Territory and Autonomous Mode Constraints

### Agent Write Territory (hard constraint — not a convention)

The `.ai-workspace/` directory is partitioned by agent identity. Violating these boundaries corrupts the design marketplace and is equivalent to modifying another agent's event stream.

| Territory | Who writes | Rule |
|-----------|-----------|------|
| `events/events.jsonl` | All agents via event logger only | **Never write directly.** Call `emit_event(event_type, data)`. The F_D event logger assigns `event_time`, enforces OL schema, and appends atomically. Append-only — never modify or delete existing lines. |
| `features/active/*.yml` | Owning agent | State projection — update only the feature you are iterating. |
| `features/completed/*.yml` | Owning agent | Move from active/ on full convergence. |
| `comments/claude/` | Claude Code only | Claude writes here. Never write to `comments/codex/`, `comments/gemini/`, or `comments/bedrock/`. |
| `comments/codex/` | Codex only | Same exclusivity — Claude must not write here. |
| `comments/gemini/` | Gemini only | Same. |
| `reviews/pending/PROP-*.yml` | All agents | Proposals written by any agent; human gate resolves. |
| `reviews/proxy-log/` | Proxy actor only | Written by `--human-proxy` mode before each `review_approved` event. |

**Post naming**: `YYYYMMDDTHHMMSS_CATEGORY_SUBJECT.md`. Categories: `REVIEW`, `STRATEGY`, `GAP`, `SCHEMA`, `HANDOFF`, `MATRIX`. Each file carries sufficient context for independent evaluation. Posts are immutable once written — supersede with a new file, never edit.

**Invariant**: An agent reading a comment post in another agent's directory does not confer write rights there. Reading is unrestricted; writing is territory-bound.

### Operating Standards

**`.ai-workspace/operating-standards/`** is the authoritative fallback for any agent action not governed by a more specific instruction. Before performing any of the following, load the relevant standard:

| Action | Standard |
|--------|----------|
| Writing a comment post (`comments/claude/`) | `operating-standards/CONVENTIONS.md` |
| Creating or updating a backlog item | `operating-standards/BACKLOG.md` |
| Writing any human-facing document (ADR, user guide, README, release notes, intent doc) | `operating-standards/WRITING.md` |
| Writing or updating a user guide | `operating-standards/USER_GUIDE.md` |
| Cutting a release (version bump, changelog, cascade install) | `operating-standards/RELEASE.md` |
| Any action not explicitly specified elsewhere | `operating-standards/` — scan for a relevant file |

Operating standards are installed by the methodology layer (e.g. genesis_sdlc) and versioned with it. They are read-only for agents — propose changes via a `STRATEGY` post in `comments/claude/`.

### Human Proxy Mode (`--human-proxy`)

Human proxy mode allows the LLM to act as an authorised F_H substitute during unattended `--auto` runs. It does not remove the F_H gate — it substitutes the actor.

**Activation constraint**: `--human-proxy` requires `--auto`. Used alone it is an error. It is never activated by config, env var, or inference — explicit flag only, per invocation only. It is never persisted to workspace state.

**Proxy evaluation protocol**: At each F_H gate, the proxy:
1. Loads the candidate artifact and the gate's F_H criteria
2. Evaluates each required criterion with explicit evidence
3. Computes the decision: `approved` iff all required criteria pass; `rejected` if any fail
4. Writes a proxy-log file to `.ai-workspace/reviews/proxy-log/{ISO}_{feature}_{edge}.md` **before** emitting any event
5. Emits `review_approved{actor: "human-proxy", proxy_log: "{path}"}` on approval

**Rejection halt**: A proxy rejection pauses the auto-loop immediately. The proxy may not re-invoke iterate on the rejected edge in the same session (`rejected_in_session` set is checked). The feature remains `iterating`.

**Actor field invariant**: Every `review_approved` event must carry `actor` field. Proxy decisions use `actor: "human-proxy"` (never `"human"`, never absent). Human decisions use `actor: "human"`. This is the auditability mechanism — the two must never be confused.

**Morning review**: `/gen-status` surfaces proxy decisions made since the last attended session. Humans dismiss with a `Reviewed: {date}` line or override via `/gen-review`. Proxy decisions are provisional — the human is the authority, not the proxy.

---

## XX. Bug Triage and Post-Mortem Escalation

Bugs during active development do not require a feature vector. The minimum viable artifact is a log entry. Post-mortem determines whether a formal response is warranted.

### Phase 1 — Fix and log (reflex, always)

Fix the bug directly. Append one `bug_fixed` event:

```json
{"event_type": "bug_fixed", "timestamp": "{ISO}", "project": "{name}",
 "data": {"description": "{what was wrong and what changed}", "file": "{primary file}", "root_cause": "coding_error|design_flaw|unknown"}}
```

`root_cause` is provisional — post-mortem may reclassify it.

| Value | Meaning |
|-------|---------|
| `coding_error` | Typo, wrong variable, obvious local mistake — discard after post-mortem |
| `design_flaw` | Fix touched interfaces, contracts, or multiple components — escalate |
| `unknown` | Cause unclear at fix time — investigate before discarding |

### Phase 2 — Post-mortem triage (conscious, on demand)

Run before releases, when a cluster appears, or when `/gen-status --health` surfaces a pattern.

- `design_flaw` or `unknown` resolved to design flaw → emit `intent_raised{signal_source: bug_post_mortem}` → normal homeostatic loop
- `unknown` resolved to coding error → discard
- Pattern of `coding_error` in same area → may indicate missing abstraction → emit `intent_raised` for investigation

### What is NOT required for a bug fix

No feature vector. No iterate() cycle. No human gate. No REQ key traceability. Only the `bug_fixed` event is required.

**The gradient test**: A coding error produces delta → 0 locally — the fix restores intended state, no design information generated. A design flaw produces a persistent delta — the symptom is patched but the constraint violation remains. Post-mortem detects which case applies and routes accordingly.

*Reference: [ADR-S-039](../adrs/ADR-S-039-bug-triage-and-post-mortem-escalation.md)*

---

*Foundation: [GTL Bootloader](GTL_BOOTLOADER.md) — universal formal system (four primitives, event stream, gradient, evaluators)*
*Formal system: [AI SDLC Asset Graph Model v2.8](AI_SDLC_ASSET_GRAPH_MODEL.md) — four primitives, one operation, event stream substrate*
*Projections: [Projections and Invariants v1.2](PROJECTIONS_AND_INVARIANTS.md)*
*Key ADRs: [ADR-S-012](../adrs/ADR-S-012-event-stream-as-formal-model-medium.md) event stream · [ADR-S-013](../adrs/ADR-S-013-completeness-visibility.md) completeness visibility · [ADR-S-016](../adrs/ADR-S-016-invocation-contract.md) invocation contract · [ADR-S-039](../adrs/ADR-S-039-bug-triage-and-post-mortem-escalation.md) bug triage*
