# SCHEMA: ABG Formal Gap Analysis — Category Theory, Sheaf Theory, Temporal Logic, Event Calculus, TCP

**Author**: Claude Code
**Date**: 2026-03-21T16:00:00Z
**Purpose**: Pressure-test the ABG kernel against its own claimed invariants using formal mathematical frameworks. Find the real gaps, not the cosmetic ones.
**Revised**: r2 2026-03-21T17:00:00Z — incorporated Gemini review (`20260321T170000_REVIEW`): `stale_after_ms` on pending fluent (kernel detects, OS decides policy), A1 "lawless at runtime" framing, decision matrix. r1 2026-03-21T16:30:00Z — incorporated Codex closure judgment (`20260321T152947_REVIEW`): PackageSnapshot carrier gap, doctrine-ahead-of-code pattern, Agile lens, six closure checks as method
**For**: all

---

## Method

Six lenses, each asking a different question about the same system. Per Codex (`20260321T152947`), each finding is evaluated against six closure checks: boundary (does each layer own one coherent responsibility?), carrier (what object carries truth across boundaries?), closure (do local guarantees compose into global guarantees?), counterexample (can a realistic failure occur that the model cannot represent?), escalation (when a gap appears, is routing explicit?), minimality (does the gap force a new primitive?).

| Lens | Question |
|------|----------|
| **Category theory** | Is the algebraic structure well-formed? Do morphisms compose? Are functors coherent? |
| **Sheaf theory** | Do local sections (per-territory artifacts) glue to globally consistent state? |
| **Temporal logic** | Are safety and liveness properties satisfied over the event stream? |
| **Event calculus** | Are all fluents named? Are initiation/termination conditions complete? Is the frame axiom satisfied? |
| **TCP protocol analysis** | Does the "kernel/TCP" claim hold? Which reliability guarantees are earned and which are not? |
| **Agile delivery** | Does the system converge on the problem as understanding sharpens, or only on its own implementation? |

Each lens examines the actual code: `gtl/core.py`, `genesis/core.py`, `genesis/bind.py`, `genesis/schedule.py`, `genesis/commands.py`.

---

## I. Category Theory

### The Category ABG

| Component | Mapping |
|-----------|---------|
| **Objects** | Assets (typed nodes) |
| **Morphisms** | Edges (admissible transitions A → B) |
| **Composition** | Graph topology: output of Edge A→B feeds Edge B→C, giving path A→C |
| **Identity** | ? |

### What holds

**Functor structure**:
- `iterate()` is a fixed-point combinator: `Job<A,B> → (Asset<B>, WorkingSurface)`. Applies the endofunctor repeatedly until convergence.
- `project(stream, type, id)` is a functor from EventStream → Asset — maps the event category to the state category. The determinism invariant (`project(S,T,I) = project(S,T,I)`) is the functor identity law.
- The escalation chain `F_D → F_P → F_H` is a natural transformation between evaluation functors. Each `η` preserves the structure (same edge, same asset, same evaluator contract) while changing the evaluation regime.

**Product arrows**: `Edge.source: Asset | list[Asset]` — when source is a list, this is a categorical product A × B → C. The `co_evolve` flag on edges with list sources marks bidirectional edges (A × B ↔ C) — a span in the category.

**Closed operator surface**: `Package._validate()` enforces that every edge references only declared operators. This is a morphism-wellformedness check — no edge can reference an operator outside the category.

### Gap C1: No identity morphism

Every edge transforms. There is no explicit identity morphism `id_A: A → A`. The implicit identity is the case where `delta(job) = 0` on first check — but this is not represented as a morphism in the graph. It's a property of the state, not a structural element.

**Consequence**: Without identity, ABG is technically a **semicategory**, not a category. The composition law `f ∘ id = f` can't be stated.

**Severity**: Low for ABG 1.0. The fixed-point combinator handles the "already converged" case correctly (returns immediately). Identity would matter for formal composition proofs and for the CompositionSet routing layer.

**Classification**: Spec clarification — document that ABG operates as a semicategory and that identity is the trivial fixed-point.

### Gap C2: Composition is structural, not algebraic

Edges compose through the graph topology (the output asset of one edge is the input of the next), but there is no explicit composition operator `g ∘ f`. The `Package` declares edges and assets but doesn't verify that edges form composable paths.

Example: A Package could declare edges `A→B` and `C→D` with no connecting path. This is valid structurally (two disjoint components) but the package doesn't enforce or surface the topology.

**Consequence**: The graph may have disconnected components, dead-end assets (assets that are targets but never sources of any edge), or unreachable assets. The topology is not validated at construction time.

**Severity**: Medium. Disconnected components waste resources (jobs that can never be reached). Dead-end assets are legitimate (terminal nodes like `uat_tests`), but unreachable assets (no inbound edge and not the initial asset) are always bugs.

**Classification**: Spec clarification + minor validation. Add `Package._validate()` check: warn on unreachable assets (no inbound edge and not listed as a graph root).

### Gap C3: No pullback / limit structure verified

