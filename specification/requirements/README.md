# genesis_sdlc — Requirement Surface

**Status**: Active
**Purpose**: Authoritative index for the live requirement surface under `specification/requirements/`

The live requirement surface is stored as requirement families under this folder. Families are used here to keep the constitutional surface structured and non-monolithic.

## Families

| File | Family | Category | Status |
|------|--------|----------|--------|
| `01-bootstrap.md` | REQ-F-BOOT-* | Governance | Active |
| `02-graph.md` | REQ-F-GRAPH-* | Capability | Active |
| `03-commands.md` | REQ-F-CMD-* | Capability | Active |
| `04-human-gates.md` | REQ-F-GATE-* | Governance | Active |
| `05-traceability.md` | REQ-F-TAG-*, REQ-F-COV-* | Verification | Active |
| `06-documentation.md` | REQ-F-DOCS-* | Capability | Active |
| `07-testing.md` | REQ-F-TEST-* | Verification | Active |
| `08-uat.md` | REQ-F-UAT-* | Verification | Active |
| `09-backlog.md` | REQ-F-BACKLOG-* | Capability | Active |
| `10-module-decomposition.md` | REQ-F-MDECOMP-* | Capability | Active |
| `11-requirements-custody.md` | REQ-F-CUSTODY-* | Governance | Active |
| `12-territory-model.md` | REQ-F-TERRITORY-* | Constraint / Guarantee | Active |
| `13-bootloader-asset.md` | REQ-F-BOOTDOC-* | Verification | Active |
| `14-ecosystem-lifecycle.md` | REQ-F-ECO-* | Capability | Active |
| `15-mvp.md` | REQ-F-MVP-* | Release Qualification | Active |
| `16-assurance.md` | REQ-F-ASSURE-* | Release Qualification | Active |
| `17-control-plane.md` | REQ-F-CTRL-* | Runtime Control | Active |
| `18-workers.md` | REQ-F-WORKER-* | Runtime Control | Active |

## Notes

- The family files in this folder are the live constitutional requirement surface.
- REQ keys remain the traceability thread across design, code, tests, events, and evidence.
