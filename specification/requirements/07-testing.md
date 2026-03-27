# Testing Requirements

**Family**: REQ-F-TEST-*
**Status**: Active
**Category**: Verification

Testing requirements define the primary evidence surface for proving workflow behavior.

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
