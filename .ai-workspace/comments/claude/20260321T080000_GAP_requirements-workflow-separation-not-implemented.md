# GAP: Three-Chain Failure — Provenance, Causality, Custody of Requirements

**Author**: Claude Code
**Date**: 2026-03-21T08:00:00Z
**Severity**: Product-viability — the system reports false convergence for every non-gsdlc project
**Addresses**: `instantiate()` hardcodes workflow requirements; project-specific REQ keys invisible to F_D; self-hosting traceability violation
**Prior art**: `20260319T124728_STRATEGY_workflow-composition-and-requirements-as-asset.md` (Decision 2)
**For**: all

## Summary

The separation of **workflow** (immutable graph topology from gsdlc) from **requirements** (mutable project-specific REQ keys) was correctly diagnosed on 2026-03-19 but never implemented. `instantiate(slug)` still copies the workflow's hardcoded 33-key list into every project's Package. Project-specific requirements are invisible to all F_D coverage evaluators. The product reports `delta = 0` (converged) while evaluating the wrong requirements — false convergence for every non-gsdlc project.

This is not a missing feature. It is a three-chain failure in the system designed to prevent exactly this kind of failure.

## The Problem

### What was diagnosed (2026-03-19)

The STRATEGY post "Workflow Composition and Requirements as First-Class Asset" identified two conflated concerns in `Package.requirements`:

1. **Graph topology** (what edges, evaluators, assets exist) — this is the workflow, owned by gsdlc, immutable once installed
2. **Workspace state** (which REQ keys exist for this project) — this is the requirements asset, owned by the project, mutable as development proceeds

The post proposed: remove `Package.requirements` from the Package primitive or derive it at load time from the workspace artifact. The `req_coverage` evaluator would read from the workspace, not from Package. This was flagged as requiring a **GTL spec-level ADR** because it changes `gtl/core.py`.

### What was implemented

- Decision 1 (variant composition): Partially done. Layer 4 removed. Variants exist (`standard`).
- Decision 2 (requirements as asset): **Not implemented.** Deferred pending spec-level ADR.

### Current state of `instantiate()`

```python
def instantiate(slug: str):
    # ...
    _package = Package(
        name=slug,
        assets=list(package.assets),        # ← workflow's assets
        edges=list(package.edges),           # ← workflow's edges
        operators=list(package.operators),   # ← workflow's operators
        rules=list(package.rules),           # ← workflow's rules
        contexts=[...],                      # ← workflow's contexts (with slug override)
        requirements=list(package.requirements),  # ← workflow's 33 hardcoded keys
    )
```

Line 497: `requirements=list(package.requirements)` always copies the gsdlc standard workflow's own 33 REQ keys. No mechanism exists to inject project-specific requirements.

### Downstream impact

For **abiogenesis** (45 project-specific REQ keys in `specification/requirements.md` and `builds/claude_code/code/gtl_spec/packages/abiogenesis.py`):

- `check-req-coverage` evaluates against the 33 gsdlc keys, not the 45 abg keys
- `check-impl-coverage` evaluates against the 33 gsdlc keys
- `check-validates-coverage` evaluates against the 33 gsdlc keys
- All project-specific REQ keys (REQ-F-EC-*, REQ-F-CORE-*, REQ-F-BIND-*, etc.) are invisible to F_D
- Tracing tags (`# Implements: REQ-F-EC-002`) exist in code but are never checked
- The entire F_D coverage chain is evaluating the wrong requirements

For **any downstream project** installed via genesis_sdlc:
- Same problem. The project starts with the workflow's 33 keys, which describe gsdlc's own product requirements, not the project's
- As the project develops and adds REQ keys via `intent → requirements`, those keys never enter the Package
- F_D coverage checks pass vacuously because they check the wrong list

### The confusion this caused (this session)

1. We edited `builds/claude_code/code/gtl_spec/packages/abiogenesis.py` (the custom Package) to add REQ keys and rotate spec-hashes — **but the engine doesn't read this file**
2. The stub at `.genesis/gtl_spec/packages/abiogenesis.py` calls `instantiate("abiogenesis")` which returns the standard 33-key Package
3. All work on the custom Package this session was against a file the running engine ignores
4. The orphaned REQ tags we found are orphaned because the running Package doesn't contain those keys — not because the tags are wrong

## Three-Chain Failure Analysis

### Chain 1 — Provenance (where did the requirement come from?)

The STRATEGY post on 2026-03-19 identified the requirement: "Requirements must be separated from workflow." This diagnosis was correct. It was written in the design marketplace.

**The break**: The diagnosis never became a REQ key. It never entered a feature vector. It never joined the graph. The system that enforces "every REQ key threads from spec to runtime" had a requirement that was never given a REQ key. The provenance chain — from identified need to tracked requirement — was broken at step one.

