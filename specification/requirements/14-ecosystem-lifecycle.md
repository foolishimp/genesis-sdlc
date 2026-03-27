# Ecosystem Lifecycle Requirements

**Family**: REQ-F-ECO-*
**Status**: Active
**Category**: Capability

This family defines the wider ecosystem lifecycle that the software development process belongs to.

The base process workflow is the 1.0 development lifecycle. The ecosystem lifecycle extends that workflow into release, operation, observation, and homeostatic return.

### REQ-F-ECO-001 — The software development process participates in a larger ecosystem lifecycle

The SDLC does not terminate at acceptance. It exists inside a wider homeostatic ecosystem with pre-intent incubation before the workflow and operational observation after it.

**Acceptance Criteria**:
- AC-1: The ecosystem lifecycle includes `creche`, the base process workflow, `publish`, `operational_env`, `monitoring`, and `homeostatic_eval`
- AC-2: The base process workflow remains the development-lifecycle core within that larger ecosystem
- AC-3: The wider ecosystem lifecycle is requirement truth for the framework, not merely implementation commentary

### REQ-F-ECO-002 — publish is distinct from acceptance

Acceptance and publication are different lifecycle boundaries. Approval proves readiness; publish makes the accepted artifact available for operational use.

**Acceptance Criteria**:
- AC-1: `publish` is a distinct post-acceptance stage in the ecosystem lifecycle
- AC-2: `publish` occurs after the accepted development workflow and before `operational_env`
- AC-3: Release, publish-version, install, deploy, or equivalent mechanisms are lawful design encodings of `publish`, not the requirement truth itself

### REQ-F-ECO-003 — monitoring and homeostatic evaluation close the loop

Operational observation must produce signals that can be evaluated and returned to the pre-intent holding area.

**Acceptance Criteria**:
- AC-1: `monitoring` is the operational observation stage for runtime behavior, install outcomes, incidents, drift, usage, or equivalent field signals
- AC-2: `homeostatic_eval` interprets those signals into actionable observations
- AC-3: The return path from `homeostatic_eval` leads to `creche` as the pre-intent holding area
- AC-4: Promoted items from that return path may later re-enter the normal renewal path as backlog items or intent vectors

### REQ-F-ECO-004 — automation mechanisms do not replace lifecycle stages

Automation mechanisms may encode parts of the ecosystem lifecycle, but they are not themselves the lifecycle ontology.

**Acceptance Criteria**:
- AC-1: `ci_cd` is not required as a constitutional lifecycle node
- AC-2: Installers, release tooling, deployment topology, telemetry stacks, and runtime infrastructure are design encodings of ecosystem stages rather than replacements for those stages
- AC-3: A conformant realization preserves the lifecycle meaning of `publish`, `operational_env`, `monitoring`, and `homeostatic_eval` regardless of the automation stack used
