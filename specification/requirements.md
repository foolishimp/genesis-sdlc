# genesis_sdlc — Requirements

**Derived from**: `gtl_spec/packages/genesis_sdlc.py` (the GTL Package IS the requirement registry)
**Traces to**: INT-001, INT-002, INT-003
**Status**: Approved
**Date**: 2026-03-20

These REQ keys are the traceability thread. Every design ADR, every code file, every test must tag back to these keys. The GTL Package in `genesis_sdlc.py` is the authoritative key registry — this document provides human-readable descriptions and acceptance criteria for each registered key.

---

## Bootstrap (REQ-F-BOOT-*)

### REQ-F-BOOT-001 — gen-install bootstraps .genesis/ into target project

The installer copies the genesis engine and methodology into a target project so it can run without an installed package.

**Acceptance Criteria**:
- AC-1: `install(target, source)` creates `.genesis/genesis/` with engine modules copied from the abiogenesis engine
- AC-2: Creates `.genesis/genesis.yml` pointing to `gtl_spec/packages/<slug>:package` and `gtl_spec/packages/<slug>:worker`
- AC-3: Creates `.ai-workspace/` directory structure (events/, features/active/, features/completed/, comments/, reviews/)
- AC-4: Installs operating standards from `specification/standards/` into `.ai-workspace/operating-standards/`
- AC-5: Installs command files from plugin sources into `.claude/commands/`
- AC-6: Generates `CLAUDE.md` from `gtl_spec/GENESIS_BOOTLOADER.md`
- AC-7: Idempotent — re-running updates engine files and standards, preserves workspace state and local specs
- AC-8: Emits `genesis_sdlc_installed` event on completion with version, spec_hash, and migration outcome

### REQ-F-BOOT-002 — .genesis/genesis.yml config resolves Package/Worker

The engine reads its Package and Worker from a config file at startup.

**Acceptance Criteria**:
- AC-1: `genesis.yml` contains `package:` and `worker:` fields as Python import paths (`module:var`)
- AC-2: Missing `genesis.yml` produces an informative error, not a crash
- AC-3: Engine resolves Package and Worker via `importlib` from the configured path

### REQ-F-BOOT-003 — Installer copies released spec into .genesis/spec/ as immutable layer

The three-layer install architecture separates immutable methodology spec from mutable project spec.

**Acceptance Criteria**:
- AC-1: `install()` copies `sdlc_graph.py` into `.genesis/spec/genesis_sdlc.py` as the frozen methodology layer
- AC-2: The installed spec is versioned: `.genesis/workflows/genesis_sdlc/standard/v{VERSION}/` contains the release snapshot
- AC-3: The frozen spec is never modified after install — it represents the methodology version that was installed

### REQ-F-BOOT-004 — Installer generates starter local spec in gtl_spec/packages/{slug}.py

Projects get a local spec that imports from the installed methodology and can be customised.

**Acceptance Criteria**:
- AC-1: If `gtl_spec/packages/{slug}.py` does not exist, installer generates a starter file that imports the standard Package
- AC-2: If the file already exists, installer never overwrites it — local spec is project-owned
- AC-3: Generated starter is a minimal wrapper that can be extended with project-specific edges and evaluators

### REQ-F-BOOT-005 — Reinstall replaces .genesis/spec/ atomically; never overwrites local gtl_spec/

Upgrade safety: the methodology layer is replaceable, the project layer is sacred.

**Acceptance Criteria**:
- AC-1: `install()` replaces `.genesis/spec/` and `.genesis/workflows/` atomically on reinstall
- AC-2: `gtl_spec/packages/{slug}.py` is never overwritten if it exists
- AC-3: One-time provenance migration runs on upgrade: re-emits old events with new schema and workflow version

---

## SDLC Graph (REQ-F-GRAPH-*)

### REQ-F-GRAPH-001 — GTL Package defines the SDLC graph

The Package declares a typed asset graph with admissible transitions.

**Acceptance Criteria**:
- AC-1: Ten assets: `intent`, `requirements`, `feature_decomp`, `design`, `module_decomp`, `code`, `unit_tests`, `integration_tests`, `user_guide`, `uat_tests`
- AC-2: Nine edges with the topology: `intent→requirements→feature_decomp→design→module_decomp→code↔unit_tests→integration_tests→user_guide→uat_tests`
- AC-3: Each edge has at least one evaluator
- AC-4: The `code↔unit_tests` edge is co-evolving (`co_evolve=True`)
- AC-5: Package is loadable: `python gtl_spec/packages/genesis_sdlc.py` produces valid JSON describing the graph

