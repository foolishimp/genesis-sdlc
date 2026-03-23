# HANDOFF: Installer Bug Fixes + Graph Topology Redesign Specification

**Author**: Claude
**Date**: 2026-03-23T05:00:00+11:00
**Session**: Continuation from corrupted-install forensics session
**For**: Jim (morning review) + Codex

---

## What was done this session

Two work streams: (1) fix the installer to produce a clean install, (2) write the graph topology redesign specification.

---

## Work Stream 1: Installer Bug Fixes

### Commit: `b6c23af`

```
fix: installer path bugs and runtime contract wiring for ABG v1.0
```

**5 bugs fixed, reviewed by Codex, committed:**

| # | Bug | File | Fix |
|---|-----|------|-----|
| 1 | `gtl_bootloader` pointed to non-existent `.genesis/gtl_spec/GTL_BOOTLOADER.md` | sdlc_graph.py:61 | → `workspace://CLAUDE.md` (transport compromise, not final) |
| 2 | `design_adrs` had source-repo prefix `builds/python/` | sdlc_graph.py:85 | → `workspace://design/adrs/` |
| 3 | `instantiate()` adr_path hardcoded source layout | sdlc_graph.py:490 | → `"design/adrs"` |
| 4 | `.ai-workspace/modules/` not scaffolded | install.py:1132 | Added to workspace dirs |
| 5 | `migrate_full_copy()` used undefined `source_path` | install.py:513,526 | → `wrapper_path` |

**Additional installer changes** (from prior session, survived revert):
- `_wire_runtime_contract()` — the #1 hard blocker for ABG v1.0 boot chain
- Removed `install_immutable_spec()` (dead code)
- Removed legacy `.genesis/gtl_spec/` references
- Source root detection fix
- Structured project scaffolding system
- CLAUDE.md template updates

### Codex review findings that shaped the commit

1. **Fix 2 was initially wrong** — I changed module-scope `this_spec` to `workspace://CLAUDE.md`, collapsing two constitutional surfaces (GTL law + SDLC spec) into the same file. Codex caught it. Reverted: `this_spec` stays at `workspace://builds/python/src/genesis_sdlc/sdlc_graph.py` for self-hosting. Installed projects use `_this_spec` from `instantiate()` which correctly points to the generated wrapper.

2. **Fix 1 is a transport compromise** — `gtl_bootloader` → `CLAUDE.md` works mechanically but conflates GTL bootloader with project header + SDLC bootloader. Acceptable as interim, not final.

3. **ABG still accepts `--project-slug`** — my rationale that "ABG v1.0 doesn't accept it" was wrong. It just doesn't need it for kernel install. Change approved, rationale corrected.

### Verification

Clean install into `test_install/`:
- Zero errors
- 10 assets, 9 edges (current graph — bootloader not yet added)
- All 6 context locators resolve to existing paths
- Boot chain: `.genesis/genesis.yml` → `runtime_contract: .gsdlc/release/genesis.yml` → Package → Worker
- Requirements parsed from scaffolded `specification/requirements.md`

### Root-level self-hosting files

The genesis_sdlc repo root still has flushed (deleted, unstaged) `.genesis/`, `.gsdlc/`, `.claude/commands/`, and `CLAUDE.md`. These need a reinstall of genesis_sdlc into itself — separate from the test_install work.

---

## Work Stream 2: Graph Topology Redesign Specification

### Strategy post written

```
.ai-workspace/comments/claude/20260323T040000_STRATEGY_graph-topology-redesign-specification.md
```

~400 lines covering:

### Key design decisions in the spec

**1. Three-concern separation**

The graph currently conflates:
- **Artifact lineage** (what is this asset derived from?)
- **Evidence prerequisites** (what must converge before this edge fires?)
- **Delivery ordering** (implicit from topology)

The redesign makes each explicit. Lineage lives in `Asset.lineage`. Prerequisites live in multi-source `Edge.source`. Delivery falls out from the DAG.

**2. Four changed edges**

| Edge | Was | Now | Creative input | Evidence gate |
|------|-----|-----|---------------|--------------|
| E7 | unit_tests → integration_tests | [code, unit_tests] → integration_tests | code | unit_tests |
| E8 | (new) | [requirements, design, integration_tests] → bootloader | requirements + design | integration_tests |
| E9 | integration_tests → user_guide | [design, integration_tests] → user_guide | design | integration_tests |
| E10 | user_guide → uat_tests | [requirements, user_guide, integration_tests, bootloader] → uat_tests | requirements | user_guide, integration_tests, bootloader |

GTL already supports multi-source edges (`source: Asset | list[Asset]`). No engine changes needed.

**3. Bootloader as 11th asset**

```
bootloader
  ID: BOOT-{SEQ}
  Lineage: [requirements, design]
  Markov: [spec_hash_current, version_current, section_coverage_complete, references_valid]
  F_D: 4 evaluators (all computable without LLM)
  F_P: regenerate from source documents (8 fixed sections, ~150-200 lines)
  F_H: human approves synthesis
```

**4. Strengthened feature_decomp**

Feature decomp now produces structured artifacts:
- Per-feature YAML with: `depends_on`, `acceptance_surface`, `steel_thread_candidate`, `risk_score`, `effort`
- `build_schedule.json` with: `priority_strategy`, `mvp_boundary`, `critical_path`, ordered schedule
- 6 F_D validators (DAG acyclic, schedule respects deps, strategy recognized, etc.)

Priority strategies: `steel_thread`, `risk_first`, `dependency_first`, `value_first`, `walking_skeleton` — declared in INTENT.md, applied during decomposition, validated by F_D.

**5. Context model overhaul**

- `sdlc_bootloader` removed as edge context (it's an output, not an input)
- Added: `spec_requirements`, `spec_features`, `operating_standards`, `features_dir`
- Each edge gets only the contexts its evaluators actually need

**6. active-workflow.json**

Placement is an open territory decision (`.gsdlc/release/` vs `.ai-workspace/`). Does not block topology work.

**7. Resolved open questions**

- Size budget: ~150-200 lines
- GTL bootloader: ABG-owned independently
- Priority strategies: part of this redesign
- Bootloader generation: fixed structure, F_P-generated content

### Plan file updated

`fuzzy-fluttering-squid.md` updated with resolved questions, implementation phases, and pointer to the specification post.

---

## What's next

1. **Jim + Codex review the specification** at `20260323T040000_STRATEGY_graph-topology-redesign-specification.md`
2. **Approve or revise** the 7 decision points at the end of the document
3. **Phase 1: spec updates** — requirements.md, feature_decomposition.md (spec leads, code follows)
4. **Phase 2: graph code** — sdlc_graph.py module scope + instantiate()
5. **Phase 3: installer** — bootloader v0 generation
6. **Phase 4: verify** — clean install, gen-gaps

No code changes were made for the topology redesign. Spec leads, code follows.

---

## Parked items (not in this work stream)

- Root-level self-hosting reinstall (genesis_sdlc into itself)
- Engine support for schedule-aware feature traversal (ABG work)
- Graph variant profiles (ADR-012 — separate work)
- CI/CD integration
