# UAT Requirements

**Family**: REQ-F-UAT-*
**Status**: Still needed
**Category**: Verification

UAT requirements define the release-acceptance evidence surface and its human approval boundary.

### REQ-F-UAT-001 — Sandbox install + e2e proof required to ship

**Acceptance Criteria**:
- AC-1: The `[requirements, integration_tests]→uat_tests` edge requires sandbox evidence before approval — UAT accepts against requirements with sandbox proof
- AC-2: Unit tests alone are necessary but not sufficient — sandbox proof is the acceptance bar
- AC-3: Human cannot approve UAT without integration test report showing all_pass

### REQ-F-UAT-002 — integration_tests asset produces structured report

**Acceptance Criteria**:
- AC-1: `integration_tests` is an asset in the graph with edge `[code, unit_tests]→integration_tests` — code provides the install target, unit_tests provide the evidence gate
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
