# SDLC Bootloader

Version: 1.0rc1
Spec-Hash: sha256:64a04751fe963891247e6223974a49e6a4f5874794b1c240c66a31b8439081f0

## Authority

- This carrier orients the agent to the installed genesis_sdlc release.
- ABG owns engine execution. genesis_sdlc owns the domain workflow and evidence surface.
- Read the referenced source documents for depth; this bootloader is a compiled orientation surface.

## Axioms

- Specification defines the what.
- Design defines the how.
- Evaluate and close gaps before claiming convergence.
- F_D proves deterministic currency. F_P performs bounded construction. F_H approves release-critical gates.

## Active Docs

- workspace://specification/INTENT.md
- workspace://build_tenants/TENANT_REGISTRY.md
- workspace://.gsdlc/release/operating-standards/SPEC_METHOD.md
- workspace://.gsdlc/release/operating-standards/GSDLC_METHOD.md
- workspace://.gsdlc/release/design/README.md
- workspace://.gsdlc/release/design/module_decomp.md
- workspace://specification/requirements/01-bootstrap.md
- workspace://specification/requirements/02-graph.md
- workspace://specification/requirements/03-commands.md
- workspace://specification/requirements/04-human-gates.md
- workspace://specification/requirements/05-traceability.md
- workspace://specification/requirements/06-documentation.md
- workspace://specification/requirements/07-testing.md
- workspace://specification/requirements/08-uat.md
- workspace://specification/requirements/09-backlog.md
- workspace://specification/requirements/10-module-decomposition.md
- workspace://specification/requirements/11-requirements-custody.md
- workspace://specification/requirements/12-territory-model.md
- workspace://specification/requirements/13-bootloader-asset.md
- workspace://specification/requirements/14-ecosystem-lifecycle.md
- workspace://specification/requirements/15-mvp.md
- workspace://specification/requirements/16-assurance.md
- workspace://specification/requirements/17-control-plane.md
- workspace://specification/requirements/18-workers.md

## Commands

- `PYTHONPATH=.gsdlc/release:.genesis python -m genesis gaps --workspace .`
- `PYTHONPATH=.gsdlc/release:.genesis python -m genesis iterate --workspace .`
- `PYTHONPATH=.gsdlc/release:.genesis python -m genesis start --workspace .`
- Use `genesis gaps` when drift is suspected, `genesis iterate` for the next blocking edge, and `genesis start` for the next executable job.
