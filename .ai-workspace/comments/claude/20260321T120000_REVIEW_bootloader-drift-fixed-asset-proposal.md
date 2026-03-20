# REVIEW: SDLC bootloader drift fixed + bootloader-as-asset workflow

**Author**: claude
**Date**: 2026-03-21
**Addresses**: 20260320T183000_REVIEW_bootloader-split-completed.md
**For**: all

## Summary

The bootloader split (GTL + SDLC) established clean ownership boundaries. However, SDLC_BOOTLOADER.md immediately drifted from the actual graph — phantom assets (`basis_projections`, `design_recommendations`, `cicd`, `telemetry`) that never existed in `sdlc_graph.py`. This drift is now fixed. The structural problem — hand-maintained docs with no F_D evaluator — remains. Proposal: make bootloaders proper graph assets.

## Drift fixed (immediate)

Four sections of `SDLC_BOOTLOADER.md` referenced assets that don't exist in the implemented graph:

| Section | What was wrong | What it says now |
|---------|---------------|-----------------|
| §XIII Feature vector | Included `basis_proj`, `cicd`, `telemetry` | Matches actual 10-asset chain |
| §XIV Graph diagram | Showed aspirational multi-branch topology (Test Cases, CI/CD, Running System, Telemetry, Observer loop) | Shows actual linear topology with verification tail |
| §XIV Zoom profiles | `Basis Proj` in Full and Standard | Full includes `Integration → Guide → UAT` |
| §XIV Standard profile | Referenced `design_recommendations`, `basis_projections`, version "v2.9" | Matches `sdlc_graph.py` edge names exactly |

Same fixes applied to `CLAUDE.md` (which carries the installed copy). ADR-004 references to `basis_projections` left intact — they document the historical design decision to collapse that node.

## Actual install workflow (as-built)

The install chain is a two-stage cascade. Each stage is idempotent — safe to re-run, marker-bounded, legacy-aware.

### Stage 1: abiogenesis (`gen-install.py`)

```
abg gen-install.py --target <project>
    │
    ├─ 1. Install engine (.genesis/gtl_spec/, .genesis/genesis.yml)
    ├─ 2. Scaffold builds/<platform>/
    └─ 3. install_claude_md()
           │
           ├─ Read .genesis/gtl_spec/GTL_BOOTLOADER.md
           ├─ If <!-- GENESIS_BOOTLOADER_START --> found → remove legacy block
           ├─ If <!-- GTL_BOOTLOADER_START --> found → replace between markers
           ├─ Else → append with markers
           └─ Result: CLAUDE.md has GTL bootloader (§I–XI)
```

### Stage 2: genesis_sdlc (`install.py`)

```
genesis_sdlc.install --target <project> --slug <name>
    │
    ├─ 1. _run_abiogenesis_installer()     → delegates to Stage 1
    ├─ 2. install_workflow_release()        → versioned workflow (Layer 2, immutable)
    ├─ 3. install_active_workflow()         → active baseline pointer + migration detect
    ├─ 4. install_immutable_spec()          → spec/genesis_sdlc.py compat shim
    ├─ 5. install_sdlc_starter_spec()       → generated wrapper (Layer 3, rewritable)
    ├─ 6. install_commands()                → slash commands (.claude/commands/)
    ├─ 7. install_claude_md()
    │      │
    │      ├─ Read SDLC_BOOTLOADER.md (from genesis_sdlc source)
    │      ├─ Prepend operating protocol (slug + platform)
    │      ├─ If <!-- GENESIS_BOOTLOADER_START --> found → remove legacy block
    │      ├─ If <!-- SDLC_BOOTLOADER_START --> found → replace between markers
    │      ├─ Else → append with markers
    │      └─ Result: CLAUDE.md now has GTL (§I–XI) + SDLC (§XII–XX)
    ├─ 8. install_operating_standards()     → .ai-workspace/operating-standards/
    └─ 9. Create workspace dirs             → features/, reviews/, comments/, backlog/
```

### Cascade order

```
abiogenesis (abg)
    └─→ genesis_sdlc (gsdlc)
            └─→ all dependent projects
                    (each gets reinstalled via genesis_sdlc.install)
```

The cascade is: `abg → gsdlc → dependents`. Never `abg → dependents` directly. gsdlc's installer calls abg's installer internally (step 1), so a single `genesis_sdlc.install` on a dependent project cascades both stages.

### CLAUDE.md marker layout (post-install)

```markdown
# CLAUDE.md — {project_name}
...project-local header...

<!-- GTL_BOOTLOADER_START -->
# GTL Bootloader (§I–XI) — universal formal system
...four primitives, iterate, evaluators, event stream...
<!-- GTL_BOOTLOADER_END -->

<!-- SDLC_BOOTLOADER_START -->
## Operating protocol
...slug-specific command table...

# SDLC Bootloader (§XII–XX) — SDLC instantiation
...graph topology, feature vectors, profiles, workspace territory...
<!-- SDLC_BOOTLOADER_END -->
```

## Structural problem: bootloader has no F_D evaluator

The split solved ownership (who writes which bootloader). It did not solve consistency (does the bootloader match the graph?). Today:

- `sdlc_graph.py` has 10 assets, 9 edges, 25 evaluators — all F_D checkable
- `SDLC_BOOTLOADER.md` references asset names, edge chains, zoom profiles — none F_D checked
- Drift is detected by humans reading diffs, not by the system

This is the same failure mode as untested code: it works until it doesn't, and you find out too late.

## Proposed: bootloader_doc as graph asset

Add `bootloader_doc` to the SDLC graph:

```
design ──→ module_decomp ──→ code ↔ unit_tests ──→ integration_tests
   │                                                      ↑
   └──→ bootloader_doc ──────────────────────────────────┘
```

| Component | Detail |
|-----------|--------|
| **Asset** | `bootloader_doc` (BOOTDOC-{SEQ}), lineage=[design] |
| **Edge** | `design→bootloader_doc` |
| **F_D evaluator** | `graph_consistency` — parse asset/edge names from sdlc_graph.py, check they appear in SDLC_BOOTLOADER.md |
| **F_P evaluator** | `synthesize_bootloader` — agent renders specification/ content into bootloader markdown |
| **Join** | `integration_tests.lineage` becomes `[unit_tests, bootloader_doc]` — sandbox install requires consistent bootloader |
| **Context** | `specification_dir` — workspace://specification/ |

Same pattern for GTL_BOOTLOADER.md in abiogenesis (checking against `gtl/core.py` types).

The join at `integration_tests` is structurally correct: the sandbox e2e test runs `genesis_sdlc.install`, which copies the bootloader into the target's CLAUDE.md. If the bootloader is stale, the installed CLAUDE.md is stale, and the sandbox test is testing against wrong constraints.

## Recommended Action

1. **Done**: SDLC_BOOTLOADER.md drift fixed in both files. Cascade to dependents on next install.
2. **Next**: Implement `bootloader_doc` asset via `/gen-start` — this is a proper feature requiring a feature vector, design edge, and the new F_D evaluator.
