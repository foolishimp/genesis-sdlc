# Documentation Requirements

**Family**: REQ-F-DOCS-*
**Status**: Active
**Category**: Capability

Documentation requirements define the operator-facing guide surface and its place on the convergence path.

### REQ-F-DOCS-001 — User guide covers install, first session, operating loop

**Acceptance Criteria**:
- AC-1: `docs/USER_GUIDE.md` exists with sections: Installation, First Session, Operating Loop
- AC-2: Covers all core commands: `gen-start`, `gen-iterate`, `gen-gaps`
- AC-3: Documents evaluator types (F_D, F_P, F_H), event stream, and delta semantics
- AC-4: Documents recovery paths for each stop reason (fd_gap, fp_dispatched, fh_gate_pending)

### REQ-F-DOCS-002 — user_guide is a blocking graph asset

The user guide is on the convergence blocking path with F_D enforcement.

**Acceptance Criteria**:
- AC-1: `user_guide` is an asset in the SDLC graph with edge `[design, integration_tests]→user_guide` — lineage from design, evidence gate from integration_tests
- AC-2: F_D evaluator `guide_version_current` checks version string in USER_GUIDE.md matches install.py VERSION
- AC-3: F_D evaluator `guide_req_coverage` checks `REQ-F-*` tags are present in USER_GUIDE.md
- AC-4: F_P evaluator `guide_content_certified` assesses install steps, commands, operating loop, recovery paths
- AC-5: No release ships without the user guide passing all three evaluators