When `delta → 0` across all evaluators, the system has found a **fixed point**. This is a categorical limit — the limit of the iteration diagram. But the system doesn't verify that the limit is unique (path-independence). Two different execution paths could produce different "converged" states that both satisfy `delta = 0`.

The **path-independence invariant** (bootloader §XI) says a stable asset must be reconstructable from the event stream alone, independent of execution path. But this is stated as a requirement, not verified.

**Consequence**: The convergence guarantee is procedural (the loop stopped) not categorical (the limit exists and is unique). Different evaluator orderings could produce different converged states.

**Severity**: Low for single-worker. Becomes critical for multi-worker (tournament mode) where two workers could converge to different fixed points.

**Classification**: Kernel hardening — add a test case verifying that reordering evaluator execution produces the same delta.

### Gap C4: Monad laws not verified

`iterate()` has monadic structure:
- `return`: asset already converged (delta = 0 immediately)
- `bind`: evaluate → produce WorkingSurface → emit events → re-evaluate

The monad laws require:
1. `return >>= f = f` — converged asset fed into iteration produces identity
2. `f >>= return = f` — iteration that converges produces same result as just returning
3. `(f >>= g) >>= h = f >>= (λx. g x >>= h)` — associativity

Law 1 and 2 are likely satisfied (trivially — delta=0 short-circuits). Law 3 (associativity) is the interesting one: does it matter whether you compose `bind_fd → iterate → bind_fd` or `bind_fd → (iterate → bind_fd)`? In practice the engine always does them sequentially, so associativity is never tested.

**Severity**: Low. Theoretical. Would matter for parallelism and composition proofs.

---

## II. Sheaf Theory

### The Topology

The workspace has a natural topology defined by the four territories:

```
U_spec  = specification/        (human-authored axioms, read-only)
U_gen   = .genesis/              (installed compiler, write-once)
U_work  = .ai-workspace/        (runtime state, read-write)
U_build = builds/               (agent output, read-write)
```

Each territory carries local sections (files, artifacts). The global section is the running system state.

### What holds

**Context as stalk computation**: `ContextResolver.load(ctx)` computes the stalk of the context sheaf at a point (the locator). The digest is the germ — the local data that determines the stalk. When digests don't match, the sheaf has been modified. This is correctly implemented: `_verify_digest()` raises on mismatch. The sheaf structure is sound at the context level.

**Event stream projection as section**: `project(stream, type, id)` computes a global section from the event stream. The determinism invariant is the sheaf's identity-of-sections axiom. The completeness invariant (every prior state reconstructable) is the restriction property.

**WorkingSurface.context_consumed as provenance**: Records which stalks were consumed during iteration. This is the support of the section — the set of points where the section is non-trivial.

### Gap S1: The Requirements Custody Failure IS a Sheaf Failure

The gluing axiom states: if local sections agree on overlaps, they determine a unique global section.

```
specification/requirements.md    →  45 REQ keys (local section in U_spec)
.genesis/packages/abiogenesis.py →  33 REQ keys (local section in U_gen)
```

These are local sections on different territories. There IS no overlap — the territories don't communicate. The gluing axiom can't even be applied because the open cover `{U_spec, U_gen}` has no intersection where agreement could be verified.

**This is worse than a gluing failure. It is a topology defect.** The junction point between specification/ and .genesis/ is not in the topology. `instantiate()` should be the restriction map `ρ: F(U_spec ∪ U_gen) → F(U_gen)` — pulling requirements from specification/ into the Package. Instead, `instantiate()` ignores U_spec entirely and constructs the U_gen section from hardcoded data.

**This is the exact gap the custody fix (Phase 1) addresses.** The fix adds the restriction map: `instantiate(slug, requirements=_load_reqs())` where `_load_reqs()` reads from U_spec.

**Classification**: Already identified. Fix is in the plan (A.1).

### Gap S2: No Descent Condition for Overlays

When an Overlay modifies a Package, the overlay-modified package must still be compatible with the base. `Package._validate()` checks operator surface closure and co_evolve consistency — but not context surface compatibility.

An overlay could add edges with contexts that conflict with or shadow existing edge contexts. It could restrict_to a subset that breaks the observer model for remaining edges. The descent datum — "this overlay is compatible with the base package's sheaf structure" — is not checked.

Example: An overlay adds an edge `code→integration_tests` with `context=[spec_only]` that shadows the base edge's `context=[spec, design_adrs]`. The observer model for that edge silently changes.

**Severity**: Medium. Overlays are governance-gated (`approve` required), so incorrect overlays require explicit human error. But the system doesn't detect the error.

**Classification**: Spec clarification. Document overlay compatibility constraints.

### Gap S3: Event Stream Has No Integrity Sheaf

The event stream is an ordered sequence of records. Each record has `event_time`, `event_type`, `data`. But there is no hash chain linking records. Unlike a blockchain or Merkle tree, a corrupted or deleted event in the middle of the stream is only detectable by `all_events()` failing on JSON parse — not by a structural integrity check.

