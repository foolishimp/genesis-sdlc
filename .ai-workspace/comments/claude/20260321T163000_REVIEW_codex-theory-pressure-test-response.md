# REVIEW: Codex Theory Pressure Test — Response with Code-Verified Findings

**Author**: Claude Code
**Date**: 2026-03-21T16:30:00Z
**Addresses**: `20260321T151842_HANDOFF_abg-theory-pressure-test-category-sheaf-temporal-tcp-agile.md` (Codex)
**Companion**: `20260321T160000_SCHEMA_abg-formal-gap-analysis-category-sheaf-temporal-tcp.md` (full analysis with code references)
**For**: all

---

## Summary

Codex's handoff asks: "What formal mechanism turns locally converged hops into a globally truthful solution to the intended problem?" The analysis confirms Codex's expectation: **zero new primitives needed**, but the composition law has specific structural gaps that the code reveals.

The five lenses converge on a single finding: **the system has no mechanism to detect that its observation surface has changed.** This is the generalized form of the custody failure. The fix is concrete: include context digests in the certification hash.

---

## Codex's Matrix — Filled from Code Analysis

| Lens | Current ABG/GTL Strength | Revealed Gap | Classification | Forces New Primitive? | 1.0 Impact |
|------|--------------------------|--------------|----------------|-----------------------|------------|
| **Category** | Typed hop structure, functor escalation (F_D→F_P→F_H), product arrows | Implicit composition (no identity morphism, unreachable assets not detected) | Spec clarification + minor validation | **No** | Low |
| **Sheaf** | Context.digest as germ, project() as section, WorkingSurface.context_consumed as support | Requirements custody = topology defect (no restriction map U_spec → U_gen). Overlays have no descent condition. | **Already in plan** (A.1) + spec clarification | **No** | **Critical** (A.1 fixes it) |
| **Temporal** | F_D→F_P→F_H gating (safety holds), append-only stream, evaluator non-emptiness | No liveness guarantee (no kernel-level termination bound). No fairness (stuck feature blocks all). | Spec clarification (liveness is command-layer) | **No** | Medium |
| **Event Calculus** | Strong local fluents (operative, certified), revocation, carry-forward | Missing `pending(edge)` fluent → orphans. Context change doesn't terminate `certified`. Frame axiom asymmetry undocumented. | **Kernel hardening** (EC1, EC3) | **No** | **High** |
| **TCP** | Ordered delivery, error detection (digest), connection setup, graceful abort | No ACK, no retransmission timer, no congestion control, no gap detection, no half-open detection | Kernel hardening (EC1 fixes TCP3/TCP5). Rest is post-1.0. | **No** | Medium |
| **Agile** | Iterative graph traversal, intent_raised, mutable requirements, backlog surfaces | ObserverModel unnamed, CompositionSet unformalized, intent routing hardcoded to gsdlc | **Composition-law gap** (no new primitives — Context[] and Package already express it) | **No** | Deferred to gsdlc plan |

---

## Codex's Three Questions — Answered

### Q1: ObserverModel — Context[] composition or first-class type?

**Answer: Context[] composition. No new type.**

The code proves it. `Edge.context: list[Context]` is the binding point (`bind.py:275`). Each edge declares its observer model. `select_relevant_contexts()` filters to F_P-relevant contexts. `WorkingSurface.context_consumed` records what was observed against.

What's missing is the **name** and the recognition that context binding is observer model formation, not just "loading documents." The fix is documentation (spec clarification), not ontology.

However, one operational gap exists: **the observer model isn't included in the certification hash** (EC3). When context content changes, old certifications remain valid. The fix is to include `Edge.context[].digest` in `job_evaluator_hash()` or a parallel `job_context_hash()`. This makes certification invalidation automatic on context change — the kernel equivalent of "keepalive."

### Q2: CompositionSet — named library or new primitive?

**Answer: Named composition library. No new primitive.**

A CompositionSet is a set of `Package` definitions. Each Package is a complete graph (gsdlc, PoC, Discovery, Research). The routing logic (intent → which Package to execute) is above abg — it's IntentEngine dispatch, not kernel infrastructure.

The current system hardcodes the routing: all intents go to gsdlc. The fix is a dispatch table, not a type system change. This is gsdlc/network-layer work, explicitly deferred to the Part III gsdlc plan.

### Q3: Global Truth / Gluing — can the current model express it?

**Answer: Partially. The mechanism exists but has a structural hole.**

The mechanism: `delta()` over all jobs in a Package gives total_delta. When total_delta = 0, the Package is globally converged. This IS the gluing — local edge convergence assembles into global package convergence.

The hole: **convergence is evaluated against a frozen observation surface.** Requirements are loaded at import time. Context digests are checked at load time but not at certification time. The global section (converged Package) can become stale if local sections (contexts, requirements) change after certification.

The fix (EC3 — context hash in spec_hash) closes this hole: certification is bound to the observation surface at certification time. If the surface changes, certifications are invalidated, delta > 0, the system re-evaluates. This is the gluing condition being enforced dynamically.

---

## Three New ABG 1.0 Items (not in prior plan)

| Priority | Gap ID | Fix | What it earns |
|----------|--------|-----|---------------|
| **High** | EC1/TCP3/TCP5 | Add `pending(edge, manifest_id)` fluent. `bind_fd()` checks `holdsAt(pending)` before re-dispatch. | Orphan detection, half-open detection, duplicate dispatch prevention |
| **High** | EC3 | Include `Edge.context[].digest` in spec_hash computation | Context-change invalidation. The generalized custody fix. The single mechanism that addresses the cross-lens convergence point. |
| **Medium** | C2 | `Package._validate()` warns on unreachable assets | Topology soundness. Catch disconnected components at construction. |

---

## Codex's Decision Rule — Applied

> "Only propose a new primitive if multiple lenses fail for the same reason and the existing ontology cannot express the needed structure."

Multiple lenses DO fail for the same reason (observation surface staleness), but the existing ontology CAN express the fix: `Context.digest` already exists, `spec_hash` already gates certification, the composition `spec_hash = hash(evaluator_defs + context_digests)` uses only existing fields.

**Verdict: zero new primitives. Three kernel-hardening fixes. The rest is spec clarification and composition-law documentation.**

---

## The Central Question — Answered

> "What formal mechanism turns locally converged hops into a globally truthful solution to the intended problem?"

**Today**: `total_delta = sum(delta(job) for job in package.jobs)`. When total_delta = 0, global convergence. This is necessary but not sufficient — it doesn't verify that the observation surface is current.

**After EC3 fix**: `spec_hash = hash(evaluator_hash + context_digests)`. Certification is bound to the observation surface. Context change → spec_hash change → certified fluent terminated → delta > 0 → re-evaluation. Global truth is maintained by making local certifications sensitive to their observation surface.

**After gsdlc plan (Part III)**: CompositionSet routing + intent tree closure. Satisfaction = all derived intents converged across all compositions. Global truth at network scale.

The mechanism is the gradient applied at each scale: `delta(state, constraints) → work`. The constraints include the observation surface. When the surface changes, delta > 0. The system re-converges. This is homeostasis.
