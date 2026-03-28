# MVP Requirements

**Family**: REQ-F-MVP-*
**Status**: Active
**Category**: Release Qualification

This family defines the 1.0 MVP boundary and the operational proof required to claim it.

### REQ-F-MVP-001 — MVP freezes the 1.0 base workflow

The MVP boundary is the current base software-development workflow. It is a scope freeze, not an invitation to keep adding adjacent lifecycle features before the current workflow is operational.

**Acceptance Criteria**:
- AC-1: The MVP scope is the 1.0 base workflow from `intent` through `uat_tests`
- AC-2: `publish`, `operational_env`, `monitoring`, and `homeostatic_eval` remain valid lifecycle truth but are not required to close the MVP boundary
- AC-3: `backlog_homeostasis` is not required for MVP closure

### REQ-F-MVP-002 — MVP is operational rather than merely declarative

The framework does not satisfy MVP by describing the workflow alone. It satisfies MVP only when the frozen workflow can be installed and exercised end-to-end.

**Acceptance Criteria**:
- AC-1: The active build tenant installs into a fresh sandbox and exposes the active workflow without manual repair
- AC-2: A minimal project specification can traverse the workflow from `intent` through `uat_tests`
- AC-3: All base-workflow edges required for that scenario can converge within the installed sandbox
- AC-4: The operational proof is derived from the active framework surface rather than a parallel demo-only harness

### REQ-F-MVP-003 — MVP qualification includes fake-lane and live-lane proof

The frozen workflow must be provable both as workflow law and as real agent-driven execution.

**Acceptance Criteria**:
- AC-1: The MVP workflow has a fake-lane qualification that proves the end-to-end workflow boundary deterministically
- AC-2: The MVP workflow has a live-lane qualification that proves that same end-to-end boundary through real F_P execution
- AC-3: Fake and live qualification preserve a shared scenario identity so their runs can be compared postmortem
- AC-4: Successful MVP qualification yields a converged end state for the base workflow with `total_delta: 0`
- AC-5: Once the assurance control plane exists, MVP live qualification runs through the resolved runtime and backend adapter path rather than a legacy runtime branch