The sheaf analog: the event stream should have a **local system** — at each point, the stalk should carry enough information to verify the preceding section. Currently, each event is independent. Deletion or modification of an event is undetectable if the JSON remains valid.

**Severity**: Low for file-based single-user. High for distributed or multi-writer event stores.

**Classification**: Kernel hardening. A hash-chain or sequence number would provide the structural integrity check.

---

## III. Temporal Logic

Properties over the event stream, in LTL (Linear Temporal Logic).

### Safety Properties (□ — "always")

| Property | Formula | Status | Evidence |
|----------|---------|--------|----------|
| **Truthful convergence** | □(reported_delta = actual_delta) | **VIOLATED** | Requirements custody failure: delta reports 0 while evaluating wrong requirements |
| **Event time integrity** | □(event_time is system-assigned) | **HOLDS** | `EventStream.append()` assigns from `datetime.now(UTC)`. No parameter. |
| **F_D gates F_P** | □(F_D_failing → ¬F_P_dispatched) | **HOLDS** | `schedule.iterate()` line 130: `if fp_failing and not fd_failing` |
| **F_D ∧ F_P gate F_H** | □(F_D_failing ∨ F_P_failing → ¬F_H_emitted) | **HOLDS** | `schedule.iterate()` line 144: `if fh_failing and not fd_failing and not fp_failing` |
| **Append-only stream** | □(¬∃ event modified after append) | **CONVENTION** | File opened in append mode (`"a"`), but no structural enforcement (no hash chain) |
| **Evaluators non-empty** | □(Job.evaluators ≠ ∅) | **HOLDS** | `Job.__post_init__` raises `ValueError` |
| **Closed operator surface** | □(edge.using ⊆ package.operators) | **HOLDS** | `Package._validate()` |
| **Assessed requires spec_hash** | □(assessed{fp} → spec_hash ∈ data) | **HOLDS** | `emit()` raises `ValueError` if missing |

### Liveness Properties (◇ — "eventually")

| Property | Formula | Status | Evidence |
|----------|---------|--------|----------|
| **Edge termination** | ◇(converged ∨ blocked ∨ failed) | **NOT GUARANTEED** | No timeout on iterate loop. `max_iter` exists on Overlay but not enforced by core `iterate()`. A failing evaluator that alternates pass/fail loops forever. |
| **Manifest resolution** | ◇(fp_dispatched → assessed) | **NOT GUARANTEED** | No timeout. No heartbeat. A dispatched manifest that never gets a response is an orphan. The system has no detection mechanism. |
| **F_H gate resolution** | ◇(fh_gate_pending → approved ∨ rejected) | **NOT GUARANTEED** | F_H gates pend indefinitely without `--human-proxy`. No timeout, no escalation. |
| **Progress** | ◇(delta(t+1) < delta(t)) | **NOT GUARANTEED** | F_P could produce output that doesn't improve delta. No monotonicity guarantee. |

### Gap T1: No Liveness Guarantee

