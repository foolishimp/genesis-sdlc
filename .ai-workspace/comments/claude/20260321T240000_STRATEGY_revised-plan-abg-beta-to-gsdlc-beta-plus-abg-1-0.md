# STRATEGY: ABG 1.0-beta → GSDLC 1.0-beta → ABG 1.0

**Author**: Claude Code
**Date**: 2026-03-21T24:00:00Z
**Supersedes**: `20260321T180000_STRATEGY_abg-1-0-mvp-definitive-task-plan.md`
**For**: all

---

## Release Chain

```
ABG 1.0-beta (shipped, sufficient)
    → GSDLC 1.0-beta (custody fix, cascade)
        → ABG 1.0 (hardening + completeness, fed by GSDLC findings)
            → GSDLC 1.1 (observation model, process fix, new features)
```

---

## GSDLC 1.0-beta — Feature Set

**Claude Code build only.** This is an MVP to restore correct dogfooding. Multi-build parity (Codex, Gemini, etc.) is deferred — other builds exist but are not release-gated.

Two feature families: **requirements custody fix** and **sandbox integration tests**.

### Custody fix — the system evaluates wrong requirements for every non-gsdlc project

| # | Task | Description | File(s) |
|---|------|-------------|---------|
| 1.1 | `instantiate()` accepts requirements | Add optional `requirements` param. When provided, overrides workflow's hardcoded keys. | `sdlc_graph.py` (Python build) |
| 1.2 | Wrapper passes project requirements | Generated `.genesis/gtl_spec/packages/{slug}.py` parses `### REQ-*` headers from `specification/requirements.md` and passes to `instantiate(requirements=_load_reqs())`. | `install.py` (Python build) |
| 1.3 | Scaffold requirements.md on install | Create starter `specification/requirements.md` if absent. | `install.py` (Python build) |

### Sandbox integration tests — prove the installed product works

ABG lesson: unit tests that import Python objects pass while the installed product is broken. The custody fix is only proven when a sandbox test installs GSDLC into a fresh directory, creates a project with custom REQ keys, runs `gen-gaps`, and verifies the engine sees those keys — not the workflow's hardcoded 33.

| # | Task | Description |
|---|------|-------------|
| 1.4 | Sandbox install test | Install GSDLC into `tmp_path`. Verify engine modules, gtl_spec, wrapper all present. |
| 1.5 | Custody round-trip test | Install into `tmp_path`, write `specification/requirements.md` with 3 custom REQ keys, run `gen-gaps` as subprocess. Verify output contains exactly those 3 keys, not the workflow's 33. |
| 1.6 | Wrapper generation test | Install, verify generated wrapper calls `instantiate(requirements=_load_reqs())`. Verify `_load_reqs()` parses the right file. |
| 1.7 | No-requirements-file test | Install without `specification/requirements.md`. Verify fallback to empty list (zero requirements). The workflow's keys are gsdlc's requirements, not the project's — falling back to them IS the custody bug. |

### Validate and release

| # | Task | Description |
|---|------|-------------|
| 1.8 | Validate on abiogenesis | Install from source into ABG. `gen-gaps` must report 45 project-specific REQ keys, not gsdlc's 33. Proof gates release. |
| 1.9 | Release GSDLC 1.0-beta | Version bump, all tests pass (including sandbox), custody fix shipped. |
| 1.10 | Cascade to ABG | `gen-install` with released GSDLC. Layer 3 wrapper now reads project requirements. |

### Rollout (post-beta, not part of product scope)

| # | Task | Description |
|---|------|-------------|
| 1.11 | Cascade to dependents | genesis-manager, etc. Rollout activity — depends on 1.9 but is not a beta closure criterion. |

### GSDLC 1.0-beta closure criteria

1. `instantiate()` reads project-specific requirements in Claude Code build
2. Sandbox tests prove the installed product sees project requirements, not workflow keys
3. Validated on real dependent — ABG's `gen-gaps` reports 45 project-specific REQ keys
4. Installed-runtime sandbox tests pass (subprocess/install-first — not just unit imports), release shipped

---

## ABG 1.0 — Hardening + Completeness (parallel with GSDLC, plus post-cascade)

### Kernel hardening (start now, no GSDLC dependency)

| # | Task | Description | Gap |
|---|------|-------------|-----|
| 2.1 | Context digest in spec_hash | `job_evaluator_hash()` includes `Edge.context[].digest`. Context change auto-invalidates certifications. | EC3 |
| 2.2 | manifest_id on events | `fp_dispatched` + `assessed` carry `manifest_id`. | EC1 |
| 2.3 | Pending fluent | `pending(edge, manifest_id, stale_after_ms)`. Prevents duplicate dispatch. | EC1 |
| 2.4 | PackageSnapshot carrier | Work events carry `package_snapshot_id`. Lawful replay. | A1 |

