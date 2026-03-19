# Changelog — genesis_sdlc (builds/python)

---

## v0.2.1 — 2026-03-20

**Bootloader**: v3.0.2
**Spec hash**: `9a96e8f7acb2118c`
**Test results**: 107 passed, 0 failed

### Added
- `instantiate(slug)` entry point in `sdlc_graph.py` — all slug-specific customisation (req_coverage command, sdlc_spec context locator) assembled inside the versioned release; Layer 3 becomes a two-line system-owned wrapper (REQ-F-VAR-001)
- `workflow_activated` event emitted on install — records previous version for provenance
- One-time provenance migration on upgrade from old workflow naming — re-emits fp_assessments with job_evaluator_hash and review_approved events with workflow_version

### Changed
- Workflow name: `genesis_sdlc` → `genesis_sdlc.standard` in `active-workflow.json`
- Immutable release path: `genesis_sdlc/v{V_U}/` → `genesis_sdlc/standard/v{V_U}/`
- Layer 3 generated wrapper: multi-line local overlay replaced with two-line `instantiate(slug)` call — rewritten on every redeploy, not written-once
- `guide_version_current` evaluator: fixed POSIX sh quoting bug (embedded `\"` caused exit code 2); now checks `**Version**: {ver}` field specifically
- `guide_req_coverage` evaluator: now checks for `<!-- Covers: REQ-F-* -->` blocks specifically, not any REQ-F-* token anywhere in the file

### Fixed
- USER_GUIDE.md version bumped to 0.2.1; §2 and §8 updated to describe generated wrapper model accurately
- `gtl_spec/packages/genesis_sdlc.py` docstring updated to reflect full 9-edge graph

**REQ keys added**: `REQ-F-VAR-001`

---

## v0.2.0 — 2026-03-19

**Bootloader**: v3.0.2
**Spec hash**: `566a3dcf6df16675`
**Test results**: 109 passed, 2 skipped, 0 failed

### Added
- `design→module_decomp→code` edges replace the former `design→code` edge — module decomposition now sits between design and code, mirroring the role feature_decomp plays between requirements and design (REQ-F-MDECOMP-001..005)
- `module_decomp` asset with markov conditions: `all_features_assigned`, `dependency_dag_acyclic`, `build_order_defined`
- `module_coverage` F_D evaluator — every design feature must be assigned to ≥1 module before code is written
- F_H gate at `design→module_decomp` — module build schedule approved before construction starts
- `.ai-workspace/modules/MOD-*.yml` artifacts — one per module, declares rank, dependencies, and `implements_features`
- `install_immutable_spec()` — copies released `sdlc_graph.py` into `{target}/.genesis/spec/genesis_sdlc.py` as immutable Layer 2 (REQ-F-BOOT-003)
- `BOOTLOADER_VERSION` constant in `install.py` — tracks deployed bootloader version
- `builds/python/CHANGELOG.md` — this file

### Changed
- Local project spec (`gtl_spec/packages/{slug}.py`) is never overwritten on reinstall — only the abiogenesis stub is replaced on first install; subsequent installs leave user customisations intact (REQ-F-BOOT-004/005)
- `--verify` now checks `immutable_spec` (`.genesis/spec/genesis_sdlc.py`)
- All F_D evaluator commands that invoke pytest or python now prepend `PYTHONPATH=builds/python/src/:.genesis` — tests always run against the RC source, not the installed package (REQ-F-TEST-003)
- Graph is now 8 assets, 7 edges, 7 jobs (was 7/6/6)
- `RELEASE.md` updated: Step 1b (bootloader check), Step 2b (CHANGELOG), `BOOTLOADER_VERSION` in files table, `spec_hash` in emit-event payload, standards edits now require a release

### Fixed
- `test_sdlc_graph.py`, `test_installer.py`, `test_e2e_sandbox.py` updated for new graph shape

**REQ keys added**: `REQ-F-MDECOMP-001`, `REQ-F-MDECOMP-002`, `REQ-F-MDECOMP-003`, `REQ-F-MDECOMP-004`, `REQ-F-MDECOMP-005`, `REQ-F-BOOT-003`, `REQ-F-BOOT-004`, `REQ-F-BOOT-005`, `REQ-F-TEST-003`

---

## v0.1.6 — prior release

See git log for history before CHANGELOG was introduced.
