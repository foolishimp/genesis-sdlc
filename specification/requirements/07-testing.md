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
- AC-1: All F_D evaluator `command:` fields that invoke pytest pin `PYTHONPATH` to the active build-tenant source root plus `.genesis`
- AC-2: This ensures tests import from the active authoring source tree, not from any system-installed package
- AC-3: F_D evaluator acyclicity is preserved — test commands never invoke genesis subcommands

### REQ-F-TEST-004 — Sandbox-backed e2e scenarios preserve persistent run archives

Fresh sandbox execution is scratch space. Postmortem requires a durable run record.

**Acceptance Criteria**:
- AC-1: Every sandbox-backed e2e scenario supports a persistent run archive under a stable, non-temporary `test_runs/` root
- AC-2: Archive paths are scenario-oriented and encode at minimum use-case identity plus sortable run timestamp
- AC-3: Each archived run preserves the full sandbox workspace needed for replay-free postmortem
- AC-4: Each archived run preserves operator-facing run metadata and summary artifacts, including subprocess logs, convergence summary, outcome classification, and worker/backend provenance
- AC-5: Archive materialization occurs before fixture teardown or sandbox cleanup
- AC-6: Archived runs are immutable and non-overwriting; a later run does not destroy a prior archive

### REQ-F-TEST-005 — Scenario qualification supports fake-lane and live-lane parity

Workflow scenarios that depend on F_P closure or transport-sensitive behavior require both law-proof and real-agent proof.

**Acceptance Criteria**:
- AC-1: Scenario-oriented workflow tests distinguish fake-lane and live-lane qualification where F_P dispatch or transport-sensitive behavior is part of the scenario
- AC-2: The fake lane proves workflow law over the scenario boundary without depending on live model quality or transport success
- AC-3: The live lane proves the same scenario boundary through real agent execution over the declared F_P dispatch surface
- AC-4: Live-lane execution is explicit and gated by a dedicated test switch or marker; it does not run accidentally in the default fast lane
- AC-5: Fake and live lanes preserve the same scenario identity so postmortem can compare them as two realizations of one test contract
- AC-6: Once the control-plane compile and backend adapter layer exist, live qualification executes through that same resolved runtime and adapter layer rather than a parallel hardcoded transport path
