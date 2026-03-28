# Assurance Requirements

**Family**: REQ-F-ASSURE-*
**Status**: Active
**Category**: Release Qualification

This family defines the dual-proof and qualification surfaces that let the framework answer what was built, whether it is complete, and what certified its correctness.

### REQ-F-ASSURE-001 — The workflow preserves dual provenance paths

The framework does not rely on one proof path to certify itself. It preserves separate but connected realization and acceptance paths.

**Acceptance Criteria**:
- AC-1: The design realization path runs through `design -> module_decomp -> code` and `design -> module_decomp -> unit_tests`
- AC-2: The requirements-facing acceptance path runs through `requirements -> integration_tests -> user_guide -> uat_tests`
- AC-3: `integration_tests` joins implementation evidence with requirements-facing behavior rather than acting as an isolated afterthought
- AC-4: The framework does not treat generated code as the sole authority for proving that the product is complete or correct

### REQ-F-ASSURE-002 — Qualification is bundled with the active build tenant

Assurance is part of the framework realization. It is not a detached demo harness.

**Acceptance Criteria**:
- AC-1: The active build tenant includes a qualification surface that exercises the installed workflow in a fresh sandbox
- AC-2: Qualification supports both fake-lane and live-lane execution over the same scenario identities
- AC-3: Qualification runs against the active framework surface rather than a parallel mock-only implementation
- AC-4: Persistent run archives are produced for postmortem and operator review
- AC-5: Once the assurance control plane exists, qualification consumes the same resolved runtime and backend adapter layer used by the live product path

### REQ-F-ASSURE-003 — Run archives answer the three operator questions

The archived qualification surface must make it possible to answer what was built, whether the required workflow converged fully, and what evidence certified correctness.

**Acceptance Criteria**:
- AC-1: A run archive preserves the produced artifacts plus the manifest/result material needed to show what was built
- AC-2: A run archive preserves convergence state, including edge-level gap status and final `total_delta`, so completeness can be answered directly
- AC-3: A run archive preserves deterministic findings, assessed events, human approvals, and integration/UAT evidence so correctness can be answered directly
- AC-4: The archive makes clear that assurance is downstream of the active intent and requirement surfaces and does not substitute for their truth