### REQ-F-GRAPH-002 — Asset.markov conditions are acceptance criteria

Each asset type defines its own stability conditions.

**Acceptance Criteria**:
- AC-1: Every `Asset` in the Package has a non-empty `markov` list of named conditions
- AC-2: Markov conditions are surfaced in the F_P manifest as part of the output contract
- AC-3: An asset is stable when all markov conditions are met and all edge evaluators pass

---

## Commands (REQ-F-CMD-*)

### REQ-F-CMD-001 — gen gaps reports delta per edge

`gen-gaps` computes the convergence state of the workspace by running evaluators over all jobs.

**Acceptance Criteria**:
- AC-1: Returns JSON with `total_delta`, `converged`, and per-job `gaps[]`
- AC-2: Each gap entry contains: `edge`, `delta`, `failing` (evaluator names), `passing`, `delta_summary`
- AC-3: Runs all F_D evaluators as subprocesses; evaluates F_H via event stream projection; evaluates F_P via assessed event matching with spec_hash validation
- AC-4: `converged: true` iff `total_delta == 0`

### REQ-F-CMD-002 — gen iterate runs one bind-and-iterate pass

`gen-iterate` selects the first unconverged job and executes one F_D→F_P→F_H cycle.

**Acceptance Criteria**:
- AC-1: Selects first unconverged job in topological edge order
- AC-2: Calls `bind_fd()` to pre-compute all F_D results, F_H gates, and F_P assessments
- AC-3: Enforces F_D→F_P→F_H ordering — no F_P dispatch while F_D failing, no F_H gate while F_P unresolved
- AC-4: On F_D failure: reports failing evaluator details, exits code 4
- AC-5: On F_P needed: writes manifest to `.ai-workspace/fp_manifests/`, exits code 2
- AC-6: On F_H needed: reports evaluator criteria, exits code 3
- AC-7: On convergence: exits code 0

### REQ-F-CMD-003 — gen start --auto loops until blocked

`gen-start` is the state-machine entry point that loops `gen-iterate` until convergence or a blocking condition.

**Acceptance Criteria**:
- AC-1: Determines workspace convergence state before iterating
- AC-2: If converged: closes completed features, exits code 0
- AC-3: If not converged: dispatches `gen-iterate` for the next job
- AC-4: `--auto` loops up to MAX_AUTO (50) iterations, stopping on: convergence, `fp_dispatched`, `fh_gate_pending`, `fd_gap`, or max iterations
- AC-5: `--human-proxy` requires `--auto`; performs F_H evaluation per proxy protocol
- AC-6: Exit codes: 0 (converged), 2 (fp_dispatched), 3 (fh_gate_pending), 4 (fd_gap), 5 (max_iterations)

---

## Human Gates (REQ-F-GATE-*)

### REQ-F-GATE-001 — F_H evaluators gate spec/design boundaries

Human approval is required at spec and design boundaries before downstream work proceeds.

**Acceptance Criteria**:
- AC-1: F_H evaluators detected at bind time by projecting the event stream for `approved{kind: fh_review}` events
- AC-2: If no operative approval exists for the current edge, the evaluator is in the `failing` set
- AC-3: `iterate()` emits `fh_gate_pending` with evaluator criteria and exits code 3
- AC-4: F_H gate criteria surfaced verbatim from `Evaluator.description`
- AC-5: `actor` field mandatory on all `approved` events: `"human"` or `"human-proxy"` — never absent
- AC-6: The ordering invariant (F_D→F_P→F_H) prevents reviewing candidates with deterministic failures

---

## Traceability (REQ-F-TAG-*, REQ-F-COV-*)

### REQ-F-TAG-001 — Implements: tags enforced on all source files

Every source file must trace to at least one REQ key.

**Acceptance Criteria**:
- AC-1: `check-tags --type implements --path <src/>` scans for `# Implements: REQ-*` comments
- AC-2: Exit 0 if every `.py` file (excluding `__init__.py`) has at least one tag; exit 1 otherwise
- AC-3: Output lists files with their tag status

### REQ-F-TAG-002 — Validates: tags enforced on all test files

Every test file must trace to at least one REQ key.

**Acceptance Criteria**:
- AC-1: `check-tags --type validates --path <tests/>` scans for `# Validates: REQ-*` comments
- AC-2: Exit 0 if every test file has at least one tag; exit 1 otherwise

### REQ-F-COV-001 — REQ key coverage enforced by check-req-coverage

