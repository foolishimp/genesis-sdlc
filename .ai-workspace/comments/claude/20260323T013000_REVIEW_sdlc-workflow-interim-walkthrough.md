# REVIEW: SDLC Workflow Interim Walkthrough — Boot Chain, Graph, and Iterate Loop

**Author**: Claude
**Date**: 2026-03-23T01:30:00+11:00
**Addresses**: `sdlc_graph.py`, `install.py`, `.gsdlc/release/`, `.genesis/`
**For**: all
**Status**: INTERIM — captures state after ABG v1.0 + installer deconstruction fixes

---

## 1. Boot Chain

How a cold Claude Code session becomes operational.

```mermaid
sequenceDiagram
    participant CC as Claude Code
    participant ABG as .genesis/genesis.yml
    participant RC as runtime_contract
    participant DOM as .gsdlc/release/genesis.yml
    participant WRP as project_package.py
    participant SPEC as spec.py (versioned)
    participant PKG as Package + Worker

    CC->>ABG: Read .genesis/genesis.yml
    Note over ABG: Seed config — no package/worker
    ABG->>RC: Follow runtime_contract pointer
    RC->>DOM: .gsdlc/release/genesis.yml
    Note over DOM: package: gtl_spec.packages.project_package:package<br/>worker: gtl_spec.packages.project_package:worker<br/>pythonpath: [.gsdlc/release]
    DOM->>WRP: Import gtl_spec.packages.project_package
    Note over WRP: _load_reqs() → parse REQ-* from specification/requirements.md
    WRP->>SPEC: instantiate(slug, req_keys, platform, src_dir)
    SPEC->>PKG: Returns (Package, Worker)
    PKG->>CC: Engine has typed graph, evaluators, operators
```

**Key insight**: `.genesis/genesis.yml` is a pointer, not a config. ABG writes it as a seed. The GSDLC installer writes `runtime_contract: .gsdlc/release/genesis.yml` into it. That single line connects kernel to domain.

---

## 2. Territory Model

Four territories with distinct ownership and mutation rules.

```mermaid
graph TB
    subgraph KERNEL["<b>.genesis/</b> — ABG kernel (immutable)"]
        direction LR
        K1["genesis/ (8 engine modules)"]
        K2["gtl/ (type system)"]
        K3["genesis.yml (seed → runtime_contract)"]
    end

    subgraph DOMAIN["<b>.gsdlc/release/</b> — Domain methodology (immutable between releases)"]
        direction LR
        D1["workflows/genesis_sdlc/standard/vX_Y_Z/ (versioned spec.py)"]
        D2["gtl_spec/packages/project_package.py (generated wrapper)"]
        D3["genesis.yml (domain contract)"]
        D4["active-workflow.json (baseline pointer)"]
        D5["SDLC_BOOTLOADER.md"]
        D6["operating-standards/"]
    end

    subgraph AUTHORED["<b>specification/ + builds/ + design/ + docs/</b> — Human authored"]
        direction LR
        A1["specification/INTENT.md"]
        A2["specification/requirements.md"]
        A3["specification/feature_decomposition.md"]
        A4["builds/python/src/ + tests/"]
        A5["design/adrs/"]
        A6["docs/USER_GUIDE.md"]
    end

    subgraph RUNTIME["<b>.ai-workspace/</b> — Mutable runtime state"]
        direction LR
        R1["events/events.jsonl"]
        R2["features/active/*.yml"]
        R3["modules/*.yml"]
        R4["comments/claude/ + codex/"]
        R5["reviews/pending/"]
        R6["uat/sandbox_report.json"]
    end

    KERNEL -->|runtime_contract| DOMAIN
    DOMAIN -->|instantiate| AUTHORED
    DOMAIN -->|emit events| RUNTIME

    style KERNEL fill:#e8d5b7,stroke:#8b6914
    style DOMAIN fill:#b7d5e8,stroke:#14698b
    style AUTHORED fill:#d5e8b7,stroke:#698b14
    style RUNTIME fill:#e8b7d5,stroke:#8b1469
```

**Ownership rules**:
| Territory | Owner | Write rule |
|-----------|-------|------------|
| `.genesis/` | ABG installer only | Never edit directly |
| `.gsdlc/release/` | GSDLC installer only | Never edit between releases |
| `specification/` + `builds/` + `design/` + `docs/` | Human + agents | Editable — authored content |
| `.ai-workspace/` | Agents via `emit()` | Append-only events, territory-partitioned posts |

---

## 3. SDLC Graph Topology

10 assets, 9 edges. The spec/design boundary sits at `feature_decomp → design`.