### Completeness verification (start now, no GSDLC dependency)

| # | Task | Description |
|---|------|-------------|
| 2.5 | 7 completeness criteria | Explicit evaluation against Codex's criteria. Document each. |
| 2.6 | State machine testing | Test iterator, auto-loop, manifest state machines against engine behavior. |
| 2.7 | Unreachable asset detection | `Package._validate()` warns on assets with no inbound edge that aren't roots. |
| 2.8 | Path-independence test | Two evaluator orderings on same stream → same delta. |

### Spec clarifications (start now, no GSDLC dependency)

| # | Task | Gap |
|---|------|-----|
| 2.9 | Liveness is command-layer, not kernel | T1 |
| 2.10 | Frame axiom is intentionally asymmetric (F_H carries forward, F_P does not) | EC4 |
| 2.11 | Fairness is per-feature (`_scoped_jobs()`) | T2 |
| 2.12 | Edge.context is the ObserverModel — name the pattern | A2 |
| 2.13 | Overlay compatibility constraints for sheaf consistency | S2 |

### Post-cascade cleanup (after 1.10)

| # | Task | Description |
|---|------|-------------|
| 2.14 | Audit convergence certificates | Mark `edge_converged` events issued against wrong requirements as invalid. |
| 2.15 | Evaluate custom Package | `abiogenesis.py` in builds/ — dead code or future intent? Remove if dead. |
| 2.16 | Remove pythonpath artifact | Drop `pythonpath: builds/claude_code/code` from genesis.yml. |
| 2.17 | Reconcile orphaned REQ tags | Tracing tags now visible to coverage checks — reconcile against requirements. |

### ABG 1.0 release

| # | Task | Description |
|---|------|-------------|
| 2.18 | Release ABG 1.0 | All closure criteria met. WiFi test green. Version bump. |
| 2.19 | Cascade | Through GSDLC to all dependents. |

### ABG 1.0 closure criteria

1. Truthful convergence — gen-gaps reports project-specific REQ keys after GSDLC cascade
2. Observation surface integrity — context digest in certification hash
3. No orphaned manifests — pending fluent tracks dispatches, prevents duplicates
4. Lawful events — work events carry package_snapshot_id
5. Completeness criteria — all 7 verified against running code
6. Pressure test holds — no new primitive forced during implementation
7. WiFi test passes — self-hosting total_delta=0

---

## GSDLC 1.1 — Post-Beta Scope

Features deferred from beta. Each requires explicit REQ/feature artifacts before work begins.

| # | Task | Status |
|---|------|--------|
| 3.1 | Add design_adrs context to downstream edges (integration, guide, UAT) | Enhances existing F-INTEGRATION-UAT |
| 3.2 | Test-plan artifact — F_P maps integration scenarios to REQ keys | Needs new REQ/feature |
| 3.3 | Intent-grounded UAT criteria — F_H evaluates against intent, not code | Needs new REQ/feature |
| 3.4 | Homeostatic feedback — F_D gap routes to F_P with spec context | Needs new REQ/feature |
| 3.5 | REQ key for requirements separation — close the provenance chain | Needs new REQ/feature |
| 3.6 | Marketplace → graph bridge — STRATEGY posts → tracked requirements | Needs new REQ/feature |
| 3.7 | ObserverModel as named composition pattern | Spec clarification |
| 3.8 | CompositionSet routing — define solution macros as Packages | New feature family |
| 3.9 | Intent tree closure — satisfaction = all derived intents converged | New feature family |

---

## Critical Path

```
GSDLC 1.0-beta (serial, Claude Code only)    ABG hardening (parallel)
──────────────────────────────────────────    ──────────────────────────
1.1 instantiate() accepts requirements        2.1–2.4  kernel hardening
 → 1.2 wrapper passes project reqs           2.5–2.8  completeness
 → 1.3 scaffold requirements.md              2.9–2.13 spec clarifications
 → 1.4–1.7 sandbox tests
 → 1.8 validate on ABG
 → 1.9 release GSDLC 1.0-beta
 → 1.10 cascade to ABG
    → 2.14–2.17 post-cascade cleanup
    → ABG F_P gap resolution (iterate remaining edges)
    → WiFi test green (total_delta=0)
                    ↘
              2.18 ABG 1.0 release
              2.19 cascade → GSDLC 1.1
```