Every REQ key in the Package must appear in at least one feature vector.

**Acceptance Criteria**:
- AC-1: `check-req-coverage --package <pkg:var> --features <dir/>` loads Package.requirements and scans YAML `satisfies:` lists
- AC-2: Exit 0 if every REQ key appears in at least one feature vector; exit 1 with gap list otherwise
- AC-3: Coverage computable without LLM invocation — pure F_D check

---

## Documentation (REQ-F-DOCS-*)

### REQ-F-DOCS-001 — User guide covers install, first session, operating loop

**Acceptance Criteria**:
- AC-1: `docs/USER_GUIDE.md` exists with sections: Installation, First Session, Operating Loop
- AC-2: Covers all core commands: `gen-start`, `gen-iterate`, `gen-gaps`
- AC-3: Documents evaluator types (F_D, F_P, F_H), event stream, and delta semantics
- AC-4: Documents recovery paths for each stop reason (fd_gap, fp_dispatched, fh_gate_pending)

### REQ-F-DOCS-002 — user_guide is a blocking graph asset

The user guide is on the convergence blocking path with F_D enforcement.

**Acceptance Criteria**:
- AC-1: `user_guide` is an asset in the SDLC graph with edge `integration_tests→user_guide`
- AC-2: F_D evaluator `guide_version_current` checks version string in USER_GUIDE.md matches install.py VERSION
- AC-3: F_D evaluator `guide_req_coverage` checks `REQ-F-*` tags are present in USER_GUIDE.md
- AC-4: F_P evaluator `guide_content_certified` assesses install steps, commands, operating loop, recovery paths
- AC-5: No release ships without the user guide passing all three evaluators

---

## Testing (REQ-F-TEST-*)

### REQ-F-TEST-001 — Integration and E2E tests are the primary test surface

**Acceptance Criteria**:
- AC-1: At least one `@pytest.mark.e2e` test exists — enforced by `e2e_tests_exist` F_D evaluator
- AC-2: E2E tests exercise the full install→evaluate→converge cycle against a real sandbox
- AC-3: Unit tests are supplementary — acceptable only for write-primitive invariants (emit, project, EventStream)

### REQ-F-TEST-002 — coverage_complete F_P evaluates integration coverage

**Acceptance Criteria**:
- AC-1: The `coverage_complete` F_P evaluator assesses whether the test suite covers all REQ keys with integration or E2E scenarios
- AC-2: Pure unit tests mocking internals do not satisfy coverage for workflow features
- AC-3: Assessment is against REQ key traceability, not line coverage metrics

### REQ-F-TEST-003 — Test evaluator commands pin PYTHONPATH

Version sandboxing ensures tests run against the release candidate source, not stale installed copies.

**Acceptance Criteria**:
- AC-1: All F_D evaluator `command:` fields that invoke pytest use `PYTHONPATH=builds/python/src/:.genesis`
- AC-2: This ensures tests import from the build source tree, not from any system-installed package
- AC-3: F_D evaluator acyclicity is preserved — test commands never invoke genesis subcommands

---

## UAT (REQ-F-UAT-*)

### REQ-F-UAT-001 — Sandbox install + e2e proof required to ship

**Acceptance Criteria**:
- AC-1: The `unit_tests→uat_tests` edge (now `unit_tests→integration_tests`) requires sandbox evidence before approval
- AC-2: Unit tests alone are necessary but not sufficient — sandbox proof is the acceptance bar
- AC-3: Human cannot approve UAT without integration test report showing all_pass

### REQ-F-UAT-002 — integration_tests asset produces structured report

**Acceptance Criteria**:
- AC-1: `integration_tests` is an asset in the graph with edge `unit_tests→integration_tests`
- AC-2: F_P evaluator `sandbox_e2e_passed` installs into a fresh sandbox and runs `pytest -m e2e`
- AC-3: F_P writes structured report to `.ai-workspace/uat/sandbox_report.json` with fields: `install_success`, `sandbox_path`, `test_count`, `pass_count`, `fail_count`, `all_pass`, `timestamp`
- AC-4: F_D evaluator `sandbox_report_exists` checks the report exists and `all_pass: true`
- AC-5: Convergence is deterministic — no human judgment required for this edge

### REQ-F-UAT-003 — uat_tests simplified to pure F_H gate

**Acceptance Criteria**:
- AC-1: `uat_tests` asset has a single F_H evaluator: `uat_accepted`
- AC-2: Human reviews: (1) sandbox_report.json shows all_pass, (2) USER_GUIDE.md is coherent and version-current, (3) every operator-facing feature is documented
- AC-3: No release ships without human approval at this gate
- AC-4: `--human-proxy` may proxy this gate only if the sandbox report is available and all e2e scenarios pass