```mermaid
graph LR
    INT[intent<br/><i>INT-*</i>]
    REQ[requirements<br/><i>REQ-*</i>]
    FD[feature_decomp<br/><i>FD-*</i>]
    DES[design<br/><i>DES-*</i>]
    MOD[module_decomp<br/><i>MOD-*</i>]
    CODE[code<br/><i>CODE-*</i>]
    UT[unit_tests<br/><i>TEST-*</i>]
    IT[integration_tests<br/><i>ITEST-*</i>]
    UG[user_guide<br/><i>GUIDE-*</i>]
    UAT[uat_tests<br/><i>UAT-*</i>]

    INT -->|"E1: F_H gate"| REQ
    REQ -->|"E2: F_D + F_P + F_H"| FD
    FD -->|"E3: F_P + F_H"| DES
    DES -->|"E4: F_D + F_P + F_H"| MOD
    MOD -->|"E5: F_D + F_P"| CODE
    CODE <-->|"E6: co-evolve<br/>F_D + F_P"| UT
    UT -->|"E7: F_D + F_P"| IT
    IT -->|"E8: F_D + F_P + F_H"| UG
    UG -->|"E9: pure F_H"| UAT

    style INT fill:#fff3cd,stroke:#856404
    style REQ fill:#fff3cd,stroke:#856404
    style FD fill:#fff3cd,stroke:#856404
    style DES fill:#d1ecf1,stroke:#0c5460
    style MOD fill:#d1ecf1,stroke:#0c5460
    style CODE fill:#d4edda,stroke:#155724
    style UT fill:#d4edda,stroke:#155724
    style IT fill:#f8d7da,stroke:#721c24
    style UG fill:#f8d7da,stroke:#721c24
    style UAT fill:#f8d7da,stroke:#721c24
```

**Colour key**:
- Yellow: WHAT (specification territory — tech-agnostic)
- Blue: WHAT→HOW boundary (design territory)
- Green: HOW (implementation territory — tech-bound)
- Red: ACCEPTANCE (validation + release gate)

### Edge Detail Table

| # | Edge | Evaluators | Gate |
|---|------|-----------|------|
| E1 | intent → requirements | `intent_approved` (F_H) | Human confirms scope |
| E2 | requirements → feature_decomp | `req_coverage` (F_D), `decomp_complete` (F_P), `decomp_approved` (F_H) | REQ coverage + human |
| E3 | feature_decomp → design | `design_coherent` (F_P), `design_approved` (F_H) | ADRs + human |
| E4 | design → module_decomp | `module_coverage` (F_D), `module_schedule` (F_P), `schedule_approved` (F_H) | DAG + human |
| E5 | module_decomp → code | `impl_tags` (F_D), `code_complete` (F_P) | Tag check + agent |
| E6 | code ↔ unit_tests | `tests_pass` (F_D), `validates_tags` (F_D), `e2e_tests_exist` (F_D), `coverage_complete` (F_P) | pytest + tags |
| E7 | unit_tests → integration_tests | `sandbox_report_exists` (F_D), `sandbox_e2e_passed` (F_P) | Sandbox proof |
| E8 | integration_tests → user_guide | `guide_version_current` (F_D), `guide_req_coverage` (F_D), `guide_content_certified` (F_P) | Version + coverage |
| E9 | user_guide → uat_tests | `uat_accepted` (F_H) | Human final gate |

---

## 4. Evaluator Escalation — The Iterate Loop

Every edge converges through the same loop: `iterate(job, evaluator_fn, asset) → (Asset, WorkingSurface)`.

```mermaid
stateDiagram-v2
    [*] --> F_D: Edge selected
    F_D --> PASS_D: All F_D pass
    F_D --> F_P: F_D blocked (ambiguity)

    F_P --> F_D: Artifacts produced → re-check
    F_P --> F_H: Agent stuck (persistent ambiguity)

    PASS_D --> F_P_CHECK: F_P evaluators?
    F_P_CHECK --> F_P_RUN: Yes
    F_P_CHECK --> CONVERGED: No → edge done

    F_P_RUN --> F_D: Re-evaluate after agent work

    F_H --> APPROVED: Human approves
    F_H --> REJECTED: Human rejects

    APPROVED --> F_D: Back to deterministic check
    REJECTED --> [*]: Halt — no retry in session

    CONVERGED --> [*]: delta = 0
```

**Dispatch contract**: The manifest JSON at `fp_manifest_path` is the authoritative F_P dispatch. It carries structured fields (source/target assets, markov conditions, evaluators, contexts, delta). The `prompt` field is a human-readable render. CLAUDE.md is transport convenience.

**Key rule**: F_P does NOT call the event logger. F_P produces artifacts; F_D reads them and emits events.

---

## 5. Traceability Thread

REQ keys are the traceable thread from specification to runtime.

