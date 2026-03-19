# ADR-007: Integration Tests and User Guide as First-Class Graph Assets

**Implements**: REQ-F-UAT-002, REQ-F-UAT-003, REQ-F-DOCS-002
**Status**: Accepted
**Date**: 2026-03-19
**Intent**: INT-003

---

## Context

The v0.2.0 graph had `unit_tests → uat_tests` as a single edge. The sandbox e2e run was an F_P evaluator inside the UAT job — meaning sandbox proof was treated as an agent assessment, not a deterministic convergence gate. The user guide (`docs/USER_GUIDE.md`) had a REQ key (REQ-F-DOCS-001) but no graph asset, no F_D checks, and no F_P certification. Both were observable but not structurally blocking.

Two failure modes resulted:
1. Sandbox results could be claimed without a verifiable structured report
2. The user guide drifted (v0.1.3 while codebase was at v0.2.0) with no enforcement

---

## Decision

Insert two new assets into the graph between `unit_tests` and `uat_tests`:

```
code ↔ unit_tests → integration_tests → user_guide → uat_tests
```

**`integration_tests`** (REQ-F-UAT-002):
- Markov: `[sandbox_install_passes, e2e_scenarios_pass]`
- F_D: `sandbox_report_exists` — reads `.ai-workspace/uat/sandbox_report.json`, asserts `all_pass: true` and `install_success: true`
- F_P: `sandbox_e2e_passed` — installs into fresh `/tmp/uat_sandbox_*`, runs `pytest -m e2e`, writes structured JSON report
- No F_H gate — sandbox pass is deterministic, not a judgment call

**`user_guide`** (REQ-F-DOCS-002):
- Markov: `[version_current, req_coverage_tagged, content_certified]`
- F_D: `guide_version_current` — checks version string in `docs/USER_GUIDE.md` matches `install.py:VERSION`
- F_D: `guide_req_coverage` — checks `<!-- Covers: REQ-F-* -->` tags are present
- F_P: `guide_content_certified` — certifies coherent coverage of install, first session, commands, operating loop, recovery
- F_H gate (via `integration_tests→user_guide` edge) — human approves guide before shipping

**`uat_tests`** (REQ-F-UAT-003):
- Markov simplified to `[accepted_by_human]` — sandbox conditions move to integration_tests
- F_H only on `user_guide→uat_tests` edge — pure human gate
- Human reviews sandbox report and user guide before approving the release

---

## Consequences

**Positive:**
- Sandbox e2e is now a deterministic blocking gate (`sandbox_report_exists` F_D)
- User guide version currency is enforced before shipping
- UAT is clearly scoped: human approves once evidence is assembled, not while assembling it
- Graph grows from 8 assets/7 edges to 10 assets/9 edges/9 jobs

**Negative:**
- Release process is longer — two new convergence gates must pass
- `docs/USER_GUIDE.md` must be maintained per release (version bump + REQ coverage tags)

---

## Alternatives Considered

**Keep UAT as a single edge with all three evaluator types (status quo):** Rejected — this conflates construction (running the sandbox) with human judgment (approving the release). F_P and F_H on the same edge means the human is approving evidence that may still be assembling.

**Move sandbox entirely to CI/CD (not in graph):** Out of scope for V1 (no CI/CD asset). Deferred.