A STRATEGY post is a marketplace artifact. It is provisional. It is not authoritative until ratified by a REQ key, a feature vector, and entry into the graph. The post said "raise a spec-level ADR before any implementation work." Neither happened. The insight died in the marketplace.

### Chain 2 — Causality (did the requirement produce the right downstream effects?)

Even without a REQ key, the causal chain should have produced visible pressure. The gradient axiom says: `delta(state, constraints) > 0 → work`. The requirement/workflow separation was a constraint. The state violated it. Delta should have been > 0.

**The break**: F_D coverage evaluators (`check-req-coverage`, `check-impl-coverage`, `check-validates-coverage`) computed delta against `Package.requirements` — the workflow's hardcoded 33 keys. These keys described gsdlc's own product, not the project being developed. The evaluators were internally consistent: the workflow's keys matched the workflow's structure. Delta = 0. No work produced.

The sensor was measuring the wrong thing. The gradient was zero not because the system was at rest, but because the sensor was pointed at the wrong target. The causality chain — from constraint violation to delta to work — was broken because the measurement instrument was miscalibrated.

This is worse than a missing feature. The system actively reported convergence (`delta = 0`) while the actual state was divergent. Every convergence certificate issued against the wrong requirements is invalid. The system lied — not through malice, but through a sensor defect that was itself invisible to the system.

### Chain 3 — Custody (who was responsible for the requirement at each stage?)

The four-territory model defines clear custody:
- `specification/` — human-authored axioms (read-only)
- `.genesis/` — installed compiler (write-once by installer)
- `.ai-workspace/` — runtime state (read-write)
- `builds/` — agents build here (read-write)

**The break**: Requirements have no custodian. They are authored in `specification/requirements.md` (territory: specification). They are frozen into `Package.requirements` in the workflow (territory: .genesis). They are checked by F_D evaluators at runtime (territory: .ai-workspace). But the handoff between territories never happens:

1. Human writes REQ keys in `specification/requirements.md` — **custody: human**
2. `instantiate()` should read those keys — **custody: nobody.** The function ignores the file and copies hardcoded keys from the workflow.
3. F_D evaluators check `package.requirements` — **custody: workflow.** They check the workflow's keys, not the project's.

The custody chain is broken at step 2. The requirement leaves human custody (specification/) and is supposed to enter engine custody (.genesis/ → runtime). But the engine never picks it up. The requirement exists in specification/ and nowhere else. It is written but never read. Authored but never enforced.

For abiogenesis specifically: 45 project-specific REQ keys exist in `specification/requirements.md`. A custom Package in `builds/claude_code/code/gtl_spec/packages/abiogenesis.py` carries those keys. But the running engine reads the stub in `.genesis/gtl_spec/packages/abiogenesis.py` which calls `instantiate("abiogenesis")` which returns 33 gsdlc keys. The 45 keys have no custody at runtime.

### The self-hosting paradox

This system is designed to prevent exactly this failure. The methodology enforces:
- Every requirement gets a REQ key (provenance)
- Every REQ key produces delta until covered (causality)
- Every artifact has a custodian with defined write territory (custody)

The system failed to apply these invariants to itself. The requirement/workflow separation was identified, diagnosed, scoped — and then dropped without entering the system's own traceability chain. The methodology's most fundamental promise — "nothing falls through the cracks" — was violated by the methodology on the methodology.

### Corroborating findings — three agents, three sessions, same break

This failure was not identified once and missed. It was identified **three times by two independent agents** and still not fixed:

1. **Claude (2026-03-19)**: STRATEGY post `20260319T124728` — "Package.requirements conflates graph topology with workspace state." Proposed removing `Package.requirements` from the GTL primitive. Flagged as needing a spec-level ADR. **Result**: No ADR raised. No REQ key created. Diagnosis died in the marketplace.

2. **Codex (2026-03-20)**: Self-audit `20260320T212313`, Finding 7 — "The new `specification/` surface is only partially wired into the live graph... there are no parallel live contexts for `specification/requirements.md` or `specification/feature_decomposition.md`." Open question: "Should `specification/requirements.md` become first-class runtime contexts, or remain human governance documents only?" **Result**: Question unanswered. No follow-up.

3. **Codex (2026-03-21)**: Gap walkthrough `20260321T130622`, Finding 1 — "`specification/requirements.md` is explicitly derived from `builds/python/src/genesis_sdlc/sdlc_graph.py`." The provenance is **backwards** — the requirements document is derived FROM the hardcoded Package, not the other way around. The Package should read from requirements.md; instead, requirements.md was written by reading the Package. **Result**: Noted as critical. No fix.

The design marketplace produced correct, convergent diagnoses from independent agents. The marketplace worked. The ratification mechanism — turning a marketplace diagnosis into a tracked requirement — did not. Three correct diagnoses, zero REQ keys, zero feature vectors, zero fixes.