```mermaid
graph TD
    SPEC["specification/requirements.md<br/><code>### REQ-F-AUTH-001</code>"]
    FV["features/active/auth.yml<br/><code>satisfies: [REQ-F-AUTH-001]</code>"]
    ADR["design/adrs/ADR-auth.md<br/><code>Implements: REQ-F-AUTH-001</code>"]
    SRC["src/auth.py<br/><code># Implements: REQ-F-AUTH-001</code>"]
    TST["tests/test_auth.py<br/><code># Validates: REQ-F-AUTH-001</code>"]
    GUIDE["docs/USER_GUIDE.md<br/><code>&lt;!-- Covers: REQ-F-AUTH-001 --&gt;</code>"]

    SPEC -->|"E2: req_coverage (F_D)"| FV
    FV -->|"E3: design_coherent (F_P)"| ADR
    ADR -->|"E5: impl_tags (F_D)"| SRC
    SRC -->|"E6: validates_tags (F_D)"| TST
    TST -->|"E8: guide_req_coverage (F_D)"| GUIDE

    style SPEC fill:#fff3cd
    style FV fill:#fff3cd
    style ADR fill:#d1ecf1
    style SRC fill:#d4edda
    style TST fill:#d4edda
    style GUIDE fill:#f8d7da
```

**Coverage is computable without LLM**: parse REQ keys from requirements.md, check `satisfies:` in feature vectors, grep `# Implements:` and `# Validates:` tags in source/tests, parse `<!-- Covers: -->` in guide. These are all F_D evaluators.

---

## 6. Workflow Commands

```mermaid
flowchart TD
    USER((User))

    USER -->|"go / build / fix"| GS["/gen-start --auto"]
    USER -->|"one step"| GI["/gen-iterate --feature F --edge E"]
    USER -->|"what's broken"| GG["/gen-gaps"]
    USER -->|"status"| GST["/gen-status"]
    USER -->|"approve"| GR["/gen-review --feature F"]

    GS --> LOOP{"Auto-loop:<br/>select edge → iterate → check delta"}
    GI --> SINGLE["Single F_D→F_P→F_H cycle"]
    GG --> DELTA["delta(state, constraints) → work"]
    GST --> STATE["Events, features, edge state"]
    GR --> GATE["F_H gate — present candidate"]

    LOOP -->|"delta > 0"| LOOP
    LOOP -->|"delta = 0 or F_H blocks"| STOP((Stop))
    SINGLE --> STOP
```

---

## 7. Open Design Issues

### 7.1 Edge Topology — Edges 7-9

**Current** (as coded):
```
unit_tests → integration_tests → user_guide → uat_tests
```

**Problem**: This implies integration tests come from unit tests and user guide comes from integration tests. The actual dependency is:
- **integration_tests** should source from **code** (sandbox install + e2e)
- **user_guide** should source from **design** (content) + **integration_tests** (version proof)
- **uat_tests** should source from **requirements** (acceptance) + **user_guide** (documentation proof)

```mermaid
graph LR
    CODE2[code] -->|"sandbox install"| IT2[integration_tests]
    DES2[design] -->|"content source"| UG2[user_guide]
    IT2 -->|"version proof"| UG2
    REQ2[requirements] -->|"acceptance criteria"| UAT2[uat_tests]
    UG2 -->|"documentation proof"| UAT2

    style CODE2 fill:#d4edda
    style DES2 fill:#d1ecf1
    style IT2 fill:#f8d7da
    style UG2 fill:#f8d7da
    style REQ2 fill:#fff3cd
    style UAT2 fill:#f8d7da
```

**Status**: Not yet fixed in sdlc_graph.py. The graph is informational — the real graph comes from spec. This is a design decision to be resolved.

### 7.2 active-workflow.json Placement

Currently at `.gsdlc/release/active-workflow.json` — but this is immutable territory and the file is a mutable pointer. It should either:
- Move to `.ai-workspace/` (mutable territory), or
- Be acknowledged as a controlled exception (installer writes it, nothing else does)

### 7.3 Bootloader Version Reconciliation

Python build ships SDLC_BOOTLOADER v1.1.0. Codex build had v1.2.0. The Codex build is being deleted but any content from v1.2.0 that's valid should be merged up.

### 7.4 builds/python/ Path Duplication in instantiate()

`instantiate()` generates paths like `builds/python/src/` and `builds/python/tests/`. But from the installed project's perspective, the layout is just `src/` and `tests/` (no `builds/` prefix). The top-level module-scope operators use `src/` and `tests/` (correct for installed context), but `instantiate()` rebuilds them as `builds/{platform}/{src_dir}` — which is the source repo layout, not the installed layout.

---

## Summary

The SDLC workflow is architecturally sound: typed graph, evaluator escalation, event stream, traceability. The boot chain is correct once `runtime_contract` wiring is in place. The installer fixes from this session (Finding 1-5 in the deconstruction review) are necessary and sufficient for a clean install.

Remaining work:
1. Edge 7-9 topology redesign
2. active-workflow.json territory decision
3. `instantiate()` path resolution (source repo vs installed layout)
4. Clean install end-to-end validation