---

## Backlog (REQ-F-BACKLOG-*)

### REQ-F-BACKLOG-001 — Backlog schema and directory convention

**Acceptance Criteria**:
- AC-1: `.ai-workspace/backlog/BL-*.yml` files follow a defined YAML schema with fields: `id`, `title`, `description`, `status`, `priority`, `created`, `signal_source`
- AC-2: Status values: `draft`, `ready`, `promoted`, `deferred`
- AC-3: Directory is created by the installer as part of workspace bootstrap

### REQ-F-BACKLOG-002 — Sensory system surfaces ready items

**Acceptance Criteria**:
- AC-1: `gen-gaps` and `gen-status` output includes a count of ready backlog items
- AC-2: Ready items are those with `status: ready`
- AC-3: The backlog serves as the pre-intent holding area — ideas in gestation before formal intent

### REQ-F-BACKLOG-003 — gen backlog list

**Acceptance Criteria**:
- AC-1: `gen backlog list` shows all backlog items with id, title, status, and priority
- AC-2: Output is human-readable with optional `--json` for machine consumption

### REQ-F-BACKLOG-004 — gen backlog promote

**Acceptance Criteria**:
- AC-1: `gen backlog promote BL-xxx` emits an `intent_raised` event with `signal_source: backlog`
- AC-2: Marks the backlog item as `status: promoted`
- AC-3: The promoted item enters the normal homeostatic loop

---

## Module Decomposition (REQ-F-MDECOMP-*)

### REQ-F-MDECOMP-001 — design→module_decomp edge

**Acceptance Criteria**:
- AC-1: `design→module_decomp` edge exists in the Package with F_D, F_P, and F_H evaluators
- AC-2: F_P evaluator (`module_schedule`) decomposes design ADRs into modules
- AC-3: Output: one `.yml` per module in `.ai-workspace/modules/` with fields: `id`, `name`, `description`, `implements_features`, `dependencies`, `rank`, `interfaces`, `source_files`

### REQ-F-MDECOMP-002 — Module dependency DAG is acyclic with defined build order

**Acceptance Criteria**:
- AC-1: Module `dependencies` fields form an acyclic directed graph
- AC-2: `rank` field defines build order: rank=1 modules have no dependencies (leaves), higher ranks depend on lower
- AC-3: Build order is leaf-to-root — each module is built against stable interfaces from already-built dependencies

### REQ-F-MDECOMP-003 — module_coverage F_D evaluator

**Acceptance Criteria**:
- AC-1: F_D evaluator `module_coverage` checks every feature vector stem appears in at least one module YAML
- AC-2: Exit 0 if all features assigned; exit 1 with uncovered list
- AC-3: Pure F_D check — no LLM invocation

### REQ-F-MDECOMP-004 — F_H gate: module schedule approved before code

**Acceptance Criteria**:
- AC-1: F_H evaluator `schedule_approved` gates the `design→module_decomp` edge
- AC-2: Human confirms: module boundaries are clean, dependency DAG is acyclic, build order is sensible, every feature is assigned
- AC-3: No code is written until the module schedule is approved

### REQ-F-MDECOMP-005 — module_decomp→code replaces design→code

**Acceptance Criteria**:
- AC-1: The Package has no direct `design→code` edge
- AC-2: Code construction proceeds from `module_decomp→code` — the module schedule is the input constraint for code, not design directly
- AC-3: `module_decomp→code` evaluators include `impl_tags` (F_D) and `code_complete` (F_P)

---

## Key Counts

| Category | REQ Keys |
|----------|----------|
| Bootstrap | REQ-F-BOOT-001 through 005 (5) |
| SDLC Graph | REQ-F-GRAPH-001, 002 (2) |
| Commands | REQ-F-CMD-001 through 003 (3) |
| Human Gates | REQ-F-GATE-001 (1) |
| Traceability | REQ-F-TAG-001, 002, REQ-F-COV-001 (3) |
| Documentation | REQ-F-DOCS-001, 002 (2) |
| Testing | REQ-F-TEST-001 through 003 (3) |
| UAT | REQ-F-UAT-001 through 003 (3) |
| Backlog | REQ-F-BACKLOG-001 through 004 (4) |
| Module Decomposition | REQ-F-MDECOMP-001 through 005 (5) |
| **Total** | **31 keys** |
