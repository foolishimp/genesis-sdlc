# F_P Customization

This folder holds project-local F_P customization for bounded constructive turns.

## Purpose

- keep the installed release immutable
- tune F_P behavior for this specific project
- map customization intent back to project requirements and design

## Structure

- `INTENT.md` describes why the project is tuning F_P
- `edge-overrides/` contains machine-readable per-edge overrides

Use `.gsdlc/release/project-templates/design/fp/edge-overrides/EDGE_OVERRIDE_TEMPLATE.json` as the authoritative template shape for edge override files.