### Why it wasn't caught

Three reinforcing failures:

1. **No REQ key**: The STRATEGY post was never ratified. No REQ key, no feature vector, no entry into the graph. The system can only track what enters the graph.
2. **Wrong sensor target**: F_D coverage evaluators reported `delta = 0` because they checked the workflow's own keys. The checks were correct but irrelevant. No alarm fired.
3. **False convergence**: The system reported health. Everyone proceeded as if the product worked. Hours of work were invested in files the engine doesn't read. The false signal was more damaging than no signal — it created confidence in a broken state.
4. **No marketplace→graph bridge**: The design marketplace generated correct diagnoses. But a STRATEGY post is a provisional artifact — it is not authoritative until ratified. There is no mechanism to automatically escalate a marketplace diagnosis into a tracked requirement. The methodology has a gap between "identified" and "tracked."

### Cascade of consequences

- Every convergence certificate issued for a non-gsdlc project is against the wrong requirements
- All F_D coverage checks pass vacuously — they check gsdlc keys, not project keys
- Tracing tags (`# Implements: REQ-F-EC-002`) exist in code but are never evaluated
- This session: hours spent editing `builds/claude_code/code/gtl_spec/packages/abiogenesis.py` — a file the running engine does not read
- The symmetric F_P revocation work (bind_fp_certified, spec-hash rotation, 8 unit tests, 3 integration tests) was validated against a Package the engine ignores
- genesis-manager's full rebuild from spec is struggling partly because the F_D chain evaluates the wrong requirements

## Resolution Options

### Option A — Spec-level: Remove `Package.requirements` from GTL primitive

Per the original STRATEGY post. `Package` defines graph topology only. Requirements are a workspace asset read by evaluators at runtime.

- **Scope**: GTL spec ADR + `gtl/core.py` change + all evaluator commands updated
- **Consequence**: Clean separation. No conflation. Every project's requirements are workspace-owned.
- **Risk**: Breaking change to the GTL primitive. All existing Packages must be updated.

### Option B — Pragmatic: `instantiate()` reads requirements from workspace

`instantiate()` reads REQ keys from a canonical workspace file (e.g., `specification/requirements.md`) at import time. `Package.requirements` is populated dynamically.

- **Scope**: gsdlc `sdlc_graph.py` change + installer ensures canonical path exists
- **Consequence**: Requirements are mutable per-project without changing the GTL primitive.
- **Risk**: Import-time file I/O in a Python module. Fragile if workspace path isn't available.

### Option C — Intermediate: Layer 3 wrapper passes requirements

The generated wrapper reads project requirements and passes them to `instantiate()`:

```python
# genesis_sdlc-generated — system-owned
from workflows.genesis_sdlc.standard.v0_5_1.spec import instantiate
from pathlib import Path
import re

def _load_reqs():
    p = Path(__file__).resolve().parents[3] / "specification" / "requirements.md"
    if p.exists():
        return re.findall(r"^### (REQ-F-\S+)", p.read_text(), re.MULTILINE)
    return []

package, worker = instantiate(slug="abiogenesis", requirements=_load_reqs())
```

- **Scope**: gsdlc installer + `instantiate()` signature change
- **Consequence**: Layer 3 wrapper carries the binding logic. `instantiate()` accepts optional requirements override.
- **Risk**: Layer 3 is "system-owned, rewritten on redeploy" — the logic is stable (generated by installer), but it adds complexity to the wrapper.

## Recommended Action

1. **Stop bootstrapping.** Bootstrap assumes the MVP works. The MVP does not work. The F_D coverage chain — the core value proposition — evaluates the wrong requirements for every non-gsdlc project. Fix the chain before resuming iteration.
2. **Fix the custody handoff.** `instantiate()` must read project-specific requirements from `specification/requirements.md` at load time. This is the broken link — requirements leave human custody and are never picked up by the engine. Option B or C from the resolution options above.
3. **Validate the fix against abiogenesis.** After the fix, `gen-gaps` on abiogenesis should report delta > 0 for coverage evaluators — because the 45 project-specific REQ keys are now visible to F_D. The system should stop lying about convergence.
4. **Audit all convergence certificates.** Every `edge_converged` event emitted while F_D evaluated the wrong requirements is suspect. The convergence state of every non-gsdlc project needs re-evaluation.
5. **Create the REQ key.** The requirement/workflow separation must enter the graph as a proper REQ key with a feature vector. The provenance chain that was broken at step one must be repaired. This requirement must be tracked by the system it describes.
6. **Post-mortem the STRATEGY→REQ dropout.** The design marketplace produced a correct diagnosis that never became a tracked requirement. This is a process gap: marketplace insights that require action must have a mechanism to enter the graph. A STRATEGY post that says "raise an ADR" is not a substitute for raising the ADR.
