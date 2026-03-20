# genesis_sdlc — Feature Decomposition

**Traces to**: INT-001, INT-002, INT-003
**Requirements**: specification/requirements.md
**REQ key registry**: builds/python/src/genesis_sdlc/sdlc_graph.py
**Status**: Approved
**Date**: 2026-03-20

---

## Feature Map

| Feature | Title | Satisfies | Depends On | MVP |
|---------|-------|-----------|------------|-----|
| REQ-F-GRAPH | SDLC Graph Definition | GRAPH-001, GRAPH-002 | — | Y |
| REQ-F-BOOT | Project Bootstrap | BOOT-001, BOOT-002 | GRAPH | Y |
| REQ-F-BOOT-V2 | Three-Layer Install Architecture | BOOT-003, BOOT-004, BOOT-005, BOOT-006 | BOOT, GRAPH | Y |
| REQ-F-CMD | Engine Commands | CMD-001, CMD-002, CMD-003 | BOOT | Y |
| REQ-F-GATE | Human Approval Gates | GATE-001 | CMD | Y |
| REQ-F-TAG | Code and Test Traceability Tags | TAG-001, TAG-002 | CMD | Y |
| REQ-F-COV | REQ Key Coverage Enforcement | COV-001 | GRAPH | Y |
| REQ-F-TEST | Testing — Integration-Primary Surface | TEST-001, TEST-002 | GRAPH, GATE | Y |
| REQ-F-TEST-V2 | Test Version Sandboxing | TEST-003 | TEST, BOOT-V2 | Y |
| REQ-F-UAT | UAT — Sandbox Proof Required to Ship | UAT-001 | GRAPH, GATE | Y |
| REQ-F-INT-003 | Integration Tests + User Guide as Graph Assets | UAT-002, UAT-003, DOCS-002 | UAT, DOCS, GRAPH | Y |
| REQ-F-DOCS | User Documentation | DOCS-001 | CMD, GRAPH | Y |
| REQ-F-BACKLOG | Backlog — Pre-Intent Holding Area | BACKLOG-001..004 | — | Y |
| REQ-F-MDECOMP | Module Decomposition and Build Scheduling | MDECOMP-001..005 | GRAPH, GATE | Y |

---

## Dependency DAG

```
REQ-F-GRAPH
    ├── REQ-F-BOOT
    │    └── REQ-F-BOOT-V2    (extends install architecture)
    │         └── REQ-F-TEST-V2  (PYTHONPATH sandboxing needs three-layer install)
    ├── REQ-F-COV              (needs REQ keys from Package)
    ├── REQ-F-TEST             (needs graph for evaluator definitions)
    ├── REQ-F-UAT              (needs graph for uat_tests edge)
    │    └── REQ-F-INT-003     (inserts integration_tests + user_guide into graph)
    ├── REQ-F-MDECOMP          (needs graph for module_decomp asset)
    └── REQ-F-BOOT → REQ-F-CMD  (needs bootstrap to run commands)
         ├── REQ-F-GATE        (needs commands for F_H protocol)
         ├── REQ-F-TAG         (needs check-tags command)
         └── REQ-F-DOCS        (needs commands to document)

REQ-F-BACKLOG                  (independent — pre-intent holding area)
```

**Build order** (topological sort):
1. REQ-F-GRAPH, REQ-F-BACKLOG (no dependencies)
2. REQ-F-BOOT, REQ-F-COV, REQ-F-TEST, REQ-F-UAT, REQ-F-MDECOMP (depend on GRAPH)
3. REQ-F-BOOT-V2 (depends on BOOT)
4. REQ-F-CMD (depends on BOOT)
5. REQ-F-GATE, REQ-F-TAG, REQ-F-DOCS (depend on CMD)
6. REQ-F-TEST-V2 (depends on TEST + BOOT-V2)
7. REQ-F-INT-003 (depends on UAT + DOCS + GRAPH)

---

## MVP Scope

All 14 features are MVP. This is the minimum standard SDLC package that provides a complete graph from intent through UAT with convergence enforcement at every edge.

**Deferred** (V2+):
- Variant evolution model (REQ-F-VAR-*, REQ-F-PROV-* — proposed, not yet in Package registry)
- CI/CD and telemetry graph extensions
- Multi-agent coordination
- Package distribution via registry

---

## Module Mapping

The genesis_sdlc implementation consists of a single Python package. Features map to implementation modules as follows:

