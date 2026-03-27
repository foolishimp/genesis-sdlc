# genesis_sdlc — Requirement Surface

**Status**: Still needed
**Purpose**: Authoritative index for the live requirement surface under `specification/requirements/`
**Source**: Decomposed from the prior monolithic `specification/requirements.md`

The live requirement surface is stored as requirement families under this folder. Families are used here to keep the constitutional surface structured and non-monolithic.

## Families

| File | Family | Category | Status |
|------|--------|----------|--------|
| `01-bootstrap.md` | REQ-F-BOOT-* | Governance | Still needed |
| `02-graph.md` | REQ-F-GRAPH-* | Capability | Still needed |
| `03-commands.md` | REQ-F-CMD-* | Capability | Still needed |
| `04-human-gates.md` | REQ-F-GATE-* | Governance | Still needed |
| `05-traceability.md` | REQ-F-TAG-*, REQ-F-COV-* | Verification | Still needed |
| `06-documentation.md` | REQ-F-DOCS-* | Capability | Still needed |
| `07-testing.md` | REQ-F-TEST-* | Verification | Still needed |
| `08-uat.md` | REQ-F-UAT-* | Verification | Still needed |
| `09-backlog.md` | REQ-F-BACKLOG-* | Capability | Still needed |
| `10-module-decomposition.md` | REQ-F-MDECOMP-* | Capability | Still needed |
| `11-requirements-custody.md` | REQ-F-CUSTODY-* | Governance | Still needed |
| `12-territory-model.md` | REQ-F-TERRITORY-* | Constraint / Guarantee | Still needed |
| `13-bootloader-asset.md` | REQ-F-BOOTDOC-* | Verification | Still needed |

## Notes

- `specification/requirements/` is the live constitutional requirement surface.
- The prior top-level `specification/requirements.md` no longer carries the detailed requirement content.
- REQ keys remain the traceability thread across design, code, tests, events, and evidence.