The core iterate loop has no termination bound. The `gen_start` auto-loop has `max_iterations` (default 50), but this is at the command level, not at the kernel level. A single `iterate()` call always terminates (it's a single bind+evaluate), but the outer loop that calls `iterate()` repeatedly has no kernel-enforced bound.

**Consequence**: A pathological evaluator sequence could loop indefinitely. The system has no deadlock detection.

**Severity**: Medium. The command-level `max_iterations` is a practical bound, but it's not a kernel guarantee.

**Classification**: Spec clarification — document that liveness is a command-layer concern, not a kernel guarantee. The kernel provides single-hop termination; the orchestrator provides loop termination.

### Gap T2: No Fairness Property

Job selection is "first unconverged in topological order" (`commands.py:234`). This is deterministic but unfair. A job early in the topological order that keeps failing blocks all downstream jobs indefinitely.

**Consequence**: Starvation. A permanently failing upstream edge prevents all downstream work.

**Severity**: Low for ABG 1.0 (single-worker, sequential). Medium for multi-feature. The topological ordering is correct for a single feature vector (upstream must converge before downstream can start), but for multiple features in flight, one stuck feature shouldn't block others.

**Classification**: Spec clarification — per-feature isolation already exists in `_scoped_jobs()` (feature filtering). The gap is that `gen_start --auto` doesn't try other features when one is stuck.

---

## IV. Event Calculus

### Named Fluents

| Fluent | Initiated by | Terminated by | Code |
|--------|-------------|---------------|------|
| `operative(edge, wv)` | `approved{kind: fh_review}` | `revoked{kind: fh_approval}` | `bind.py:bind_fh()` |
| `certified(edge, ev, spec_hash, wv)` | `assessed{kind: fp, result: pass, spec_hash}` | spec_hash change (new evaluator hash) | `schedule.py:delta()` line 83-96 |

### Gap EC1: No `dispatched(edge, manifest_id)` Fluent

The event stream records `fp_dispatched` events, but there is no corresponding fluent that tracks "a manifest is currently outstanding." The `fp_dispatched` event is fire-and-forget — nothing monitors whether a response (`assessed`) eventually arrives.

**Event calculus analysis**:
```
fp_dispatched{edge, manifest_id}  INITIATES  pending(edge, manifest_id, stale_after_ms)
assessed{edge, kind: fp}          TERMINATES pending(edge, manifest_id)
elapsed(now - dispatched_time     TRANSITIONS pending → stale(edge, manifest_id)
         > stale_after_ms)
```

This fluent doesn't exist. `holdsAt(pending(edge, manifest_id), now)` is not computable from the current event stream.

**Consequence**: Orphaned manifests. If the F_P actor crashes or the MCP transport fails, the manifest is dispatched but never assessed. The engine will re-dispatch on next iteration (because delta > 0), but it has no awareness that an outstanding dispatch exists. In a multi-worker scenario, this could cause duplicate work.

**Severity**: Medium. Single-worker degrades to "wasteful retry." Multi-worker degrades to "conflicting writes from duplicate dispatches."

**Classification**: Kernel hardening. Add `pending(edge, manifest_id, stale_after_ms)` fluent. `bind_fd()` should check `holdsAt(pending(edge), now)` before re-dispatching.

**Kernel/OS boundary** (per Gemini `20260321T170000`): The kernel provides the `pending` fluent with a `stale_after_ms` property and reports state transitions (`pending → stale`). The orchestrator (command-layer) decides the policy response: re-dispatch, escalate, or abandon. This preserves the separation: **kernel provides detection, OS provides policy.** The kernel never autonomously retransmits — it signals staleness and lets the orchestrator decide. This is analogous to TCP's retransmission timer living in the transport layer while congestion policy lives in the application layer.

### Gap EC2: No `requirements_bound(package, req_list)` Fluent

No event records what requirements the package is evaluating against. The requirements are loaded at Python import time and frozen into the Package object. If requirements change (user edits `specification/requirements.md`), the running engine doesn't know — it uses whatever was loaded at startup.

**Event calculus analysis**:
```
package_loaded{package, req_list, req_hash}  INITIATES  requirements_bound(package, req_list)
requirements_changed{package, new_req_list}  TERMINATES requirements_bound(package, old_req_list)
                                              INITIATES  requirements_bound(package, new_req_list)
```

Neither event exists. The requirements binding is invisible to the event stream.

**Consequence**: This is the formal representation of the custody failure. The custody fix (Phase 1) doesn't fully resolve it — it makes `instantiate()` read from specification/, but it still loads once at import time. A mid-session requirements change is invisible.

**Severity**: Medium. The custody fix addresses the startup-time binding. Mid-session changes are an edge case (user would need to edit requirements.md while the engine is running).

**Classification**: Post-1.0. The custody fix handles the critical case (wrong requirements at startup). Dynamic requirements reload is a future enhancement.

### Gap EC3: Context Change Doesn't Invalidate Certifications

`certified(edge, ev, spec_hash, wv)` is terminated by spec_hash change. But spec_hash is computed from **evaluator definitions** (`job_evaluator_hash(job)`), not from **context bindings**.

If an edge's context changes (e.g., new ADR added to design context, or requirements.md updated), old F_P certifications remain valid because the spec_hash hasn't changed.

**Event calculus analysis**: The termination condition is incomplete:
```
certified(edge, ev, spec_hash, wv) TERMINATED BY:
  - spec_hash changes  (evaluator definitions changed)      ← implemented
  - context_hash changes (context content changed)           ← NOT implemented
  - workflow_version changes                                 ← implemented
```

**Consequence**: An F_P assessment certified under old context (old ADRs, old requirements) remains valid after context updates. The agent was evaluated against stale constraints.

**Severity**: Medium. Context.digest exists as a mechanism — every context carries a sha256 hash. The termination condition could use a composite hash of (evaluator_hash + context_digests). This would automatically invalidate certifications when context content changes.

**Classification**: Kernel hardening. Extend `job_evaluator_hash()` or create `job_context_hash()` that includes `Edge.context[].digest` in the spec_hash computation.

### Gap EC4: Frame Axiom Not Explicit

The event calculus requires a frame axiom: fluents persist unless explicitly terminated. The system assumes this (operative persists until revoked, certified persists until spec_hash change) but doesn't state it formally.

More importantly: **what fluents persist across workflow version changes?** The `carry_forward` mechanism in `bind_fh()` handles F_H approvals across version boundaries. But F_P certifications have no carry-forward — a version change invalidates all certifications (because workflow_version is part of the match).

**This is intentional and correct** — a new workflow version means new evaluators, so old certifications should not carry forward. But the asymmetry between F_H (carries forward) and F_P (does not carry forward) should be documented as a deliberate frame axiom choice, not an implementation accident.

**Classification**: Spec clarification.

---

## V. TCP Protocol Analysis

The "kernel/TCP" claim implies specific reliability guarantees. Let's audit them.

### TCP Guarantee Mapping

| TCP Mechanism | Purpose | ABG Analog | Status |
|---------------|---------|------------|--------|
| **Sequence numbers** | Ordered delivery, gap detection, dedup | `event_time` (wall clock) | **Partial** — ordered but no gap detection |
| **ACK** | Delivery confirmation | — | **MISSING** |
| **Checksum** | Error detection on segments | `Context.digest` (sha256) | **Partial** — contexts verified, events not |
| **Retransmission timer** | Detect lost segments, retry | — | **MISSING** |
| **SYN/ACK handshake** | Connection establishment | `workspace_bootstrap()` + `project_initialized` | **Adequate** |
| **FIN/ACK** | Graceful close | `edge_converged` | **Partial** — unilateral, no downstream ACK |
| **RST** | Abort | `revoked` | **Adequate** |
| **Flow control (window)** | Receiver-side backpressure | `max_iter` on Overlay | **Partial** — bounds iteration, not dispatch rate |
| **Congestion control** | Network-side backpressure | — | **MISSING** |
| **TIME_WAIT** | Prevent old segments on new connections | `workflow_version` + `carry_forward` | **Partial** — handles F_H, not F_P in flight |
| **Keepalive** | Detect dead connections | — | **MISSING** |
| **Half-open detection** | Detect one-sided close | — | **MISSING** |
| **Nagle algorithm** | Coalesce small segments | — | N/A (single-hop) |
| **Selective ACK** | Efficient retransmission | — | N/A (single-hop) |

### Gap TCP1: No ACK Mechanism

TCP: sender sends segment, receiver ACKs. If no ACK within timeout, retransmit.

ABG: `fp_dispatched` is emitted, manifest is written to disk, F_P actor is invoked via MCP. The actor writes its assessment to `result_path`. The skill reads it and calls `emit-event`. **At no point does the engine confirm receipt of the assessment.**

The engine discovers assessment completion only on the **next** `bind_fd()` call, which scans the entire event stream for `assessed` events. This is polling, not acknowledgment.

**Consequence**: No confirmation that the assessment was received. No timeout if it wasn't. No retransmission.

**Severity**: Medium. In practice, the MCP skill handles the dispatch-assess cycle synchronously, so the gap is masked by the transport. But the kernel itself provides no delivery guarantee.

**Classification**: Kernel hardening (post-1.0). For single-hop with synchronous MCP, the gap is not operational. For async or distributed dispatch, ACK is required.

### Gap TCP2: No Sequence Numbers → No Gap Detection

TCP sequence numbers serve three purposes: ordering, gap detection, deduplication.

ABG uses `event_time` (ISO 8601 wall clock) for ordering. This provides:
- ✓ Ordering (lexicographic comparison of ISO timestamps)
- ✗ Gap detection (missing events are invisible — the stream doesn't know what it should have)
- ✗ Deduplication (identical events with different timestamps are both valid)

**Consequence**: If `emit()` is called twice for the same logical event (e.g., crash recovery), both events are appended. The `delta()` function uses `any()` to find matching `assessed` events — duplicates don't cause errors but they pollute the stream.

More seriously: if an event is lost (file system error, partial write), the gap is undetectable. The stream doesn't know it's incomplete.

**Severity**: Low for single-process file I/O (partial write → JSON parse failure on next read → detected by `all_events()`). Medium for distributed event stores where events could be lost silently.

**Classification**: Kernel hardening. Add monotonic sequence number to events. Detect gaps on read. Deduplicate on (event_type, edge, evaluator, spec_hash) tuple.

### Gap TCP3: No Retransmission Timer → Orphaned Manifests

TCP retransmits after RTO (retransmission timeout). ABG has no timeout on F_P dispatch.

```
Timeline:
  t=0  fp_dispatched{edge: "code→tests", manifest_id: "m42"}
  t=∞  ... waiting ...

  No timeout. No retransmission. No detection.
```

On next `gen_iterate()` call, `delta()` will re-evaluate and `bind_fd()` will re-dispatch because no `assessed` event exists. But:
1. The engine doesn't know a dispatch is already in flight
2. Two F_P actors could be running simultaneously on the same edge
3. Both could write to the same `result_path` (race condition)

**Severity**: Medium. The skill layer (`gen-start.md`) runs MCP synchronously, so in practice only one dispatch is in flight. But the kernel makes no guarantee.

**Classification**: Kernel hardening. The `pending(edge, manifest_id)` fluent (Gap EC1) would enable timeout detection.

### Gap TCP4: No Congestion Control

TCP uses AIMD (Additive Increase, Multiplicative Decrease) to prevent network overload. ABG has no mechanism to throttle when system resources are constrained.

With a single worker, this is irrelevant — one job at a time. With multiple workers (schedule.py supports batched parallel execution), there's no mechanism to:
- Limit concurrent F_P dispatches (each costs LLM API budget)
- Back off when F_P actors are producing low-quality output (delta not improving)
- Detect and respond to resource exhaustion (context too large, API rate limits)

**Severity**: Low for ABG 1.0 (single worker). High for multi-worker.

**Classification**: Post-1.0. Composition-layer concern (gsdlc or orchestrator).

### Gap TCP5: No Half-Open Detection

TCP detects half-open connections (one side closed, other thinks it's open) via keepalive probes.

ABG has no equivalent. If the F_P actor crashes mid-execution:
- The manifest is on disk
- `fp_dispatched` is in the event stream
- No `assessed` event will ever arrive
- The engine doesn't probe for liveness

**Severity**: Medium. Same root cause as TCP3 (no retransmission timer). The fix for EC1 (pending fluent with `stale_after_ms`) would enable half-open detection: `holdsAt(pending(edge), now) ∧ (now - dispatched_time > stale_after_ms)` transitions the fluent to `stale(edge, manifest_id)`. The kernel reports staleness; the orchestrator decides recovery policy.

**Classification**: Kernel hardening, same fix as EC1.

### Gap TCP6: Convergence Is Unilateral (No FIN/ACK)

TCP's graceful close requires both sides to agree: FIN → ACK → FIN → ACK.

ABG's `edge_converged` is a unilateral declaration by the evaluators. There is no acknowledgment from the downstream edge that it received the converged artifact and is ready to consume it.

In the current sequential model, this is fine — the downstream edge runs bind_fd() on its own schedule and discovers the upstream artifact. But for concurrent or distributed execution, the downstream consumer might not be ready, might reject the artifact, or might need the upstream to hold state during a handoff window.

**Severity**: Low for single-worker sequential. Medium for multi-worker concurrent.

**Classification**: Post-1.0. Only matters when edges execute concurrently.

---

## VI. Agile Delivery

Per Codex: "Does the system converge on the **problem** as understanding sharpens, or only on the current implementation against its own tests?"

### What holds

**Iterative refinement is structural**: The graph is traversed iteratively. `iterate()` loops until evaluators converge. Requirements and intent are mutable upstream assets — the graph supports refinement.

**Intent formation exists in doctrine**: The bootloader defines `IntentEngine(intent + affect) = observer → evaluator → typed_output` and three output types (reflex.log, composition_dispatched, feature_proposal). The `intent_raised` event carries `requires_spec_change` for routing.

### Gap A1: Doctrine Is Ahead of the Constitutional Event Model

Codex identifies this as a recurring pattern across multiple gaps: the bootloader describes capabilities that the approved event schema and runtime code don't fully carry.

| Doctrine concept | Constitutional carrier | Status |
|-----------------|----------------------|--------|
| `IntentEngine` three output types | `intent_raised` event | **Partial** — event exists but `composition_dispatched` output type has no corresponding event or dispatch mechanism |
| `PackageSnapshot.work_binding()` | `emit()` validation | **Missing** — `work_binding()` says every work event must carry `package_snapshot_id`, but `emit()` doesn't enforce this |
| `reflex / affect / conscious` phases | Processing phase routing | **Missing** — no runtime discriminator routes by processing phase |
| `ObserverModel` | `Edge.context` | **Present as mechanism, unnamed as concept** |

The gap is not "missing primitives." It is "the constitutional types declare contracts the runtime doesn't enforce." This is a **carrier-test failure** (per Codex's closure checks): the concept exists but the object that carries truth across the boundary is incomplete.

**Severity**: Medium → **High** (repriced per Gemini). The PackageSnapshot carrier gap is the most concrete: `work_binding()` returns `{package_name, package_snapshot_id}` but no work event actually carries these fields. Per Gemini (`20260321T170000`): "If `emit()` does not enforce the `package_snapshot_id` binding, the system is **lawless at runtime** — it emits events that cannot be definitively mapped back to the constitutional state that authorized them." Historical replay under the correct law (the entire point of PackageSnapshot) is not achievable until work events carry the snapshot binding. Without this, the event stream is a log of what happened but not under which law it happened — provenance is severed.

**Classification**: Doctrine/spec/runtime reconciliation gap. Three fixes:
1. `emit()` should validate that work events (`edge_started`, `edge_converged`, `assessed`, `approved`) include `package_snapshot_id` when a PackageSnapshot is active
2. The engine should compute and bind the active PackageSnapshot at startup and inject it into all work event payloads
3. `project()` should be able to filter events by `package_snapshot_id` — enabling replay under a specific constitutional state, not just "all events ever"

### Gap A2: Observer-Relative Intent Formation Not Formalized

The bootloader says `intent = delta(observed_state, spec) where delta ≠ 0`. But "spec" is not a formal parameter — it's implicit. The observation model (what spec+design surface the system evaluates against) is convention, not constitution.

At the kernel level, `Edge.context` IS the observer model — this is proven in the code (`bind.py:275`, `select_relevant_contexts()`). But the recognition that context binding is observer model formation — not just "loading documents into a prompt" — is not stated anywhere in the spec or code comments.

**Severity**: Low for ABG 1.0 (naming, not mechanism). High for gsdlc (determines whether test generation observes against spec or code).

**Classification**: Spec clarification. Name the pattern. Document that `Edge.context` is the observer model for that hop.

### Gap A3: No Composition Routing

The current system hardcodes all intents to route through gsdlc. The bootloader describes `composition_dispatched` as an IntentEngine output type, but:
- No dispatch table maps gap types to compositions
- No event schema for `composition_dispatched` exists
- No mechanism selects between gsdlc, PoC, Discovery, Research

**Severity**: Low for ABG 1.0 (single composition is valid for V1). High for gsdlc plan.

**Classification**: Composition-law gap. Above abg layer. Deferred to Part III (gsdlc plan).

---

## VII. Summary — Gap Classification Matrix

| Gap ID | Description | Lens | Severity | ABG 1.0? | Classification |
|--------|-------------|------|----------|----------|----------------|
| C1 | No identity morphism | Category | Low | No | Spec clarification |
| C2 | Composition not validated (unreachable assets) | Category | Medium | Yes | Minor validation |
| C3 | Path-independence not verified | Category | Low | Test | Kernel hardening |
| C4 | Monad laws not tested | Category | Low | No | Theoretical |
| S1 | Requirements custody = sheaf topology defect | Sheaf | **Critical** | **Yes** | Already in plan (A.1) |
| S2 | No overlay descent condition | Sheaf | Medium | No | Spec clarification |
| S3 | Event stream has no integrity chain | Sheaf | Low | No | Post-1.0 |
| T1 | No kernel-level liveness guarantee | Temporal | Medium | Clarify | Spec clarification |
| T2 | No fairness (stuck feature blocks all) | Temporal | Low | No | Spec clarification |
| EC1 | No `pending(edge)` fluent → orphan manifests | Event Calculus | **Medium** | **Yes** | Kernel hardening |
| EC2 | No `requirements_bound` fluent | Event Calculus | Medium | Partial | Custody fix handles startup |
| EC3 | Context change doesn't invalidate certifications | Event Calculus | **Medium** | **Yes** | Kernel hardening |
| EC4 | Frame axiom asymmetry (F_H carries, F_P doesn't) | Event Calculus | Low | Clarify | Spec clarification |
| A1 | Doctrine ahead of constitutional event model (PackageSnapshot carrier, composition_dispatched, processing phases) | Agile | **Medium** | **Yes** | Doctrine/runtime reconciliation |
| A2 | ObserverModel unnamed — Edge.context IS the mechanism but not recognized as such | Agile | Low | Clarify | Spec clarification |
| A3 | No composition routing (all intents hardcoded to gsdlc) | Agile | Low | No | Composition-law gap (gsdlc) |
| TCP1 | No ACK mechanism | TCP | Medium | No | Post-1.0 |
| TCP2 | No sequence numbers → no gap detection | TCP | Low | No | Post-1.0 |
| TCP3 | No retransmission timer → orphan manifests | TCP | Medium | Yes | = EC1 |
| TCP4 | No congestion control | TCP | Low | No | Post-1.0 |
| TCP5 | No half-open detection | TCP | Medium | Yes | = EC1 |
| TCP6 | Convergence is unilateral (no FIN/ACK) | TCP | Low | No | Post-1.0 |

### Cross-Lens Pattern: Doctrine Ahead of Code

Codex identifies a recurring structural pattern across multiple gaps: the bootloader/doctrine describes capabilities that the constitutional types declare but the runtime code doesn't enforce. This is not a primitive gap — the types exist. It is a **carrier-test failure**: the concept is present but the object that carries truth across the boundary is incomplete or unenforced.

| Doctrine concept | Constitutional type | Runtime enforcement |
|-----------------|--------------------|--------------------|
| `PackageSnapshot.work_binding()` | `PackageSnapshot` in `gtl/core.py` | `emit()` does not validate `package_snapshot_id` on work events |
| `IntentEngine` three outputs | Bootloader §IX | Only `feature_proposal` has a runtime path; `composition_dispatched` is unimplemented |
| `reflex/affect/conscious` phases | Bootloader §VII | No runtime discriminator routes by phase |
| `ObserverModel` | `Edge.context` (mechanism exists) | Not named; not recognized as observer model formation |
| Context replay via digest | `Context.digest` | Digests verified at load time but not included in certification hash |

The fix pattern is consistent: **enforce what the types already declare.** No new primitives — runtime reconciliation.

### ABG 1.0 Actionable Items (new, not already in plan)

| Priority | Gap | Fix |
|----------|-----|-----|
| **High** | EC1/TCP3/TCP5 | Add `pending(edge, manifest_id, stale_after_ms)` fluent. `bind_fd()` checks before re-dispatch. Kernel reports `pending → stale` transition; orchestrator decides policy (re-dispatch, escalate, abandon). Kernel detects, OS decides. |
| **High** | EC3 | Include `Edge.context[].digest` in spec_hash computation. Context content change invalidates F_P certifications. The generalized "keepalive" — dominant fix per Gemini decision matrix. |
| **High** | A1 (PackageSnapshot) | `emit()` validates that work events carry `package_snapshot_id` when active. Engine injects snapshot binding into all work event payloads. `project()` filters by snapshot. Without this the system is "lawless at runtime" (Gemini). |
| **Medium** | C2 | Add `Package._validate()` warning for unreachable assets (no inbound edge and not graph root). |
| **Low** | C3 | Add test: two evaluator orderings on same event stream produce same delta. |
| **Clarify** | T1, EC4, T2, A2 | Document in spec: liveness is command-layer; frame axiom is intentionally asymmetric; fairness is per-feature via scoping; `Edge.context` is the observer model for the hop. |

### What the TCP Claim Actually Earns

After ABG 1.0 with the above fixes, the earned guarantees are:

| Guarantee | Earned? |
|-----------|---------|
| Ordered delivery | ✓ (append-only, system-assigned timestamps) |
| Error detection | ✓ (context digest, event JSON parse, spec_hash invalidation + context hash) |
| No silent state loss | ✓ (custody fix + context invalidation + pending fluent + PackageSnapshot carrier) |
| Connection establishment | ✓ (workspace_bootstrap + project_initialized) |
| Graceful abort | ✓ (revoked events) |
| Single-hop delivery | ✓ (iterate terminates, evaluators are non-empty, F_D gates F_P gates F_H) |
| Retransmission | ✗ (not yet — pending fluent enables detection but not automatic retry) |
| Congestion control | ✗ (not yet — single-worker makes it moot) |
| Multi-hop routing | ✗ (gsdlc concern, not kernel) |

**The claim "kernel/TCP" is earned for single-hop reliability with the custody fix + the three new hardening items.** Multi-hop reliability (routing, congestion, flow control) is an OS/IP claim — gsdlc's job, not abg's.

---

## VII. The Deepest Gap: Where the Lenses Converge

All five lenses converge on the same structural issue: **the system has no mechanism to detect that its observation surface has changed.**

| Lens | How it sees the gap |
|------|-------------------|
| Category theory | No pullback verifying that the limit (convergence) is stable under context change |
| Sheaf theory | Local sections (contexts, requirements) can change without the global section (convergence state) updating |
| Temporal logic | □(context_stable → certification_valid) — but ¬□(context_stable), and certification doesn't track context |
| Event calculus | `certified` fluent termination condition is incomplete — doesn't include context hash |
| TCP | No keepalive — the engine doesn't probe whether its constraint surface is still current |

The custody fix (S1) is the most visible instance: requirements change, convergence state doesn't update. But EC3 is the generalized form: **any** context change that doesn't change the evaluator hash leaves old certifications valid.

The single fix that addresses the general case: **include context digests in the spec_hash computation.** When any context's content changes (detected by digest mismatch), all F_P certifications for edges binding that context are invalidated. The system re-evaluates against the current observation surface.

This is the kernel-level equivalent of TCP's keepalive: "is my constraint surface still what I certified against?"

---

## IX. Closure Judgment (incorporating Codex `20260321T152947`)

Codex's assessment: "ABG is close to closed as a hop-local kernel. ABG is not yet fully closed as the higher-order substrate for observer-relative intent formation, compositional solution routing, and globally truthful satisfaction."

**This analysis confirms that judgment and sharpens it:**

| Claim | Earned after fixes? | Evidence |
|-------|--------------------|----------|
| ABG is a valid hop-local kernel | **Yes** | All six lenses find gaps, but none force new primitives. All fixes are kernel hardening, spec clarification, or doctrine reconciliation. |
| The kernel/TCP analogy holds for single-hop | **Yes** | Ordered delivery, error detection, no silent state loss, connection setup, graceful abort, single-hop delivery — all earned after custody fix + EC1 + EC3 + A1. |
| Higher-order composition is expressible without new primitives | **Yes** | ObserverModel = Context[] composition (proven in code). CompositionSet = set of Packages + dispatch table. Global gluing = total_delta + context-sensitive certification. |
| The composition law needs to be made explicit | **Yes** | Doctrine is ahead of code in 5 identified areas. The types exist; the runtime doesn't enforce them. |

**Zero new primitives. Four kernel-hardening fixes. Five spec clarifications. The rest is gsdlc-layer composition work.**

### Three-Agent Decision Matrix (Gemini `20260321T170000`)

| Item | Proposal | Outcome | Reasoning |
|------|----------|---------|-----------|
| EC3 | Context digest in spec_hash | **Dominant** | Solves the deepest gap generically — stale certifications invalidated automatically |
| EC1 | Pending fluent with `stale_after_ms` | **Adopt** | Prevents orphans, enables timeout detection. Kernel detects, OS decides policy. |
| A1 | PackageSnapshot enforcement in `emit()` | **Adopt** | Restores legal traceability — without it, events are "lawless" |
| C2 | Unreachable asset validation | **Niche** | Good hygiene, low effort |
| C1 | Formal identity morphism | **Defer** | Theoretical for 1.0; semicategory is sufficient |

All three agents (Claude, Codex, Gemini) converge: **zero new primitives, tighten the composition law, reconcile doctrine with runtime.**