| Module | Primary Features | Key Functions |
|--------|-----------------|---------------|
| `install.py` | BOOT, BOOT-V2 | `install()`, `install_commands()`, `install_claude_md()`, `install_operating_standards()`, `_migrate_provenance()`, `_verify()` |
| `sdlc_graph.py` | GRAPH, MDECOMP | `package`, `worker`, `instantiate()` — the Package definition and all evaluators |
| `__init__.py` | — | Version and public exports |

**Supplementary** (not genesis_sdlc source — these are the abiogenesis engine, installed at `.genesis/`):
- `genesis/__main__.py` — CLI: `gen-start`, `gen-iterate`, `gen-gaps`, `emit-event`, `check-tags`, `check-*-coverage`
- `genesis/bind.py` — `bind_fd()`, `bind_fp()`, `bind_fh()`, evaluator execution
- `genesis/schedule.py` — `delta()`, `iterate()`, `schedule()`
- `genesis/commands.py` — `gen_gaps()`, `gen_iterate()`, `gen_start()`
- `genesis/core.py` — `emit()`, `project()`, `EventStream`, `ContextResolver`

---

## Feature Details

### REQ-F-GRAPH — SDLC Graph Definition

The GTL Package at `builds/python/src/genesis_sdlc/sdlc_graph.py` defines the typed asset graph. This is the constitutional source — all other features implement or enforce what the Package declares.

**Key artifacts**: 10 assets with markov conditions, 9 edges with evaluators, 6 operators (1 F_P, 1 F_H, 4 F_D), 5 contexts.

### REQ-F-BOOT — Project Bootstrap

The installer (`install.py`) copies the engine, generates config, creates workspace directories, and installs operating standards and commands. Idempotent — safe to re-run.

### REQ-F-BOOT-V2 — Three-Layer Install Architecture

Separates immutable methodology spec (Layer 1: `.genesis/spec/`), versioned release snapshot (Layer 2: `.genesis/workflows/genesis_sdlc/standard/v{VERSION}/`), and mutable local spec (Layer 3: `.genesis/gtl_spec/packages/`). ADR-008 records the four-territory model.

### REQ-F-CMD — Engine Commands

Three commands as named compositions over engine functions. `gen-gaps` is pure observation. `gen-iterate` is one cycle. `gen-start` is the auto-loop.

### REQ-F-GATE — Human Approval Gates

F_H evaluators at spec/design boundaries. The ordering invariant (F_D→F_P→F_H) prevents wasted review. Proxy mode substitutes the LLM with audit trail.

### REQ-F-TAG — Traceability Tags

`# Implements: REQ-*` in source, `# Validates: REQ-*` in tests. Two F_D evaluators enforce presence. Pure grep — no LLM.

### REQ-F-COV — Coverage Enforcement

Every REQ key in Package.requirements must appear in at least one feature vector's `satisfies:` field. F_D check via `check-req-coverage`.

### REQ-F-TEST — Integration-Primary Test Surface

E2E and integration tests are the primary evidence surface. Unit tests supplement for write-primitive invariants only. `e2e_tests_exist` F_D enforces minimum.

### REQ-F-TEST-V2 — Test Version Sandboxing

F_D evaluator commands pin `PYTHONPATH=builds/python/src/:.genesis` so tests import from the release candidate source tree, not stale installs.

### REQ-F-UAT — Sandbox Proof Required to Ship

Unit tests alone do not satisfy UAT. Sandbox install + e2e run is the acceptance proof. No release without it.

### REQ-F-INT-003 — Integration Tests + User Guide as Graph Assets

Inserts `integration_tests` and `user_guide` as first-class assets between `unit_tests` and `uat_tests`. Separates deterministic sandbox proof from human judgment. User guide has F_D version/coverage checks.

### REQ-F-DOCS — User Documentation

`docs/USER_GUIDE.md` with install steps, first session walkthrough, command reference, operating loop, and recovery paths.

### REQ-F-BACKLOG — Pre-Intent Holding Area

`.ai-workspace/backlog/BL-*.yml` — ideas in gestation before formal intent. `gen backlog list` and `gen backlog promote` commands. Sensory system surfaces ready items.

### REQ-F-MDECOMP — Module Decomposition

Inserts `module_decomp` between `design` and `code`. Decomposes design into modules with dependency DAG and build order. F_H gate ensures schedule is approved before construction.

---

## Coverage Summary

```
Requirements: 31 REQ keys defined
Covered:      31/31  [==========]  100%
Gaps:         (none)
Features:     14 vectors — all completed
```
