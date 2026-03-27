# genesis_sdlc — Requirements

**Status**: Superseded as monolithic requirement surface
**Live requirement surface**: `specification/requirements/`
**Purpose**: Migration index and compatibility landing document

The detailed requirement content for genesis_sdlc now lives under `specification/requirements/` as requirement families.

This file remains only as:

- a stable landing path during migration
- an index to the live family files
- a declaration that the monolithic requirement surface is no longer authoritative

## Requirement Families

| File | Family | Category | Status |
|------|--------|----------|--------|
| `requirements/01-bootstrap.md` | REQ-F-BOOT-* | Governance | Still needed |
| `requirements/02-graph.md` | REQ-F-GRAPH-* | Capability | Still needed |
| `requirements/03-commands.md` | REQ-F-CMD-* | Capability | Still needed |
| `requirements/04-human-gates.md` | REQ-F-GATE-* | Governance | Still needed |
| `requirements/05-traceability.md` | REQ-F-TAG-*, REQ-F-COV-* | Verification | Still needed |
| `requirements/06-documentation.md` | REQ-F-DOCS-* | Capability | Still needed |
| `requirements/07-testing.md` | REQ-F-TEST-* | Verification | Still needed |
| `requirements/08-uat.md` | REQ-F-UAT-* | Verification | Still needed |
| `requirements/09-backlog.md` | REQ-F-BACKLOG-* | Capability | Still needed |
| `requirements/10-module-decomposition.md` | REQ-F-MDECOMP-* | Capability | Still needed |
| `requirements/11-requirements-custody.md` | REQ-F-CUSTODY-* | Governance | Still needed |
| `requirements/12-territory-model.md` | REQ-F-TERRITORY-* | Constraint / Guarantee | Still needed |
| `requirements/13-bootloader-asset.md` | REQ-F-BOOTDOC-* | Verification | Still needed |

## Authority

- `specification/requirements/` is the sole live constitutional requirement surface.
- This file is not co-equal authority with the family files.
- The previous monolithic content is preserved in version control history; ongoing repricing happens in the family files.
