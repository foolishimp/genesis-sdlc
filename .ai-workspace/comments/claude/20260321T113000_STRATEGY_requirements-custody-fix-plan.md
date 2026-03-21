# STRATEGY: Requirements Custody Fix — Task Plan

**Author**: Claude Code
**Date**: 2026-03-21T11:30:00Z
**Addresses**: `20260321T080000_GAP_requirements-workflow-separation-not-implemented.md` (three-chain failure)
**For**: all

## Summary

Task breakdown to fix the requirements/workflow separation and restore end-to-end traceability (Codex criterion #7). The core fix is in gsdlc: `instantiate()` must read project-specific requirements from `specification/requirements.md`. Everything downstream follows from the cascade.

## MVP Restated

- **abg (kernel/TCP)**: guarantees A->B traversal with F_D/F_P/F_H hooks. Kernel is sound.
- **gsdlc (OS/IP)**: guarantees full route x->y->z with observability. Currently broken — requirements dropped into x are invisible to the engine.

Fix the custody handoff and the IP layer can route again.

---

## Task Plan

| # | Task | Project | Dependency |
|---|------|---------|------------|
| **Phase 1: Fix the Custody Handoff** | | | |
| 1.1 | `instantiate(slug, requirements=None)` — accept project requirements override | gsdlc | — |
| 1.2 | Installer generates Layer 3 wrapper that parses REQ keys from `specification/requirements.md` and passes to `instantiate()` | gsdlc | 1.1 |
| 1.3 | Installer scaffolds starter `specification/requirements.md` on fresh install | gsdlc | 1.1 |
| 1.4 | Validate: `gen-gaps` on abiogenesis shows project-specific REQ keys, delta > 0 for coverage evaluators | abg | 1.2, 2.2 |
| **Phase 2: Cascade and Verify** | | | |
| 2.1 | Release gsdlc with fix (version bump, tests pass) | gsdlc | 1.1, 1.2, 1.3 |
| 2.2 | Cascade gsdlc into abiogenesis (`gen-install`) | abg | 2.1 |
| 2.3 | Cascade into all dependents (genesis-manager, etc.) | dependents | 2.2 |
| **Phase 3: Clean Up Migration Debris** | | | |
| 3.1 | Evaluate/remove custom Package at `builds/claude_code/code/gtl_spec/packages/abiogenesis.py` — is it dead code or future intent? | abg | 1.4 |
| 3.2 | Remove `pythonpath: builds/claude_code/code` from abiogenesis `genesis.yml` (pre-migration artifact, causes shadowing risk) | abg | 3.1 |
| 3.3 | Reconcile orphaned REQ tags against now-visible coverage checks | abg | 1.4 |
| **Phase 4: Process Fix** | | | |
| 4.1 | Create REQ key for requirements/workflow separation — close the provenance chain that was broken at step one | gsdlc | 2.1 |
| 4.2 | Backlog-to-graph bridge — mechanism for STRATEGY posts that require action to enter the graph as tracked requirements | gsdlc | 4.1 |

## Project Ownership

| Project | Task count | Tasks |
|---------|-----------|-------|
| gsdlc | 6 | 1.1, 1.2, 1.3, 2.1, 4.1, 4.2 |
| abg | 4 | 1.4, 2.2, 3.1, 3.2, 3.3 |
| dependents | 1 | 2.3 |

## Critical Path

```
1.1 (instantiate signature)
 │
 ├──> 1.2 (installer generates wrapper)
 │     │
 │     ├──> 1.3 (scaffold requirements.md)
 │     │
 │     └──> 2.1 (release gsdlc)
 │           │
 │           └──> 2.2 (cascade to abg)
 │                 │
 │                 └──> 1.4 (validate gen-gaps)
 │                       │
 │                       ├──> 3.1, 3.2, 3.3 (cleanup — parallelisable)
 │                       │
 │                       └──> 2.3 (cascade to dependents)
 │
 └──> 4.1, 4.2 (process fix — parallelisable after 2.1)
```

All blocking work is in gsdlc until the cascade. abg work is validation and cleanup.

## Design Notes

### Task 1.1 — `instantiate()` signature change

```python
def instantiate(slug: str, requirements: list[str] | None = None):
    # ...
    _package = Package(
        name=slug,
        # ...
        requirements=requirements if requirements is not None else list(package.requirements),
    )
```

Backward compatible: existing callers without `requirements` parameter get the workflow defaults.

### Task 1.2 — Layer 3 wrapper generation

The installer generates:

```python
# genesis_sdlc-generated — system-owned; rewritten on every redeploy.
from workflows.genesis_sdlc.standard.v{VERSION}.spec import instantiate
from pathlib import Path as _Path
import re as _re

def _load_reqs():
    _p = _Path(__file__).resolve().parents[3] / "specification" / "requirements.md"
    if _p.exists():
        return _re.findall(r"^### (REQ-F-\S+)", _p.read_text(), _re.MULTILINE)
    return []

package, worker = instantiate(slug="{SLUG}", requirements=_load_reqs())
```

- `parents[3]` navigates from `.genesis/gtl_spec/packages/{slug}.py` to workspace root
- Parser extracts `### REQ-F-*` headers — the canonical format in `specification/requirements.md`
- Falls back to empty list if file doesn't exist (fresh install before first `intent -> requirements` iteration)
- System-owned: rewritten on every `gen-install`, so the logic is stable and versioned with the installer

### Task 1.3 — Scaffold

Installer creates `specification/requirements.md` with:

```markdown
# Requirements

Requirements emerge from iterating the intent -> requirements edge.
Each requirement is a `### REQ-F-*` heading followed by acceptance criteria.
```

Only if the file doesn't already exist.

## Validation Criteria

After Phase 2 cascade into abiogenesis:

1. `gen-gaps` reports abiogenesis project-specific REQ keys (REQ-F-EC-*, REQ-F-CORE-*, etc.) in coverage evaluator output
2. `check-req-coverage` checks against 45 project keys, not 33 gsdlc keys
3. `check-impl-coverage` and `check-validates-coverage` check against project keys
4. delta > 0 for any uncovered project REQ key (the system stops lying)
5. Codex criterion #7 satisfied: REQ key in `specification/requirements.md` -> `Package.requirements` -> F_D coverage -> feature vector -> code tag -> test tag -> convergence certificate

## Phase 5: Spec-Derived Test Assurance — The Observation Model

The requirements custody fix (Phases 1-2) ensures F_D evaluates the right requirements. But convergence still only means "code is self-consistent" — not "code fulfills intent." The deeper problem: **intent formation is model-relative**, and the model the system observes against determines whether homeostasis converges on the right target. If the observation model is the code surface, the system converges on itself. If the observation model is spec + design, the system converges on the problem.

### The consciousness loop

The three processing phases (Reflex → Affect → Conscious) form a homeostatic loop:

```
observe(state, model) → evaluate(delta) → intent → new feature vector
                ▲                                        │
                └────────────────────────────────────────┘
```

The **model** in `observe(state, model)` determines what the system sees. For test edges, the model must be **spec + design** — requirements define acceptance, design defines interfaces, and test scenarios are derived from both. If the model is the code itself, observation is circular: the system observes what it built, evaluates against what it built, and generates intent to build more of what it built.

This is the same class of failure as the requirements custody break: the sensor was pointed at the wrong target. Phase 5 ensures the test-generation sensor points at spec + design.

### What the current graph does

The gsdlc standard workflow currently enforces:

- `code → unit_tests`: F_D checks that tests exist and pass. F_P generates tests. **No constraint on what the tests are derived from.**
- `unit_tests → integration_tests`: Same — existence and pass/fail only. **No spec/design context loaded.**
- `user_guide → uat_tests`: UAT is a **pure F_H gate** — human judgment on whether the system solves the problem. No F_P dispatch.

The gap: F_P on test edges currently receives code as primary context. It reverse-engineers tests from implementation. The tests verify what code does, not what was specified.

### What must change

The fix is not more tag checking or coverage counting. It is establishing spec + design as the **observation model** for test generation and evaluation.

| # | Task | Project | Dependency |
|---|------|---------|------------|
| 5.1 | **F_P context for test edges**: `code → unit_tests` and `unit_tests → integration_tests` edges must load `specification/requirements.md` and `builds/*/design/adrs/` as primary context. The F_P actor derives test scenarios from what was specified, not from what was implemented. Code is secondary context (what to test against), not primary (what to test for). | gsdlc | 2.1 |
| 5.2 | **Test-plan artifact**: F_P on integration_tests edge must produce a test-plan section (inline or separate) that maps each test scenario to its source REQ key and design decision. This is the artifact that proves "test came from spec" — not a tag, but a derivation trace. F_D checks that the mapping exists and REQ keys are valid. | gsdlc | 5.1 |
| 5.3 | **F_H criteria for UAT gate**: The `user_guide → uat_tests` edge is pure F_H (human judgment). Define explicit F_H criteria: "Does this system solve the problem stated in intent?" The F_H actor receives intent + requirements as context. If `--human-proxy` is active, the proxy evaluates against intent, not code. | gsdlc | 5.1 |
| 5.4 | **Homeostatic feedback**: When F_D on integration_tests detects a gap (REQ key has no test scenario in the test-plan), the affect signal routes to F_P with spec+design context to generate the missing scenario. When F_H on UAT rejects, the intent feeds back to requirements (the iterate loop narrows). Define the feedback edges explicitly in the graph or document why existing edges suffice. | gsdlc | 5.2, 5.3 |

### How this maps to the consciousness loop

| Loop element | Graph mechanism | Model |
|-------------|----------------|-------|
| **Observe** | F_D on test edges reads test-plan artifact | spec + design (requirements, ADRs) |
| **Evaluate** | F_D computes delta: REQ keys without test scenarios | requirements coverage |
| **Intent** | Affect escalates gap to F_P | spec + design context loaded |
| **New feature vector** | F_P generates test scenarios from spec, not code | spec-derived |
| **Human judgment** | F_H on UAT: "does this solve the problem?" | intent + requirements |

### Why tag checking alone fails

Tasks 5.1 and 5.3 in the previous version of this plan added `# Validates: REQ-F-*` tag checks and coverage counting. These are necessary F_D wiring but insufficient — they verify that a tag exists, not that the tagged test was derived from the requirement. A test reverse-engineered from code can carry a correct `# Validates:` tag and still not test what the requirement specifies. The test-plan artifact (task 5.2) is the mechanism that makes the derivation auditable.

### Why this matters

The iterate loop narrows the problem space:
- **First pass**: intent is broad, requirements are coarse, test-plan covers major scenarios
- **Each iteration**: intent is refined, requirements sharpen, test-plan becomes more specific
- **Convergence**: the system solves the problem as understood, and the test-plan proves derivation from spec

Without spec-derived observation, the iterate loop is closed but the feedback signal is wrong. F_P constructs code that passes tests, but the tests were derived from the code, so the loop is circular. The gradient reports delta=0 but the system hasn't converged on the problem — it has converged on itself.

This is exactly what happened with the requirements custody failure: the system reported convergence against the wrong target. The observation model fix prevents the same class of failure at the test layer.

---

## Updated Project Ownership

| Project | Task count | Tasks |
|---------|-----------|-------|
| gsdlc | 10 | 1.1, 1.2, 1.3, 2.1, 4.1, 4.2, 5.1, 5.2, 5.3, 5.4 |
| abg | 5 | 1.4, 2.2, 3.1, 3.2, 3.3 |
| dependents | 1 | 2.3 |

## What This Does NOT Fix

- GTL primitive change (removing `Package.requirements` from `gtl/core.py`) — deferred to spec-level ADR (Option A from the GAP post)
- Custom graph topology for abiogenesis (bootloader_doc asset, extra edges) — separate concern, evaluated in Task 3.1
- Multi-worker scheduling — deferred, kernel supports it but not exercised
